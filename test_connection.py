#!/usr/bin/env python3
"""
Test connection to Azure OpenAI and Azure Search services.
Run this to verify your .env configuration is correct.
"""
import os
import sys
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

# Load environment variables
load_dotenv('.env')

def test_connections():
    print("🔍 Testing Azure Service Connections...\n")
    
    # Check environment variables
    azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_openai_key = os.getenv("AZURE_OPENAI_KEY")
    search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    search_key = os.getenv("AZURE_SEARCH_KEY")
    search_index = os.getenv("AZURE_SEARCH_INDEX")
    
    errors = []
    
    # Test Azure OpenAI
    print("1️⃣ Testing Azure OpenAI Connection...")
    if not azure_openai_endpoint:
        errors.append("❌ AZURE_OPENAI_ENDPOINT not found in environment")
        print("  ❌ Missing AZURE_OPENAI_ENDPOINT")
        print("  💡 Update AZURE_OPENAI_ENDPOINT in .env")
    elif not azure_openai_key:
        errors.append("❌ AZURE_OPENAI_KEY not found in environment")
        print("  ❌ Missing AZURE_OPENAI_KEY")
        print("  💡 Update AZURE_OPENAI_KEY in .env")
    else:
        try:
            client = AzureOpenAI(
                azure_endpoint=azure_openai_endpoint,
                api_key=azure_openai_key,
                api_version=os.getenv("OPENAI_API_VERSION", "2024-02-01-preview")
            )
            # Test with a simple embedding call
            response = client.embeddings.create(
                input="test",
                model=os.getenv("AZURE_OPENAI_EMBED_MODEL", "text-embedding-ada-002")
            )
            print("  ✅ Azure OpenAI connection successful!")
            print(f"  📊 Embedding dimension: {len(response.data[0].embedding)}")
            print(f"  🔧 Using deployment: {os.getenv('AZURE_OPENAI_EMBED_MODEL')}")
        except Exception as e:
            errors.append(f"❌ Azure OpenAI connection failed: {str(e)}")
            print(f"  ❌ Connection failed: {str(e)}")
    
    print()
    
    # Test Azure Search
    print("2️⃣ Testing Azure Search Connection...")
    if not search_endpoint:
        errors.append("❌ AZURE_SEARCH_ENDPOINT not found in environment")
        print("  ❌ Missing AZURE_SEARCH_ENDPOINT")
        print("  💡 Update AZURE_SEARCH_ENDPOINT in .env")
    elif not search_key:
        errors.append("❌ AZURE_SEARCH_KEY not found in environment")
        print("  ❌ Missing AZURE_SEARCH_KEY")
        print("  💡 Update AZURE_SEARCH_KEY in .env")
    elif not search_index:
        errors.append("❌ AZURE_SEARCH_INDEX not found in environment")
        print("  ❌ Missing AZURE_SEARCH_INDEX")
        print("  💡 Update AZURE_SEARCH_INDEX in .env")
    else:
        try:
            search_client = SearchClient(
                endpoint=search_endpoint,
                index_name=search_index,
                credential=AzureKeyCredential(search_key)
            )
            # Test with a simple search
            results = search_client.search(search_text="test", top=1)
            count = sum(1 for _ in results)
            print("  ✅ Azure Search connection successful!")
            print(f"  📚 Index: {search_index}")
            print(f"  🔍 Test search returned {count} result(s)")
        except Exception as e:
            errors.append(f"❌ Azure Search connection failed: {str(e)}")
            print(f"  ❌ Connection failed: {str(e)}")
    
    print("\n" + "="*50 + "\n")
    
    if errors:
        print("❌ Connection tests failed with errors:")
        for error in errors:
            print(f"  • {error}")
        return False
    else:
        print("✅ All connections successful! Your environment is properly configured.")
        return True

if __name__ == "__main__":
    success = test_connections()
    sys.exit(0 if success else 1) 