"""
FastAPI implementation with ScrapeGraphAI-based HTML parser
AI-powered content extraction using Ollama (TinyLlama)
"""

from fastapi import FastAPI, Query, HTTPException
import feedparser
import htmlparser
import requests
import time
from time import mktime
import json
from lxml import etree
from minify_html import minify
from emoji import demojize
from datetime import datetime
import os
from typing import Optional

parserapi = FastAPI(
    title="ParserAPI",
    description="AI-powered feed parser supporting RSS, Atom, JSON feeds, and intelligent HTML parsing",
    version="4.0.0",
    redoc_url=None
)

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'

def fetch_url(url):
    """Fetch URL with error handling and retry logic"""
    headers_list = [
        {
            'User-Agent': USER_AGENT,
            'Accept': 'application/rss+xml, application/xml, application/atom+xml, text/xml, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache'
        },
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*'
        },
        {
            'User-Agent': 'curl/7.68.0',
            'Accept': '*/*'
        }
    ]
    
    last_error = None
    for headers in headers_list:
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=15,
                allow_redirects=True
            )
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            last_error = e
            if e.response.status_code != 403:
                raise ValueError(f"URL fetch failed: {str(e)}")
            # Try next headers on 403
            continue
        except Exception as e:
            raise ValueError(f"URL fetch failed: {str(e)}")
    
    # If all attempts failed with 403
    raise ValueError(f"URL fetch failed with 403 Forbidden after trying multiple user agents")

def detect_content_type(response):
    """Detect the content type of the response"""
    ctype = response.headers.get('Content-Type', '').split(';')[0].lower()
    if not ctype:
        if response.content.lstrip().startswith(b'{'):
            return 'json'
        if b'<rss' in response.content.lower():
            return 'xml'
    return ctype

def parse_xml(content):
    """Parse XML/RSS feed content"""
    try:
        parser = etree.XMLParser(recover=True)
        tree = etree.fromstring(content, parser=parser)
        content = etree.tostring(tree)
    except Exception:
        pass

    feed = feedparser.parse(content)
    if feed.bozo:
        raise ValueError(f"XML parsing error: {feed.bozo_exception.getMessage()}")
    return feed

def parse_json(content):
    """Parse JSON feed content"""
    try:
        data = json.loads(content)
        return {
            'title': data.get('title', ''),
            'link': data.get('home_page_url', ''),
            'description': data.get('description', ''),
            'entries': data.get('items', []),
            'version': 'json'
        }
    except Exception as e:
        raise ValueError(f"JSON parsing error: {str(e)}")

def format_content(content, content_type='html'):
    """Format content based on type"""
    if content_type == 'html':
        return minify(content, minify_js=True, minify_css=True)
    return demojize(content)

def extract_title(entry):
    """Extract title from entry with multiple fallbacks"""
    # Try direct title field
    if entry.get('title') and entry.get('title').strip():
        return entry.get('title').strip()
    
    # Try summary/description
    summary = entry.get('summary', '') or entry.get('description', '')
    if summary:
        # Extract first line or sentence
        from html.parser import HTMLParser
        
        class HTMLTextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text = []
            def handle_data(self, data):
                self.text.append(data)
        
        parser = HTMLTextExtractor()
        try:
            parser.feed(summary)
            text = ' '.join(parser.text).strip()
            if text:
                # Get first sentence or first 100 chars
                first_sentence = text.split('.')[0].strip()
                if len(first_sentence) > 10 and len(first_sentence) < 150:
                    return first_sentence
                elif len(text) > 10:
                    return text[:100].strip() + ('...' if len(text) > 100 else '')
        except:
            pass
    
    # Try content field
    content = entry.get('content', [{}])[0].get('value', '') if isinstance(entry.get('content', []), list) else ''
    if content:
        try:
            parser = HTMLTextExtractor()
            parser.feed(content)
            text = ' '.join(parser.text).strip()
            if text:
                first_sentence = text.split('.')[0].strip()
                if len(first_sentence) > 10 and len(first_sentence) < 150:
                    return first_sentence
                elif len(text) > 10:
                    return text[:100].strip() + ('...' if len(text) > 100 else '')
        except:
            pass
    
    # Try extracting from URL
    link = entry.get('link', '')
    if link:
        # Get the last part of URL and clean it up
        from urllib.parse import urlparse, unquote
        path = urlparse(link).path
        if path:
            # Get last segment
            segments = [s for s in path.split('/') if s]
            if segments:
                title = segments[-1]
                # Clean up common patterns
                title = unquote(title)
                title = title.replace('_', ' ').replace('-', ' ')
                # Remove file extensions
                title = title.rsplit('.', 1)[0] if '.' in title else title
                if len(title) > 10:
                    return title.title()
    
    return 'Untitled Entry'

@parserapi.get("/parse")
async def parse_feed(
    url: str = Query(..., description="The URL to parse")
):
    """
    Parse a feed from the given URL.
    
    Supports:
    - RSS/Atom/JSON feeds
    - AI-powered HTML parsing using ScrapeGraphAI + Ollama (TinyLlama)
    
    Returns structured feed data with articles/posts.
    """

    try:
        response = fetch_url(url)
        content_type = detect_content_type(response)
        final_feed = None
        source = "Direct feed"

        if 'html' in content_type:
            # Use AI-powered HTML parser
            final_feed = htmlparser.parse_html_to_feed(
                response.content.decode('utf-8', errors='ignore'), 
                url
            )
            source = "AI HTML parser (Ollama - TinyLlama)"
        else:
            # Try parsing as XML or JSON
            try:
                if 'xml' in content_type:
                    final_feed = parse_xml(response.content)
                elif 'json' in content_type:
                    final_feed = parse_json(response.content)
                else:
                    raise ValueError("Unsupported content type")
            except Exception as e:
                # Fallback to AI HTML parser
                final_feed = htmlparser.parse_html_to_feed(
                    response.content.decode('utf-8', errors='ignore'),
                    url
                )
                source = " XML parser (rss/xml/json fallback)"

        # Build feed metadata
        feed_metadata = {
            "title": final_feed.get('title', 'Untitled Feed'),
            "link": final_feed.get('link', url),
            "description": final_feed.get('description', ''),
            "language": final_feed.get('language', ''),
            "updated": final_feed.get('updated', datetime.now().isoformat()),
            "version": final_feed.get('version', '')
        }

        # Sort entries by date
        sorted_entries = sorted(
            final_feed.get('entries', []),
            key=lambda entry: mktime(
                next(
                    (d for d in [
                        entry.get('published_parsed'),
                        entry.get('updated_parsed')
                    ] if isinstance(d, time.struct_time) and 1970 <= getattr(d, 'tm_year', 0) <= 2038),
                    time.struct_time((1970, 1, 1, 0, 0, 0, 3, 1, 0))
                )
            ),
            reverse=True
        )

        # Format response - return simplified structure
        items = []
        for entry in sorted_entries[:5]:  # Limit to top 5 items
            items.append({
                'title': extract_title(entry),
                'link': entry.get('link', '')
            })
        
        return items

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@parserapi.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "4.0.0",
        "parser": "ParserAPI"
    }


@parserapi.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "ParserAPI",
        "version": "4.0.0",
        "description": "AI-powered feed parser with Ollama (TinyLlama)",
        "endpoints": {
            "/parse": "Parse a feed from URL (GET)",
            "/health": "Health check (GET)",
            "/docs": "Interactive API documentation (Swagger UI)"
        },
        "usage": {
            "example": "/parse?url=https://example.com"
        }
    }