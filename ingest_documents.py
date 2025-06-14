"""Ingest documents from Azure Blob Storage into Azure AI Search as vector embeddings.

Prerequisites (all set via a .env file in project root):
    OPENAI_API_TYPE=azure
    OPENAI_API_VERSION=2024-02-01-preview
    AZURE_OPENAI_ENDPOINT=<https://your-oai.openai.azure.com>
    AZURE_OPENAI_KEY=<YOUR_OAI_KEY>
    AZURE_OPENAI_MODEL=gpt-35-turbo
    AZURE_OPENAI_EMBED_MODEL=text-embedding-ada-002

    AZURE_SEARCH_ENDPOINT=<https://your-search.search.windows.net>
    AZURE_SEARCH_KEY=<YOUR_SEARCH_ADMIN_KEY>
    AZURE_SEARCH_INDEX=bullpen-index

    AZURE_BLOB_CONN_STR="DefaultEndpointsProtocol=..."  # full connection string
    AZURE_BLOB_CONTAINER=bullpen-docs

Install extras if missing:
    pip install python-dotenv langchain langchain-community azure-search-documents azure-identity azure-storage-blob pypdf python-docx tiktoken
"""

import os
import tempfile
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import AzureOpenAIEmbeddings
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain.docstore.document import Document
from tenacity import retry, stop_after_attempt, wait_random_exponential

# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

load_dotenv()

# Load configuration from environment
OPENAI_API_TYPE = os.getenv("OPENAI_API_TYPE", "azure")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION", "2024-02-01-preview")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_EMBED_MODEL = os.getenv("AZURE_OPENAI_EMBED_MODEL", "text-embedding-ada-002")

# Azure AI Search configuration
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")

# Azure Blob Storage configuration
AZURE_BLOB_CONN_STR = os.getenv("AZURE_BLOB_CONN_STR")
AZURE_BLOB_CONTAINER = os.getenv("AZURE_BLOB_CONTAINER")

# Validate required environment variables
required_vars = {
    "AZURE_OPENAI_ENDPOINT": AZURE_OPENAI_ENDPOINT,
    "AZURE_OPENAI_KEY": AZURE_OPENAI_KEY,
    "AZURE_SEARCH_ENDPOINT": AZURE_SEARCH_ENDPOINT,
    "AZURE_SEARCH_KEY": AZURE_SEARCH_KEY,
    "AZURE_SEARCH_INDEX": AZURE_SEARCH_INDEX,
    "AZURE_BLOB_CONN_STR": AZURE_BLOB_CONN_STR,
    "AZURE_BLOB_CONTAINER": AZURE_BLOB_CONTAINER
}

missing_vars = [var for var, value in required_vars.items() if not value]
if missing_vars:
    print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
    print("Please check your .env file.")
    exit(1)

# Set AZURE_OPENAI_API_KEY for LangChain compatibility
os.environ["AZURE_OPENAI_API_KEY"] = AZURE_OPENAI_KEY

# ---------------------------------------------------------------------------
# Loader helpers
# ---------------------------------------------------------------------------

def load_blob_documents() -> List[Document]:
    """Downloads blobs into temp files and returns LangChain Documents."""
    service_client = BlobServiceClient.from_connection_string(AZURE_BLOB_CONN_STR)
    container_client = service_client.get_container_client(AZURE_BLOB_CONTAINER)

    docs: List[Document] = []
    
    # Define valid extensions to process
    valid_extensions = {".pdf", ".docx", ".doc", ".txt", ".md"}

    with tempfile.TemporaryDirectory() as tmpdir:
        for blob in container_client.list_blobs():
            blob_name: str = blob.name
            
            # --- FIX: Skip irrelevant files like .DS_Store ---
            blob_path_obj = Path(blob_name)
            if blob_path_obj.name.startswith('.') or blob_path_obj.suffix.lower() not in valid_extensions:
                print(f"⏩ Skipping non-document file: {blob_name}")
                continue
            # --- END FIX ---

            blob_path = Path(tmpdir) / blob_path_obj.name
            print(f"Downloading {blob_name} -> {blob_path}")
            try:
                with open(blob_path, "wb") as f:
                    downloader = container_client.download_blob(blob)
                    f.write(downloader.readall())
            except Exception as e:
                print(f"Failed to download {blob_name}: {e}")
                continue # Skip to next blob

            # Decide loader based on extension
            suffix = blob_path.suffix.lower()
            if suffix == ".pdf":
                loader = PyPDFLoader(str(blob_path))
            elif suffix in {".doc", ".docx"}:
                loader = Docx2txtLoader(str(blob_path))
            else:
                loader = TextLoader(str(blob_path), encoding="utf-8")

            try:
                file_docs = loader.load()
                # attach metadata about original blob name
                for d in file_docs:
                    d.metadata["source"] = blob_name
                docs.extend(file_docs)
            except Exception as e:
                print(f"Failed to parse {blob_name}: {e}")

    return docs


def chunk_documents(documents: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    chunked_docs: List[Document] = splitter.split_documents(documents)
    print(f"Chunked into {len(chunked_docs)} documents")
    return chunked_docs

# ---------------------------------------------------------------------------
# Main ingestion flow
# ---------------------------------------------------------------------------

def main() -> None:
    print("Loading documents from Blob Storage…")
    raw_docs = load_blob_documents()
    print(f"Loaded {len(raw_docs)} raw documents")

    docs = chunk_documents(raw_docs)

    print("Creating Azure OpenAI embedding client…")
    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        azure_deployment=AZURE_OPENAI_EMBED_MODEL,
        model="text-embedding-ada-002",
        openai_api_version=OPENAI_API_VERSION,
        chunk_size=16,  # Use a smaller chunk size to manage request size
    )

    print("Connecting to / creating Azure AI Search vector store…")
    vector_store = AzureSearch(
        azure_search_endpoint=AZURE_SEARCH_ENDPOINT,
        azure_search_key=AZURE_SEARCH_KEY,
        index_name=AZURE_SEARCH_INDEX,
        embedding_function=embeddings.embed_query,
    )
    
    # --- FIX: Add robust retry logic for adding documents ---
    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
    def add_documents_with_retry(docs_to_add):
        """A wrapper function to apply tenacity retry logic."""
        print(f"Attempting to add {len(docs_to_add)} documents to the index...")
        vector_store.add_documents(documents=docs_to_add)

    print("Adding documents to the index with retry logic (this may take a while)…")
    # To avoid hitting limits, add documents in smaller batches
    batch_size = 100 
    for i in range(0, len(docs), batch_size):
        batch = docs[i:i + batch_size]
        try:
            add_documents_with_retry(batch)
            print(f"✅ Successfully added batch {i//batch_size + 1}/{(len(docs)-1)//batch_size + 1}")
        except Exception as e:
            print(f"❌ Failed to add a batch after several retries: {e}")
            print("Moving to the next batch.")
            continue
    # --- END FIX ---
    
    print("✅ Ingestion complete!")


if __name__ == "__main__":
    main() 