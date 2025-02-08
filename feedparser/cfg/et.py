# cfg/et.py

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
author_selector = ''

# Selector for tags or categories
tag_selector = ''