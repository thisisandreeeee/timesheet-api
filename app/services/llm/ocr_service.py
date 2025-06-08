import json
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
            return self._format_results(results)
            
        except Exception as e:
            logger.error(f"Error processing document with LLM: {str(e)}")
            # Return an error result with all required fields
            return [{
                "page_number": 1,
                "confidence": "low",
                "text": f"Error processing document: {str(e)}",
                "data": {}
            }]
    
    def _format_results(self, results: Any) -> List[Dict[str, Any]]:
        """Format and standardize LLM results.
        
        Args:
            results: Raw results from LLM
            
        Returns:
            List of formatted page results
        """
        # Initialize empty result list
        page_results = []
        
        # Handle different result formats
        if isinstance(results, dict):
            if "pages" in results and isinstance(results["pages"], list):
                # Use the pages list directly
                page_results = results["pages"]
            elif "error" in results and "raw_content" in results:
                # Try to parse raw_content as JSON
                try:
                    parsed_content = json.loads(results["raw_content"])
                    if isinstance(parsed_content, dict) and "pages" in parsed_content:
                        page_results = parsed_content["pages"]
                    else:
                        page_results = [parsed_content]
                except (json.JSONDecodeError, TypeError):
                    page_results = [results]
            else:
                # Create a single page result
                page_results = [results]
        elif isinstance(results, list):
            # Use the list directly
            page_results = results
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
            
            # Create standardized result structure
            formatted_result = {
                "page_number": result.get("page_number", i + 1),
                "text": result.get("text", ""),
                "confidence": result.get("confidence", "medium"),
                "data": {}
            }
            
            # Extract data fields
            if "data" in result and isinstance(result["data"], dict):
                formatted_result["data"] = result["data"]
            else:
                # Move all fields except standard ones to data
                data = {}
                keys_to_exclude = ["page_number", "text", "confidence"]
                for key, value in result.items():
                    if key not in keys_to_exclude:
                        data[key] = value
                formatted_result["data"] = data
            
            formatted_results.append(formatted_result)
        
        return formatted_results


# Create a default OCR service instance
default_ocr_service = OCRService() 