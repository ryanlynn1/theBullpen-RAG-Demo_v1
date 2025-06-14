import os
import json
import asyncio
import httpx
import time
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from sse_starlette.sse import EventSourceResponse
import logging
from typing import List, Dict
import traceback
import sys
import re
import nltk

# --- Setup and Configuration ---

# Ensure NLTK 'punkt' is downloaded
try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    print("Downloading NLTK 'punkt' model...")
    nltk.download('punkt', quiet=True)
    print("✅ NLTK 'punkt' downloaded.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
# Try multiple locations for .env file
env_loaded = False
env_locations = [
    Path(".env"),  # Current directory
    Path("../.env"),  # Parent directory
    Path(__file__).parent.parent / ".env",  # Project root (relative to this file)
]

for env_path in env_locations:
    if env_path.exists():
        load_dotenv(dotenv_path=str(env_path), override=True)
        env_loaded = True
        logger.info(f"✅ Loaded .env from: {env_path.absolute()}")
        break

if not env_loaded:
    logger.warning("⚠️ No .env file found. Using system environment variables.")

# --- Environment Variable Validation ---

def validate_env() -> None:
    """Validate all required environment variables are present."""
    required_vars = {
        "OPENAI_API_TYPE": "Azure OpenAI API type (should be 'azure')",
        "OPENAI_API_VERSION": "Azure OpenAI API version",
        "AZURE_OPENAI_ENDPOINT": "Azure OpenAI endpoint URL",
        "AZURE_OPENAI_KEY": "Azure OpenAI API key",
        "AZURE_OPENAI_EMBED_MODEL": "Azure OpenAI embedding model deployment name",
        "AZURE_GPT4O_DEPLOYMENT": "Azure OpenAI GPT-4o chat model deployment name",
        "AZURE_SEARCH_ENDPOINT": "Azure AI Search endpoint URL",
        "AZURE_SEARCH_KEY": "Azure AI Search API key",
        "AZURE_SEARCH_INDEX": "Azure AI Search index name",
        "PERPLEXITY_API_KEY": "Perplexity API key for external search"
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"  - {var}: {description}")
    
    if missing_vars:
        error_msg = "❌ Missing required environment variables:\n" + "\n".join(missing_vars)
        logger.error(error_msg)
        logger.error("\n📝 Please create a .env file in the project root with all required variables.")
        logger.error("   See backend/env.example for the template.")
        sys.exit(1)
    
    logger.info("✅ Environment validation passed - all required variables present")

# Run validation before starting
validate_env()

# FastAPI app setup
app = FastAPI(
    title="the Bullpen RAG API",
    description="An API for the Bullpen RAG system with multi-tool agent capabilities.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Service Credentials and Clients ---

def initialize_azure_clients(max_retries: int = 3, retry_delay: float = 1.0):
    """Initialize Azure clients with retry logic."""
    for attempt in range(max_retries):
        try:
            # Azure Services Configuration (using standardized names)
            AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
            AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")
            AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
            AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
            AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
            OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION")
            AZURE_OPENAI_EMBED_MODEL = os.getenv("AZURE_OPENAI_EMBED_MODEL")
            AZURE_GPT4O_DEPLOYMENT = os.getenv("AZURE_GPT4O_DEPLOYMENT")
            
            # Perplexity API Configuration
            PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

            # Debug: Print the chat deployment being used
            logger.info(f"🔧 Using chat deployment: {AZURE_GPT4O_DEPLOYMENT}")
            logger.info(f"🔧 Using embedding model: {AZURE_OPENAI_EMBED_MODEL}")

            # Initialize Clients
            search_client = SearchClient(
                endpoint=AZURE_SEARCH_ENDPOINT,
                index_name=AZURE_SEARCH_INDEX,
                credential=AzureKeyCredential(AZURE_SEARCH_KEY)
            )
            openai_client = AzureOpenAI(
                api_key=AZURE_OPENAI_KEY,
                api_version=OPENAI_API_VERSION,
                azure_endpoint=AZURE_OPENAI_ENDPOINT
            )
            
            # Test connections
            logger.info(f"Testing Azure Search connection (attempt {attempt + 1}/{max_retries})...")
            search_client.search(search_text="test", top=1)
            
            logger.info("✅ Successfully initialized Azure clients.")
            return search_client, openai_client, {
                "AZURE_SEARCH_ENDPOINT": AZURE_SEARCH_ENDPOINT,
                "AZURE_SEARCH_INDEX": AZURE_SEARCH_INDEX,
                "AZURE_OPENAI_ENDPOINT": AZURE_OPENAI_ENDPOINT,
                "OPENAI_API_VERSION": OPENAI_API_VERSION,
                "AZURE_OPENAI_EMBED_MODEL": AZURE_OPENAI_EMBED_MODEL,
                "AZURE_GPT4O_DEPLOYMENT": AZURE_GPT4O_DEPLOYMENT,
                "PERPLEXITY_API_KEY": PERPLEXITY_API_KEY
            }

        except Exception as e:
            logger.error(f"❌ Failed to initialize clients (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                raise

# Initialize clients with retry logic
try:
    search_client, openai_client, config = initialize_azure_clients()
    
    # Extract config values for global use
    AZURE_SEARCH_ENDPOINT = config["AZURE_SEARCH_ENDPOINT"]
    AZURE_SEARCH_INDEX = config["AZURE_SEARCH_INDEX"]
    AZURE_OPENAI_ENDPOINT = config["AZURE_OPENAI_ENDPOINT"]
    OPENAI_API_VERSION = config["OPENAI_API_VERSION"]
    AZURE_OPENAI_EMBED_MODEL = config["AZURE_OPENAI_EMBED_MODEL"]
    AZURE_GPT4O_DEPLOYMENT = config["AZURE_GPT4O_DEPLOYMENT"]
    PERPLEXITY_API_KEY = config["PERPLEXITY_API_KEY"]
    
except Exception as e:
    logger.error(f"Failed to initialize Azure clients after all retries: {e}")
    # Continue running but services will be unavailable
    search_client = None
    openai_client = None

# --- Pydantic Models ---

class ChatRequest(BaseModel):
    message: str
    conversation_history: List[Dict[str, str]]

# --- Core Logic ---

async def get_embedding(text: str, max_retries: int = 3):
    """Generates embeddings for a given text using Azure OpenAI with retry logic."""
    if not openai_client:
        logger.error("OpenAI client not initialized")
        raise HTTPException(status_code=503, detail="OpenAI service unavailable")
    
    for attempt in range(max_retries):
        try:
            response = openai_client.embeddings.create(
                input=text, 
                model=AZURE_OPENAI_EMBED_MODEL
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding generation failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5 * (2 ** attempt))  # Exponential backoff
            else:
                raise

async def classify_query(question: str) -> str:
    """Classify whether a query needs internal, external, or hybrid search."""
    
    # Enhanced keyword detection
    internal_keywords = ['globelink', 'project alpha', 'arr', 'enterprise value', 'nda', 'loi', 'debt schedule', 'moic', 'our deal', 'our company', 'our documents']
    external_keywords = ['market cap', 'stock price', 'tesla', 'apple', 'crowdstrike', 'nasdaq', 'current', 'today', 'public company']
    
    # Hybrid query indicators - questions that compare internal data with external market data
    hybrid_indicators = [
        'compare', 'comparison', 'benchmark', 'vs', 'versus', 'against', 
        'market average', 'industry average', 'public companies', 'competitors',
        'market multiples', 'market valuation', 'industry standard', 'peer group',
        'how does our', 'how does globelink', 'relative to', 'compared to'
    ]
    
    question_lower = question.lower()
    
    # Check for hybrid queries first (most specific)
    has_internal = any(keyword in question_lower for keyword in internal_keywords)
    has_external_indicators = any(keyword in question_lower for keyword in external_keywords)
    has_hybrid_indicators = any(indicator in question_lower for indicator in hybrid_indicators)
    
    if has_internal and (has_hybrid_indicators or has_external_indicators):
        logger.info(f"Query classification: '{question}' → hybrid (internal + comparison/external indicators)")
        return "hybrid"
    
    # Check for clear external indicators
    if any(keyword in question_lower for keyword in external_keywords):
        logger.info(f"Query classification: '{question}' → external (keyword match)")
        return "external"
    
    # Check for clear internal indicators
    if has_internal:
        logger.info(f"Query classification: '{question}' → internal (keyword match)")
        return "internal"
    
    # Fallback to LLM classification for ambiguous cases
    try:
        classification_prompt = f"""You are a query classifier for a financial private equity firm's RAG system.

Classify this question into exactly ONE category:

Question: "{question}"

Categories:
- INTERNAL: Questions about our company's deals, projects, documents, or proprietary information
- EXTERNAL: Questions about public companies, market data, stock prices, or general knowledge  
- HYBRID: Questions comparing our internal data with external market information

Examples:
- "What is CrowdStrike's market cap?" → EXTERNAL
- "What was the ARR for GlobeLink?" → INTERNAL  
- "How does GlobeLink's ARR compare to public SaaS companies?" → HYBRID
- "What are average revenue multiples for cybersecurity companies vs our deal?" → HYBRID

Respond with exactly one word: INTERNAL, EXTERNAL, or HYBRID"""

        response = openai_client.chat.completions.create(
            model=AZURE_GPT4O_DEPLOYMENT,
            messages=[{"role": "user", "content": classification_prompt}],
            max_tokens=20
        )
        
        classification = response.choices[0].message.content.strip().upper()
        if classification in ["INTERNAL", "EXTERNAL", "HYBRID"]:
            logger.info(f"Query classification: '{question}' → {classification.lower()} (LLM)")
            return classification.lower()
        else:
            logger.warning(f"Invalid LLM classification: {classification}, defaulting to external")
            return "external"
            
    except Exception as e:
        logger.error(f"Error classifying query: {e}")
        # Default to external search for safety
        return "external"

async def search_web(query: str) -> Dict:
    """Search the web using Perplexity API."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-sonar-small-128k-online",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful assistant providing accurate, up-to-date information. Always cite your sources."
                        },
                        {
                            "role": "user", 
                            "content": query
                        }
                    ]
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                logger.info(f"Web search successful for query: '{query}'")
                return {
                    "content": content,
                    "source": "Perplexity AI",
                    "query": query
                }
            else:
                logger.error(f"Perplexity API error: {response.status_code} - {response.text}")
                return {"content": "Unable to fetch web results", "source": "Error", "query": query}
                
    except Exception as e:
        logger.error(f"Error in web search: {e}")
        return {"content": f"Web search failed: {str(e)}", "source": "Error", "query": query}

def clean_text(text: str) -> str:
    """Cleans raw text by normalizing whitespace and removing common artifacts."""
    # Replace multiple spaces, newlines, and tabs with a single space
    text = re.sub(r'\s+', ' ', text).strip()
    # Attempt to fix words that are incorrectly joined by removing a newline
    # e.g. "managementand" -> "management and"
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    # Remove unicode characters that are not standard
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    return text

def extract_snippet(full_text: str, query: str, window_size: int = 1) -> str:
    """Extracts the most relevant sentence(s) from a text chunk based on a query."""
    try:
        sentences = nltk.sent_tokenize(full_text)
        if not sentences:
            return full_text[:500] # Fallback for text without clear sentences

        # Find the sentence with the highest number of query words
        query_words = set(query.lower().split())
        best_sentence_index = -1
        max_score = 0

        for i, sentence in enumerate(sentences):
            sentence_words = set(sentence.lower().split())
            score = len(query_words.intersection(sentence_words))
            if score > max_score:
                max_score = score
                best_sentence_index = i
        
        # If no direct word overlap, fall back to the first sentence
        if best_sentence_index == -1:
            best_sentence_index = 0

        # Create the snippet with a window of surrounding sentences
        start_index = max(0, best_sentence_index - window_size)
        end_index = min(len(sentences), best_sentence_index + window_size + 1)
        
        snippet = " ".join(sentences[start_index:end_index])
        
        # Add ellipsis if the snippet is not the start or end of the document
        if start_index > 0:
            snippet = "... " + snippet
        if end_index < len(sentences):
            snippet = snippet + " ..."
            
        return snippet
    except Exception as e:
        logger.error(f"Error extracting snippet: {e}")
        return full_text[:500] # Fallback to truncated text on error

async def search_internal_documents(query: str, k: int = 5):
    """Performs a vector search on the internal Azure AI Search index."""
    try:
        vector = await get_embedding(query)
        vector_query = VectorizedQuery(vector=vector, k_nearest_neighbors=k, fields="content_vector")
        
        results = search_client.search(
            search_text=None,
            vector_queries=[vector_query],
            select=["metadata", "content", "id"]  # Removed source field - doesn't exist in index
        )
        
        documents = []
        for result in results:
            # Extract source path from metadata field
            metadata = result.get("metadata", "Unknown Document")
            source_path = metadata
            
            # If metadata is a dict/JSON string, try to extract source from it
            if isinstance(metadata, str):
                try:
                    import json
                    metadata_dict = json.loads(metadata)
                    source_path = metadata_dict.get("source", metadata)
                except:
                    source_path = metadata
            elif isinstance(metadata, dict):
                source_path = metadata.get("source", str(metadata))
            
            # --- FEATURE: Clean and extract snippet for display ---
            cleaned_content = clean_text(result["content"])
            snippet = extract_snippet(cleaned_content, query)
            # --- END FEATURE ---

            # Generate blob URL if we have blob storage configured
            blob_url = f"#{result['id']}"  # Default fallback
            if os.getenv("AZURE_BLOB_CONN_STR") and os.getenv("AZURE_BLOB_CONTAINER"):
                # Extract storage account name from connection string
                conn_str = os.getenv("AZURE_BLOB_CONN_STR", "")
                account_match = re.search(r'AccountName=([^;]+)', conn_str)
                if account_match:
                    account_name = account_match.group(1)
                    container = os.getenv("AZURE_BLOB_CONTAINER")
                    # Create proper blob URL
                    blob_url = f"https://{account_name}.blob.core.windows.net/{container}/{source_path}"
            
            documents.append({
                "title": source_path,
                "content": result["content"], # Full content for LLM context
                "snippet": snippet, # Clean snippet for UI display
                "url": blob_url,
                "score": result["@search.score"],
                "metadata": {
                    "source": source_path,
                    "id": result.get("id", ""),
                    "query_used": query
                }
            })
        
        logger.info(f"Found {len(documents)} internal documents for query: '{query}'")
        return documents
    except Exception as e:
        logger.error(f"Error in search_internal_documents: {e}")
        return []

# --- API Endpoints ---

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to the Bullpen AI RAG System API",
        "version": app.version,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Performs a health check on the API and its dependent services."""
    try:
        if not search_client:
            raise HTTPException(status_code=503, detail="Search service not initialized")
        
        # A simple query to test the search client
        search_client.search(search_text="test", top=1)
        return {
            "status": "ok", 
            "version": app.version,
            "services": {
                "search": "connected" if search_client else "unavailable",
                "openai": "connected" if openai_client else "unavailable"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unavailable: {e}")

@app.get("/healthz")
async def healthz():
    """Kubernetes-style health check endpoint."""
    try:
        # Basic connectivity checks
        checks = {
            "api": "ok",
            "azure_search": "unknown",
            "azure_openai": "unknown",
            "perplexity": "unknown"
        }
        
        # Test Azure Search
        if search_client:
            try:
                search_client.search(search_text="test", top=1)
                checks["azure_search"] = "ok"
            except Exception as e:
                checks["azure_search"] = f"error: {str(e)}"
        else:
            checks["azure_search"] = "not initialized"
        
        # Test Azure OpenAI
        if openai_client:
            try:
                # Simple embedding test
                await get_embedding("test")
                checks["azure_openai"] = "ok"
            except Exception as e:
                checks["azure_openai"] = f"error: {str(e)}"
        else:
            checks["azure_openai"] = "not initialized"
        
        # Determine overall status
        overall_status = "ok" if all(v == "ok" or v == "unknown" for v in checks.values()) else "degraded"
        status_code = 200 if overall_status == "ok" else 503
        
        return {
            "status": overall_status,
            "version": app.version,
            "checks": checks,
            "environment": {
                "chat_model": AZURE_GPT4O_DEPLOYMENT if 'AZURE_GPT4O_DEPLOYMENT' in globals() else "not configured",
                "embedding_model": AZURE_OPENAI_EMBED_MODEL if 'AZURE_OPENAI_EMBED_MODEL' in globals() else "not configured",
                "search_index": AZURE_SEARCH_INDEX if 'AZURE_SEARCH_INDEX' in globals() else "not configured"
            }
        }
    except Exception as e:
        logger.error(f"Healthz check failed: {e}")
        return {"status": "error", "error": str(e)}, 503

@app.post("/chat")
async def chat(request: Request, chat_request: ChatRequest):
    """Intelligent chat endpoint with routing for internal, external, and hybrid queries."""
    async def stream_generator():
        try:
            # Step 1: Classify the query
            yield json.dumps({"type": "status", "content": "Confirming receipt, working on it now."}) + "\n\n"
            query_type = await classify_query(chat_request.message)
            
            internal_results = []
            external_results = None
            
            # Step 2: Execute search based on classification
            if query_type == "external":
                # External search only
                yield json.dumps({"type": "status", "content": "Searching the web for current information..."}) + "\n\n"
                external_results = await search_web(chat_request.message)
                
            elif query_type == "hybrid":
                # Hybrid search: both internal and external
                yield json.dumps({"type": "status", "content": "Searching internal documents..."}) + "\n\n"
                internal_results = await search_internal_documents(chat_request.message)
                
                yield json.dumps({"type": "status", "content": "Searching the web for market data..."}) + "\n\n"
                # Create a web search query focused on the external part
                web_query = f"cybersecurity SaaS companies ARR revenue multiples market data {chat_request.message}"
                external_results = await search_web(web_query)
                
            else:
                # Internal search only  
                yield json.dumps({"type": "status", "content": "Searching internal documents..."}) + "\n\n"
                internal_results = await search_internal_documents(chat_request.message)
            
            # Step 3: Handle results and generate response
            if query_type == "external":
                if not external_results:
                    error_message = {
                        "type": "content", 
                        "content": "I couldn't find current information about your query. Please try rephrasing your question."
                    }
                    yield json.dumps(error_message) + "\n\n"
                    yield "[DONE]\n\n"
                    return
                
                # Create prompt for external-only response
                final_prompt = f"""You are a concise financial analyst. 

STRICT RULES:
- Answer in 3-5 bullet points ONLY
- Each bullet: ONE key fact (≤20 words)
- End each bullet with [Source: specific name/date]
- NO introductions, NO conclusions, NO fluff

### Data:
{external_results}

### Question:
{chat_request.message}

ANSWER:"""

            elif query_type == "hybrid":
                if not internal_results and not external_results:
                    message = {
                        "type": "content",
                        "content": "I couldn't find relevant information in our documents or current market data."
                    }
                    yield json.dumps(message) + "\n\n"
                    yield "[DONE]\n\n"
                    return
                
                # Show internal sources if found
                if internal_results:
                    sources = [
                        {
                            "title": doc["title"],
                            "content": doc["snippet"], # Use the clean snippet
                            "score": doc["score"]
                        }
                        for doc in internal_results[:3]
                    ]
                    yield json.dumps({"type": "sources", "sources": sources}) + "\n\n"
                
                # Create comprehensive prompt for hybrid response
                internal_context = "\n\n".join([f"Document: {doc['title']}\n{doc['content']}" for doc in internal_results]) if internal_results else "No internal data found."
                external_context = external_results if external_results else "No external market data found."
                
                final_prompt = f"""You are a concise financial analyst.

STRICT RULES:
- Answer in 3-5 bullet points ONLY
- Each bullet: ONE key fact (≤20 words)
- End each bullet with [Source: document/website name]
- NO introductions, NO conclusions, NO fluff

### Internal Data:
{internal_context}

### External Data:
{external_context}

### Question:
{chat_request.message}

ANSWER:"""

            else:
                # Internal search only
                if not internal_results:
                    no_docs_message = "I couldn't find any relevant information in our internal documents to answer your question."
                    yield json.dumps({"type": "content", "content": no_docs_message}) + "\n\n"
                    yield "[DONE]\n\n"
                    return

                sources = [
                    {
                        "title": doc["title"],
                        "content": doc["snippet"], # Use the clean snippet
                        "score": doc["score"]
                    }
                    for doc in internal_results[:3]
                ]
                yield json.dumps({"type": "sources", "sources": sources}) + "\n\n"

                context = "\n\n".join([f"Title: {doc['title']}\nContent: {doc['content']}" for doc in internal_results])
                final_prompt = f"""You are a concise financial analyst.

STRICT RULES:
- Answer in 3-5 bullet points ONLY
- Each bullet: ONE key fact (≤20 words)
- End each bullet with [Source: document name]
- NO introductions, NO conclusions, NO fluff

### Documents:
{context}

### Question:
{chat_request.message}

ANSWER:"""

            # Define a context for error messages before calling the LLM
            error_context = "No specific information was retrieved before the error."
            if internal_results:
                error_context = "Based on our internal documents, I found:\n" + "\n".join([f"- {doc['title']}" for doc in internal_results[:3]])
            elif external_results:
                error_context = "Based on web search, I found some initial information."

            # Step 4: Generate streaming response
            yield json.dumps({"type": "status", "content": "Generating response..."}) + "\n\n"
            
            # Stream the response
            try:
                stream = openai_client.chat.completions.create(
                    model=AZURE_GPT4O_DEPLOYMENT,
                    messages=[
                        {"role": "system", "content": final_prompt},
                        {"role": "user", "content": chat_request.message}
                    ],
                    stream=True,
                    max_tokens=300,
                    temperature=0.2,
                    frequency_penalty=0.2
                )

                for chunk in stream:
                    if await request.is_disconnected():
                        logger.warning("Client disconnected, closing stream.")
                        break
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        yield json.dumps({"type": "content", "content": content}) + "\n\n"
            
            except Exception as chat_error:
                error_message = str(chat_error)
                logger.error(f"Error during chat generation: {error_message}", exc_info=True)
                
                # Create a more user-friendly error message
                if "DeploymentNotFound" in error_message:
                    error_response = f"""I apologize, but I'm having trouble accessing our AI model right now. Here's what I found that might help:

{error_context}

**Technical Details:** The AI model deployment '{AZURE_GPT4O_DEPLOYMENT}' was not found. Please verify:
- The deployment name is correct in your .env file
- The deployment is active in your Azure OpenAI resource
- You're using the correct Azure OpenAI endpoint

(Note: Our team has been notified and is working to restore full functionality.)"""
                elif "BadRequest" in error_message and "api versions" in error_message.lower():
                    error_response = f"""I encountered a technical issue, but let me share what I found that might help:

{error_context}

**Technical Details:** API version mismatch. Current version: {OPENAI_API_VERSION}
Please ensure this version is supported by your Azure OpenAI deployment.

(Note: Our team has been notified about the configuration issue.)"""
                elif "Unauthorized" in error_message or "401" in error_message:
                    error_response = f"""Authentication failed with Azure OpenAI. Here's what I found before the error:

{error_context}

**Technical Details:** Please verify your AZURE_OPENAI_KEY is correct and has proper permissions."""
                else:
                    error_response = f"""I apologize for the technical difficulty. While our team investigates, here's what I found in our documents:

{error_context}

**Error:** {error_message[:200]}..."""
                
                # Stream the error response in a natural way
                yield json.dumps({"type": "content", "content": error_response}) + "\n\n"
            
            yield "[DONE]\n\n"

        except Exception as e:
            logger.error(f"Error during chat generation: {e}", exc_info=True)
            error_message = json.dumps({"type": "error", "content": f"An unexpected error occurred: {e}"})
            yield f"{error_message}\n\n"
            yield "[DONE]\n\n"

    return EventSourceResponse(stream_generator())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 