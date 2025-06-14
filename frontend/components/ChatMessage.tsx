import React, { useState } from 'react'
import { ChatMessage as ChatMessageType, DocumentSource } from '../types/chat'
import BullpenIcon from './ui/BullpenIcon'

interface ChatMessageProps {
  message: ChatMessageType
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const [showSources, setShowSources] = useState(false)
  const [expandedSource, setExpandedSource] = useState<number | null>(null)

  const formatContent = (content: string) => {
    // First, process markdown with special handling for financial data
    const processedContent = content
      // Format currency with optional suffixes (K, M, B) - black bold instead of green
      .replace(/\$([\d,]+(?:\.\d{2})?)(K|M|MM|B)?/g, '<span class="font-bold">$$$1$2</span>')
      // Format percentages - black bold instead of blue
      .replace(/([\d.]+%)/g, '<span class="font-bold">$1</span>')
      // Format company names when bolded - black bold instead of navy
      .replace(/\*\*(GlobeLink|CrowdStrike|Zscaler|Project Alpha)\*\*/gi, '<span class="font-bold">$1</span>')
      // Enhanced header formatting - changed to black
      .replace(/^## (.+)$/gm, '<h2 class="text-xl font-bold text-gray-900 mt-3 mb-1.5 border-b border-gray-200 pb-1">$1</h2>')
      .replace(/^### (.+)$/gm, '<h3 class="text-lg font-semibold text-gray-900 mt-2 mb-1">$1</h3>')
      // Enhanced bullet point formatting with minimal spacing - black bullet
      .replace(/^- (.+)$/gm, '<div class="flex items-start mb-0.5"><span class="text-gray-900 mr-2 mt-0.5">•</span><span class="flex-1">$1</span></div>')
      // Format numbered lists with minimal spacing
      .replace(/^\d+\. (.+)$/gm, '<div class="flex items-start mb-0.5"><span class="text-gray-900 mr-2 font-semibold">$&</span></div>')
      // Bold text formatting
      .replace(/\*\*(.+?)\*\*/g, '<span class="font-bold text-gray-900">$1</span>')
      // Italic text formatting
      .replace(/\*(.+?)\*/g, '<span class="italic text-gray-700">$1</span>')
      // Code formatting
      .replace(/`(.+?)`/g, '<code class="bg-gray-100 px-2 py-1 rounded text-sm font-mono">$1</code>')
      // Line breaks with minimal spacing
      .replace(/\n\n/g, '<div class="mb-1.5"></div>')
      .replace(/\n/g, '<br class="leading-tight">');

    return processedContent;
  }

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-bullpen-green bg-green-50'
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-50'
    return 'text-red-600 bg-red-50'
  }

  const getScoreLabel = (score: number) => {
    if (score >= 0.8) return 'High Relevance'
    if (score >= 0.6) return 'Medium Relevance'
    return 'Low Relevance'
  }

  return (
    <div className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} mb-6`}>
      <div className={`max-w-4xl ${message.role === 'user' ? 'ml-12' : 'mr-12'}`}>
        {/* Message Header */}
        <div className={`flex items-center mb-2 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
          {message.role === 'assistant' && (
            <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium bullpen-gradient text-white">
              <BullpenIcon width={20} height={19} className="text-white" />
            </div>
          )}
          <span className={`text-sm text-gray-500 ${message.role === 'user' ? 'order-first mr-2 ml-0' : 'ml-2'}`}>
            {message.role === 'user' ? 'You' : 'the Bullpen'}
          </span>
        </div>

        {/* Message Content */}
        <div className={`rounded-2xl px-6 py-4 shadow-sm ${
          message.role === 'user'
            ? 'bg-bullpen-blue text-white'
            : 'bg-white border border-gray-200'
        }`}>
          <div 
            className={`${
              message.role === 'user' 
                ? 'prose prose-invert' 
                : 'prose prose-sm prose-gray max-w-none prose-p:my-1 prose-ul:my-1 prose-li:my-0.5 prose-headings:text-gray-900'
            }`}
            dangerouslySetInnerHTML={{ 
              __html: message.role === 'assistant' 
                ? formatContent(message.content) 
                : message.content 
            }}
          />
        </div>

        {/* Sources Section */}
        {message.role === 'assistant' && message.sources && message.sources.length > 0 && (
          <div className="mt-4">
            <button
              onClick={() => setShowSources(!showSources)}
              className="flex items-center text-sm text-gray-600 hover:text-bullpen-blue transition-colors"
            >
              <svg 
                className={`w-4 h-4 mr-2 transition-transform ${showSources ? 'rotate-90' : ''}`}
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              {showSources ? 'Hide' : 'Show'} Sources ({message.sources.length})
            </button>

            {showSources && (
              <div className="mt-3 space-y-3">
                {message.sources.map((source, index) => (
                  <div key={index} className="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
                    {/* Source Header */}
                    <div 
                      className="px-4 py-3 bg-white border-b border-gray-200 cursor-pointer hover:bg-gray-50 transition-colors"
                      onClick={() => setExpandedSource(expandedSource === index ? null : index)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="flex-shrink-0">
                            <div className="w-8 h-8 bg-bullpen-blue bg-opacity-10 rounded-lg flex items-center justify-center">
                              <svg className="w-4 h-4 text-bullpen-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                              </svg>
                            </div>
                          </div>
                          <div className="flex-1 min-w-0">
                            <h4 className="text-sm font-medium text-bullpen-charcoal truncate">
                              {source.title.split('/').pop()}
                            </h4>
                            <div className="flex items-center space-x-2 mt-1">
                              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getScoreColor(source.score)}`}>
                                {getScoreLabel(source.score)} ({(source.score * 100).toFixed(0)}%)
                              </span>
                              {source.metadata?.query_used && (
                                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                                  Query: {source.metadata.query_used}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        <svg 
                          className={`w-5 h-5 text-gray-400 transition-transform ${expandedSource === index ? 'rotate-180' : ''}`}
                          fill="none" 
                          stroke="currentColor" 
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </div>
                    </div>

                    {/* Expanded Source Content */}
                    {expandedSource === index && (
                      <div className="px-4 py-3">
                        <div className="text-sm text-gray-700 leading-relaxed">
                          <div 
                            dangerouslySetInnerHTML={{ __html: formatContent(source.content) }}
                            className="prose prose-sm max-w-none"
                          />
                        </div>
                        
                        {/* Metadata */}
                        {source.metadata && Object.keys(source.metadata).length > 0 && (
                          <div className="mt-3 pt-3 border-t border-gray-200">
                            <h5 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                              Document Metadata
                            </h5>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                              {source.metadata.path && (
                                <div>
                                  <span className="font-medium text-gray-600">Path:</span>
                                  <span className="ml-1 text-gray-500 font-mono">{source.metadata.path}</span>
                                </div>
                              )}
                              {source.metadata.highlights && (
                                <div className="md:col-span-2">
                                  <span className="font-medium text-gray-600">Highlights:</span>
                                  <div className="ml-1 text-gray-500 italic">
                                    {JSON.stringify(source.metadata.highlights)}
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Timestamp */}
        <div className={`mt-2 text-xs text-gray-400 ${message.role === 'user' ? 'text-right' : 'text-left'}`}>
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  )
}

export default ChatMessage 