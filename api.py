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
from html import unescape
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
    from lxml import html as lxml_html
    from urllib.parse import urlparse, unquote
    import re
    
    def clean_title(raw_value):
        if not raw_value:
            return None
        text = unescape(raw_value)
        text = re.sub(r'\s+', ' ', text).strip()
        if 5 <= len(text) <= 200:
            return text
        return None

    # Try direct title-like fields first
    candidate_fields = [
        entry.get('title'),
        entry.get('media_title'),
        entry.get('summary_title'),
        entry.get('itunes_title'),
        entry.get('summary'),
        entry.get('description')
    ]

    title_detail = entry.get('title_detail')
    if isinstance(title_detail, dict):
        candidate_fields.append(title_detail.get('value'))

    summary_detail = entry.get('summary_detail')
    if isinstance(summary_detail, dict):
        candidate_fields.append(summary_detail.get('value'))

    for field in candidate_fields:
        candidate = clean_title(field)
        if candidate:
            return candidate
    
    def extract_from_html(html_content):
        """Extract title from HTML content"""
        if not html_content:
            return None
            
        try:
            tree = lxml_html.fromstring(html_content)

            # Priority 0: look for explicit metadata titles
            meta_paths = [
                '//meta[@property="og:title"]/@content',
                '//meta[@name="og:title"]/@content',
                '//meta[@name="twitter:title"]/@content',
                '//meta[@property="twitter:title"]/@content',
                '//meta[@name="title"]/@content'
            ]
            for path in meta_paths:
                for value in tree.xpath(path):
                    title = clean_title(value)
                    if title:
                        return title

            # Priority 0.5: document title element
            doc_title = clean_title(tree.xpath('string(//title)'))
            if doc_title:
                return doc_title

            # Priority 1: Try all heading tags directly (h1-h6)
            for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                headings = tree.xpath(f'.//{tag}')
                for h in headings:
                    title = clean_title(h.text_content())
                    if title:
                        return title
            
            # Priority 2: Try common title class names
            title_classes = [
                "//*[contains(@class, 'title')]",
                "//*[contains(@class, 'headline')]",
                "//*[contains(@class, 'entry-title')]",
                "//*[contains(@class, 'post-title')]",
                "//*[contains(@class, 'article-title')]",
            ]
            for xpath in title_classes:
                elements = tree.xpath(xpath)
                for elem in elements:
                    title = clean_title(elem.text_content())
                    if title:
                        return title
            
            # Priority 3: Look inside article/post containers
            containers = tree.xpath('//article | //*[contains(@class, "post")] | //*[contains(@class, "entry")] | //*[contains(@class, "story")]')
            for container in containers:
                # Try headings inside containers
                for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    headings = container.xpath(f'.//{tag}')
                    for h in headings:
                        title = clean_title(h.text_content())
                        if title:
                            return title

            # Priority 3.4: attribute-based hints (lower priority to avoid dates)
            attr_selectors = [
                'string(//*[@aria-label][1]/@aria-label)',
                'string(//*[@data-title][1]/@data-title)',
                'string(//*[@title][1]/@title)'
            ]
            for selector in attr_selectors:
                value = tree.xpath(selector)
                title = clean_title(value)
                if title:
                    return title

            # Priority 3.5: first substantial paragraph text
            paragraph = clean_title(tree.xpath('string(//p[normalize-space()][1])'))
            if paragraph:
                return paragraph
            
            # Priority 4: Get first substantial text (fallback)
            text = tree.text_content().strip()
            if text:
                # Remove extra whitespace
                text = re.sub(r'\s+', ' ', text)
                # Try to get first sentence
                sentences = re.split(r'[.!?]\s+', text)
                for sentence in sentences:
                    title = clean_title(sentence)
                    if title:
                        return title
                # Or just first 100 chars
                if len(text) > 10:
                    snippet = text[:100].strip() + ('...' if len(text) > 100 else '')
                    title = clean_title(snippet)
                    if title:
                        return title
        except Exception as e:
            pass
        
        return None
    
    # Try summary/description field
    summary = entry.get('summary', '') or entry.get('description', '')
    if summary:
        title = extract_from_html(summary)
        if title:
            return title
    
    # Try explicit HTML fields returned by scrapers
    html_fields = [
        entry.get('content_html'),
        entry.get('summary_html'),
        entry.get('standfirst'),
        entry.get('description_html')
    ]
    for html_field in html_fields:
        title = extract_from_html(html_field)
        if title:
            return title

    # Try content field
    content_list = entry.get('content', [])
    if isinstance(content_list, list) and content_list:
        content = content_list[0].get('value', '')
        if content:
            title = extract_from_html(content)
            if title:
                return title
    elif isinstance(content_list, str):
        title = extract_from_html(content_list)
        if title:
            return title
    
    # Try extracting from URL as last resort
    link = entry.get('link', '')
    if link:
        try:
            path = urlparse(link).path
            if path:
                segments = [s for s in path.split('/') if s]
                if segments:
                    title = segments[-1]
                    title = unquote(title)
                    # Remove file extension
                    title = title.rsplit('.', 1)[0] if '.' in title else title
                    # Clean up slug
                    title = title.replace('_', ' ').replace('-', ' ')
                    # Remove numbers at start if present
                    title = re.sub(r'^\d+\s*', '', title)
                    title = clean_title(title.title())
                    if title:
                        return title
        except:
            pass
    
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

        # Format items
        items = []
        for entry in sorted_entries[:5]:  # Return top 10 items
            content = format_content(
                getattr(entry, 'content', [{}])[0].get('value', '') or 
                entry.get('content', [{}])[0].get('value', '') if isinstance(entry.get('content', []), list) and entry.get('content') else
                entry.get('summary', ''),
                'html'
            )

            extracted_title = extract_title(entry)
            if extracted_title == 'Untitled Entry' and content:
                fallback_entry = {
                    'summary': content,
                    'content': [{'value': content}]
                }
                fallback_title = extract_title(fallback_entry)
                if fallback_title != 'Untitled Entry':
                    extracted_title = fallback_title

            items.append({
                "title": extracted_title,
                "link": entry.get('link', ''),
                "published": entry.get('published', entry.get('date', '')),
                "summary": format_content(entry.get('summary', ''), 'text'),
                "author": entry.get('author', 'Unknown'),
                "categories": [tag.get('term') for tag in entry.get('tags', [])],
                "content": content
            })

        return {
            "items": items
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