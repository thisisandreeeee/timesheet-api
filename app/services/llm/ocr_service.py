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
            return [
                {
                    "page_number": 1,
                    "data": {},
                }
            ]

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
            pdf_contents.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:application/pdf;base64,{base64_pdf}",
                        "detail": "high",
                    },
                }
            )

        # Create the full message
        return [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [{"type": "text", "text": user_prompt}, *pdf_contents],
            },
        ]

    def _format_results(self, results: Any) -> List[Dict[str, Any]]:
        """Format and standardize LLM results.

        Args:
            results: Raw results from LLM

        Returns:
            List of formatted page results
        """
        # Validate that results is a dictionary with 'pages' key
        if (
            isinstance(results, dict)
            and "pages" in results
            and isinstance(results["pages"], list)
        ):
            formatted_results = []
            for i, page in enumerate(results["pages"]):
                if not isinstance(page, dict):
                    logger.warning(f"Unexpected page result type: {type(page)}")
                    continue

                # Create standardized result structure with only page_number and data
                formatted_result = {
                    "page_number": page.get("page_number", i + 1),
                    "data": (
                        page.get("data", {})
                        if isinstance(page.get("data"), dict)
                        else {}
                    ),
                }

                formatted_results.append(formatted_result)

            return formatted_results
        else:
            logger.error(f"Unexpected result format from LLM: {results}")
            return [{"page_number": 1, "data": {}}]


# Create a default OCR service instance
default_ocr_service = OCRService()
