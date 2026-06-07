import os
from supabase import create_client
from api_scraper import get_tiktok_posts, get_youtube_posts
import pandas as pd
from datetime import datetime

def run_update():
    # 1. Połączenie
    supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
    
    # 2. Pobierz listę profili do śledzenia
    profiles = supabase.table("obserwowane_profile").select("*").execute().data
    
    print(f"Bot: Znalazłem {len(profiles)} profili w bazie obserwowanych.")
    
    for p in profiles:
        nazwa = p['nazwa']
        platforma = p['platforma'].lower() # Wymuszamy małe litery
        
        data = []
        error_msg = ""
        
        # 3. Przekierowanie ruchu w zależności od platformy
        if platforma == "tiktok":
            print(f"Bot: Pobieram TikToki dla @{nazwa}...")
            data, error_msg = get_tiktok_posts(nazwa)
        elif platforma == "youtube":
            print(f"Bot: Pobieram YouTube Shorts dla @{nazwa}...")
            data, error_msg = get_youtube_posts(nazwa)
        else:
            print(f"Bot: Pomijam nieznaną platformę '{platforma}' dla @{nazwa}")
            continue
            
        if data:
            # 4. Oblicz średnią i zapisz do tabeli historii
            df = pd.DataFrame(data)
            avg_eng = df["engagement"].mean()
            ostatni_post = df.iloc[0]
            v_score = ostatni_post["engagement"] / avg_eng if avg_eng > 0 else 0
            
            entry = {
                "profil": nazwa,
                "platforma": platforma.capitalize(), # Zapisujemy ładnie: Tiktok / Youtube
                "srednia": int(avg_eng),
                "ostatni_post": int(ostatni_post["engagement"]),
                "v_score": float(v_score),
                "data": datetime.now().isoformat(),
                "url_posta": ostatni_post["url"],
                "tytul": ostatni_post["title"],
                "miniaturka": ostatni_post["thumbnail"]
            }
            
            supabase.table("historia_analiz").insert(entry).execute()
            print(f"Bot: SUKCES - Zaktualizowano dane dla @{nazwa} ({platforma})!")
        else:
            print(f"Bot: BŁĄD POBIERANIA - Nie mam danych dla @{nazwa}. Powód: {error_msg}")

if __name__ == "__main__":
    run_update()
