#!/usr/bin/env python3
"""Debug Azure OpenAI connection issues."""
import os
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load environment variables
load_dotenv('.env')

print("🔍 Azure OpenAI Debug Information:\n")

# Print configuration
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_version = os.getenv("OPENAI_API_VERSION")
embed_model = os.getenv("AZURE_OPENAI_EMBED_MODEL")

print(f"Endpoint: {endpoint}")
print(f"API Version: {api_version}")
print(f"Embedding Deployment: {embed_model}")
print(f"Key Present: {'Yes' if os.getenv('AZURE_OPENAI_KEY') else 'No'}")

print("\n🧪 Testing connection...\n")

try:
    # Try with different API versions
    versions_to_try = [api_version, "2023-05-15", "2024-02-01", "2023-12-01-preview"]
    
    for version in versions_to_try:
        print(f"Trying API version: {version}")
        try:
            client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=os.getenv("AZURE_OPENAI_KEY"),
                api_version=version
            )
            
            response = client.embeddings.create(
                input="test",
                model=embed_model
            )
            
            print(f"✅ SUCCESS with version {version}!")
            print(f"   Embedding dimensions: {len(response.data[0].embedding)}")
            print(f"\n💡 Update your .env file:")
            print(f"   OPENAI_API_VERSION={version}")
            break
            
        except Exception as e:
            print(f"❌ Failed with {version}: {str(e)}\n")
            
except Exception as e:
    print(f"❌ General error: {str(e)}") 