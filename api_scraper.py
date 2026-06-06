import yt_dlp
import requests
from datetime import datetime
import os

def get_instagram_posts(target_profile):
    rapidapi_key = os.environ.get("RAPIDAPI_KEY")
    rapidapi_host = os.environ.get("RAPIDAPI_HOST")
    
    if not rapidapi_key or not rapidapi_host:
        return [], "Brak kluczy API dla Instagrama na serwerze."

    url = f"https://{rapidapi_host}/get_ig_user_posts.php"
    payload = {"username_or_url": target_profile, "amount": 10}
    headers = {
        "X-RapidAPI-Key": rapidapi_key,
        "X-RapidAPI-Host": rapidapi_host,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        response = requests.post(url, data=payload, headers=headers)
        data = response.json()

        if "message" in data and "exceeded" in data.get("message", "").lower():
            return [], "Wykorzystano darmowy limit zapytań API. Spróbuj TikToka."
        
        items = data.get("posts", [])
        if not items:
            items = data.get("data", {}).get("items", [])
        if not items:
            items = data.get("items", data.get("data", []))

        posts_data = []
        for item in items[:10]:
            node = item.get("node", item) 
            likes = node.get("like_count", 0)
            comments = node.get("comment_count", 0)
            timestamp = node.get("taken_at", node.get("timestamp", datetime.now().timestamp()))
            
            try:
                post_date = datetime.fromtimestamp(timestamp)
            except:
                post_date = datetime.now()
                
            posts_data.append({
                "date": post_date, 
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
