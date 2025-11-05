"""
HTML Parser using ScrapeGraphAI with Gemini API
This module extracts structured feed data from HTML pages using AI.
"""

import os
from datetime import datetime
from urllib.parse import urljoin, urlparse
from scrapegraphai.graphs import SmartScraperGraph
from typing import Dict, List, Any


class ScrapeGraphHTMLParser:
    """
    Parser that uses ScrapeGraphAI with Gemini to extract feed data from HTML.
    """
    
    def __init__(self, gemini_api_key: str = None):
        """
        Initialize the parser with Gemini API key.
        
        Args:
            gemini_api_key: Google Gemini API key. If not provided, reads from GEMINI_API_KEY env var.
        """
        self.api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY environment variable or pass it directly.")
        
        # Configure ScrapeGraphAI with Gemini
        self.graph_config = {
            "llm": {
                "api_key": self.api_key,
                "model": "gemini-pro",
            },
            "verbose": False,
            "headless": True,
        }
    
    def parse_html_to_feed(self, html_content: str, base_url: str) -> Dict[str, Any]:
        """
        Parse HTML content into a feed structure using ScrapeGraphAI.
        
        Args:
            html_content: Raw HTML content as string
            base_url: Base URL of the page for resolving relative links
            
        Returns:
            Dictionary containing feed metadata and entries
        """
        parsed_url = urlparse(base_url)
        domain = parsed_url.netloc.lower()
        
        # Define the schema we want to extract
        prompt = """
        Extract the following information from this webpage:
        
        1. Feed metadata:
           - title: The main title of the website/page
           - language: The language code if available (e.g., 'en', 'es')
           
        2. Articles/Posts (extract all available):
           For each article/post/blog entry, extract:
           - title: The article title/headline
           - link: The URL/link to the full article (can be relative or absolute)
           - published: Publication date/time if available
           - author: Author name if available
           - summary: A brief summary or excerpt of the article
           - content: The main content/body of the article (full HTML if available)
           - tags: Any categories, tags, or keywords associated with the article
           
        Return the data as a structured JSON object with:
        - feed_title: string
        - feed_language: string
        - articles: array of objects with the fields mentioned above
        
        Make sure to extract ALL visible articles/posts/blog entries from the page.
        """
        
        try:
            # Create the smart scraper
            smart_scraper = SmartScraperGraph(
                prompt=prompt,
                source=html_content,
                config=self.graph_config
            )
            
            # Run the scraper
            result = smart_scraper.run()
            
            # Process and structure the results
            feed_data = self._structure_feed_data(result, base_url)
            
            return feed_data
            
        except Exception as e:
            # Fallback to basic extraction if AI parsing fails
            print(f"ScrapeGraphAI parsing failed: {str(e)}")
            return self._fallback_parse(html_content, base_url)
    
    def _structure_feed_data(self, raw_result: Dict, base_url: str) -> Dict[str, Any]:
        """
        Structure the raw ScrapeGraphAI result into the expected feed format.
        
        Args:
            raw_result: Raw result from ScrapeGraphAI
            base_url: Base URL for resolving relative links
            
        Returns:
            Structured feed dictionary
        """
        # Extract feed metadata
        feed_title = raw_result.get('feed_title', 'Untitled Feed')
        feed_language = raw_result.get('feed_language', '')
        articles = raw_result.get('articles', [])
        
        # Process entries
        entries = []
        for article in articles:
            # Resolve relative URLs
            link = article.get('link', base_url)
            if link and not link.startswith(('http://', 'https://')):
                link = urljoin(base_url, link)
            
            # Get content
            content_html = article.get('content', '')
            summary = article.get('summary', '')
            
            # If no summary but has content, create one
            if not summary and content_html:
                # Strip HTML tags for summary
                import re
                summary_text = re.sub(r'<[^>]+>', '', content_html)
                summary = (summary_text[:200] + '...') if len(summary_text) > 200 else summary_text
            
            # Process tags
            tags_raw = article.get('tags', [])
            if isinstance(tags_raw, str):
                tags_raw = [tags_raw]
            tags = [{'term': tag} for tag in tags_raw if tag]
            
            entry = {
                'title': article.get('title', 'Untitled Entry'),
                'link': link,
                'published': article.get('published', ''),
                'content': [{'value': content_html}] if content_html else [],
                'summary': summary,
                'author': article.get('author', ''),
                'tags': tags
            }
            
            entries.append(entry)
        
        # Construct the final feed
        feed = {
            'title': feed_title,
            'link': base_url,
            'description': '',
            'language': feed_language,
            'updated': datetime.now().isoformat(),
            'entries': entries,
            'version': 'html-scrapegraph'
        }
        
        return feed
    
    def _fallback_parse(self, html_content: str, base_url: str) -> Dict[str, Any]:
        """
        Fallback parser when ScrapeGraphAI fails.
        Uses basic BeautifulSoup parsing.
        
        Args:
            html_content: Raw HTML content
            base_url: Base URL
            
        Returns:
            Basic feed structure
        """
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract basic metadata
        title_tag = soup.find('title')
        feed_title = title_tag.get_text(strip=True) if title_tag else 'Untitled Feed'
        
        html_tag = soup.find('html')
        language = html_tag.get('lang', '') if html_tag else ''
        
        # Try to find articles
        entries = []
        article_tags = soup.find_all('article') or soup.find_all('div', class_=lambda x: x and 'post' in x.lower())
        
        for article in article_tags[:10]:  # Limit to 10 entries
            title_elem = article.find(['h1', 'h2', 'h3'])
            title = title_elem.get_text(strip=True) if title_elem else 'Untitled Entry'
            
            link_elem = article.find('a', href=True)
            link = urljoin(base_url, link_elem['href']) if link_elem else base_url
            
            entry = {
                'title': title,
                'link': link,
                'published': '',
                'content': [{'value': str(article)}],
                'summary': '',
                'author': '',
                'tags': []
            }
            entries.append(entry)
        
        return {
            'title': feed_title,
            'link': base_url,
            'description': '',
            'language': language,
            'updated': datetime.now().isoformat(),
            'entries': entries,
            'version': 'html-fallback'
        }


# Module-level function for backward compatibility
def parse_html_to_feed(html_content: str, base_url: str, gemini_api_key: str = None) -> Dict[str, Any]:
    """
    Parse HTML content to feed format using ScrapeGraphAI.
    
    Args:
        html_content: Raw HTML content
        base_url: Base URL of the page
        gemini_api_key: Optional Gemini API key
        
    Returns:
        Structured feed dictionary
    """
    parser = ScrapeGraphHTMLParser(gemini_api_key=gemini_api_key)
    return parser.parse_html_to_feed(html_content, base_url)