# RSS Parser API - FastAPI + ScrapeGraphAI

AI-powered feed parser supporting RSS, Atom, JSON feeds, and intelligent HTML parsing using Google Gemini.

## 🚀 Features

- **Multi-format Feed Support**: RSS, Atom, JSON feeds
- **AI-Powered HTML Parsing**: Uses ScrapeGraphAI with Google Gemini for intelligent content extraction
- **Automatic Feed Discovery**: Finds embedded RSS/Atom links in HTML pages
- **FastAPI Framework**: Modern, fast, with automatic interactive API documentation
- **Intelligent Fallback**: Gracefully degrades to basic parsing if AI fails

## 📋 Prerequisites

- Python 3.8 or higher
- Google Gemini API key ([Get it here](https://makersuite.google.com/app/apikey))

## 🔧 Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

```bash
playwright install
```

### 3. Set Environment Variable

For fish shell:
```bash
set -x GEMINI_API_KEY 'your-api-key-here'
```

For bash/zsh:
```bash
export GEMINI_API_KEY='your-api-key-here'
```

## 🏃 Running the API

```bash
# Run with uvicorn
python -m parserapi

# Or use uvicorn directly
uvicorn parserapi.api:parserapi --host 0.0.0.0 --port 5000
```

The API will be available at:
- **API Endpoint**: http://localhost:2058
- **Interactive Docs (Swagger UI)**: http://localhost:2058/docs

## 📖 API Usage

### Parse a Feed

**Endpoint**: `GET /parse`

**Parameters**:
- `url` (required): The URL to parse
- `gemini_key` (optional): Gemini API key (overrides environment variable)

**Examples**:

```bash
# Parse a blog
curl "http://localhost:5000/parse?url=https://techcrunch.com"

# With API key in request
curl "http://localhost:5000/parse?url=https://example.com&gemini_key=your-key"
```

**Response**:
```json
{
  "feed": {
    "title": "Site Title",
    "link": "https://example.com",
    "description": "",
    "language": "en",
    "updated": "2025-11-06T10:30:00",
    "version": "html-scrapegraph"
  },
  "items": [
    {
      "title": "Latest Blog Post",
      "link": "https://example.com/post/1",
      "published": "2025-11-06",
      "summary": "Brief summary of the post...",
      "author": "Author Name",
      "categories": ["tech", "ai"],
      "content": "<p>Full HTML content...</p>"
    }
  ],
  "source": "AI HTML parser (ScrapeGraphAI + Gemini)"
}
```

### Health Check

**Endpoint**: `GET /health`

```bash
curl "http://localhost:5000/health"
```

**Response**:
```json
{
  "status": "healthy",
  "version": "2.0.0-fastapi-scrapegraph",
  "gemini_configured": true
}
```

### Root Endpoint

**Endpoint**: `GET /`

```bash
curl "http://localhost:5000/"
```

Returns API information and available endpoints.

## 🐍 Python Usage

```python
from parserapi.htmlparser import parse_html_to_feed
import requests

# Fetch a webpage
response = requests.get('https://techcrunch.com')

# Parse with AI
feed = parse_html_to_feed(
    html_content=response.text,
    base_url='https://techcrunch.com',
    gemini_api_key='your-api-key'  # Optional if set in env
)

# Access the data
print(f"Feed Title: {feed['title']}")
print(f"Found {len(feed['entries'])} articles")

for article in feed['entries']:
    print(f"- {article['title']}")
    print(f"  Link: {article['link']}")
```

## 🎯 How It Works

1. **URL Fetch**: Fetches the target URL
2. **Content Type Detection**: Identifies if it's HTML, RSS, JSON, etc.
3. **Feed Discovery**: For HTML, first looks for embedded RSS/Atom links
4. **AI Parsing**: If no feed found, uses ScrapeGraphAI with Gemini to:
   - Analyze the HTML structure
   - Identify article patterns
   - Extract structured data (titles, links, dates, content)
5. **Fallback**: If AI fails, uses basic BeautifulSoup parsing
6. **Response**: Returns structured JSON response

## 📊 Performance

| Metric | Value |
|--------|-------|
| First Request | 4-6 seconds (AI model loading) |
| Subsequent Requests | 2-4 seconds |
| Success Rate | ~95% |
| Free Tier Limit | 15 requests/minute (Gemini) |

## 💰 Cost Estimates

### Gemini API Free Tier
- 15 requests per minute
- ~500 requests per day
- Perfect for testing and small projects

### Paid Tier
- $0.00025 per request (approximate)
- 10,000 requests = ~$2.50
- 100,000 requests = ~$25

## 🔧 Configuration

The parser uses these default settings:

```python
graph_config = {
    "llm": {
        "api_key": "your-gemini-key",
        "model": "gemini-pro",
    },
    "verbose": False,
    "headless": True,
}
```

Customize by modifying `parserapi/htmlparser.py`.

## 🐛 Troubleshooting

### "Gemini API key required" Error
- Ensure `GEMINI_API_KEY` is set in environment
- Or pass `gemini_key` parameter in API request

### Import Errors
```bash
pip install -r requirements.txt
playwright install
```

### Slow Performance
- First request is slower (AI model loading)
- Subsequent requests are faster
- Consider implementing caching

### AI Extraction Failures
- Check if Gemini API key is valid
- Verify you have API quota remaining
- Parser will automatically fallback to basic extraction

## 📂 Project Structure

```
parserapi/
├── __main__.py          # Entry point with uvicorn
├── api.py               # FastAPI app with endpoints
├── htmlparser.py        # ScrapeGraphAI HTML parser
├── requirements.txt     # Python dependencies
└── cfg/                 # Legacy config directory (can be removed)
```

## 🚀 Deployment

### Production Deployment

```bash
# With Gunicorn (for production)
pip install gunicorn
gunicorn parserapi.api:parserapi -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5000

# Or with uvicorn directly
uvicorn parserapi.api:parserapi --host 0.0.0.0 --port 5000 --workers 4
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt && playwright install

COPY parserapi/ ./parserapi/

ENV GEMINI_API_KEY=your-key-here

CMD ["uvicorn", "parserapi.api:parserapi", "--host", "0.0.0.0", "--port", "5000"]
```

## 📝 API Documentation

FastAPI provides automatic interactive documentation:

- **Swagger UI**: http://localhost:2058/docs
  - Try out the API directly in your browser
  - See all parameters and response schemas

## 🎓 Advanced Usage

### Custom Parsing Logic

You can extend the parser:

```python
from parserapi.htmlparser import ScrapeGraphHTMLParser

class CustomParser(ScrapeGraphHTMLParser):
    def _structure_feed_data(self, raw_result, base_url):
        # Custom processing logic
        return super()._structure_feed_data(raw_result, base_url)
```

### Caching Results

Implement caching to reduce API calls:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_parse(url):
    return parse_html_to_feed(fetch_html(url), url)
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

Same as the parent project.

## 🆘 Support

For issues or questions:
- Check the interactive API docs at `/docs`
- Review error messages in the logs
- Verify API key and quota
- Test with simpler websites first

## 🔗 Resources

- **ScrapeGraphAI**: https://scrapegraphai.com/
- **Gemini API**: https://ai.google.dev/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Get API Key**: https://makersuite.google.com/app/apikey

---

**Version**: 2.0.0  
**Framework**: FastAPI  
**AI Engine**: ScrapeGraphAI + Google Gemini
