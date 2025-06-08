import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.llm.client import LLMClient, LLMConfig, LLMProvider
from app.services.llm.config import LLMConfigManager
from app.services.llm.ocr_service import OCRService


class TestLLMConfig:
    """Tests for LLM configuration."""
    
    def test_default_config(self):
        """Test default LLM configuration."""
        config = LLMConfig()
        assert isinstance(config.provider, str)
        assert isinstance(config.model, str)
        assert config.temperature == 0.0
        assert config.max_tokens is None
    
    def test_custom_config(self):
        """Test custom LLM configuration."""
        config = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-opus-20240229",
            temperature=0.2,
            max_tokens=4000
        )
        assert config.provider == LLMProvider.ANTHROPIC
        assert config.model == "claude-3-opus-20240229"
        assert config.temperature == 0.2
        assert config.max_tokens == 4000
    
    def test_get_model_string(self):
        """Test getting the model string for different providers."""
        # OpenAI
        config = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4-vision")
        assert config.get_model_string() == "gpt-4-vision"
        
        # Anthropic
        config = LLMConfig(provider=LLMProvider.ANTHROPIC, model="claude-3-opus-20240229")
        assert config.get_model_string() == "anthropic/claude-3-opus-20240229"
        
        # Gemini
        config = LLMConfig(provider=LLMProvider.GEMINI, model="gemini-pro-vision")
        assert config.get_model_string() == "gemini/gemini-pro-vision"


class TestLLMConfigManager:
    """Tests for LLM configuration manager."""
    
    def test_default_config(self):
        """Test getting default configuration."""
        manager = LLMConfigManager()
        config = manager.get_config()
        assert isinstance(config, LLMConfig)
        assert isinstance(config.provider, str)
    
    def test_register_and_get_config(self):
        """Test registering and retrieving a route configuration."""
        manager = LLMConfigManager()
        
        # Create a custom config
        custom_config = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-opus-20240229"
        )
        
        # Register it for a route
        route_path = "/test/route"
        manager.register_route_config(route_path, custom_config)
        
        # Get the config for that route
        retrieved_config = manager.get_config(route_path)
        assert retrieved_config.provider == LLMProvider.ANTHROPIC
        assert retrieved_config.model == "claude-3-opus-20240229"
        
        # Get config for a non-existent route
        default_config = manager.get_config("/non/existent")
        assert default_config != custom_config
        assert isinstance(default_config, LLMConfig)


@pytest.mark.asyncio
class TestLLMClient:
    """Tests for LLM client."""
    
    async def test_init_client(self):
        """Test initializing the LLM client."""
        with patch("app.services.llm.client.litellm") as mock_litellm:
            client = LLMClient()
            assert client.config is not None
            # Check API keys were set
            assert mock_litellm.request_timeout == client.config.request_timeout
    
@pytest.mark.asyncio
class TestOCRService:
    """Tests for OCR service."""
    
    async def test_process_document(self):
        """Test processing a document with the OCR service."""
        # Create a mock LLM client
        mock_client = MagicMock()
        mock_client.process_pdf = AsyncMock(return_value={
            "pages": [
                {
                    "page_number": 1,
                    "title": "Test Document",
                    "date": "2023-01-01"
                },
                {
                    "page_number": 2,
                    "author": "John Doe",
                    "signature": True
                }
            ]
        })
        
        # Create the service with the mock client
        service = OCRService(mock_client)
        
        # Process a document
        pdf_pages = [b"pdf_page1", b"pdf_page2"]
        extract_keys = ["title", "date", "author"]
        route_path = "/test/route"
        
        # Call the service
        with patch("app.services.llm.ocr_service.config_manager.get_config") as mock_get_config:
            mock_get_config.return_value = LLMConfig()
            
            results = await service.process_document(
                pdf_pages=pdf_pages,
                extract_keys=extract_keys,
                route_path=route_path
            )
        
        # Verify results
        assert isinstance(results, list)
        assert len(results) == 2
        assert results[0]["page_number"] == 1
        assert "data" in results[0]
        assert results[0]["data"]["title"] == "Test Document"
        assert results[1]["page_number"] == 2
        
        # Verify the client was called correctly
        mock_client.process_pdf.assert_called_once_with(
            pdf_bytes=pdf_pages,
            prompt="Extract data from the following PDF document pages.",
            extract_keys=extract_keys,
            config=mock_get_config.return_value
        )
    
    async def test_process_document_error(self):
        """Test error handling in the OCR service."""
        # Create a mock LLM client that raises an exception
        mock_client = MagicMock()
        mock_client.process_pdf = AsyncMock(side_effect=Exception("API error"))
        
        # Create the service with the mock client
        service = OCRService(mock_client)
        
        # Process a document
        pdf_pages = [b"pdf_page1"]
        
        # Call the service and verify it handles the error gracefully
        with patch("app.services.llm.ocr_service.config_manager.get_config"):
            results = await service.process_document(pdf_pages=pdf_pages)
        
        # Verify error results
        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]["confidence"] == "low"
        assert "Error processing document" in results[0]["text"]
        assert isinstance(results[0]["data"], dict)
        assert results[0]["data"] == {} 