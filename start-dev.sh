#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting the Bullpen RAG Demo...${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo -e "${YELLOW}Creating .env from template...${NC}"
    
    if [ -f backend/env.example ]; then
        cp backend/env.example .env
        echo -e "${GREEN}✅ Created .env file from backend/env.example${NC}"
        echo -e "${YELLOW}⚠️  Please edit .env and add your Azure credentials before continuing.${NC}"
        exit 1
    else
        echo -e "${RED}❌ backend/env.example not found. Cannot create .env file.${NC}"
    exit 1
fi
fi

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Check if backend is already running
if check_port 8000; then
    echo -e "${YELLOW}⚠️  Port 8000 is already in use. Backend might be running.${NC}"
else
    echo -e "${BLUE}Starting backend server...${NC}"
cd backend
    uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..
    echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"
fi

# Give backend time to start
echo -e "${BLUE}Waiting for backend to initialize...${NC}"
sleep 5

# Check if frontend is already running
if check_port 3000; then
    echo -e "${YELLOW}⚠️  Port 3000 is already in use. Frontend might be running.${NC}"
else
    echo -e "${BLUE}Starting frontend...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..
    echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"
fi

# Give frontend time to start
sleep 3

echo -e "${GREEN}✅ System should be running!${NC}"
echo -e "${BLUE}📍 Frontend: http://localhost:3000${NC}"
echo -e "${BLUE}📍 Backend API: http://localhost:8000${NC}"
echo -e "${BLUE}📍 API Docs: http://localhost:8000/docs${NC}"

# Run verification
echo -e "\n${BLUE}Running system verification...${NC}"
sleep 2
python3 verify_system.py

# Keep script running
echo -e "\n${YELLOW}Press Ctrl+C to stop all services${NC}"
wait 