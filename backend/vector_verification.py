import os
import sys
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

def find_dotenv():
    """
    Finds the .env file by searching recursively upwards from the script's directory.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    while current_dir != os.path.dirname(current_dir): # Stop at root
        dotenv_path = os.path.join(current_dir, '.env')
        if os.path.exists(dotenv_path):
            print(f"✅ Found .env file at: {dotenv_path}")
            return dotenv_path
        current_dir = os.path.dirname(current_dir)
    return None

def verify_vectorization():
    """
    Connects to an Azure Cognitive Search index, retrieves a sample document,
    and checks for the presence of a 'vector' field to determine if the
    data has been vectorized.
    """
    try:
        # Load environment variables from .env file
        dotenv_path = find_dotenv()
        if dotenv_path:
            load_dotenv(dotenv_path=dotenv_path)
        else:
            print("❌ Error: .env file not found in the project root or parent directories.")
            sys.exit(1)


        # Get Azure Search configuration from environment variables
        search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        search_key = os.getenv("AZURE_SEARCH_KEY")
        index_name = os.getenv("AZURE_SEARCH_INDEX")

        if not all([search_endpoint, search_key, index_name]):
            print("❌ Error: Azure Search environment variables not set.")
            print("Please ensure AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY, and AZURE_SEARCH_INDEX are in your .env file.")
            return

        print(f"✅ Found all necessary environment variables.")
        print(f"   - Index Name: {index_name}")

        # Create a SearchClient
        credential = AzureKeyCredential(search_key)
        search_client = SearchClient(endpoint=search_endpoint,
                                     index_name=index_name,
                                     credential=credential)
        
        print(f"\n🔎 Connecting to Azure Search index '{index_name}'...")

        # Get the total document count
        doc_count = search_client.get_document_count()
        print(f"   - Index contains {doc_count} documents.")

        if doc_count == 0:
            print("\n⚠️ The index is empty. Cannot verify vectorization.")
            return

        # Retrieve the first document from the index
        print("   - Fetching a sample document to inspect its structure...")
        
        # Explicitly request specific fields including the vector field
        results = search_client.search(search_text="*", top=1, include_total_count=True, select="id,content,metadata,content_vector")
        
        sample_doc = next(iter(results), None)

        if not sample_doc:
            print("\n❌ Could not retrieve a sample document, even though the count is non-zero.")
            return

        print("   - Successfully fetched a sample document.")

        # --- Verification Logic ---
        print("\n🔍 Inspecting document fields...")
        fields = sample_doc.keys()
        print(f"   - Document contains the following fields: {list(fields)}")

        # Common names for vector fields
        vector_field_candidates = ['vector', 'contentVector', 'embedding', 'content_vector']
        found_vector_field = None
        
        for field in vector_field_candidates:
            if field in fields:
                found_vector_field = field
                break

        if found_vector_field:
            print(f"\n✅ Found a potential vector field: '{found_vector_field}'.")
            vector_content = sample_doc.get(found_vector_field)
            if isinstance(vector_content, list) and all(isinstance(x, (int, float)) for x in vector_content):
                print(f"   - The field contains a list of numbers (embedding).")
                print(f"   - Vector dimension: {len(vector_content)}")
                print("\n🎉 Verdict: Your data appears to be VECTORIZED.")
            else:
                print(f"   - The field '{found_vector_field}' does not contain a valid vector (list of numbers).")
                print("\n❌ Verdict: Your data is NOT VECTORIZED, although a potential vector field exists.")
        else:
            print("\n❌ No common vector field ('vector', 'contentVector', 'embedding', 'content_vector') found in the document.")
            print("\n🔍 Note: Vector fields are often not marked as 'retrievable' in Azure Search indexes.")
            print("   This means they exist and work for search operations, but aren't returned in results.")
            print("   To verify if vector search is working, try running a semantic search query.")
            print("\n⚠️  Verdict: Vector field not visible in results (this may be normal behavior).")

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        print("Please check your Azure credentials and network connection.")

if __name__ == "__main__":
    verify_vectorization() 