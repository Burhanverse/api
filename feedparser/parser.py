import re
from selectolax.parser import HTMLParser
from urllib.parse import urljoin
from datetime import datetime

def parse_html_to_feed(html_content, base_url):
    """
    Parse HTML content into a feed structure.
    
    First, attempt to extract the article using newspaper3k. If that fails or the result is too short,
    fall back to using CSS selector heuristics via Selectolax.
    """
    # --- Attempt extraction with newspaper3k ---
    try:
        from newspaper import Article  # newspaper4k
        article_obj = Article(base_url)
        article_obj.set_html(html_content)
        article_obj.parse()
        
        # Use newspaper if we got a sufficiently long article text.
        if article_obj.text and len(article_obj.text.strip()) > 200:
            entry = {
                'title': article_obj.title or 'Untitled Entry',
                'link': base_url,
                'published': article_obj.publish_date.isoformat() if article_obj.publish_date else '',
                # Newspaper returns plain text. In a real-world scenario you might choose to wrap this in <p> tags,
                # or use another method to generate HTML.
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
                'language': '',  # newspaper doesn't provide language information
                'updated': datetime.now().isoformat(),
                'entries': [entry],
                'version': 'html'
            }
            return feed
    except Exception as e:
        # If newspaper fails (or doesn't extract enough content), we'll fall back to our CSS-based approach.
        # You might want to log the exception here.
        pass

    # --- Fallback: CSS selector heuristics with Selectolax ---
    tree = HTMLParser(html_content)
    
    # Get language from the <html> tag.
    html_node = tree.css('html')
    language = html_node[0].attributes.get('lang', '') if html_node else ''
    
    # Extract the feed title from the <title> tag.
    feed_title_elem = tree.css_first('title')
    feed_title = feed_title_elem.text(strip=True) if feed_title_elem else 'Untitled Feed'
    
    entries = []
    
    # --- Step 1. Identify candidate article containers ---
    # Define selectors to catch semantic articles as well as elements that might be used as article containers.
    selectors = [
        'article',
        '[itemtype*="Article"]',  # Schema.org articles
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
    
    # Remove duplicate elements (by their Python id).
    seen = set()
    unique_candidates = []
    for elem in candidate_elements:
        if id(elem) not in seen:
            seen.add(id(elem))
            unique_candidates.append(elem)
    
    # Filter out candidates that are likely too trivial (e.g. very short text)
    filtered_candidates = []
    MIN_TEXT_LENGTH = 50  # tweak this threshold as needed
    for candidate in unique_candidates:
        if len(candidate.text(strip=True)) >= MIN_TEXT_LENGTH:
            filtered_candidates.append(candidate)
    
    # Fallback: if no candidate is found, use the entire <body>.
    if not filtered_candidates:
        filtered_candidates = tree.css('body')
    
    # --- Step 2. Process each candidate as a potential article ---
    for candidate in filtered_candidates:
        # Extract title: look for header tags and a “headline” microdata property.
        title_elem = candidate.css_first('h1, h2, h3, [itemprop="headline"], .title')
        title = title_elem.text(strip=True) if title_elem else None
        # Fallback: sometimes the first link might have meaningful text.
        if not title:
            link_elem = candidate.css_first('a[href]')
            title = link_elem.text(strip=True) if link_elem else None
        if not title:
            title = 'Untitled Entry'
        
        # Extract link: use the first anchor tag inside the container.
        link = base_url
        link_elem = candidate.css_first('a[href]')
        if link_elem:
            href = link_elem.attributes.get('href', '')
            if href:
                link = urljoin(base_url, href)
        
        # Extract published date: look for <time> or similar elements.
        published = ''
        date_elem = candidate.css_first('time, [datetime], .date, .published, .posted-on')
        if date_elem:
            datetime_attr = date_elem.attributes.get('datetime')
            if datetime_attr:
                published = datetime_attr
            else:
                published = date_elem.text(strip=True)
        
        # Extract content: look for elements likely to hold the article body.
        content_elem = candidate.css_first('[itemprop="articleBody"], .content, .entry-content, .post-content')
        if content_elem:
            content_html = content_elem.html
        else:
            # Fallback: use the entire candidate HTML.
            content_html = candidate.html
        
        # Extract author.
        author = ''
        author_elem = candidate.css_first('[itemprop="author"], .author, .byline')
        if author_elem:
            author = author_elem.text(strip=True)
        
        # Extract categories/tags.
        tags = []
        tag_elems = candidate.css('[rel="tag"], .category, .tag')
        for tag in tag_elems:
            tag_text = tag.text(strip=True)
            if tag_text:
                tags.append({'term': tag_text})
        
        # Create a summary by stripping HTML from the content.
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
