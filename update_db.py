import os
from supabase import create_client
from api_scraper import get_tiktok_posts
import pandas as pd

def run_update():
    # 1. Połączenie
    supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
    
    # 2. Pobierz listę profili do śledzenia
    profiles = supabase.table("obserwowane_profile").select("*").execute().data
    
    for p in profiles:
        nazwa = p['nazwa']
        platforma = p['platforma']
        
        # 3. Pobierz dane
        if platforma == "Tiktok":
            data, _ = get_tiktok_posts(nazwa)

            if data:
                # 4. Oblicz średnią i zapisz do tabeli historii
                avg_eng = pd.DataFrame(data)["engagement"].mean()
                entry = {
                    "profil": nazwa,
                    "platforma": platforma,
                    "srednia": int(avg_eng),
                    "data": datetime.now().isoformat()
                }
                supabase.table("historia_analiz").insert(entry).execute()
                print(f"Zaktualizowano: {nazwa}")
        else:
            print(f"Pomijam {platforma} dla profilu {nazwa}")

if __name__ == "__main__":
    run_update()
