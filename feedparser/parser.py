import re
from selectolax.parser import HTMLParser
from urllib.parse import urljoin
from datetime import datetime

def parse_html_to_feed(html_content, base_url):

    try:
        from newspaper import Article  # newspaper4k
        article_obj = Article(base_url)
        article_obj.set_html(html_content)
        article_obj.parse()

        if article_obj.text and len(article_obj.text.strip()) > 200:
            entry = {
                'title': article_obj.title or 'Untitled Entry',
                'link': base_url,
                'published': article_obj.publish_date.isoformat() if article_obj.publish_date else '',
                'content': [{'value': article_obj.text}],
                'summary': (article_obj.text[:200] + '...') if len(article_obj.text) > 200 else article_obj.text,
                'author': ', '.join(article_obj.authors) if article_obj.authors else '',
                'tags': [{'term': tag} for tag in article_obj.keywords] if hasattr(article_obj, 'keywords') and article_obj.keywords else []
            }
            feed_title = article_obj.title if article_obj.title else 'Untitled Feed'
            feed = {
                'title': feed_title,
                'link': base_url,
                'description': '',
                'language': '',
                'updated': datetime.now().isoformat(),
                'entries': [entry],
                'version': 'html'
            }
            return feed
    except Exception as e:
        # If newspaper4k fails or doesn't produce enough content, fall back to CSS-based approach.
        pass

    # --- Fallback: CSS selector heuristics with Selectolax ---
    tree = HTMLParser(html_content)
    
    html_node = tree.css('html')
    language = html_node[0].attributes.get('lang', '') if html_node else ''
    
    feed_title_elem = tree.css_first('title')
    feed_title = feed_title_elem.text(strip=True) if feed_title_elem else 'Untitled Feed'
    
    entries = []
    
    # --- Identify candidate article containers ---
    # Expand selectors to catch semantic articles and also elements that might be used as article containers,
    # including those using data attributes (common on sites with obfuscated or randomized classes).
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
        '[data-type*="in_view"]',
        '[data-testid*="virginia-section-8"]'
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
    
    # Filter out candidates that are too trivial (for example, with very short text).
    filtered_candidates = []
    MIN_TEXT_LENGTH = 50  # Tweak this threshold as needed
    for candidate in unique_candidates:
        if len(candidate.text(strip=True)) >= MIN_TEXT_LENGTH:
            filtered_candidates.append(candidate)
    
    # Fallback: if no candidate is found, use the entire <body>.
    if not filtered_candidates:
        filtered_candidates = tree.css('body')
    
    # --- Process each candidate as a potential article ---
    for candidate in filtered_candidates:
        # --- Title Extraction ---
        title_elem = candidate.css_first(
            'p, [data-testid*="card-headline"], h1, [itemprop="headline"], .title, '
            '[data-type*="in_view"] p, '
        )
        title = title_elem.text(strip=True) if title_elem else None
        
        # Additional fallbacks
        if not title:
            title = candidate.attributes.get('aria-label', '').strip() or None
        
        if not title:
            link_elem = candidate.css_first('a[href]')
            title = link_elem.text(strip=True) if link_elem else None
        
        if not title:
            title = 'Untitled Entry'
        
        # --- Link Extraction ---
        # Use the first anchor tag inside the container.
        link = base_url
        link_elem = candidate.css_first('a[href]')
        if link_elem:
            href = link_elem.attributes.get('href', '')
            if href:
                link = urljoin(base_url, href)
        
        # --- Published Date Extraction ---
        published = ''
        date_elem = candidate.css_first('time, [datetime], .date, .published, .posted-on')
        if date_elem:
            datetime_attr = date_elem.attributes.get('datetime')
            published = datetime_attr if datetime_attr else date_elem.text(strip=True)
        
        # --- Content Extraction ---
        content_elem = candidate.css_first('[itemprop="articleBody"], .content, .entry-content, .post-content')
        if content_elem:
            content_html = content_elem.html
        else:
            # Fallback: use the entire candidate HTML.
            content_html = candidate.html
        
        # --- Author Extraction ---
        author = ''
        author_elem = candidate.css_first('[itemprop="author"], .author, .byline')
        if author_elem:
            author = author_elem.text(strip=True)
        
        # --- Categories/Tags Extraction ---
        tags = []
        tag_elems = candidate.css('[rel="tag"], .category, .tag')
        for tag in tag_elems:
            tag_text = tag.text(strip=True)
            if tag_text:
                tags.append({'term': tag_text})
        
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
    
    # --- Final feed assembly ---
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
