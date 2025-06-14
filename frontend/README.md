# Bullpen AI Frontend

A modern chat interface for the Bullpen AI document search system built with Next.js, TypeScript, and Tailwind CSS.

## Features

- Real-time streaming chat interface
- Document source citations
- Responsive design
- Local storage for chat history
- Error handling and retry functionality

## Getting Started

1. Install dependencies:
```bash
npm install
```

2. Run the development server:
```bash
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

- `components/` - React components
- `hooks/` - Custom React hooks
- `pages/` - Next.js pages and API routes
- `types/` - TypeScript type definitions
- `styles/` - Global CSS styles
- `lib/` - Utility functions

## API Integration

The frontend connects to a FastAPI backend through the `/api/chat` endpoint. Update the API route in `pages/api/chat.ts` to connect to your production backend.

## Deployment

Build the application for production:

```bash
npm run build
npm start
``` 