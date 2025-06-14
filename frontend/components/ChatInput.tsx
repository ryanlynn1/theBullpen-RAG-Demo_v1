import React, { useState, useRef, useEffect } from 'react'

interface ChatInputProps {
  onSendMessage: (message: string) => void
  disabled?: boolean
  isLoading?: boolean
  onStopGeneration?: () => void
  variant?: 'light' | 'dark'
}

const ChatInput: React.FC<ChatInputProps> = ({ 
  onSendMessage, 
  disabled = false, 
  isLoading = false,
  onStopGeneration,
  variant = 'light'
}) => {
  const [message, setMessage] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (message.trim() && !disabled && !isLoading) {
      onSendMessage(message.trim())
      setMessage('')
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value)
    
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`
    }
  }

  useEffect(() => {
    if (textareaRef.current && !isLoading) {
      textareaRef.current.focus()
    }
  }, [isLoading])

  const textareaClass = variant === 'light'
    ? 'bg-white border-gray-300 text-black'
    : 'bg-white border-gray-500 text-black placeholder-gray-400';

  return (
    <form onSubmit={handleSubmit} className="flex items-start space-x-3">
      <div className="flex-1 relative">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder={disabled ? "Connecting to backend..." : "Ask the Bullpen..."}
          disabled={disabled}
          className={`w-full px-4 py-3 pr-12 border rounded-xl resize-none focus:ring-2 focus:ring-bullpen-green focus:border-transparent transition-all duration-200 ${
            disabled ? 'bg-gray-100 text-gray-500' : textareaClass
          }`}
          style={{ minHeight: '48px', maxHeight: '120px' }}
          rows={1}
        />
      </div>

      {/* Send/Stop Button */}
      {isLoading ? (
        <button
          type="button"
          onClick={onStopGeneration}
          className="flex-shrink-0 w-12 h-12 bg-red-500 hover:bg-red-600 text-white rounded-xl transition-colors duration-200 flex items-center justify-center mt-0"
          title="Stop generation"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 6h12v12H6z" />
          </svg>
        </button>
      ) : (
        <button
          type="submit"
          disabled={!message.trim() || disabled}
          className={`flex-shrink-0 w-12 h-12 rounded-xl transition-all duration-200 flex items-center justify-center mt-0 ${
            message.trim() && !disabled
              ? 'bg-bullpen-green hover:opacity-90 text-white shadow-lg hover:shadow-xl transform hover:scale-105'
              : 'bg-black text-gray-400 cursor-not-allowed'
          }`}
          title="Send message (Enter)"
        >
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
          </svg>
        </button>
      )}
    </form>
  )
}

export default ChatInput 