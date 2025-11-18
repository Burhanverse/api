import uvicorn
from .api import parserapi

if __name__ == '__main__':
    print("Starting ParserAPI with FastAPI + ScrapeGraphAI...")
    print("API Documentation: http://0.0.0.0:2058/docs")
    uvicorn.run(parserapi, host='0.0.0.0', port=2058, log_level="info")
