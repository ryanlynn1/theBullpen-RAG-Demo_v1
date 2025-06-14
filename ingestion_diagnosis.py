#!/usr/bin/env python3
"""
Ingestion Diagnosis Script for the Bullpen RAG Demo

This script safely performs the following actions:
1.  Connects to Azure Blob Storage and Azure AI Search.
2.  Lists all files in your configured blob container.
3.  Queries the search index to find out which documents are already indexed.
4.  Compares the two lists to identify files that failed to ingest.
5.  Attempts to ingest a single missing file to capture the specific rate-limit error.
6.  Prints a summary report.

This script is READ-ONLY for your application code and will NOT modify it.
"""

import os
import sys
import traceback
import tempfile
from pathlib import Path
from typing import List, Set, Dict

from dotenv import load_dotenv
from colorama import init, Fore, Style

from azure.core.exceptions import HttpResponseError
from azure.storage.blob import BlobServiceClient
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import AzureOpenAIEmbeddings
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain.docstore.document import Document

# --- Setup and Configuration ---

# Initialize colorama
init(autoreset=True)

def print_status(message, status="info"):
    """Prints a colored status message."""
    if status == "success":
        print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")
    elif status == "error":
        print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")
    elif status == "warning":
        print(f"{Fore.YELLOW}⚠️  {message}{Style.RESET_ALL}")
    else:
        print(f"{Fore.BLUE}ℹ️  {message}{Style.RESET_ALL}")

# Load .env file from the project root
env_path = Path(__file__).parent.parent / '.env'
if not env_path.exists():
    env_path = Path('.env') # Fallback to current dir

if env_path.exists():
    print_status(f"Loading environment variables from: {env_path.resolve()}", "info")
    load_dotenv(dotenv_path=env_path)
else:
    print_status("No .env file found. Please ensure it is in the project root.", "error")
    sys.exit(1)

# Load configuration from environment
OPENAI_API_TYPE = os.getenv("OPENAI_API_TYPE", "azure")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION", "2024-02-01-preview")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_EMBED_MODEL = os.getenv("AZURE_OPENAI_EMBED_MODEL", "text-embedding-ada-002")
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")
AZURE_BLOB_CONN_STR = os.getenv("AZURE_BLOB_CONN_STR")
AZURE_BLOB_CONTAINER = os.getenv("AZURE_BLOB_CONTAINER")

# LangChain compatibility
os.environ["AZURE_OPENAI_API_KEY"] = AZURE_OPENAI_KEY

# --- Diagnostic Functions ---

def get_blobs_in_container() -> Set[str]:
    """Returns a set of all blob names in the container."""
    print_status("Connecting to Azure Blob Storage...", "info")
    try:
        service_client = BlobServiceClient.from_connection_string(AZURE_BLOB_CONN_STR)
        container_client = service_client.get_container_client(AZURE_BLOB_CONTAINER)
        blob_names = {blob.name for blob in container_client.list_blobs()}
        print_status(f"Found {len(blob_names)} files in container '{AZURE_BLOB_CONTAINER}'.", "success")
        return blob_names
    except Exception as e:
        print_status(f"Failed to connect to Blob Storage: {e}", "error")
        sys.exit(1)

def get_indexed_document_sources() -> Set[str]:
    """Queries the search index and returns a set of unique source document names."""
    print_status(f"Connecting to Azure AI Search index '{AZURE_SEARCH_INDEX}'...", "info")
    try:
        search_client = SearchClient(
            endpoint=AZURE_SEARCH_ENDPOINT,
            index_name=AZURE_SEARCH_INDEX,
            credential=AzureKeyCredential(AZURE_SEARCH_KEY)
        )
        
        # This assumes a large number of documents; for very large indexes, paging is needed.
        results = search_client.search(search_text="*", select="metadata", include_total_count=True)
        count = results.get_count()
        print_status(f"Index contains {count} total chunks.", "info")

        sources = set()
        for result in results:
            metadata = result.get("metadata")
            if isinstance(metadata, str):
                try:
                    import json
                    metadata = json.loads(metadata)
                except:
                    pass # Not json
            
            if isinstance(metadata, dict) and "source" in metadata:
                sources.add(metadata["source"])
            elif isinstance(metadata, str):
                sources.add(metadata) # Fallback if metadata is just the source string

        print_status(f"Found {len(sources)} unique source documents in the index.", "success")
        return sources
    except HttpResponseError as e:
        if "index_not_found" in e.message.lower():
            print_status(f"Search index '{AZURE_SEARCH_INDEX}' does not exist.", "warning")
            return set()
        print_status(f"Failed to query search index: {e}", "error")
        sys.exit(1)
    except Exception as e:
        print_status(f"An unexpected error occurred while querying the search index: {e}", "error")
        sys.exit(1)

