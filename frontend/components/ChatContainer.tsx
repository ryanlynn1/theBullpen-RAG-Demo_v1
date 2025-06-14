import React, { useRef, useEffect } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import { ChatMessage as ChatMessageType } from '../types/chat';
import BullpenLogo from './ui/BullpenLogo';
import BullpenIcon from './ui/BullpenIcon';

interface ChatContainerProps {
  messages: ChatMessageType[];
  isTyping: boolean;
  isLoading: boolean;
  statusMessage: string | null;
  onSendMessage: (message: string) => void;
  onStopGeneration: () => void;
}

const ChatContainer: React.FC<ChatContainerProps> = ({
  messages,
  isTyping,
  isLoading,
  statusMessage,
  onSendMessage,
  onStopGeneration,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  if (messages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-start pt-24 h-full bg-bullpen-charcoal overflow-hidden text-center">
        <div className="flex items-center justify-center mb-6">
          <BullpenIcon width={64} height={61} className="text-white" />
        </div>
        <div className="mb-4">
          <BullpenLogo width={200} height={62} className="text-white mx-auto mb-2" />
          <h2 className="text-2xl font-bold bullpen-text-gradient">How can we help?</h2>
        </div>
        <div className="w-full px-6 mt-8 max-w-4xl">
          <ChatInput
            onSendMessage={onSendMessage}
            disabled={isLoading}
            isLoading={isLoading}
            onStopGeneration={onStopGeneration}
            variant="dark"
          />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-bullpen-charcoal">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {messages.map((message: ChatMessageType) => (
          <ChatMessage key={message.id} message={message} />
        ))}
        
        {/* Typing Indicator */}
        {isTyping && (
          <div className="flex justify-start mb-6">
            <div className="max-w-4xl mr-12">
              <div className="flex items-center mb-2">
                <div className="w-8 h-8 rounded-full bullpen-gradient flex items-center justify-center">
                  <BullpenIcon width={20} height={19} className="text-white" />
                </div>
                <span className="ml-2 text-sm text-gray-500">the Bullpen</span>
              </div>
              <div className="bg-white border border-gray-200 rounded-2xl px-6 py-4 shadow-sm">
                <div className="flex items-center space-x-2">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-bullpen-blue rounded-full animate-pulse"></div>
                    <div className="w-2 h-2 bg-bullpen-blue rounded-full animate-pulse" style={{ animationDelay: '200ms' }}></div>
                    <div className="w-2 h-2 bg-bullpen-blue rounded-full animate-pulse" style={{ animationDelay: '400ms' }}></div>
                  </div>
                  <span className="text-gray-700 text-sm">{statusMessage || "Thinking..."}</span>
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-700 bg-bullpen-charcoal-dark px-6 py-4">
        <div className="mx-auto max-w-4xl">
          <ChatInput 
            onSendMessage={onSendMessage} 
            disabled={isLoading}
            isLoading={isLoading}
            onStopGeneration={onStopGeneration}
            variant="light"
          />
        </div>
      </div>
    </div>
  );
};

export default ChatContainer; 