# src/analyzer.py
from textblob import TextBlob
import pandas as pd

def analyze_sentiment(comments):
    results = []
    
    for comment_data in comments:
        text = comment_data["translated_comment"]
        polarity = TextBlob(text).sentiment.polarity
        sentiment = "positive" if polarity > 0 else "negative" if polarity < 0 else "neutral"
        comment_data["sentiment"] = sentiment
        comment_data["polarity"] = polarity
        results.append(comment_data)
    
    # Summarize sentiment
    df = pd.DataFrame(results)
    if not df.empty:
        sentiment_counts = df["sentiment"].value_counts(normalize=True) * 100
        summary = {
            "positive_pct": sentiment_counts.get("positive", 0),
            "negative_pct": sentiment_counts.get("negative", 0),
            "neutral_pct": sentiment_counts.get("neutral", 0)
        }
    else:
        summary = {"positive_pct": 0, "negative_pct": 0, "neutral_pct": 0}
    
    return results, summary