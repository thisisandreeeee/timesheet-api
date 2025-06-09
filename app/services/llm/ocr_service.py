import base64
import json
import logging
from typing import Any, Dict, List, Optional

from app.services.llm.client import LLMClient, default_client
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
        route_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Process document PDF pages using LLM-based OCR.
        
        Args:
            pdf_pages: List of document page PDFs as bytes
            route_path: Optional API route path to get specific LLM config
            
        Returns:
            List of dictionaries with OCR results for each page
        """
        # Get route-specific LLM config if available
        llm_config = config_manager.get_config(route_path)
        logger.info(f"Using LLM config for route {route_path}: {llm_config}")
        
        # Create the messages for the LLM request
        messages = self._create_pdf_messages(pdf_pages)
        
        # Process all pages with the LLM
        try:
            results = await self.llm_client.completion(
                messages=messages,
                config=llm_config,
                response_format={"type": "json_object"},
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
    
    def _create_pdf_messages(
        self,
        pdf_pages: List[bytes],
    ) -> List[Dict[str, Any]]:
        """Create messages for PDF processing with the LLM.
        
        Args:
            pdf_pages: List of PDF page bytes to process
            
        Returns:
            List of message dictionaries to send to the LLM
        """
        # Create prompts
        system_prompt = "You are an expert document processor specialized in extracting information from PDFs."

        user_prompt = """You are an expert document processor specialized in extracting information from scanned copies of timesheets. Please extract the following fields from the PDF document:
- name: string
- staff_code: string
- month: string
- total_working_days: int
- total_ot_hours: int
- total_working_sundays: int
- total_sunday_ot: int

Some of the fields may be ambiguous due to human error. Ensure that the following rules are followed, and fix any deviations:
- staff_code must follow the naming convention of `<letter>-<numbers>`
- month must follow the naming convention of `%b-%Y`

Information about each PDF:
- Sundays/public holidays are highlighted. If the start/end or HR fields are updated for that date, that means the person worked on the day. If they are left blank, then the person did not work on that day. The supervisor's signature column indicates if the work on that date has been verified.

For each page, return a dictionary with 'page_number' which is an auto incrementing field, 'explanation' which details the reasoning you have used to infer ambiguous fields, and 'data' which contains the extracted fields.

Return the result as a JSON object with 'pages' as the key, containing an array of page results.
{{ 'pages': [{{ 'page_number': int, 'data': {{ 'field1': 'value1', ... }} }}, ...] }}"""
        
        # Prepare PDF pages for the LLM
        pdf_contents = []
        for pdf_page in pdf_pages:
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
        return [
            {"role": "system", "content": system_prompt},
            {
                "role": "user", 
                "content": [
                    {"type": "text", "text": user_prompt},
                    *pdf_contents
                ]
            }
        ]
    
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