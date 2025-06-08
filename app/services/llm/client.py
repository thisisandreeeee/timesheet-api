import base64
import json
import logging
import os
import re
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import httpx
import litellm
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


class LLMConfig(BaseModel):
    """LLM configuration settings."""
    provider: LLMProvider = Field(
        default_factory=lambda: os.getenv("DEFAULT_LLM_PROVIDER", LLMProvider.OPENAI)
    )
    model: str = Field(
        default_factory=lambda: os.getenv("DEFAULT_LLM_MODEL", "gpt-4-vision")
    )
    request_timeout: int = Field(
        default_factory=lambda: int(os.getenv("LLM_REQUEST_TIMEOUT", "60"))
    )
    max_retries: int = Field(
        default_factory=lambda: int(os.getenv("LLM_MAX_RETRIES", "3"))
    )
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    
    def get_model_string(self) -> str:
        """Get the litellm model string for the provider and model."""
        model_map = {
            LLMProvider.OPENAI: lambda m: m,  # OpenAI models are already in correct format
            LLMProvider.ANTHROPIC: lambda m: f"anthropic/{m}",
            LLMProvider.GEMINI: lambda m: f"gemini/{m}",
        }
        return model_map[self.provider](self.model)


class LLMClient:
    """Client for making API calls to LLMs using litellm."""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """Initialize the LLM client.
        
        Args:
            config: LLM configuration. If None, default config will be used.
        """
        self.config = config or LLMConfig()
        
        # Set API keys from environment
        litellm.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        litellm.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        # For Gemini, litellm uses the GOOGLE_API_KEY environment variable
        if os.getenv("GEMINI_API_KEY"):
            os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY", "")
        
        # Configure litellm
        litellm.request_timeout = self.config.request_timeout
        
    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, litellm.exceptions.ServiceUnavailableError)),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(lambda self: self.config.max_retries),
        reraise=True,
    )
    async def process_pdf(
        self,
        pdf_bytes: List[bytes],
        prompt: str,
        extract_keys: Optional[List[str]] = None,
        config: Optional[LLMConfig] = None,
    ) -> Dict[str, Any]:
        """Process PDF pages using vision LLM.
        
        Args:
            pdf_bytes: List of PDF page bytes to process
            prompt: The prompt to send to the LLM
            extract_keys: Optional list of keys to extract from the document
            config: Optional LLM configuration to override the default
            
        Returns:
            Dictionary containing LLM response data
        """
        # Use provided config or default
        config = config or self.config
        
        # Create prompts based on extraction needs
        system_prompt = "You are an expert document processor specialized in extracting information from PDFs."
        
        if extract_keys:
            fields_prompt = ", ".join(extract_keys)
            user_prompt = (
                f"Please extract the following fields from the PDF document: {fields_prompt}.\n"
                f"For each page, return a dictionary with 'page_number' and 'data' containing extracted fields.\n"
                f"Return the result as a JSON object with 'pages' as the key, containing an array of page results.\n"
                f"Example format: {{ 'pages': [{{ 'page_number': int, 'data': {{ 'field1': 'value1', ... }} }}, ...] }}"
            )
        else:
            user_prompt = (
                f"Extract all relevant information from this PDF document.\n"
                f"For each page, return a dictionary with 'page_number' and 'data' containing all extracted fields.\n"
                f"Return the result as a JSON object with 'pages' as the key, containing an array of page results.\n"
                f"Example format: {{ 'pages': [{{ 'page_number': int, 'data': {{ 'field1': 'value1', ... }} }}, ...] }}"
            )
        
        # Prepare PDF pages for the LLM
        pdf_contents = []
        for pdf_page in pdf_bytes:
            # Convert PDF page bytes to base64
            base64_pdf = base64.b64encode(pdf_page).decode("utf-8")
            
            # Add to message content
            pdf_contents.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:application/pdf;base64,{base64_pdf}",
                    "detail": "high"
                }
            })
        
        # Create the full message
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user", 
                "content": [
                    {"type": "text", "text": user_prompt},
                    *pdf_contents
                ]
            }
        ]
        
        try:
            logger.info(f"Sending PDF processing request to {config.provider} model {config.model}")
            
            # Make the API call
            response = await litellm.acompletion(
                model=config.get_model_string(),
                messages=messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                response_format={"type": "json_object"},
            )
            
            # Parse the response
            content = response.choices[0].message.content
            logger.info(f"Received response from LLM: {content[:100]}...")
            
            return self._parse_llm_response(content)
            
        except Exception as e:
            logger.error(f"Error calling LLM API: {str(e)}")
            raise
    
    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM response content into structured data.
        
        Args:
            content: LLM response content as string
            
        Returns:
            Dictionary containing parsed data
        """
        # First try direct JSON parsing
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # If direct parsing fails, try to extract JSON from content
            try:
                # Look for JSON-like structure in the content
                json_match = re.search(r'(\{.*\})', content, re.DOTALL)
                if json_match:
                    potential_json = json_match.group(1)
                    return json.loads(potential_json)
            except Exception:
                pass
            
            # If all parsing attempts fail, return error object
            return {
                "error": "Failed to parse LLM response as JSON",
                "raw_content": content
            }


# Create a default client instance
default_client = LLMClient() 