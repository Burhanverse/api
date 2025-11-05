# cfg/et.py
# Candidate article containers
candidate_selectors = [
    '[id*="topStories"]', #home page
    '[class*="eachStory"]', #agriculture
    '[id*="pageContent"]', #tech
    '[class*="story_sec"]', #crypto
]

# Selector to extract the article title
title_selector = [
    'h1, h2, h3, h4, h5, h6',
    '[class*="story_lg_head"]',
]

# Selector for publication date
date_selector = 'div.date, time'

# Selector for  author
author_selector = 'span.byline__name'

# Selector for tags or categories
tag_selector = 'ul.tags li'