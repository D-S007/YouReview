# src/scraper.py
from googleapiclient.discovery import build
import yaml
from datetime import datetime, timedelta

def load_config(config_path="config/app_config.yaml"):
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

def load_api_config(config_path="config/api_config.yaml"):
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

def scrape_youtube_comments(query):
    config = load_config()
    api_config = load_api_config()
    youtube = build("youtube", "v3", developerKey=api_config["youtube"]["api_key"])
    
    # Calculate date threshold
    threshold_date = (datetime.now() - timedelta(days=config["scraper"]["min_days_old"])).isoformat() + "Z"
    
    # Search videos
    search_response = youtube.search().list(
        q=query + " review",  # Add "review" to prioritize relevant videos
        part="id,snippet",
        maxResults=config["scraper"]["max_videos"],
        type="video",
        publishedAfter=threshold_date
    ).execute()
    
    comments = []
    for item in search_response["items"]:
        title = item["snippet"]["title"].lower()
        description = item["snippet"]["description"].lower()
        
        # Filter videos by keywords
        if any(keyword in title or keyword in description for keyword in config["scraper"]["include_keywords"]) and \
           not any(keyword in title or keyword in description for keyword in config["scraper"]["exclude_keywords"]):
            video_id = item["id"]["videoId"]
            try:
                comment_response = youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    maxResults=config["scraper"]["max_comments_per_video"]
                ).execute()
                for comment_item in comment_response["items"]:
                    comment = comment_item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                    comments.append({
                        "video_id": video_id,
                        "comment": comment,
                        "video_title": item["snippet"]["title"],
                        "published_at": item["snippet"]["publishedAt"]
                    })
            except Exception as e:
                print(f"Error fetching comments for video {video_id}: {e}")
    
    return comments