def load_single_blob(blob_name: str) -> List[Document]:
    """Downloads and loads a single blob into LangChain documents."""
    service_client = BlobServiceClient.from_connection_string(AZURE_BLOB_CONN_STR)
    container_client = service_client.get_container_client(AZURE_BLOB_CONTAINER)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        blob_path = Path(tmpdir) / Path(blob_name).name
        print_status(f"Downloading '{blob_name}' for diagnosis...", "info")
        with open(blob_path, "wb") as f:
            downloader = container_client.download_blob(blob_name)
            f.write(downloader.readall())

        suffix = blob_path.suffix.lower()
        if suffix == ".pdf": loader = PyPDFLoader(str(blob_path))
        elif suffix in {".doc", ".docx"}: loader = Docx2txtLoader(str(blob_path))
        else: loader = TextLoader(str(blob_path), encoding="utf-8")
        
        file_docs = loader.load()
        for d in file_docs:
            d.metadata["source"] = blob_name
        return file_docs

def main():
    """Main diagnostic flow."""
    print("\n--- Starting Ingestion Diagnosis ---")
    
    # 1. Get file lists
    blobs = get_blobs_in_container()
    indexed_sources = get_indexed_document_sources()
    
    # 2. Find the difference
    missing_files = blobs - indexed_sources
    
    print("\n--- Diagnosis Report ---")
    if not missing_files:
        print_status("All documents in blob storage appear to be indexed.", "success")
        print(f"  - Total files in blob: {len(blobs)}")
        print(f"  - Unique sources in index: {len(indexed_sources)}")
        sys.exit(0)
    
    print_status(f"Found {len(missing_files)} file(s) in blob storage that are NOT in the search index:", "warning")
    for i, file in enumerate(missing_files):
        print(f"  {i+1}. {file}")
        if i > 10:
            print("  ...")
            break

    # 3. Try to ingest the first missing file to replicate the error
    target_file = list(missing_files)[0]
    print(f"\n--- Attempting to Ingest '{target_file}' to Capture Error ---")
    
    try:
        raw_docs = load_single_blob(target_file)
        
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs_to_ingest = splitter.split_documents(raw_docs)
        print_status(f"Split '{target_file}' into {len(docs_to_ingest)} chunks.", "info")

        embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            azure_deployment=AZURE_OPENAI_EMBED_MODEL,
            chunk_size=16  # Use a smaller chunk size to avoid client-side rate limits
        )
        
        vector_store = AzureSearch(
            azure_search_endpoint=AZURE_SEARCH_ENDPOINT,
            azure_search_key=AZURE_SEARCH_KEY,
            index_name=AZURE_SEARCH_INDEX,
            embedding_function=embeddings.embed_query, # Pass the function directly
        )

        print_status("Calling vector_store.add_documents()...", "info")
        vector_store.add_documents(documents=docs_to_ingest)
        
        print_status(f"Successfully ingested '{target_file}' this time.", "success")
        print_status("The issue might be intermittent or related to ingesting many files at once.", "warning")

    except HttpResponseError as e:
        print_status("Caught an Azure HTTP Response Error! This is likely the cause.", "error")
        print(f"\n{Fore.RED}--- Azure Error Details ---{Style.RESET_ALL}")
        print(f"Status Code: {e.status_code}")
        print(f"Reason: {e.reason}")
        print(f"Error Message: {e.message}")
        if e.status_code == 429:
            print("\nThis is a 'Too Many Requests' error. You are hitting a rate limit on the Azure Search or OpenAI service.")
            print("To fix this, you need to add retry logic with exponential backoff to `ingest_documents.py`.")
            
    except Exception as e:
        print_status(f"Caught a non-Azure exception during ingestion attempt: {type(e).__name__}", "error")
        print(f"\n{Fore.RED}--- Python Exception Details ---{Style.RESET_ALL}")
        print(traceback.format_exc())

    print("\n--- Diagnosis Complete ---")

if __name__ == "__main__":
    main() 