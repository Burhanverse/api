import uvicorn
from .api import parserapi

if __name__ == '__main__':
    print("Starting ParserAPI with FastAPI + ScrapeGraphAI...")
    print("API Documentation: http://0.0.0.0:5000/docs")
    print("Alternative Docs: http://0.0.0.0:5000/redoc")
    uvicorn.run(parserapi, host='0.0.0.0', port=5000, log_level="info")
