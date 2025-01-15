from flask import Flask, request, jsonify
from waitress import serve
import feedparser

app = Flask(__name__)

feedparser.USER_AGENT = "rssify/3.8 +https://burhanverse.eu.org/"

@app.route('/parse', methods=['GET'])
def parse_rss():
    rss_url = request.args.get('url')
    if not rss_url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    try:
        feed = feedparser.parse(rss_url)
        if feed.bozo:
            return jsonify({"error": "Invalid RSS feed format"}), 400

        items = []
        for entry in feed.entries:
            items.append({
                "title": entry.get("title", "No title"),
                "link": entry.get("link", "No link"),
                "published": entry.get("published", "No published date"),
                "summary": entry.get("summary", "No summary"),
            })

        return jsonify({"feed": {
            "title": feed.feed.get("title", "No title"),
            "link": feed.feed.get("link", "No link"),
            "description": feed.feed.get("description", "No description"),
        }, "items": items})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting server with waitress...")
    serve(app, host='0.0.0.0', port=5000)
