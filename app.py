import os
import streamlit as st
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get environment variables with validation
def get_env_config():
    api_key = os.getenv('CB_GPT_API_KEY')
    api_url = os.getenv('CB_GPT_API_URL', 'https://cb-gpt-api.coinbase.com/v1/completions')
    
    if not api_key or api_key == "your_api_key_here":
        st.error("⚠️ CB-GPT API key not found! Please set up your .env file with a valid API key.")
        st.stop()
    
    return api_key, api_url

# Configure page settings
st.set_page_config(
    page_title="DASAF powered by CB-GPT",
    page_icon="🔗",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .stTextInput > div > div > input {
        background-color: #f0f2f6;
    }
    .stSelectbox > div > div > select {
        background-color: #f0f2f6;
    }
    </style>
    """, unsafe_allow_html=True)

def query_cb_gpt(prompt, blockchain=None):
    """
    Query the CB-GPT API with the given prompt and blockchain context
    """
    # Get API configuration
    api_key, api_url = get_env_config()
    
    # Enhance prompt with blockchain context if provided
    if blockchain:
        context_prompt = f"Regarding the {blockchain} blockchain: {prompt}"
    else:
        context_prompt = prompt

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-4",
        "messages": [
            {
                "role": "system",
                "content": "You are a knowledgeable blockchain expert with deep understanding of blockchain documentation, whitepapers, consensus mechanisms, and technical implementations."
            },
            {
                "role": "user",
                "content": context_prompt
            }
        ]
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 401:
            return {"error": "Invalid API key. Please check your CB_GPT_API_KEY in the .env file."}
        elif isinstance(e, requests.exceptions.ConnectionError):
            return {"error": "Failed to connect to the API. Please check your internet connection and API URL."}
        elif isinstance(e, requests.exceptions.Timeout):
            return {"error": "Request timed out. The API server might be experiencing high load."}
        else:
            return {"error": f"An error occurred: {str(e)}"}

def main():
    st.title("🔗 Blockchain Information Query Tool")
    
    # Display API configuration status
    with st.sidebar:
        st.header("Configuration")
        try:
            api_key, api_url = get_env_config()
            st.success("✅ API Configuration loaded successfully")
            # Show masked API key
            masked_key = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else "***"
            st.code(f"API URL: {api_url}\nAPI Key: {masked_key}")
        except Exception as e:
            st.error(f"❌ API Configuration Error: {str(e)}")
        
        blockchain_options = [
            "General (No specific blockchain)",
            "Ethereum",
            "Solana",
            "Avalanche",
            "Polygon",
            "Binance Smart Chain",
            "Cardano"
        ]
        selected_blockchain = st.selectbox(
            "Select Blockchain",
            blockchain_options
        )
        
        st.markdown("---")
        st.markdown("### Query Categories")
        st.markdown("""
        - Consensus Mechanisms
        - Validator Requirements
        - Cryptographic Methods
        - Whitepapers & Documentation
        """)

    # Main content area
    query_type = st.radio(
        "Select Query Type",
        [
            "Consensus Mechanism",
            "Validator Requirements",
            "Cryptographic Methods",
            "Whitepaper & Documentation",
            "Custom Query"
        ]
    )

    # Pre-made prompts based on query type
    prompt_templates = {
        "Consensus Mechanism": "Explain the consensus mechanism, including how block producers are selected and the source of randomness.",
        "Validator Requirements": "What are the validator requirements, including minimum stake, hardware requirements, and rewards structure?",
        "Cryptographic Methods": "Describe the cryptographic methods used for transaction signing and block hashing.",
        "Whitepaper & Documentation": "Provide links and summaries of official whitepapers and developer documentation."
    }

    if query_type == "Custom Query":
        query = st.text_area("Enter your blockchain question:", height=100)
    else:
        query = prompt_templates[query_type]
        st.info(f"Using template: {query}")
        custom_query = st.text_area("Add additional details to your query (optional):", height=100)
        if custom_query:
            query = f"{query} {custom_query}"

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        search_button = st.button("🔍 Search", use_container_width=True)

    if search_button and query:
        with st.spinner("Fetching information..."):
            selected_chain = None if selected_blockchain == "General (No specific blockchain)" else selected_blockchain
            response = query_cb_gpt(query, selected_chain)
            
            if "error" in response:
                st.error(f"Error: {response['error']}")
            else:
                try:
                    answer = response["choices"][0]["message"]["content"]
                    
                    # Display the response in a nice format
                    st.markdown("### Response")
                    st.markdown(answer)
                    
                    # Add copy button
                    st.markdown("---")
                    st.markdown("Copy response to clipboard:")
                    st.code(answer)
                except (KeyError, IndexError) as e:
                    st.error("Error parsing the API response. Please try again.")

if __name__ == "__main__":
    main() 