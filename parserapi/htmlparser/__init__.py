"""
HTML Parser Module - AI-powered feed extraction using ScrapeGraphAI + Gemini

Simple usage:
    from parserapi.htmlparser import parse_html_to_feed
    
    feed = parse_html_to_feed(html_content, base_url)
"""

from .parser import parse_html_to_feed, ScrapeGraphHTMLParser
from .config import ParserConfig

__all__ = ['parse_html_to_feed', 'ScrapeGraphHTMLParser', 'ParserConfig']
