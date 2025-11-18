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
        # Look for .env in root directory (3 levels up from this file)
        # Path structure: api/parserapi/htmlparser/config.py -> root
        env_file = Path(__file__).parent.parent.parent.parent / '.env'
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        if key.strip() not in os.environ:
                            os.environ[key.strip()] = value.strip().strip('"').strip("'")
    
    @property
    def ollama_base_url(self) -> str:
        """Get Ollama base URL (default: http://localhost:11434)"""
        return os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    
    @property
    def ollama_model(self) -> str:
        """Get Ollama model (default: tinyllama:1.1b)"""
        return os.getenv('OLLAMA_MODEL', 'tinyllama:1.1b')
    
    @property
    def max_articles(self) -> int:
        """Maximum articles to extract (default: 2)"""
        return int(os.getenv('PARSER_MAX_ARTICLES', '2'))
    
    def get_graph_config(self, base_url: Optional[str] = None, model: Optional[str] = None) -> dict:
        """
        Get ScrapeGraphAI configuration for Ollama
        
        Args:
            base_url: Optional Ollama base URL override
            model: Optional model name override
            
        Returns:
            Configuration dictionary
        """
        return {
            "llm": {
                "model": f"ollama/{model or self.ollama_model}",
                "base_url": base_url or self.ollama_base_url,
            },
            "verbose": False,
            "headless": True,
        }

# Global configuration instance
config = ParserConfig()
