import type { NextApiRequest, NextApiResponse } from 'next'

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  const { question, conversation_history = [] } = req.body

  if (!question) {
    return res.status(400).json({ error: 'Question is required' })
  }

  try {
    // Proxy request to FastAPI backend
    const backendUrl = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    console.log(`Connecting to backend at: ${backendUrl}`)
    
    const response = await fetch(`${backendUrl}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        message: question,
        conversation_history: conversation_history
      }),
    })

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`)
    }

    // Set up Server-Sent Events headers
    res.writeHead(200, {
      'Content-Type': 'text/plain',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Cache-Control',
    })

    // Stream the response from backend to frontend
    const reader = response.body?.getReader()
    const decoder = new TextDecoder()

    if (reader) {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6) // Remove 'data: '
            if (dataStr === '[DONE]') {
              res.write('data: {"done": true}\n\n')
              continue
            }
            
            try {
              const data = JSON.parse(dataStr)
              
              if (data.type === 'content') {
                // Convert backend format to frontend format
                res.write(`data: ${JSON.stringify({ token: data.content })}\n\n`)
              } else if (data.type === 'sources') {
                // Forward sources data
                res.write(`data: ${JSON.stringify({ sources: data.sources })}\n\n`)
              } else if (data.type === 'status') {
                // Forward status updates
                res.write(`data: ${JSON.stringify({ status: data.content })}\n\n`)
              }
            } catch (e) {
              // Skip malformed JSON
              continue
            }
          }
        }
      }
    }

    res.end()
  } catch (error) {
    console.error('Chat API error:', error)
    
    // Fallback to mock response if backend is not available
    res.writeHead(200, {
      'Content-Type': 'text/plain',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Cache-Control',
    })

    const mockResponse = `I'm currently unable to connect to the backend service. This is a mock response to your question: "${question}". Please ensure the FastAPI backend is running on port 8000.`
    
    const words = mockResponse.split(' ')
    
    for (let i = 0; i < words.length; i++) {
      const token = i === 0 ? words[i] : ' ' + words[i]
      res.write(`data: ${JSON.stringify({ token })}\n\n`)
      
      await new Promise(resolve => setTimeout(resolve, 50))
    }

    res.write(`data: ${JSON.stringify({
      done: true,
      answer: mockResponse,
      sources: []
    })}\n\n`)

    res.end()
  }
} 