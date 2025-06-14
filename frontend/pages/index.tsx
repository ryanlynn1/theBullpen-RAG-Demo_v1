import Head from 'next/head'
import React, { useState, useRef, useEffect } from 'react';
import ChatContainer from '../components/ChatContainer'
import Sidebar from '../components/Sidebar'
import BullpenLogo from '../components/ui/BullpenLogo';
import BullpenIcon from '../components/ui/BullpenIcon';
import { useChatHistory } from '../hooks/useChatHistory';
import { ChatMessage as ChatMessageType } from '../types/chat';

export default function Home() {
  const { messages, addMessage, clearHistory } = useChatHistory();
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('disconnected');
  const abortControllerRef = useRef<AbortController | null>(null);

  // Check backend connection on mount
  useEffect(() => {
    checkConnection();
  }, []);

  const checkConnection = async () => {
    setConnectionStatus('connecting');
    try {
      const response = await fetch('/api/health');
      if (response.ok) {
        setConnectionStatus('connected');
        setError(null);
      } else {
        setConnectionStatus('disconnected');
        setError('Backend service is not responding properly');
      }
    } catch (err) {
      setConnectionStatus('disconnected');
      setError('Cannot connect to backend. Please ensure the server is running.');
    }
  };

  const handleSendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return;

    setError(null);
    setIsLoading(true);
    setIsTyping(true);
    setStatusMessage("Confirming receipt, working on it now."); // Set initial status

    const userMessage: ChatMessageType = {
      id: Date.now().toString(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    };
    addMessage(userMessage);

    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: content.trim(),
          conversation_history: messages.slice(-6).map((msg: ChatMessageType) => ({
            role: msg.role,
            content: msg.content
          }))
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      let assistantMessage: ChatMessageType = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        sources: [],
      };

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              setIsTyping(false);
              setStatusMessage(null);
              break;
            }
            try {
              const parsed = JSON.parse(data);
              if (parsed.sources) {
                assistantMessage.sources = parsed.sources;
              } else if (parsed.token) {
                assistantMessage.content += parsed.token;
              } else if (parsed.status) {
                // Handle status updates
                setStatusMessage(parsed.status);
              } else if (parsed.done) {
                setIsTyping(false);
                setStatusMessage(null);
                break;
              }
              addMessage({ ...assistantMessage });
            } catch (e) {
              console.warn('Failed to parse SSE data:', data);
            }
          }
        }
      }
      if (assistantMessage.content) addMessage({ ...assistantMessage });
    } catch (err: any) {
      if (err.name === 'AbortError') return console.log('Request aborted');
      const errorMessage = err.message || 'An unexpected error occurred';
      setError(errorMessage);
      addMessage({
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `❌ Error: ${errorMessage}`,
        timestamp: new Date(),
      });
    } finally {
      setIsLoading(false);
      setIsTyping(false);
      setStatusMessage(null);
      abortControllerRef.current = null;
    }
  };

  const handleStopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsLoading(false);
      setIsTyping(false);
    }
  };

  const handleClearChat = () => {
    if (window.confirm('Are you sure you want to clear the chat history?')) {
      clearHistory();
      setError(null);
    }
  };

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'text-bullpen-green bg-green-50';
      case 'connecting': return 'text-yellow-600 bg-yellow-50';
      case 'disconnected': return 'text-red-600 bg-red-50';
    }
  };
  
  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case 'connected': return 'Connected';
      case 'connecting': return 'Connecting...';
      case 'disconnected': return 'Disconnected';
    }
  };

  return (
    <>
      <Head>
        <title>Bullpen AI - Financial Document Analysis</title>
        <meta name="description" content="AI-powered financial document analysis and chat assistant by the Bullpen" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="alternate icon" href="/favicon.ico" />
      </Head>
      <div className="flex flex-col h-screen">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <BullpenIcon width={40} height={38} className="text-bullpen-charcoal" />
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getConnectionStatusColor()}`}>
                  <div className={`w-2 h-2 rounded-full mr-2 ${
                    connectionStatus === 'connected' ? 'bg-bullpen-green' :
                    connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' :
                    'bg-red-500'
                  }`} />
                  {getConnectionStatusText()}
                </div>
                {connectionStatus === 'disconnected' && (
                  <button onClick={checkConnection} className="text-xs text-bullpen-blue hover:text-bullpen-primary underline">
                    Retry
                  </button>
                )}
              </div>
              {messages.length > 0 && (
                <button onClick={handleClearChat} className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors">
                  Clear Chat
                </button>
              )}
            </div>
          </div>
        </header>

        {/* Error Banner */}
        {error && (
          <div className="bg-red-50 border-b border-red-200 px-6 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <svg className="w-5 h-5 text-red-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                <span className="text-sm text-red-800">{error}</span>
              </div>
              <button onClick={() => setError(null)} className="text-red-400 hover:text-red-600">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>
          </div>
        )}

        <main className="flex flex-1 overflow-hidden">
          <Sidebar />
          <div className="flex-1 relative">
            {/* Add Deal Team Button */}
            <button className="absolute top-4 left-4 z-10 px-3 py-2 bg-black text-gray-400 text-sm font-medium rounded-lg hover:bg-bullpen-green hover:text-white transition-colors duration-200 shadow-sm">
              + Add Deal Team
            </button>
            <ChatContainer
              messages={messages}
              isTyping={isTyping}
              isLoading={isLoading}
              statusMessage={statusMessage}
              onSendMessage={handleSendMessage}
              onStopGeneration={handleStopGeneration}
            />
          </div>
        </main>
      </div>
    </>
  )
} 