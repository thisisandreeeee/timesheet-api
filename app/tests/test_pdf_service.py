import io
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.pdf_service import PDFProcessingError, process_pdf, validate_pdf


@pytest.fixture
def test_client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_pdf_file():
    """Mock PDF file fixture."""
    # Create a mock PDF file
    content = b"%PDF-1.5\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    file = io.BytesIO(content)
    return file


@pytest.mark.asyncio
async def test_validate_pdf_valid(mock_pdf_file):
    """Test validate_pdf with a valid PDF."""
    # This uses the mock PDF file from the fixture
    with patch("app.services.pdf_service.PdfReader") as mock_reader:
        # Mock the PdfReader to return valid PDF data
        mock_instance = MagicMock()
        mock_instance.pages = [MagicMock()]  # Mock having one page
        mock_reader.return_value = mock_instance
        
        result = validate_pdf(mock_pdf_file)
        assert result is True


@pytest.mark.asyncio
async def test_validate_pdf_invalid():
    """Test validate_pdf with an invalid file."""
    # Create an invalid file
    invalid_file = io.BytesIO(b"This is not a PDF file")
    
    with patch("app.services.pdf_service.PdfReader") as mock_reader:
        # Mock the PdfReader to raise an exception
        mock_reader.side_effect = Exception("Invalid PDF")
        
        with pytest.raises(PDFProcessingError):
            validate_pdf(invalid_file)


@pytest.mark.asyncio
async def test_process_pdf_success(mock_pdf_file):
    """Test successful PDF processing."""
    # Mock the necessary functions
    with patch("app.services.pdf_service.validate_pdf") as mock_validate, \
         patch("app.services.pdf_service.split_pdf") as mock_split, \
         patch("app.services.llm.ocr_service.default_ocr_service.process_document") as mock_ocr:
        
        # Configure mocks
        mock_validate.return_value = True
        mock_split.return_value = [b"page1", b"page2"]
        
        # Mock the OCR result
        mock_ocr_result = [
            {
                "page_number": 1,
                "text": "Sample text from page 1",
                "confidence": "high",
                "data": {"title": "Sample Document", "date": "2023-01-01"}
            },
            {
                "page_number": 2,
                "text": "Sample text from page 2",
                "confidence": "high",
                "data": {"author": "John Doe", "pages": "2"}
            }
        ]
        mock_ocr.return_value = mock_ocr_result
        
        # Call the function
        result = await process_pdf(mock_pdf_file, ["title", "date", "author"])
        
        # Verify the result
        assert len(result) == 2
        assert result[0]["page_number"] == 1
        assert result[0]["text"] == "Sample text from page 1"
        assert result[0]["data"]["title"] == "Sample Document"
        assert result[1]["page_number"] == 2
        assert result[1]["data"]["author"] == "John Doe"
        
        # Verify the function calls
        mock_validate.assert_called_once_with(mock_pdf_file)
        mock_split.assert_called_once_with(mock_pdf_file)
        mock_ocr.assert_called_once_with(
            pdf_pages=[b"page1", b"page2"],
            extract_keys=["title", "date", "author"],
            route_path="/ocr/pdf"
        )


@pytest.mark.asyncio
async def test_process_pdf_validation_error(mock_pdf_file):
    """Test PDF processing with validation error."""
    with patch("app.services.pdf_service.validate_pdf") as mock_validate:
        # Configure mock to return False
        mock_validate.return_value = False
        
        # Call the function and check for exception
        with pytest.raises(PDFProcessingError):
            await process_pdf(mock_pdf_file)
        
        # Verify the function call
        mock_validate.assert_called_once_with(mock_pdf_file)


@pytest.mark.asyncio
async def test_process_pdf_splitting_error(mock_pdf_file):
    """Test PDF processing with splitting error."""
    with patch("app.services.pdf_service.validate_pdf") as mock_validate, \
         patch("app.services.pdf_service.split_pdf") as mock_split:
        
        # Configure mocks
        mock_validate.return_value = True
        mock_split.side_effect = Exception("Error splitting PDF")
        
        # Call the function and check for exception
        with pytest.raises(PDFProcessingError):
            await process_pdf(mock_pdf_file)
        
        # Verify the function calls
        mock_validate.assert_called_once_with(mock_pdf_file)
        mock_split.assert_called_once_with(mock_pdf_file)


@pytest.mark.asyncio
async def test_process_pdf_ocr_error(mock_pdf_file):
    """Test PDF processing with OCR error."""
    with patch("app.services.pdf_service.validate_pdf") as mock_validate, \
         patch("app.services.pdf_service.split_pdf") as mock_split, \
         patch("app.services.llm.ocr_service.default_ocr_service.process_document") as mock_ocr:
        
        # Configure mocks
        mock_validate.return_value = True
        mock_split.return_value = [b"page1", b"page2"]
        mock_ocr.side_effect = Exception("OCR error")
        
        # Call the function and check for exception
        with pytest.raises(PDFProcessingError):
            await process_pdf(mock_pdf_file)
        
        # Verify the function calls
        mock_validate.assert_called_once_with(mock_pdf_file)
        mock_split.assert_called_once_with(mock_pdf_file)
        mock_ocr.assert_called_once() 