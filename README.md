# Bullpen AI - Complete RAG System

A production-ready Retrieval-Augmented Generation (RAG) system that combines Azure AI Search with OpenAI GPT models to provide intelligent document search and chat capabilities.

## 🏗️ Architecture

- **Frontend**: Next.js 14 with TypeScript, Tailwind CSS, and real-time streaming chat interface
- **Backend**: FastAPI with Azure AI Search integration and OpenAI API
- **Search**: Azure AI Search with existing document index
- **AI**: OpenAI GPT-4 for response generation
- **Storage**: Azure Blob Storage (existing documents)

## 🚀 Quick Start

### Prerequisites

1. **Python Environment**: Ensure you have Python 3.8+ and your virtual environment activated
2. **Node.js**: Install Node.js 18+ for the frontend
3. **API Keys**: You'll need:
   - OpenAI API key
   - Azure Search service credentials
4. **Existing Azure Resources**: This system uses your existing:
   - Azure AI Search index (`bullpen-index`)
   - Azure Blob Storage with uploaded documents

### Installation

1. **Clone and setup**:
   ```bash
   # Already in your project directory
   # Install backend dependencies
   pip install -r backend/requirements.txt
   
   # Install frontend dependencies (already done)
   cd frontend && npm install && cd ..
   ```

2. **Configure Backend Environment**:
   ```bash
   cp backend/env.example .env
   ```
   
   Edit `.env` with your credentials:
   ```env
   # Azure OpenAI Configuration
   OPENAI_API_TYPE=azure
   OPENAI_API_VERSION=2024-02-01-preview
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_KEY=your-azure-openai-key
   AZURE_OPENAI_EMBED_MODEL=text-embedding-ada-002
   AZURE_GPT4O_DEPLOYMENT=gpt-4o-mini
   
   # Azure AI Search Configuration
   AZURE_SEARCH_ENDPOINT=https://thebullpensearch.search.windows.net
   AZURE_SEARCH_KEY=your-azure-search-key
   AZURE_SEARCH_INDEX=bullpen-index
   
   # External Search
   PERPLEXITY_API_KEY=your-perplexity-key
   ```

3. **Start Development Environment**:
   ```bash
   ./start-dev.sh
   ```

This will start both services:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 📁 Project Structure

```
bullpen-ai/
├── frontend/                 # Next.js React application
│   ├── components/          # React components
│   │   ├── ui/             # Reusable UI components
│   │   ├── ChatContainer.tsx
│   │   ├── ChatMessage.tsx
│   │   └── ChatInput.tsx
│   ├── hooks/              # Custom React hooks
│   ├── pages/              # Next.js pages and API routes
│   ├── types/              # TypeScript definitions
│   └── styles/             # Global styles
├── backend/                 # FastAPI application
│   ├── main.py             # Main FastAPI app
│   ├── requirements.txt    # Python dependencies
│   └── env.example         # Environment template
├── start-dev.sh            # Development startup script
└── README.md               # This file
```

## 🔧 Configuration

### Backend Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_TYPE` | OpenAI API type (should be 'azure') | `azure` |
| `OPENAI_API_VERSION` | Azure OpenAI API version | `2024-02-01-preview` |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | `https://your-resource.openai.azure.com/` |
| `AZURE_OPENAI_KEY` | Azure OpenAI API key | `your-key` |
| `AZURE_OPENAI_EMBED_MODEL` | Embedding model deployment name | `text-embedding-ada-002` |
| `AZURE_GPT4O_DEPLOYMENT` | GPT-4o chat model deployment name | `gpt-4o-mini` |
| `AZURE_SEARCH_ENDPOINT` | Azure Search service URL | `https://your-service.search.windows.net` |
| `AZURE_SEARCH_KEY` | Azure Search admin key | `your-key` |
| `AZURE_SEARCH_INDEX` | Search index name | `bullpen-index` |
| `PERPLEXITY_API_KEY` | Perplexity API key for external search | `pplx-...` |

### Frontend Configuration

The frontend automatically connects to the backend on `localhost:8000`. For production, update the `BACKEND_URL` environment variable.

## 🎯 Features

### Chat Interface
- **Real-time Streaming**: Responses stream in real-time like ChatGPT
- **Source Citations**: Shows relevant document sources with relevance scores
- **Chat History**: Persists conversations in local storage
- **Error Handling**: Graceful error handling with retry functionality
- **Responsive Design**: Works on desktop and mobile devices

### Backend API
- **Document Search**: Integrates with your existing Azure AI Search index
- **AI Generation**: Uses OpenAI GPT-4 for intelligent responses
- **Streaming Responses**: Server-sent events for real-time chat
- **CORS Support**: Configured for frontend integration
- **Health Checks**: Built-in health monitoring endpoints

## 🔄 API Endpoints

### POST `/chat`
Main chat endpoint that accepts questions and returns streaming responses.

**Request**:
```json
{
  "question": "What are the key findings in the research?",
  "sessionId": "optional-session-id"
}
```

**Response**: Server-sent events stream with tokens and final answer with sources.

### GET `/health`
Health check endpoint.

### GET `/`
API information endpoint.

## 🚀 Production Deployment

### Frontend (Next.js)
```bash
cd frontend
npm run build
npm start
```

### Backend (FastAPI)
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Environment Variables for Production
- Set `NODE_ENV=production` for frontend
- Configure `BACKEND_URL` to point to your production backend
- Use production-grade WSGI server like Gunicorn for FastAPI

## 🔍 Usage Examples

1. **Ask about document content**:
   - "What are the main recommendations in the research?"
   - "Summarize the key findings from the documents"

2. **Search for specific information**:
   - "What does the document say about budget allocation?"
   - "Find information about project timelines"

3. **Get contextual answers**:
   - The system will search your documents and provide answers with source citations

## 🛠️ Development

### Running Individual Services

**Backend only**:
```bash
cd backend
source ../venv/bin/activate  # or .venv
uvicorn main:app --reload
```

**Frontend only**:
```bash
cd frontend
npm run dev
```

### Adding New Features

1. **Frontend**: Add components in `frontend/components/`
2. **Backend**: Extend `backend/main.py` with new endpoints
3. **Types**: Update TypeScript interfaces in `frontend/types/`

## 🔧 Troubleshooting

### Common Issues

1. **Backend connection errors**: Ensure FastAPI is running on port 8000
2. **Azure Search errors**: Verify your search credentials and index name
3. **OpenAI API errors**: Check your API key and quota
4. **Frontend build errors**: Ensure all dependencies are installed

### Logs

- **Backend logs**: Check the terminal where FastAPI is running
- **Frontend logs**: Check browser console and Next.js terminal output

## 📝 License

This project is part of the Bullpen AI system for document search and analysis.

## 🤝 Support

For issues or questions about this RAG system, please check:
1. Backend API documentation at http://localhost:8000/docs
2. Console logs for error messages
3. Ensure all environment variables are properly configured 