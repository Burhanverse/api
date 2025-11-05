from waitress import serve
from .api import parserapi

if __name__ == '__main__':
    print("Starting ParserAPI...")
    serve(parserapi, threads=8, host='0.0.0.0', port=5000)
