"""
MIT License

Copyright (c) 2025 Burhanverse <contact@burhanverse.eu.org>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from flask import Flask, request, jsonify
from waitress import serve
import feedparser
from . import htmlparser
import requests
import time
from time import mktime
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from rapidfuzz import process, fuzz
import json
from lxml import etree
from minify_html import minify
from emoji import demojize
from datetime import datetime

parserapi = Flask(__name__)
parserapi.config['USER_AGENT'] = "rssify/36 +https://burhanverse.eu.org/"

def fetch_url(url):
    try:
        response = requests.get(
            url,
            headers={'User-Agent': parserapi.config['USER_AGENT']},
            timeout=10
        )
        response.raise_for_status()
        return response
    except Exception as e:
        raise ValueError(f"URL fetch failed: {str(e)}")

def detect_content_type(response):
    ctype = response.headers.get('Content-Type', '').split(';')[0].lower()
    if not ctype:
        if response.content.lstrip().startswith(b'{'):
            return 'json'
        if b'<rss' in response.content.lower():
            return 'xml'
    return ctype

def extract_html_feeds(html, base_url):
    soup = BeautifulSoup(html, 'lxml')
    feed_links = []

    for link in soup.find_all('link', {
        'type': ['application/rss+xml', 'application/atom+xml', 'application/json']
    }):
        feed_links.append(urljoin(base_url, link.get('href')))

    for a in soup.find_all('a', href=True):
        if any(kw in a['href'].lower() for kw in ['rss', 'feed', 'atom']):
            feed_links.append(urljoin(base_url, a['href']))

    if feed_links:
        ranked_feeds = process.extract(
            'feed', 
            feed_links, 
            scorer=fuzz.partial_ratio,
            limit=3
        )
        return [feed[0] for feed in ranked_feeds]
    return []

def parse_xml(content):
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
    if content_type == 'html':
        return minify(content, minify_js=True, minify_css=True)
    return demojize(content)

@parserapi.route('/parse', methods=['GET'])
def parse_feed():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Missing URL parameter"}), 400

    try:
        response = fetch_url(url)
        content_type = detect_content_type(response)
        final_feed = None
        source = "Direct feed"

        if 'html' in content_type:
            found_feeds = extract_html_feeds(response.content, url)
            if found_feeds:
                for feed_url in found_feeds:
                    try:
                        feed_response = fetch_url(feed_url)
                        feed_content_type = detect_content_type(feed_response)
                        if 'xml' in feed_content_type:
                            feed = parse_xml(feed_response.content)
                        elif 'json' in feed_content_type:
                            feed = parse_json(feed_response.content)
                        else:
                            continue
                        final_feed = feed
                        source = "HTML discovered feed"
                        break
                    except Exception:
                        continue
            if not final_feed:
                final_feed = htmlparser.parse_html_to_feed(response.content, url)
                source = "HTML parser"
        else:
            try:
                if 'xml' in content_type:
                    final_feed = parse_xml(response.content)
                elif 'json' in content_type:
                    final_feed = parse_json(response.content)
                else:
                    raise ValueError("Unsupported content type")
            except Exception as e:
                final_feed = htmlparser.parse_html_to_feed(response.content, url)
                source = "HTML parser (fallback)"

        feed_metadata = {
            "title": final_feed.get('title', 'Untitled Feed'),
            "link": final_feed.get('link', url),
            "description": final_feed.get('description', ''),
            "language": final_feed.get('language', ''),
            "updated": final_feed.get('updated', datetime.now().isoformat()),
            "version": final_feed.get('version', '')
        }

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

        items = []
        for entry in sorted_entries[:5]:
            content = format_content(
                getattr(entry, 'content', [{}])[0].get('value', '') or 
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

        return jsonify({
            "feed": feed_metadata,
            "items": items,
            "source": source
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500