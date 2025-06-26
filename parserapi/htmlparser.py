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

import re
from selectolax.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from datetime import datetime
import importlib

def parse_html_to_feed(html_content, base_url):
    parsed_url = urlparse(base_url)
    domain = parsed_url.netloc.lower()

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

    html_node = tree.css('html')
    language = html_node[0].attributes.get('lang', '') if html_node else ''

    feed_title_elem = tree.css_first('title')
    feed_title = feed_title_elem.text(strip=True) if feed_title_elem else 'Untitled Feed'

    entries = []

    # Common candidate article containers
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
            '[id*="story"]',
            '[role="article"]'
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

    MIN_TEXT_LENGTH = 50
    filtered_candidates = [cand for cand in unique_candidates if len(cand.text(strip=True)) >= MIN_TEXT_LENGTH]

    if not filtered_candidates:
        filtered_candidates = tree.css('body')

    for candidate in filtered_candidates:
        # --- Title Extraction ---
        title = None
        title_candidates = []

        # Site-specific title extraction
        if site_config and hasattr(site_config, "title_selector"):
            title_elems = candidate.css(site_config.title_selector)
            for elem in title_elems:
                text = elem.text(strip=True)
                if text:
                    title_candidates.append(text)

        # Common selectors in priority order
        common_selectors = [
            'h1', 'h2', 'h3',
            '[itemprop="headline"]',
            '[class*="post-card_title"]',
            '.title', '.headline', '.entry-title',
            'a[rel="bookmark"]'
        ]
        for selector in common_selectors:
            elems = candidate.css(selector)
            for elem in elems:
                text = elem.text(strip=True)
                if text:
                    title_candidates.append(text)

        # Aria-label attribute
        aria_label = candidate.attributes.get('aria-label', '').strip()
        if aria_label:
            title_candidates.append(aria_label)

        # Link texts within candidate
        link_elems = candidate.css('a[href]')
        for link in link_elems:
            text = link.text(strip=True)
            if text:
                title_candidates.append(text)

        # Remove duplicates while preserving order
        seen_titles = set()
        unique_title_candidates = []
        for title in title_candidates:
            if title not in seen_titles:
                seen_titles.add(title)
                unique_title_candidates.append(title)

        if unique_title_candidates:
            title = unique_title_candidates[0]
        else:
            # Fallback to document title and global h1
            doc_title_elem = tree.css_first('title')
            doc_title = doc_title_elem.text(strip=True) if doc_title_elem else ''
            if doc_title:
                separators = ['|', '-', '—', '•', '::', '–']
                for sep in separators:
                    if sep in doc_title:
                        parts = doc_title.split(sep, 1)
                        candidate_title = parts[0].strip()
                        if candidate_title:
                            title = candidate_title
                            break
                if not title:
                    title = doc_title.strip()
            else:
                title = ''

            # Check global h2 elements if still no title
            if not title:
                h2_elems = tree.css('h2')
                for h2 in h2_elems:
                    h2_text = h2.text(strip=True)
                    if h2_text:
                        title = h2_text
                        break

        # Final fallback
        if not title:
            title = 'Untitled Entry'

        # --- Link Extraction ---
        link = base_url
        link_elem = candidate.css_first('a[href]')
        if link_elem:
            href = link_elem.attributes.get('href', '')
            if href:
                link = urljoin(base_url, href)

        # --- Published Date Extraction ---
        if site_config and hasattr(site_config, "date_selector"):
            date_elem = candidate.css_first(site_config.date_selector)
        else:
            date_elem = candidate.css_first('time, [datetime], .date, .published, .posted-on')
        published = ''
        if date_elem:
            datetime_attr = date_elem.attributes.get('datetime')
            published = datetime_attr if datetime_attr else date_elem.text(strip=True)

        # --- Content Extraction ---
        if site_config and hasattr(site_config, "content_selector"):
            content_elem = candidate.css_first(site_config.content_selector)
        else:
            content_elem = candidate.css_first('[itemprop="articleBody"], .content, .entry-content, .post-content')
        if content_elem:
            content_html = content_elem.html
        else:
            content_html = candidate.html

        # --- Author Extraction ---
        if site_config and hasattr(site_config, "author_selector"):
            author_elem = candidate.css_first(site_config.author_selector)
        else:
            author_elem = candidate.css_first('[itemprop="author"], .author, .byline')
        author = author_elem.text(strip=True) if author_elem else ''

        # --- Tags Extraction ---
        if site_config and hasattr(site_config, "tag_selector"):
            tag_elems = candidate.css(site_config.tag_selector)
        else:
            tag_elems = candidate.css('[rel="tag"], .category, .tag')
        tags = [{'term': tag.text(strip=True)} for tag in tag_elems if tag.text(strip=True)]

        # --- Summary Creation ---
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