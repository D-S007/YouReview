# src/processor.py
from langdetect import detect
from googletrans import Translator

def process_comments(comments):
    translator = Translator()
    processed_comments = []
    
    for comment_data in comments:
        text = comment_data["comment"]
        try:
            # Detect language
            lang = detect(text)
            # Translate non-English comments to English
            if lang != "en":
                translated = translator.translate(text, dest="en").text
                comment_data["original_comment"] = text
                comment_data["translated_comment"] = translated
                comment_data["language"] = lang
            else:
                comment_data["translated_comment"] = text
                comment_data["language"] = "en"
            processed_comments.append(comment_data)
        except Exception as e:
            print(f"Error processing comment: {e}")
            continue
    
    return processed_comments