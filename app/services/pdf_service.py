import io
from typing import BinaryIO, Dict, List, Optional, Any

from pypdf import PdfReader, PdfWriter

from app.services.llm.ocr_service import default_ocr_service


class PDFProcessingError(Exception):
    """Exception raised for errors in the PDF processing."""

    pass


def validate_pdf(file: BinaryIO) -> bool:
    """
    Validate if the file is a valid PDF.

    Args:
        file: The file to validate

    Returns:
        bool: True if valid PDF, False otherwise

    Raises:
        PDFProcessingError: If there's an error during validation
    """
    try:
        # Reset file pointer to beginning
        file.seek(0)

        # Check if file is a PDF
        pdf = PdfReader(file)

        # Reset file pointer to beginning again after validation
        file.seek(0)

        # If we can read at least one page, it's a valid PDF
        return len(pdf.pages) > 0
    except Exception as e:
        raise PDFProcessingError(f"Error validating PDF: {str(e)}")


def split_pdf(file: BinaryIO) -> List[bytes]:
    """
    Split a PDF file into individual pages as PDF bytes.

    Args:
        file: The PDF file to split

    Returns:
        List[bytes]: List of PDF pages as PDF bytes

    Raises:
        PDFProcessingError: If there's an error during splitting
    """
    try:
        # Reset file pointer to beginning
        file.seek(0)

        # Load PDF
        pdf = PdfReader(file)
        page_count = len(pdf.pages)

        # Create a list to hold individual page bytes
        pages = []

        # Process each page
        for i in range(page_count):
            # Create a PDF writer for a single page
            writer = PdfWriter()

            # Add the page from the original PDF
            writer.add_page(pdf.pages[i])

            # Create a BytesIO object to hold the PDF bytes
            page_bytes = io.BytesIO()

            # Write the page to the BytesIO object
            writer.write(page_bytes)

            # Get the bytes and add to pages list
            page_bytes.seek(0)
            pages.append(page_bytes.getvalue())

        return pages
    except Exception as e:
        raise PDFProcessingError(f"Error splitting PDF: {str(e)}")


async def process_pdf(
    file: BinaryIO,
    route_path: str = "/ocr/pdf",
) -> List[Dict[str, Any]]:
    """
    Process a PDF file: validate, split into pages, and perform OCR using LLM.

    Args:
        file: The PDF file to process
        route_path: API route path for LLM configuration

    Returns:
        List[Dict[str, Any]]: List of dictionaries with OCR results for each page

    Raises:
        PDFProcessingError: If there's an error during processing
    """
    # Validate PDF - if invalid, this will raise PDFProcessingError
    if not validate_pdf(file):
        raise PDFProcessingError("Invalid PDF file")

    try:
        # Split PDF into pages
        pdf_pages = split_pdf(file)

        # Process all pages with the OCR service
        return await default_ocr_service.process_document(
            pdf_pages=pdf_pages, route_path=route_path
        )
    except PDFProcessingError:
        # Re-raise PDF processing errors
        raise
    except Exception as e:
        # Wrap other exceptions in PDFProcessingError
        raise PDFProcessingError(f"Error processing PDF: {str(e)}")
