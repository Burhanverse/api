# cfg/bbc.py
# Candidate article containers
candidate_selectors = [
    '[data-testid*="dundee-card"]',
    '[data-testid*="nevada-card"]',
]

# Selector to extract the article title
title_selector = '[data-testid*="card-headline"]'

# Selector to extract the article content
content_selector = '[data-testid*="card-description"]'

# Selector for publication date
date_selector = 'div.date, time'

# Selector for  author
author_selector = 'span.byline__name'

# Selector for tags or categories
tag_selector = 'ul.tags li'