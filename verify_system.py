#!/usr/bin/env python3
"""
System Verification Script for the Bullpen RAG Demo
Checks all critical services and configurations
"""

import os
import sys
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

def print_status(message, status="info"):
    """Print colored status messages"""
    if status == "success":
        print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")
    elif status == "error":
        print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")
    elif status == "warning":
        print(f"{Fore.YELLOW}⚠️  {message}{Style.RESET_ALL}")
    else:
        print(f"{Fore.BLUE}ℹ️  {message}{Style.RESET_ALL}")

def check_env_file():
    """Check if .env file exists and is properly configured"""
    print_status("Checking environment configuration...", "info")
    
    # Look for .env file
    env_paths = [Path(".env"), Path("../.env")]
    env_found = False
    
    for path in env_paths:
        if path.exists():
            print_status(f"Found .env file at: {path.absolute()}", "success")
            load_dotenv(path)
            env_found = True
            break
    
    if not env_found:
        print_status("No .env file found! Copy backend/env.example to .env and configure it.", "error")
        return False
    
    # Check required variables
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_KEY",
        "AZURE_OPENAI_EMBED_MODEL",
        "AZURE_GPT4O_DEPLOYMENT",
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_KEY",
        "AZURE_SEARCH_INDEX",
        "PERPLEXITY_API_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print_status(f"Missing required environment variables: {', '.join(missing_vars)}", "error")
        return False
    
    print_status("All required environment variables are set", "success")
    return True

def check_backend_health():
    """Check if backend is running and healthy"""
    print_status("\nChecking backend health...", "info")
    
    try:
        # Check basic health
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_status(f"Backend is running (version {data.get('version', 'unknown')})", "success")
            
            # Check service status
            services = data.get('services', {})
            for service, status in services.items():
                if status == "connected":
                    print_status(f"  - {service}: {status}", "success")
                else:
                    print_status(f"  - {service}: {status}", "warning")
        else:
            print_status(f"Backend returned status {response.status_code}", "error")
            return False
            
        # Check detailed health
        response = requests.get("http://localhost:8000/healthz", timeout=5)
        if response.status_code == 200:
            data = response.json()
            checks = data.get('checks', {})
            
            print_status("\nDetailed service checks:", "info")
            for check, status in checks.items():
                if status == "ok":
                    print_status(f"  - {check}: {status}", "success")
                elif "error" in str(status):
                    print_status(f"  - {check}: {status}", "error")
                else:
                    print_status(f"  - {check}: {status}", "warning")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print_status("Cannot connect to backend! Is it running on port 8000?", "error")
        print_status("Start the backend with: cd backend && uvicorn main:app --reload", "info")
        return False
    except Exception as e:
        print_status(f"Error checking backend: {e}", "error")
        return False

def check_frontend_health():
    """Check if frontend is running"""
    print_status("\nChecking frontend health...", "info")
    
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print_status("Frontend is running on port 3000", "success")
            return True
        else:
            print_status(f"Frontend returned status {response.status_code}", "warning")
            return False
    except requests.exceptions.ConnectionError:
        print_status("Frontend not running on port 3000", "warning")
        print_status("Start the frontend with: cd frontend && npm run dev", "info")
        return False
    except Exception as e:
        print_status(f"Error checking frontend: {e}", "error")
        return False

def test_basic_functionality():
    """Test basic RAG functionality"""
    print_status("\nTesting basic functionality...", "info")
    
    try:
        # Test the chat endpoint
        test_query = {
            "message": "What is GlobeLink's ARR?",
            "conversation_history": []
        }
        
        response = requests.post(
            "http://localhost:8000/chat",
            json=test_query,
            stream=True,
            timeout=30
        )
        
        if response.status_code == 200:
            print_status("Chat endpoint is responding", "success")
            
            # Read a few chunks to verify streaming works
            chunks_read = 0
            for chunk in response.iter_content(chunk_size=1024):
                chunks_read += 1
                if chunks_read >= 3:  # Just read first few chunks
                    break
            
            if chunks_read > 0:
                print_status("Streaming response is working", "success")
                return True
            else:
                print_status("No streaming data received", "warning")
                return False
        else:
            print_status(f"Chat endpoint returned status {response.status_code}", "error")
            return False
            
    except Exception as e:
        print_status(f"Error testing functionality: {e}", "error")
        return False

def main():
    """Run all system checks"""
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🔍 Bullpen RAG System Verification{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    all_good = True
    
    # Check environment
    if not check_env_file():
        all_good = False
    
    # Check backend
    if not check_backend_health():
        all_good = False
    else:
        # Only test functionality if backend is healthy
        if not test_basic_functionality():
            all_good = False
    
    # Check frontend (non-critical)
    check_frontend_health()
    
    # Summary
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    if all_good:
        print_status("System is ready for demo! 🚀", "success")
        print_status("\nTo start the system:", "info")
        print("  1. Backend:  cd backend && uvicorn main:app --reload")
        print("  2. Frontend: cd frontend && npm run dev")
        print("  3. Open:     http://localhost:3000")
    else:
        print_status("System has issues that need to be fixed", "error")
        print_status("\nNext steps:", "info")
        print("  1. Fix any missing environment variables in .env")
        print("  2. Ensure Azure services are properly configured")
        print("  3. Start the backend server")
        print("  4. Run this script again to verify")
    
    return 0 if all_good else 1

if __name__ == "__main__":
    # Check if colorama is installed
    try:
        from colorama import init, Fore, Style
    except ImportError:
        print("Installing colorama for colored output...")
        os.system(f"{sys.executable} -m pip install colorama")
        from colorama import init, Fore, Style
    
    sys.exit(main()) 