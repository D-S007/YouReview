# src/app.py
from flask import Flask, request, render_template
from src.scraper import scrape_youtube_comments
from src.processor import process_comments
from src.analyzer import analyze_sentiment

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        query = request.form["query"]
        if not query:
            return render_template("index.html", error="Please enter a product name")
        
        try:
            # Scrape comments
            comments = scrape_youtube_comments(query)
            if not comments:
                return render_template("index.html", error="No relevant comments found")
            
            # Process comments
            processed_comments = process_comments(comments)
            
            # Analyze sentiment
            analyzed_comments, sentiment_summary = analyze_sentiment(processed_comments)
            
            return render_template(
                "results.html",
                comments=analyzed_comments,
                summary=sentiment_summary,
                query=query
            )
        except Exception as e:
            return render_template("index.html", error=f"An error occurred: {e}")
    
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)