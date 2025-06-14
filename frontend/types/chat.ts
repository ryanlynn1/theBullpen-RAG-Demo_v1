export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  sources?: DocumentSource[]
  isStreaming?: boolean
}

export interface DocumentSource {
  title: string
  content: string
  score: number
  metadata?: {
    path?: string
    highlights?: any
    query_used?: string
    [key: string]: any
  }
}

export interface StreamResponse {
  content?: string
  sources?: DocumentSource[]
  type: 'content' | 'sources' | 'error'
}

export interface ChatRequest {
  question: string
  sessionId?: string
} 