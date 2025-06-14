import { useState, useEffect } from 'react';
import { ChatMessage } from '../types/chat';

const STORAGE_KEY = 'bullpen-chat-history';

export const useChatHistory = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  // Load messages from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsedMessages = JSON.parse(stored);
        // Convert timestamp strings back to Date objects
        const messagesWithDates = parsedMessages.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }));
        setMessages(messagesWithDates);
      }
    } catch (error) {
      console.error('Failed to load chat history:', error);
    }
  }, []);

  // Save messages to localStorage whenever messages change
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    } catch (error) {
      console.error('Failed to save chat history:', error);
    }
  }, [messages]);

  const addMessage = (message: ChatMessage) => {
    setMessages(prev => {
      // Check if message already exists (for streaming updates)
      const existingIndex = prev.findIndex(m => m.id === message.id);
      if (existingIndex >= 0) {
        // Update existing message
        const updated = [...prev];
        updated[existingIndex] = message;
        return updated;
      } else {
        // Add new message
        return [...prev, message];
      }
    });
  };

  const clearHistory = () => {
    setMessages([]);
    localStorage.removeItem(STORAGE_KEY);
  };

  const removeMessage = (messageId: string) => {
    setMessages(prev => prev.filter(m => m.id !== messageId));
  };

  return {
    messages,
    addMessage,
    clearHistory,
    removeMessage
  };
}; 