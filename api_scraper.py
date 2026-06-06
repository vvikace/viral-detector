import yt_dlp
import requests
from datetime import datetime
import os


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
