import { useState, useCallback } from 'react'
import { ChatMessage, StreamResponse, DocumentSource } from '../types/chat'
import { useLocalStorage } from './useLocalStorage'

export function useChat() {
  const [messages, setMessages] = useLocalStorage<ChatMessage[]>('chat-messages', [])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sendMessage = useCallback(async (question: string) => {
    if (!question.trim() || isLoading) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: question.trim(),
      timestamp: new Date()
    }

    // Add user message immediately
    setMessages(prev => [...prev.slice(-19), userMessage])
    setIsLoading(true)
    setError(null)

    // Create placeholder assistant message
    const assistantMessageId = (Date.now() + 1).toString()
    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true
    }

    setMessages(prev => [...prev, assistantMessage])

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question }),
      })

      if (!response.ok) {
        throw new Error('Network response was not ok')
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let accumulatedContent = ''

      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value)
          const lines = chunk.split('\n')

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data: StreamResponse = JSON.parse(line.slice(6))
                
                if (data.token) {
                  accumulatedContent += data.token
                  setMessages(prev => prev.map(msg => 
                    msg.id === assistantMessageId 
                      ? { ...msg, content: accumulatedContent }
                      : msg
                  ))
                }

                if (data.done) {
                  setMessages(prev => prev.map(msg => 
                    msg.id === assistantMessageId 
                      ? { 
                          ...msg, 
                          content: data.answer || accumulatedContent,
                          sources: data.sources,
                          isStreaming: false
                        }
                      : msg
                  ))
                  break
                }
              } catch (parseError) {
                console.error('Error parsing SSE data:', parseError)
              }
            }
          }
        }
      }
    } catch (err) {
      setError('Connection error – retry?')
      setMessages(prev => prev.filter(msg => msg.id !== assistantMessageId))
    } finally {
      setIsLoading(false)
    }
  }, [isLoading, setMessages])

  const clearMessages = useCallback(() => {
    setMessages([])
  }, [setMessages])

  const retryLastMessage = useCallback(() => {
    const lastUserMessage = messages.filter(m => m.role === 'user').pop()
    if (lastUserMessage) {
      sendMessage(lastUserMessage.content)
    }
  }, [messages, sendMessage])

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearMessages,
    retryLastMessage
  }
} 