"""
Bullpen RAG Chat Interface - ChatGPT Style
A sleek chat interface that queries your indexed documents and provides AI responses.
"""

import os
import streamlit as st
from dotenv import load_dotenv
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain_community.embeddings import AzureOpenAIEmbeddings
import time

# Load environment variables
load_dotenv()

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
os.environ["AZURE_OPENAI_API_KEY"] = AZURE_OPENAI_KEY
AZURE_OPENAI_EMBED_MODEL = os.getenv("AZURE_OPENAI_EMBED_MODEL", "embed-thebullpen")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION", "2023-05-15")

# Azure AI Search Configuration
AZURE_SEARCH_ENDPOINT = os.environ["AZURE_SEARCH_ENDPOINT"]
AZURE_SEARCH_KEY = os.environ["AZURE_SEARCH_KEY"]
AZURE_SEARCH_INDEX = os.environ["AZURE_SEARCH_INDEX"]

# Page configuration
st.set_page_config(
    page_title="Bullpen RAG Chat",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for ChatGPT-like styling
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border: none;
    }
    
    .stChatMessage[data-testid="chat-message-user"] {
        background-color: #f7f7f8;
        margin-left: 20%;
    }
    
    .stChatMessage[data-testid="chat-message-assistant"] {
        background-color: #ffffff;
        border: 1px solid #e5e5e5;
    }
    
    .chat-header {
        text-align: center;
        padding: 2rem 0;
        border-bottom: 1px solid #e5e5e5;
        margin-bottom: 2rem;
    }
    
    .chat-title {
        font-size: 2rem;
        font-weight: 600;
        color: #1f2937;
        margin-bottom: 0.5rem;
    }
    
    .chat-subtitle {
        color: #6b7280;
        font-size: 1rem;
    }
    
    .source-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 0.375rem;
        padding: 0.75rem;
        margin-top: 1rem;
        font-size: 0.875rem;
    }
    
    .source-title {
        font-weight: 600;
        color: #374151;
        margin-bottom: 0.5rem;
    }
    
    .thinking {
        color: #6b7280;
        font-style: italic;
    }
    
    .stTextInput > div > div > input {
        border-radius: 1.5rem;
        border: 2px solid #e5e7eb;
        padding: 0.75rem 1rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    .search-result {
        background-color: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .result-title {
        font-weight: 600;
        color: #1f2937;
        margin-bottom: 0.5rem;
    }
    
    .result-content {
        color: #374151;
        line-height: 1.6;
    }
    
    .result-source {
        color: #6b7280;
        font-size: 0.875rem;
        margin-top: 0.5rem;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def initialize_vector_store():
    """Initialize the vector store with caching for better performance."""
    try:
        # Initialize embeddings
        embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            azure_deployment=AZURE_OPENAI_EMBED_MODEL,
            model="text-embedding-ada-002",
            openai_api_version=OPENAI_API_VERSION,
            chunk_size=1000,
        )
        
        # Initialize vector store
        vector_store = AzureSearch(
            azure_search_endpoint=AZURE_SEARCH_ENDPOINT,
            azure_search_key=AZURE_SEARCH_KEY,
            index_name=AZURE_SEARCH_INDEX,
            embedding_function=embeddings,
        )
        
        return vector_store
        
    except Exception as e:
        st.error(f"Failed to initialize vector store: {str(e)}")
        return None

def search_documents(vector_store, query, k=4):
    """Search for relevant documents."""
    try:
        results = vector_store.similarity_search_with_score(query, k=k)
        return results
    except Exception as e:
        st.error(f"Search failed: {str(e)}")
        return []

def format_search_results(results):
    """Format search results for display."""
    if not results:
        return "No relevant documents found."
    
    formatted_results = "Based on your documents, here's what I found:\n\n"
    
    for i, (doc, score) in enumerate(results, 1):
        source_name = doc.metadata.get('source', 'Unknown Document')
        content = doc.page_content
        
        # Truncate content if too long
        if len(content) > 300:
            content = content[:300] + "..."
        
        formatted_results += f"**📄 Result {i} - {source_name}**\n"
        formatted_results += f"{content}\n"
        formatted_results += f"*Relevance Score: {score:.3f}*\n\n"
    
    return formatted_results

def create_summary_response(results, query):
    """Create a summary response based on search results."""
    if not results:
        return "I couldn't find any relevant information in your documents for that query."
    
    # Simple response generation based on search results
    response = f"Based on your query about '{query}', I found {len(results)} relevant document(s):\n\n"
    
    for i, (doc, score) in enumerate(results, 1):
        source_name = doc.metadata.get('source', 'Unknown Document')
        content = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
        
        response += f"**{i}. From {source_name}:**\n{content}\n\n"
    
    response += "💡 *Note: For more detailed AI-generated responses, please add a chat model deployment (like GPT-3.5-turbo) to your Azure OpenAI resource.*"
    
    return response

def main():
    # Header
    st.markdown("""
    <div class="chat-header">
        <div class="chat-title">🏢 Bullpen Document Search</div>
        <div class="chat-subtitle">Search and explore your business documents</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize the vector store
    if 'vector_store' not in st.session_state:
        with st.spinner("🔄 Initializing document search..."):
            st.session_state.vector_store = initialize_vector_store()
    
    if st.session_state.vector_store is None:
        st.error("❌ Failed to initialize the document search. Please check your configuration.")
        return
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant", 
                "content": "Hello! I'm your Bullpen Document Search Assistant. I can help you find information from your business documents. What would you like to search for?"
            }
        ]
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message:
                with st.expander("📚 View Detailed Results"):
                    st.markdown(message["sources"])
    
    # Chat input
    if prompt := st.chat_input("Search your documents..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("🔍 Searching documents..."):
                try:
                    # Search for relevant documents
                    results = search_documents(st.session_state.vector_store, prompt, k=4)
                    
                    # Create response
                    response = create_summary_response(results, prompt)
                    
                    # Display the response
                    st.markdown(response)
                    
                    # Format detailed results for expandable section
                    if results:
                        detailed_results = "**📚 Detailed Search Results:**\n\n"
                        for i, (doc, score) in enumerate(results, 1):
                            source_name = doc.metadata.get('source', 'Unknown Document')
                            content = doc.page_content
                            detailed_results += f"**{i}. {source_name}** (Score: {score:.3f})\n"
                            detailed_results += f"{content}\n\n---\n\n"
                        
                        with st.expander("📚 View Detailed Results"):
                            st.markdown(detailed_results)
                        
                        # Add assistant message to chat history
                        message_data = {
                            "role": "assistant", 
                            "content": response,
                            "sources": detailed_results
                        }
                    else:
                        message_data = {"role": "assistant", "content": response}
                    
                    st.session_state.messages.append(message_data)
                    
                except Exception as e:
                    error_msg = f"❌ Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # Sidebar with information
    with st.sidebar:
        st.markdown("### 🔧 System Info")
        st.markdown(f"**Index:** {AZURE_SEARCH_INDEX}")
        st.markdown(f"**Embedding Model:** {AZURE_OPENAI_EMBED_MODEL}")
        st.markdown("---")
        
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = [
                {
                    "role": "assistant", 
                    "content": "Hello! I'm your Bullpen Document Search Assistant. I can help you find information from your business documents. What would you like to search for?"
                }
            ]
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 💡 Search Tips")
        st.markdown("""
        - Ask about specific deals, companies, or projects
        - Search for financial terms or metrics
        - Look for contract details or agreements
        - Find information about specific people or roles
        """)
        
        st.markdown("---")
        st.markdown("### 🚀 Upgrade to Full Chat")
        st.markdown("""
        To get AI-generated responses instead of just search results:
        
        1. Go to Azure OpenAI Studio
        2. Create a GPT-3.5-turbo or GPT-4 deployment
        3. Update the chat app configuration
        """)

if __name__ == "__main__":
    main() 