import os
from typing import Dict, Optional

from pydantic import BaseModel

from app.services.llm.client import LLMConfig, LLMProvider


class RouteConfig(BaseModel):
    """Configuration for a specific API route."""
    route_path: str
    llm_config: LLMConfig


class LLMConfigManager:
    """Manager for LLM configurations per route."""
    
    def __init__(self, default_config: Optional[LLMConfig] = None):
        """Initialize the LLM configuration manager.
        
        Args:
            default_config: Optional default LLM configuration. If None, a new default config will be created.
        """
        self._route_configs: Dict[str, LLMConfig] = {}
        self._default_config = default_config or LLMConfig()
    
    def register_route_config(self, route_path: str, config: LLMConfig) -> None:
        """Register a LLM configuration for a specific route.
        
        Args:
            route_path: API route path, e.g., "/ocr/pdf"
            config: LLM configuration for this route
        """
        self._route_configs[route_path] = config
    
    def get_config(self, route_path: Optional[str] = None) -> LLMConfig:
        """Get LLM configuration for a route.
        
        Args:
            route_path: API route path. If None or not found, returns default config.
            
        Returns:
            LLM configuration for the route or default config
        """
        if route_path and route_path in self._route_configs:
            return self._route_configs[route_path]
        return self._default_config


# Initialize the configuration manager
config_manager = LLMConfigManager()

# Define configuration for OCR PDF route
ocr_pdf_config = LLMConfig(
    provider=LLMProvider(os.getenv("OCR_LLM_PROVIDER", LLMProvider.GEMINI)),
    model=os.getenv("OCR_LLM_MODEL", "gemini-2.0-flash"),
    temperature=0.0,
)

# Register the OCR PDF route configuration
config_manager.register_route_config("/ocr/pdf", ocr_pdf_config) 