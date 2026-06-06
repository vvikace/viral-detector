import yt_dlp
import requests
from datetime import datetime
import os

def get_instagram_posts(target_profile):
    rapidapi_key = os.environ.get("RAPIDAPI_KEY")
    rapidapi_host = "instagram191.p.rapidapi.com/v2/user/posts/" 
    
    if not rapidapi_key:
        return [], "Brak klucza API dla Instagrama."

    url = "https://instagram191.p.rapidapi.com/v2/user/posts/"
    
    querystring = {"user_id":"25025320","count":"12"}
    
    headers = {
	"x-rapidapi-key": "f0095ca367msh620a2faa5e84fe1p1ecb81jsn53fa436172f1",
	"x-rapidapi-host": "instagram191.p.rapidapi.com",
	"Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        data = response.json()
        print(response.json())
        return data, ""
    except Exception as e: 
        return [], f"Błąd pobierania: {str(e)}"

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
