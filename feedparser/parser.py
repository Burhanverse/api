"""
MIT License

Copyright (c) 2025 Burhanverse

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

import re
from selectolax.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from datetime import datetime
import importlib

def parse_html_to_feed(html_content, base_url):
    # --- CSS selector heuristics with Selectolax ---
    parsed_url = urlparse(base_url)
    domain = parsed_url.netloc.lower()

    # Mapping of domains to config module paths.
    custom_configs = {
        'bbc.com': 'cfg.bbc',
        'timesofindia.indiatimes.com': 'cfg.toi',
        'economictimes.indiatimes.com': 'cfg.et',
    }

    site_config = None
    for key, mod_path in custom_configs.items():
        if key in domain:
            try:
                site_config = importlib.import_module(mod_path)
            except ImportError:
                site_config = None
            break

    tree = HTMLParser(html_content)

    # Get language from the <html> tag.
    html_node = tree.css('html')
    language = html_node[0].attributes.get('lang', '') if html_node else ''

    feed_title_elem = tree.css_first('title')
    feed_title = feed_title_elem.text(strip=True) if feed_title_elem else 'Untitled Feed'

    entries = []

    # --- Common candidate article containers ---
    if site_config and hasattr(site_config, "candidate_selectors"):
        selectors = site_config.candidate_selectors
    else:
        selectors = [
            'article',
            '[itemtype*="Article"]',
            '[class*="post"]',
            '[id*="post"]',
            '[class*="article"]',
            '[class*="articles"]',
            '[id*="article"]',
            '[class*="entry"]',
            '[id*="entry"]',
            '[class*="story"]',
            '[id*="story"]'
        ]

    candidate_elements = []
    for selector in selectors:
        candidate_elements.extend(tree.css(selector))

    seen = set()
    unique_candidates = []
    for elem in candidate_elements:
        if id(elem) not in seen:
            seen.add(id(elem))
            unique_candidates.append(elem)

    MIN_TEXT_LENGTH = 50  # Minimum text length to consider
    filtered_candidates = [cand for cand in unique_candidates if len(cand.text(strip=True)) >= MIN_TEXT_LENGTH]

    # Fallback: if no candidate is found, use the entire <body>.
    if not filtered_candidates:
        filtered_candidates = tree.css('body')

    # --- Process each candidate as a potential article ---
    for candidate in filtered_candidates:
        # --- Common Title Extraction ---
        if site_config and hasattr(site_config, "title_selector"):
            title_elem = candidate.css_first(site_config.title_selector)
        else:
            title_elem = candidate.css_first(
                ' h1, [itemprop="headline"], .title'
            )
        title = title_elem.text(strip=True) if title_elem else None
        if not title:
            title = candidate.attributes.get('aria-label', '').strip() or None
        if not title:
            link_elem = candidate.css_first('a[href]')
            title = link_elem.text(strip=True) if link_elem else None
        if not title:
            title = 'Untitled Entry'

        # --- Common Link Extraction ---
        link = base_url
        link_elem = candidate.css_first('a[href]')
        if link_elem:
            href = link_elem.attributes.get('href', '')
            if href:
                link = urljoin(base_url, href)

        # --- Common Published Date Extraction ---
        if site_config and hasattr(site_config, "date_selector"):
            date_elem = candidate.css_first(site_config.date_selector)
        else:
            date_elem = candidate.css_first('time, [datetime], .date, .published, .posted-on')
        published = ''
        if date_elem:
            datetime_attr = date_elem.attributes.get('datetime')
            published = datetime_attr if datetime_attr else date_elem.text(strip=True)

        # --- Common Content Extraction ---
        if site_config and hasattr(site_config, "content_selector"):
            content_elem = candidate.css_first(site_config.content_selector)
        else:
            content_elem = candidate.css_first('[itemprop="articleBody"], .content, .entry-content, .post-content')
        if content_elem:
            content_html = content_elem.html
        else:
            content_html = candidate.html

        # --- Common Author Extraction ---
        if site_config and hasattr(site_config, "author_selector"):
            author_elem = candidate.css_first(site_config.author_selector)
        else:
            author_elem = candidate.css_first('[itemprop="author"], .author, .byline')
        author = author_elem.text(strip=True) if author_elem else ''

        # --- Common Tags Extraction ---
        if site_config and hasattr(site_config, "tag_selector"):
            tag_elems = candidate.css(site_config.tag_selector)
        else:
            tag_elems = candidate.css('[rel="tag"], .category, .tag')
        tags = [{'term': tag.text(strip=True)} for tag in tag_elems if tag.text(strip=True)]

        # --- Common Summary Creation ---
        summary_text = re.sub(r'<[^>]+>', '', content_html) if content_html else ''
        summary = (summary_text[:200] + '...') if summary_text and len(summary_text) > 200 else summary_text

        entries.append({
            'title': title,
            'link': link,
            'published': published,
            'content': [{'value': content_html}],
            'summary': summary,
            'author': author,
            'tags': tags
        })

    # --- Final Feed Assembly ---
    feed = {
        'title': feed_title,
        'link': base_url,
        'description': '',
        'language': language,
        'updated': datetime.now().isoformat(),
        'entries': entries,
        'version': 'html'
    }

    return feed
