# cfg/toi.py
# Candidate article containers
candidate_selectors = [
    '[data-type*="in_view"]',
]

# Selector to extract the article title
title_selector = 'p'

# Selector for publication date
date_selector = 'div.date, time'

# Selector for  author
author_selector = 'span.byline__name'

# Selector for tags or categories
tag_selector = 'ul.tags li'