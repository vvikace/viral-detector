import os
from supabase import create_client
from api_scraper import get_tiktok_posts
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
        platforma = p['platforma']
        
        # 3. Pobierz dane
        if platforma.lower() == "tiktok":
            print(f"Bot: Pobieram posty z API dla profilu @{nazwa}...")
            data, error_msg = get_tiktok_posts(nazwa)
            
            if data:
                # 4. Oblicz średnią i zapisz do tabeli historii
                df = pd.DataFrame(data)
                avg_eng = df["engagement"].mean()
                ostatni_post = df.iloc[0]["engagement"]
                url_posta = df.iloc[0]["url"]
                v_score = ostatni_post / avg_eng if avg_eng > 0 else 0
                
                entry = {
                    "profil": nazwa,
                    "platforma": platforma,
                    "srednia": int(avg_eng),
                    "ostatni_post": int(ostatni_post),
                    "v_score": float(v_score),
                    "data": datetime.now().isoformat(),
                    "url_posta": url_posta
                }
                
                supabase.table("historia_analiz").insert(entry).execute()
                print(f"Bot: SUKCES - Zaktualizowano dane dla @{nazwa} w bazie!")
            else:
                print(f"Bot: BŁĄD POBIERANIA - Nie mam danych dla @{nazwa}. Powód: {error_msg}")
        else:
            print(f"Bot: Pomijam platformę {platforma} dla profilu {nazwa}")

if __name__ == "__main__":
    run_update()
