import logging
from typing import Any, Dict, List, Optional

from app.services.llm.client import LLMClient, LLMConfig, default_client
from app.services.llm.config import config_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OCRService:
    """Service for performing OCR on documents using LLM."""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize the OCR service.
        
        Args:
            llm_client: LLM client to use. If None, default client will be used.
        """
        self.llm_client = llm_client or default_client
    
    async def process_document(
        self,
        pdf_pages: List[bytes],
        extract_keys: Optional[List[str]] = None,
        route_path: Optional[str] = None,
        custom_prompt: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Process document PDF pages using LLM-based OCR.
        
        Args:
            pdf_pages: List of document page PDFs as bytes
            extract_keys: Optional list of keys to extract from the document
            route_path: Optional API route path to get specific LLM config
            custom_prompt: Optional custom prompt to use for the LLM
            
        Returns:
            List of dictionaries with OCR results for each page
        """
        # Get route-specific LLM config if available
        llm_config = config_manager.get_config(route_path)
        logger.info(f"Using LLM config for route {route_path}: {llm_config}")
        
        # Define the prompt for OCR
        prompt = custom_prompt or "Extract data from the following PDF document pages."
        
        # Process all pages with the LLM
        try:
            results = await self.llm_client.process_pdf(
                pdf_bytes=pdf_pages,
                prompt=prompt,
                extract_keys=extract_keys,
                config=llm_config
            )
            
            logger.info(f"Raw LLM results: {str(results)[:500]}...")
            
            # Structure the results by page
            page_results = []
            
            # Check if the results contain a 'pages' key with a list
            if isinstance(results, dict) and "pages" in results and isinstance(results["pages"], list):
                # Use the pages list directly
                page_results = results["pages"]
            # Check if we got a list directly
            elif isinstance(results, list):
                # Use the list directly
                page_results = results
            # Check if we have a single result dictionary
            elif isinstance(results, dict):
                # If there's an error key, try to extract nested JSON from raw_content
                if "error" in results and "raw_content" in results:
                    import json
                    try:
                        # Try to parse raw_content as JSON
                        raw_content = results["raw_content"]
                        parsed_content = json.loads(raw_content)
                        
                        # Check if parsed content has pages
                        if isinstance(parsed_content, dict) and "pages" in parsed_content:
                            page_results = parsed_content["pages"]
                        else:
                            # Create a single page result
                            page_results = [parsed_content]
                    except (json.JSONDecodeError, TypeError):
                        # If parsing fails, use the original dict
                        page_results = [results]
                else:
                    # Create a single page result
                    page_results = [results]
            else:
                # Handle unexpected result type
                logger.error(f"Unexpected result type from LLM: {type(results)}")
                page_results = [{"error": "Unexpected result format from LLM"}]
            
            # Format the results to include page numbers
            formatted_results = []
            for i, result in enumerate(page_results):
                if not isinstance(result, dict):
                    logger.warning(f"Unexpected page result type: {type(result)}")
                    result = {"error": f"Unexpected page result type: {type(result)}"}
                
                # Add page number if not already present
                if "page_number" not in result:
                    result["page_number"] = i + 1
                
                # Add data field if not already present
                if "data" not in result:
                    # Move all fields except page_number, confidence, and text to data
                    data = {}
                    keys_to_exclude = ["page_number"]
                    for key, value in list(result.items()):
                        if key not in keys_to_exclude:
                            data[key] = value
                            # Remove from top level
                            del result[key]
                    result["data"] = data
                
                # Ensure data is a dictionary
                if not isinstance(result["data"], dict):
                    logger.warning(f"Data is not a dictionary: {result['data']}")
                    result["data"] = {}
                
                formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error processing document with LLM: {str(e)}")
            # Return an error result with all required fields
            return [{
                "page_number": 1,
                "confidence": "low",
                "text": f"Error processing document: {str(e)}",
                "data": {}
            }]


# Create a default OCR service instance
default_ocr_service = OCRService() 