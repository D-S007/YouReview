import streamlit as st
from googleapiclient.discovery import build
from pymongo import MongoClient
import nltk
from nltk.corpus import stopwords
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pdfkit
import os

# Initialize tools
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))
analyzer = SentimentIntensityAnalyzer()

# MongoDB Atlas connection
client = MongoClient('mongodb+srv://youreview_user:your_secure_password@youreviewcluster.mongodb.net/youreview?retryWrites=true&w=majority')  # Replace with your connection string
db = client['youreview']
videos_collection = db['videos']

# YouTube API setup
youtube = build('youtube', 'v3', developerKey='YOUR_YOUTUBE_API_KEY')  # Replace with your API key

# Clean text for sentiment analysis
def clean_text(text):
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)  # Remove URLs
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    text = ' '.join(word for word in text.lower().split() if word not in stop_words)
    return text

# Main Streamlit app
st.title("YouReview: Real Product Reviews from YouTube")
st.write("Enter a product name to get a summary of user reviews from YouTube comments.")

product_name = st.text_input("Product Name (e.g., iPhone 14)", "")
if st.button("Get Reviews"):
    if not product_name:
        st.error("Please enter a product name.")
    else:
        with st.spinner("Searching YouTube videos..."):
            # Clear old data for this product
            videos_collection.delete_many({'productName': product_name})

            # Search YouTube videos
            search_response = youtube.search().list(
                q=f"{product_name} review",
                part='snippet',
                maxResults=5,
                order='viewCount',
                type='video'
            ).execute()

            videos = []
            for item in search_response['items']:
                video = {
                    'productName': product_name,
                    'videoId': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'creator': item['snippet']['channelTitle'],
                    'comments': []
                }
                videos.append(video)
            videos_collection.insert_many(videos)

        with st.spinner("Scraping comments and analyzing sentiment..."):
            for video in videos:
                comment_response = youtube.commentThreads().list(
                    part='snippet',
                    videoId=video['videoId'],
                    maxResults=10,
                    order='relevance'
                ).execute()

                comments = [
                    {
                        'text': comment['snippet']['topLevelComment']['snippet']['textOriginal'],
                        'likes': comment['snippet']['topLevelComment']['snippet']['likeCount'],
                        'sentiment': None
                    }
                    for comment in comment_response['items']
                ]

                # Analyze sentiment
                for comment in comments:
                    cleaned_text = clean_text(comment['text'])
                    scores = analyzer.polarity_scores(cleaned_text)
                    comment['sentiment'] = 'POSITIVE' if scores['compound'] > 0.05 else 'NEGATIVE' if scores['compound'] < -0.05 else 'NEUTRAL'

                # Update MongoDB
                videos_collection.update_one(
                    {'videoId': video['videoId']},
                    {'$set': {'comments': comments}}
                )

        with st.spinner("Generating PDF report..."):
            # Generate PDF
            output_file = f'reports/{product_name}_report.pdf'
            os.makedirs('reports', exist_ok=True)
            html_content = f"<h1>YouReview Report: {product_name}</h1>"
            for video in videos_collection.find({'productName': product_name}):
                html_content += f"<h2>{video['title']} (by {video['creator']})</h2>"
                for comment in video['comments']:
                    html_content += f"<p>{comment['text']} ({comment['sentiment']})</p>"
            pdfkit.from_string(html_content, output_file)

        st.success("Report generated!")
        with open(output_file, "rb") as file:
            st.download_button(
                label="Download PDF Report",
                data=file,
                file_name=f"{product_name}_report.pdf",
                mime="application/pdf"
            )