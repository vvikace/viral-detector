import yt_dlp
import requests
from datetime import datetime
import os

def get_instagram_posts(target_profile):
    rapidapi_key = os.environ.get("RAPIDAPI_KEY")
    rapidapi_host = "instagram-scraper21.p.rapidapi.com/api/v1/post-info" 
    
    if not rapidapi_key:
        return [], "Brak klucza API dla Instagrama."

    url = f"https://{rapidapi_host}/api/v1/user/posts"
    
    querystring = {"username": target_profile, "count": "10"}
    
    headers = {
        "x-rapidapi-key": rapidapi_key,
        "x-rapidapi-host": rapidapi_host
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        data = response.json()

        print(f"DEBUG API RESPONSE: {data}")

        items = data.get("data", {}).get("items", [])
        
        if not items:
            return [], "Brak postów dla tego profilu."

        posts_data = []
        for item in items[:10]:
           
            likes = item.get("like_count", 0)
            comments = item.get("comment_count", 0)
            
            timestamp = item.get("taken_at_timestamp", datetime.now().timestamp())
            
            posts_data.append({
                "date": datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d'), 
                "engagement": likes + comments
            })
            
        return posts_data, ""
        
    except Exception as e:
        return [], f"Błąd pobierania z Instagrama: {str(e)}"

def get_tiktok_posts(target_profile):
    posts_data = []
    ydl_opts = {'skip_download': True, 'playlist_items': '1-10', 'quiet': True, 'extract_flat': False}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.tiktok.com/@{target_profile}", download=False)
            for entry in info.get('entries', []):
                if not entry: continue
                likes = entry.get('like_count') or 0
                comments = entry.get('comment_count') or 0
                date_str = entry.get('upload_date')
                dt = datetime.strptime(date_str, '%Y%m%d') if date_str else datetime.now()
                posts_data.append({"date": dt, "engagement": likes + comments})
        return posts_data, ""
    except Exception as e:
        return [], f"Błąd pobierania z TikToka: {str(e)}"
