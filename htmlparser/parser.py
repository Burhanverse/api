"""
Core parser implementation using ScrapeGraphAI
"""

import os
from datetime import datetime
from urllib.parse import urljoin, urlparse
try:
    from scrapegraphai.graphs import SmartScraperGraph
    _SCRAPEGRAPHAI_AVAILABLE = True
except Exception:
    # Don't fail import-time if scrapegraphai (or its deps like langchain)
    # aren't available. We'll fall back to the simpler parser at runtime.
    SmartScraperGraph = None
    _SCRAPEGRAPHAI_AVAILABLE = False
from typing import Dict, List, Any, Optional

from .config import config
from .prompts import get_prompt
from .utils import structure_feed_data, fallback_parse


class ScrapeGraphHTMLParser:
    """
    Parser that uses ScrapeGraphAI with Ollama to extract feed data from HTML.
    """
    
    def __init__(self, ollama_base_url: Optional[str] = None, ollama_model: Optional[str] = None):
        """
        Initialize the parser with Ollama configuration.
        
        Args:
            ollama_base_url: Ollama base URL. If not provided, uses config.
            ollama_model: Ollama model name. If not provided, uses config.
        """
        self.base_url = ollama_base_url or config.ollama_base_url
        self.model = ollama_model or config.ollama_model
        
        self.graph_config = config.get_graph_config(self.base_url, self.model)
    
    def parse_html_to_feed(self, html_content: str, base_url: str) -> Dict[str, Any]:
        """
        Parse HTML content into a feed structure using ScrapeGraphAI.
        
        Args:
            html_content: Raw HTML content as string
            base_url: Base URL of the page for resolving relative links
            
        Returns:
            Dictionary containing feed metadata and entries
        """
        # If ScrapeGraphAI isn't available at import time (missing deps
        # like langchain), or if creating/running the smart scraper fails,
        # fall back to the simpler HTML extraction to avoid crashing the
        # whole API server at import.
        if not _SCRAPEGRAPHAI_AVAILABLE or SmartScraperGraph is None:
            return fallback_parse(html_content, base_url)

        try:
            # Get the appropriate prompt
            prompt = get_prompt()

            # Create the smart scraper
            smart_scraper = SmartScraperGraph(
                prompt=prompt,
                source=html_content,
                config=self.graph_config
            )

            # Run the scraper
            result = smart_scraper.run()

            # Process and structure the results
            feed_data = structure_feed_data(result, base_url, config.max_articles)

            return feed_data

        except Exception:
            # Fallback to basic extraction if AI parsing fails
            return fallback_parse(html_content, base_url)


def parse_html_to_feed(
    html_content: str, 
    base_url: str, 
    ollama_base_url: Optional[str] = None,
    ollama_model: Optional[str] = None
) -> Dict[str, Any]:
    """
    Parse HTML content to feed format using ScrapeGraphAI with Ollama.
    
    Args:
        html_content: Raw HTML content
        base_url: Base URL of the page
        ollama_base_url: Optional Ollama base URL
        ollama_model: Optional Ollama model name
        
    Returns:
        Structured feed dictionary
    """
    parser = ScrapeGraphHTMLParser(ollama_base_url=ollama_base_url, ollama_model=ollama_model)
    return parser.parse_html_to_feed(html_content, base_url)
