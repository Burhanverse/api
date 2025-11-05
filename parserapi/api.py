"""
FastAPI implementation with ScrapeGraphAI-based HTML parser
AI-powered content extraction using Google Gemini
"""

from fastapi import FastAPI, Query, HTTPException
import feedparser
from . import htmlparser
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
    title="RSS Parser API",
    description="AI-powered feed parser supporting RSS, Atom, JSON feeds, and intelligent HTML parsing",
    version="2.0.0"
)

USER_AGENT = os.getenv('UA')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

def fetch_url(url):
    """Fetch URL with error handling"""
    try:
        response = requests.get(
            url,
            headers={'User-Agent': USER_AGENT},
            timeout=10
        )
        response.raise_for_status()
        return response
    except Exception as e:
        raise ValueError(f"URL fetch failed: {str(e)}")

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

@parserapi.get("/parse")
async def parse_feed(
    url: str = Query(..., description="The URL to parse"),
    gemini_key: Optional[str] = Query(None, description="Optional Gemini API key")
):
    """
    Parse a feed from the given URL.
    
    Supports:
    - RSS/Atom/JSON feeds
    - AI-powered HTML parsing using ScrapeGraphAI + Gemini 2.5 Flash
    
    Returns structured feed data with articles/posts.
    """
    # Get Gemini API key from request or environment
    api_key = gemini_key or GEMINI_API_KEY

    try:
        response = fetch_url(url)
        content_type = detect_content_type(response)
        final_feed = None
        source = "Direct feed"

        if 'html' in content_type:
            # Use AI-powered HTML parser
            if not api_key:
                raise HTTPException(
                    status_code=400,
                    detail="Gemini API key required for HTML parsing. Set GEMINI_API_KEY or pass gemini_key parameter."
                )
            
            final_feed = htmlparser.parse_html_to_feed(
                response.content.decode('utf-8', errors='ignore'), 
                url,
                gemini_api_key=api_key
            )
            source = "AI HTML parser (Gemini 2.5 Flash)"
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
                if not api_key:
                    raise HTTPException(
                        status_code=400,
                        detail="Gemini API key required for HTML parsing. Set GEMINI_API_KEY or pass gemini_key parameter."
                    )
                
                final_feed = htmlparser.parse_html_to_feed(
                    response.content.decode('utf-8', errors='ignore'),
                    url,
                    gemini_api_key=api_key
                )
                source = "AI HTML parser (fallback)"

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

        # Format items
        items = []
        for entry in sorted_entries[:10]:  # Return top 10 items
            content = format_content(
                getattr(entry, 'content', [{}])[0].get('value', '') or 
                entry.get('content', [{}])[0].get('value', '') if isinstance(entry.get('content', []), list) and entry.get('content') else
                entry.get('summary', ''),
                'html'
            )

            items.append({
                "title": entry.get('title', 'Untitled'),
                "link": entry.get('link', ''),
                "published": entry.get('published', entry.get('date', '')),
                "summary": format_content(entry.get('summary', ''), 'text'),
                "author": entry.get('author', 'Unknown'),
                "categories": [tag.get('term') for tag in entry.get('tags', [])],
                "content": content
            })

        return {
            "feed": feed_metadata,
            "items": items,
            "source": source
        }

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
        "description": "AI-powered feed parser with Gemini",
        "endpoints": {
            "/parse": "Parse a feed from URL (GET)",
            "/health": "Health check (GET)",
            "/docs": "Interactive API documentation (Swagger UI)",
            "/redoc": "Alternative API documentation (ReDoc)"
        },
        "usage": {
            "example": "/parse?url=https://example.com",
            "with_api_key": "/parse?url=https://example.com&gemini_key=your-key"
        }
    }