import json
import os
import logging
from cb_ai_agentkit.cb_gpt_service.cb_gpt_service_api_client import CbGptServiceApiClient
from cb_ai_agentkit.config import CbGptEnv
import streamlit as st
from requests.exceptions import RequestException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CbGptClient:
    def __init__(self):
        """Initialize the CB-GPT client with credentials."""
        try:
            credentials = self._load_credentials()
            self.client = self._initialize_client(credentials)
            logger.info("CB-GPT client initialized successfully")
        except Exception as e:
            error_msg = f"Error initializing CB-GPT client: {str(e)}"
            logger.error(error_msg)
            st.error(error_msg)
            raise

    def _load_credentials(self):
        """Load API credentials from file."""
        try:
            with open('cdp_api_key.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError("Credentials file (cdp_api_key.json) not found")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in credentials file: {str(e)}")

    def _initialize_client(self, credentials):
        """Initialize the CB-GPT service client."""
        api_key = os.getenv("CB_AI_AGENTKIT_API_KEY", credentials['name'])
        api_secret = os.getenv("CB_AI_AGENTKIT_API_SECRET", credentials['privateKey'])
        
        return CbGptServiceApiClient(
            cdp_api_key=api_key,
            cdp_api_secret=api_secret,
            cb_gpt_env=CbGptEnv.PROD
        )

    def _make_request(self, system_prompt, user_prompt):
        """Make a request to CB-GPT with specific prompts."""
        try:
            request_body = self._prepare_request(system_prompt, user_prompt)
            return self._execute_request(request_body)
        except Exception as e:
            error_msg = f"Error querying CB-GPT: {str(e)}"
            logger.error(error_msg)
            st.error(error_msg)
            return None

    def _prepare_request(self, system_prompt, user_prompt):
        """Prepare the request body with prompts."""
        standard_disclaimer = (
            "Respond only with factual, publicly available information. "
            "Do not speculate, assume, hallucinate, or generate unverifiable content. "
            "If a clear, direct answer is Not verifiable with public information, "
            "state 'Not verifiable with public information' and explain why. "
            "Link to sources where possible. "
            "Keep responses brief, cohesive, and without excessive formatting or headings"
        )
        
        full_system_prompt = f"{standard_disclaimer}\n\n{system_prompt}" if system_prompt else standard_disclaimer
        
        return json.dumps({
            "messages": [
                {"role": "system", "content": full_system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False
        })

    def _execute_request(self, request_body):
        """Execute the request and process the response."""
        try:
            logger.info("Making request to CB-GPT service...")
            response = self.client.generate_content(
                model_id="o4-mini",
                request_body=request_body,
                redaction_required=False,
                uses_multimodal=False,
                incognito=False,
                or_component_id="blockchain_security_analysis"
            )
            logger.info("Received response from CB-GPT service")
            
            return self._process_response(response)
        except RequestException as e:
            error_msg = f"Network error while calling CB-GPT service: {str(e)}"
            logger.error(error_msg)
            st.error(error_msg)
            return None

    def _process_response(self, response):
        """Process and validate the response from CB-GPT."""
        if not isinstance(response, dict) or 'response' not in response:
            logger.error(f"Unexpected response format: {response}")
            st.error("Received invalid response from CB-GPT service")
            return None

        try:
            inner_response = json.loads(response['response'])
            if isinstance(inner_response, dict) and 'choices' in inner_response:
                choices = inner_response['choices']
                if choices and len(choices) > 0:
                    message = choices[0].get('message', {})
                    if message and 'content' in message:
                        return message['content']
            
            logger.error(f"Unexpected response format: {response}")
            st.error("Received unexpected response format from CB-GPT service")
            return None
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse response JSON: {str(e)}"
            logger.error(error_msg)
            st.error(error_msg)
            return None

    def analyze_blockchain_security(self, blockchain_name, risk_prompt, block_explorer_url=None):
        """Analyze blockchain security based on provided risk prompt."""
        system_prompt = """You are a blockchain security expert analyzing security risks.
Follow these steps:
1. Address the specific security risk asked
2. Provide concrete examples and data where possible
3. Cite all sources used
4. Only use factual, publicly verifiable information"""

        user_prompt = f"""Analyze the security of {blockchain_name} blockchain.
{f'Use block explorer at {block_explorer_url} for data.' if block_explorer_url else ''}
{risk_prompt}"""

        return self._make_request(system_prompt, user_prompt)

def test_client():
    """Test the CB-GPT client functionality."""
    try:
        client = CbGptClient()
        test_cases = [
            {
                "name": "Validator Distribution Analysis",
                "func": lambda: client.analyze_blockchain_security(
                    "Test Chain",
                    "Analyze validator distribution",
                    "https://example.com/explorer"
                )
            }
        ]

        for test in test_cases:
            print(f"\nTesting {test['name']}:")
            print("=" * 80)
            response = test['func']()
            print(response if response else "No response")
            print("=" * 80)

    except Exception as e:
        print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    test_client()
