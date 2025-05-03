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

from flask import Flask, request, jsonify
from ytmusicapi import YTMusic
from waitress import serve
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

tunified = Flask(__name__)
ytmusic = YTMusic()

@tunified.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    try:
        results = ytmusic.search(query, filter='songs')
        if not results:
            return jsonify({"results": []})

        response = []
        for result in results:
            response.append({
                "videoId": result["videoId"],
                "thumbnails": result.get("thumbnails", []),
            })

        return jsonify({"results": response})
    except Exception as e:
        logging.error(f"Error in YTMusicAPI endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    serve(tunified, 
          threads=32,                  
          host='0.0.0.0', 
          port=8080,
          connection_limit=1000,       
          channel_timeout=30,
          cleanup_interval=5)
