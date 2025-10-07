from flask import Flask, request, jsonify
import requests
import mysql.connector
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # allow frontend requests

# ==============================
# MySQL Connection
# ==============================
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Mysqlpassword",
    database="trendnews_schema"
)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS news_articles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255),
    source VARCHAR(100),
    publishedAt DATETIME,
    url TEXT,
    description TEXT
)
""")

# ==============================
# API Key
# ==============================
api_key = "Gnewsapi"

# ==============================
# Fetch News Function
# ==============================
def fetch_news(query="latest", language="en", max_results=10):
    url = f"https://gnews.io/api/v4/search?q={query}&lang={language}&max={max_results}&apikey={api_key}"
    response = requests.get(url)

    if response.status_code == 200:
        news_data = response.json()
        articles = news_data.get("articles", [])
        results = []

        for article in articles:
            published_at = article.get("publishedAt", None)
            if published_at:
                try:
                    published_at = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
                except ValueError:
                    published_at = None

            news_item = {
                "title": article.get("title", ""),
                "source": article.get("source", {}).get("name", ""),
                "description": article.get("description", ""),
                "publishedAt": published_at,
                "url": article.get("url", "")
            }
            results.append(news_item)

            # Insert into MySQL
            cursor.execute("""
                INSERT INTO news_articles (title, source, publishedAt, url, description)
                VALUES (%s, %s, %s, %s, %s)
            """, (news_item["title"], news_item["source"], news_item["publishedAt"],
                  news_item["url"], news_item["description"]))

        conn.commit()
        return results
    else:
        return []

# ==============================
# API Endpoint
# ==============================
@app.route("/search")
def search_news():
    query = request.args.get("q", "latest")   # default to "latest"
    results = fetch_news(query=query, language="en", max_results=9)

    for r in results:
        if isinstance(r["publishedAt"], datetime):
            r["publishedAt"] = r["publishedAt"].strftime("%Y-%m-%d %H:%M:%S")
    return jsonify(results)
    
    if not results:
        return jsonify({"error": "No news found"}), 404
    
    # Convert datetime to string for JSON
    for r in results:
        if isinstance(r["publishedAt"], datetime):
            r["publishedAt"] = r["publishedAt"].strftime("%Y-%m-%d %H:%M:%S")
    
    return jsonify(results)

# ==============================
# Run Flask
# ==============================
if __name__ == "__main__":
    app.run(debug=True)


