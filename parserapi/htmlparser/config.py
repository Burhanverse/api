"""
Configuration module for HTML Parser
"""

import os
from typing import Optional
from pathlib import Path


class ParserConfig:
    """Simple configuration manager for the HTML parser"""
    
    def __init__(self):
        """Initialize configuration from environment variables"""
        self._load_env()
        
    def _load_env(self):
        """Load environment variables from .env file if it exists"""
        env_file = Path(__file__).parent.parent.parent / '.env'
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        if key.strip() not in os.environ:
                            os.environ[key.strip()] = value.strip().strip('"').strip("'")
    
    @property
    def gemini_api_key(self) -> Optional[str]:
        """Get Gemini API key"""
        return os.getenv('GEMINI_API_KEY')
    
    @property
    def gemini_model(self) -> str:
        """Get Gemini model (default: gemini-2.5-flash-exp)"""
        return os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-exp')
    
    @property
    def max_articles(self) -> int:
        """Maximum articles to extract (default: 2)"""
        return int(os.getenv('PARSER_MAX_ARTICLES', '2'))
    
    def get_graph_config(self, api_key: Optional[str] = None) -> dict:
        """
        Get ScrapeGraphAI configuration
        
        Args:
            api_key: Optional API key override
            
        Returns:
            Configuration dictionary
        """
        return {
            "llm": {
                "api_key": api_key or self.gemini_api_key,
                "model": self.gemini_model,
            },
            "verbose": False,
            "headless": True,
        }

# Global configuration instance
config = ParserConfig()
