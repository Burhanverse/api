from flask import Flask, request, jsonify
from waitress import serve
import feedparser
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

app = Flask(__name__)
app.config['USER_AGENT'] = "rssify/364 +https://burhanverse.eu.org/"

def fetch_url(url):
    try:
        response = requests.get(
            url,
            headers={'User-Agent': app.config['USER_AGENT']},
            timeout=15
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

def format_content(content, content_type='html'):
    if content_type == 'html':
        return minify(content, minify_js=True, minify_css=True)
    return demojize(content)

@app.route('/parse', methods=['GET'])
def parse_feed():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Missing URL parameter"}), 400

    try:
        response = fetch_url(url)
        content_type = detect_content_type(response)
        final_feed = None

        if 'html' in content_type:
            found_feeds = extract_html_feeds(response.content, url)
            if not found_feeds:
                raise ValueError("No feeds found in HTML content")

            for feed_url in found_feeds:
                try:
                    feed_response = fetch_url(feed_url)
                    content_type = detect_content_type(feed_response)
                    break
                except:
                    continue
            else:
                raise ValueError("All discovered feeds failed to load")
        else:
            feed_response = response

        if 'xml' in content_type:
            feed = parse_xml(feed_response.content)
        elif 'json' in content_type:
            feed = parse_json(feed_response.content)
        else:
            raise ValueError("Unsupported content type")

        feed_metadata = {
            "title": feed.get('title', 'Untitled Feed'),
            "link": feed.get('link', url),
            "description": feed.get('description', ''),
            "language": feed.get('language', ''),
            "updated": feed.get('updated', datetime.now().isoformat()),
            "version": feed.get('version', '')
        }

        sorted_entries = sorted(
            feed.entries,
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
                getattr(entry, 'summary', ''),
                'html'
            )

            items.append({
                "title": entry.get('title', 'Untitled'),
                "link": entry.get('link', ''),
                "published": entry.get('published', entry.get('date', '')),
                "summary": format_content(entry.get('summary', ''), 'text'),
                "author": entry.get('author', 'Unknown'),
                "categories": [tag.term for tag in entry.get('tags', [])],
                "content": content
            })

        return jsonify({
            "feed": feed_metadata,
            "items": items,
            "source": "HTML discovered feed" if 'html' in content_type else "Direct feed"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting advanced feed parser...")
    serve(app, host='0.0.0.0', port=5000)