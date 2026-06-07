import yt_dlp
from datetime import datetime
import requests
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
                
                video_id = entry.get('id', '')
                url = f"https://www.tiktok.com/@{target_profile}/video/{video_id}" if video_id else "Brak linku"
                title = entry.get('title', 'Brak opisu')
                thumbnail = entry.get('thumbnail', '')
                
                posts_data.append({"date": dt, "engagement": likes + comments, "url": url, "title": title, "thumbnail": thumbnail})
        return posts_data, ""
    except Exception as e:
        return [], f"Błąd pobierania z TikToka: {str(e)}"

def get_youtube_posts(target_profile):
    posts_data = []
    ydl_opts = {'skip_download': True, 'playlist_items': '1-10', 'quiet': True, 'extract_flat': 'in_playlist'}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/@{target_profile}/shorts", download=False)
            for entry in info.get('entries', []):
                if not entry: continue
                views = entry.get('view_count') or 0
                date_str = entry.get('upload_date')
                dt = datetime.strptime(date_str, '%Y%m%d') if date_str else datetime.now()
                
                video_id = entry.get('id', '')
                url = f"https://www.youtube.com/shorts/{video_id}" if video_id else "Brak linku"
                title = entry.get('title', 'Brak tytułu')
                
                thumbnails = entry.get('thumbnails', [])
                thumbnail = thumbnails[-1].get('url', '') if thumbnails else ''
                
                posts_data.append({"date": dt, "engagement": views, "url": url, "title": title, "thumbnail": thumbnail})
        return posts_data, ""
    except Exception as e:
        return [], f"Błąd pobierania z YouTube: {str(e)}"
