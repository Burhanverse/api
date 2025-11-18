"""
Utility functions for feed processing and fallback parsing
"""

import re
from datetime import datetime
from urllib.parse import urljoin
from typing import Dict, List, Any


def structure_feed_data(raw_result: Dict, base_url: str, max_articles: int = 20) -> Dict[str, Any]:
    """
    Structure the raw ScrapeGraphAI result into the expected feed format.
    
    Args:
        raw_result: Raw result from ScrapeGraphAI
        base_url: Base URL for resolving relative links
        max_articles: Maximum number of articles to include
        
    Returns:
        Structured feed dictionary
    """
    # Extract feed metadata
    feed_title = raw_result.get('feed_title', 'Untitled Feed')
    feed_language = raw_result.get('feed_language', '')
    articles = raw_result.get('articles', [])
    
    # Limit articles
    if len(articles) > max_articles:
        articles = articles[:max_articles]
    
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
            summary = create_summary(content_html)
        
        # Process tags
        tags = process_tags(article.get('tags', []))
        
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


def create_summary(content_html: str, max_length: int = 200) -> str:
    """
    Create a summary from HTML content
    
    Args:
        content_html: HTML content
        max_length: Maximum length of summary
        
    Returns:
        Plain text summary
    """
    # Strip HTML tags
    summary_text = re.sub(r'<[^>]+>', '', content_html)
    # Clean up whitespace
    summary_text = ' '.join(summary_text.split())
    # Truncate if needed
    if len(summary_text) > max_length:
        summary_text = summary_text[:max_length] + '...'
    return summary_text


def process_tags(tags_raw: Any) -> List[Dict[str, str]]:
    """
    Process tags into standard format
    
    Args:
        tags_raw: Raw tags (can be string, list, etc.)
        
    Returns:
        List of tag dictionaries
    """
    if isinstance(tags_raw, str):
        tags_raw = [tags_raw]
    elif not isinstance(tags_raw, list):
        tags_raw = []
    
    return [{'term': tag} for tag in tags_raw if tag]


def fallback_parse(html_content: str, base_url: str) -> Dict[str, Any]:
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
