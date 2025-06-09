import io
import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.pdf_service import PDFProcessingError


@pytest.fixture
def test_client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_pdf_file():
    """Mock PDF file."""
    # Create a minimal PDF content
    content = b"%PDF-1.5\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    return content


@pytest.mark.asyncio
async def test_health_check(test_client):
    """Test health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_process_pdf_success(test_client, mock_pdf_file):
    """Test successful PDF processing endpoint."""
    # Mock the process_pdf function
    with patch("app.routers.ocr_routes.process_pdf") as mock_process:
        # Configure the mock to return sample results
        mock_process.return_value = [
            {
                "page_number": 1,
                "data": {"title": "Sample Document", "date": "2023-01-01"},
            },
            {
                "page_number": 2,
                "data": {"author": "John Doe", "pages": "2"},
            },
        ]

        # Create the file for upload
        test_file = io.BytesIO(mock_pdf_file)
        test_file.name = "test.pdf"

        # Make the request
        response = test_client.post(
            "/ocr/pdf",
            files={"file": ("test.pdf", test_file, "application/pdf")},
        )

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "pages" in data
        assert len(data["pages"]) == 2
        assert data["pages"][0]["page_number"] == 1
        assert data["pages"][0]["data"]["title"] == "Sample Document"
        assert data["pages"][1]["page_number"] == 2
        assert data["pages"][1]["data"]["author"] == "John Doe"


@pytest.mark.asyncio
async def test_process_pdf_with_llm_config(test_client, mock_pdf_file):
    """Test PDF processing with custom LLM configuration."""
    # Mock the process_pdf function
    with (
        patch("app.routers.ocr_routes.process_pdf") as mock_process,
        patch("app.routers.ocr_routes.config_manager.get_config") as mock_get_config,
        patch("app.routers.ocr_routes.config_manager.register_route_config") as mock_register_config,
    ):

        # Configure the mock to return sample results
        mock_process.return_value = [
            {
                "page_number": 1,
                "data": {"custom_field": "Custom value"},
            }
        ]

        # Create the file for upload
        test_file = io.BytesIO(mock_pdf_file)
        test_file.name = "test.pdf"

        # Create custom LLM config
        llm_config = {
            "provider": "anthropic",
            "model": "claude-3-opus-20240229",
            "temperature": 0.2,
        }

        # Make the request with custom LLM config
        response = test_client.post(
            "/ocr/pdf",
            files={"file": ("test.pdf", test_file, "application/pdf")},
            data={
                "llm_config_data": json.dumps(llm_config),
            },
        )

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "pages" in data
        assert len(data["pages"]) == 1
        assert data["pages"][0]["data"]["custom_field"] == "Custom value"


@pytest.mark.asyncio
async def test_process_pdf_invalid_file_type(test_client):
    """Test PDF processing with invalid file type."""
    # Create a non-PDF file
    test_file = io.BytesIO(b"This is not a PDF")
    test_file.name = "test.txt"

    # Make the request
    response = test_client.post(
        "/ocr/pdf", files={"file": ("test.txt", test_file, "text/plain")}
    )

    # Check response
    assert response.status_code == 400
    assert "detail" in response.json()
    assert "must be a PDF" in response.json()["detail"]


@pytest.mark.asyncio
async def test_process_pdf_processing_error(test_client, mock_pdf_file):
    """Test PDF processing with processing error."""
    # Mock the process_pdf function to raise an error
    with patch("app.routers.ocr_routes.process_pdf", side_effect=PDFProcessingError("Test error")):
        # Create the file for upload
        test_file = io.BytesIO(mock_pdf_file)
        test_file.name = "test.pdf"

        # Make the request
        response = test_client.post(
            "/ocr/pdf", files={"file": ("test.pdf", test_file, "application/pdf")}
        )

        # Check response
        assert response.status_code == 400
        assert "detail" in response.json()
        assert "Test error" in response.json()["detail"]


@pytest.mark.asyncio
async def test_process_pdf_invalid_llm_config(test_client, mock_pdf_file):
    """Test PDF processing with invalid LLM configuration."""
    # Create the file for upload
    test_file = io.BytesIO(mock_pdf_file)
    test_file.name = "test.pdf"

    # Make the request with invalid LLM config
    response = test_client.post(
        "/ocr/pdf",
        files={"file": ("test.pdf", test_file, "application/pdf")},
        data={"llm_config_data": "this is not valid json"},
    )

    # Check response
    assert response.status_code == 400
    assert "detail" in response.json()
    assert "Invalid LLM configuration" in response.json()["detail"]
