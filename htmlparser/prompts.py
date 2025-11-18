"""
Unified prompt for AI-powered content extraction
Customize this prompt to adjust extraction behavior
"""

EXTRACTION_PROMPT = """
Extract all articles, blog posts, or news items from this HTML page.

For each article/post/news item, extract ONLY these 2 fields:
1. title - The headline or title of the article
2. link - Full URL to the article (resolve relative URLs to absolute URLs)

Return a JSON object with this exact structure:
{
    "title": "Site or feed title (optional)",
    "articles": [
        {
            "title": "Article title",
            "link": "https://full-url-to-article"
        }
    ]
}

Instructions:
- Focus on main content articles only
- Ignore navigation links, ads, sidebars, footer links, and promotional content
- Ignore about pages, contact links, category pages, menu items
- Extract as many articles as you can find on the page
- Ensure all links are complete absolute URLs starting with http:// or https://
"""


def get_prompt() -> str:
    """
    Get the extraction prompt
    
    Returns:
        Prompt string
    """
    return EXTRACTION_PROMPT


def customize_prompt(
    max_articles: int = None,
    **kwargs
) -> str:
    """
    Customize the extraction prompt with additional constraints.
    
    Args:
        max_articles: Maximum number of articles to extract
        **kwargs: Additional custom instructions
    
    Returns:
        Customized prompt string
    """
    base_prompt = EXTRACTION_PROMPT
    custom_instructions = []
    
    if max_articles:
        custom_instructions.append(f"- Extract up to {max_articles} articles maximum")
    
    for key, value in kwargs.items():
        custom_instructions.append(f"- {key}: {value}")
    
    if custom_instructions:
        additional = "\n\nAdditional requirements:\n" + "\n".join(custom_instructions)
        return base_prompt + additional
    
    return base_prompt
