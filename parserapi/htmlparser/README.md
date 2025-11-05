# HTML Parser Module

Modular AI-powered HTML parser using ScrapeGraphAI and Google Gemini.

## Structure

```
htmlparser/
├── __init__.py          # Module entry point
├── config.py            # Configuration management
├── parser.py            # Core parser implementation
├── prompts.py           # AI prompt templates
└── utils.py             # Utility functions
```

## Configuration

### Environment Variables (.env file)

Create a `.env` file in the project root:

```bash
# Gemini API Configuration
GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL=gemini-pro

# Parser Settings
PARSER_VERBOSE=false          # Enable verbose logging
PARSER_HEADLESS=true          # Run browser in headless mode
PARSER_TIMEOUT=30             # Parsing timeout in seconds
PARSER_MAX_ARTICLES=20        # Maximum articles to extract
```

### Configuration via Code

```python
from parserapi.htmlparser import ParserConfig

config = ParserConfig()

# Access configuration
api_key = config.gemini_api_key
model = config.gemini_model
max_articles = config.max_articles
```

## Usage

### Basic Usage

```python
from parserapi.htmlparser import parse_html_to_feed

# Parse HTML content
feed = parse_html_to_feed(html_content, base_url)
```

### With Custom API Key

```python
from parserapi.htmlparser import parse_html_to_feed

feed = parse_html_to_feed(
    html_content, 
    base_url,
    gemini_api_key='your-key'
)
```

### Using Different Prompts

```python
from parserapi.htmlparser import parse_html_to_feed

# For news sites
feed = parse_html_to_feed(
    html_content, 
    base_url,
    prompt_type='news'
)

# For blogs
feed = parse_html_to_feed(
    html_content, 
    base_url,
    prompt_type='blog'
)

# Minimal extraction
feed = parse_html_to_feed(
    html_content, 
    base_url,
    prompt_type='minimal'
)
```

### Using the Parser Class

```python
from parserapi.htmlparser import ScrapeGraphHTMLParser

# Initialize parser
parser = ScrapeGraphHTMLParser(
    gemini_api_key='your-key',
    prompt_type='news'
)

# Parse HTML
feed = parser.parse_html_to_feed(html_content, base_url)
```

## Prompt Types

### Available Prompts

1. **default** - General purpose extraction
2. **news** - Optimized for news sites
3. **blog** - Optimized for blogs
4. **minimal** - Lightweight extraction

### Custom Prompts

```python
from parserapi.htmlparser.prompts import customize_prompt

# Customize with additional constraints
custom_prompt = customize_prompt(
    max_articles=10,
    include_images=True,
    require_dates=True,
    language_filter='en'
)
```

### Creating Your Own Prompts

Edit `prompts.py`:

```python
CUSTOM_PROMPT = """
Your custom extraction instructions here...
"""

def get_prompt(prompt_type: str = "default") -> str:
    prompts = {
        "default": DEFAULT_EXTRACTION_PROMPT,
        "custom": CUSTOM_PROMPT,  # Add your custom prompt
    }
    return prompts.get(prompt_type, DEFAULT_EXTRACTION_PROMPT)
```

## Response Format

```python
{
    'title': 'Feed Title',
    'link': 'https://example.com',
    'description': '',
    'language': 'en',
    'updated': '2025-11-06T10:30:00',
    'entries': [
        {
            'title': 'Article Title',
            'link': 'https://example.com/article',
            'published': '2025-11-06',
            'content': [{'value': '<p>HTML content...</p>'}],
            'summary': 'Brief summary...',
            'author': 'Author Name',
            'tags': [{'term': 'tag1'}, {'term': 'tag2'}]
        }
    ],
    'version': 'html-scrapegraph'
}
```

## Fallback Behavior

If AI parsing fails, the parser automatically falls back to basic BeautifulSoup extraction:

1. Attempts ScrapeGraphAI parsing
2. On failure, uses BeautifulSoup to find `<article>` tags
3. Extracts basic metadata (title, links)
4. Returns partial data rather than failing completely

## Advanced Configuration

### Custom Graph Config

```python
from parserapi.htmlparser.config import config

# Modify configuration
custom_config = config.get_graph_config()
custom_config['llm']['model'] = 'gemini-1.5-pro'
custom_config['verbose'] = True
```

### Adjusting Max Articles

Set in `.env`:
```bash
PARSER_MAX_ARTICLES=50
```

Or via environment:
```bash
export PARSER_MAX_ARTICLES=50
```

### Timeout Settings

```bash
PARSER_TIMEOUT=60  # 60 seconds
```

## Error Handling

The parser handles errors gracefully:

```python
try:
    feed = parse_html_to_feed(html_content, base_url)
except ValueError as e:
    # API key missing or invalid
    print(f"Configuration error: {e}")
except Exception as e:
    # Parsing error (will use fallback)
    print(f"Parsing error: {e}")
```

## Best Practices

1. **Use .env file** - Keep API keys secure
2. **Choose right prompt** - Use news/blog prompts for better results
3. **Set reasonable limits** - Don't extract more articles than needed
4. **Enable verbose mode** - For debugging during development
5. **Monitor API usage** - Keep track of Gemini API calls

## Troubleshooting

### "Gemini API key required"
- Set `GEMINI_API_KEY` in `.env` file
- Or pass `gemini_api_key` parameter

### Slow parsing
- First request is slower (model initialization)
- Adjust `PARSER_TIMEOUT` if needed

### Poor extraction quality
- Try different `prompt_type` (news, blog, etc.)
- Create custom prompt in `prompts.py`

### Fallback parsing triggered
- Check `PARSER_VERBOSE=true` for error details
- Verify API key is valid and has quota

## Module API Reference

### Functions

- `parse_html_to_feed(html_content, base_url, gemini_api_key=None, prompt_type='default')`

### Classes

- `ScrapeGraphHTMLParser(gemini_api_key=None, prompt_type='default')`
- `ParserConfig()`

### Utility Functions

- `structure_feed_data(raw_result, base_url, max_articles)`
- `create_summary(content_html, max_length)`
- `process_tags(tags_raw)`
- `fallback_parse(html_content, base_url)`

### Prompt Functions

- `get_prompt(prompt_type)`
- `customize_prompt(base_prompt=None, **kwargs)`
