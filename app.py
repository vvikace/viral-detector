import requests
import streamlit as st
import pandas as pd
import plotly.express as px
import yt_dlp
from datetime import datetime
from fpdf import FPDF
import io
from supabase import create_client, Client

# 1. Konfiguracja strony
st.set_page_config(page_title="Viral detector", layout="wide")
st.title("🕵️‍♂️ Viral Detector")

# 2. Sidebar
platform = st.sidebar.selectbox("Wybierz platformę:", ["Instagram", "Tiktok"])
target_profile = st.sidebar.text_input("Wpisz nazwę profilu (np. wersow):", "")
analyze_button = st.sidebar.button("Analizuj profil")

if analyze_button and target_profile:
    with st.spinner(f'Pobieranie danych z platformy {platform}...'):
        try:
            posts_data = []
            
            if platform == "Instagram":
                url = f"https://{st.secrets['RAPIDAPI_HOST']}/get_ig_user_posts.php"
                
                payload = {
                    "username_or_url": target_profile,
                    "amount": 10
                }
                
                headers = {
                    "X-RapidAPI-Key": st.secrets["RAPIDAPI_KEY"],
                    "X-RapidAPI-Host": st.secrets["RAPIDAPI_HOST"],
                    "Content-Type": "application/x-www-form-urlencoded"
                }
                
                response = requests.post(url, data=payload, headers=headers)
                data = response.json()
                
                # Pobieramy posty z klucza "posts", tak jak na Twoim screenie
                items = data.get("posts", [])
                
                for item in items[:10]:
                    # Skrypt wchodzi do pod-szufladki "node"
                    node = item.get("node", item) 
                    
                    likes = node.get("like_count", 0)
                    comments = node.get("comment_count", 0)
                    
                    timestamp = node.get("taken_at", node.get("timestamp", datetime.now().timestamp()))
                    shortcode = node.get("code", node.get("shortcode", "brak"))
                    
                    try:
                        post_date = datetime.fromtimestamp(timestamp)
                    except:
                        post_date = datetime.now()
                        
                    posts_data.append({
                        "date": post_date,
                        "likes": likes,
                        "comments": comments,
                        "engagement": likes + comments,
                        "url": f"https://www.instagram.com/p/{shortcode}/"
                    })
                # Bezpieczne wyciąganie listy postów ze struktury API
                items = data.get("data", {}).get("items", [])
                if not items:
                    items = data.get("items", data.get("data", []))
                
                for post in items[:10]:
                    # Wyciąganie wartości, które znalazłaś
                    likes = post.get("like_count", 0)
                    comments = post.get("comment_count", 0)
                    
                    # Zabezpieczenie formatu czasu i linku
                    timestamp = post.get("taken_at", post.get("timestamp", datetime.now().timestamp()))
                    shortcode = post.get("code", post.get("shortcode", "brak"))
                    
                    try:
                        post_date = datetime.fromtimestamp(timestamp)
                    except:
                        post_date = datetime.now()
                        
                    posts_data.append({
                        "date": post_date,
                        "likes": likes,
                        "comments": comments,
                        "engagement": likes + comments,
                        "url": f"https://www.instagram.com/p/{shortcode}/"
                    })
                
                for post in items:
                    likes = post.get("like_count", 0)
                    comments = post.get("comment_count", 0)
                    timestamp = post.get("taken_at", 0)
                    shortcode = post.get("code", "")
                    
                    posts_data.append({
                        "date": datetime.fromtimestamp(timestamp),
                        "likes": likes,
                        "comments": comments,
                        "engagement": likes + comments,
                        "url": f"https://www.instagram.com/p/{shortcode}/"
                    })
                    count += 1
                    
            elif platform == "Tiktok":
                ydl_opts = {
                    'skip_download': True,
                    'playlist_items': '1-10',
                    'quiet': True,
                    'extract_flat': False
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(f"https://www.tiktok.com/@{target_profile}", download=False)
                    for entry in info.get('entries', []):
                        if not entry: continue
                        likes = entry.get('like_count') or 0
                        comments = entry.get('comment_count') or 0
                        date_str = entry.get('upload_date')
                        dt = datetime.strptime(date_str, '%Y%m%d') if date_str else datetime.now()
                        
                        posts_data.append({
                            "date": dt,
                            "likes": likes,
                            "comments": comments,
                            "engagement": likes + comments,
                            "url": entry.get('webpage_url', '')
                        })
            
            if not posts_data: 
                st.error("Nie udało się pobrać danych lub profil jest pusty.")
            else:
                df = pd.DataFrame(posts_data)

                # Średnia z postów 1-10
                avg_engagement = df["engagement"].mean()
                
                # Najnowszy post (indeks 0)
                latest_post = df.iloc[0]
                v_score = latest_post["engagement"] / avg_engagement if avg_engagement > 0 else 0

                # --- ZAPIS DO BAZY SUPABASE ---
                try:
                    url = st.secrets["SUPABASE_URL"]
                    key = st.secrets["SUPABASE_KEY"]
                    supabase: Client = create_client(url, key)
                    
                    data_to_save = {
                    "profil": target_profile,
                    "platforma": platform,
                    "srednia": int(avg_engagement),
                    "ostatni_post": int(latest_post["engagement"]),
                    "v_score": float(v_score)
                }
                
                try:
                    supabase.table("historia_analiz").upsert(data_to_save).execute()
                    st.success("Dane zapisane w bazie!")
                except Exception as e:
                    st.error(f"Błąd zapisu: {e}")
    
                except Exception as db_e:
                    st.warning(f"Nie udało się zapisać do bazy (sprawdź klucze API): {db_e}")
                # ------------------------------

                # 4. Wyświetlanie wyników
                col1, col2, col3 = st.columns(3)
                col1.metric("Średnie zaangażowanie", int(avg_engagement))
                col2.metric("Ostatni post", int(latest_post["engagement"]))
                
                # Wskaźnik viralu
                delta_color = "normal" if v_score < 1.2 else "inverse"
                col3.metric("V-Score (Wiralność)", f"{v_score:.2f}x", delta=f"{int((v_score-1)*100)}%", delta_color=delta_color)

                # 5. Alerty
                if v_score > 1.5:
                    st.error(f"🚨 ALERT: Wykryto Viral! Wynik jest o {int((v_score-1)*100)}% lepszy niż średnia.")
                    st.write(f"Link do posta: {latest_post['url']}")
                else:
                    st.success("Posty są w normie. Brak anomalii viralowych.")

                # Wykres
                st.subheader("Porównanie ostatnich postów")
                fig = px.bar(df, x="date", y="engagement", title="Zaangażowanie pod ostatnimi 10 postami")
                fig.add_hline(y=avg_engagement, line_dash="dash", line_color="red", annotation_text="Średnia")
                st.plotly_chart(fig, use_container_width=True)

                # 7. Raport
                st.subheader("Opcje raportowania")
                
                report_text = f"""RAPORT ANALIZY KONKURENCJI
Data wygenerowania: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Profil śledzony: @{target_profile}
--------------------------------------------------
STATYSTYKI OGÓLNE:
Średnie zaangażowanie (10 postów): {int(avg_engagement)}
Ostatnie zaangażowanie: {int(latest_post['engagement'])}
Wskaźnik V-Score: {v_score:.2f}x

WNIOSEK:
{"WYKRYTO VIRAL! Post rośnie znacznie szybciej niż zwykle." if v_score > 1.5 else "Brak anomalii. Wzrost stabilny."}

LINK DO OSTATNIEGO POSTA:
{latest_post['url']}
--------------------------------------------------
Wygenerowano automatycznie przez Viral Detector by Wiktoria Cedro
"""

                st.download_button(
                    label="Pobierz raport tekstowy (.txt)",
                    data=report_text,
                    file_name=f"raport_{target_profile}_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain"
                )

                # Eksport danych do CSV
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Pobierz surowe dane (.csv)",
                    data=csv,
                    file_name=f"dane_{target_profile}.csv",
                    mime="text/csv"
                )

                # --- Funkcja do PDF ---
                def generate_pdf():
                    def clean(text):
                        text = str(text)
                        replacements = {
                            'ą':'a', 'ć':'c', 'ę':'e', 'ł':'l', 'ń':'n', 'ó':'o', 'ś':'s', 'ź':'z', 'ż':'z',
                            'Ą':'A', 'Ć':'C', 'Ę':'E', 'Ł':'L', 'Ń':'N', 'Ó':'O', 'Ś':'S', 'Ź':'Z', 'Ż':'Z'
                        }
                        for pl, asc in replacements.items():
                            text = text.replace(pl, asc)
                        return text

                    pdf = FPDF()
                    pdf.add_page()
                    
                    # Tytuł
                    pdf.set_font("Arial", 'B', 16)
                    pdf.cell(200, 10, txt=clean("RAPORT ANALIZY KONKURENCJI"), ln=True, align='C')
                    
                    # Dane podstawowe
                    pdf.set_font("Arial", size=12)
                    pdf.ln(10)
                    pdf.cell(200, 10, txt=clean(f"Data wygenerowania: {datetime.now().strftime('%Y-%m-%d %H:%M')}"), ln=True)
                    pdf.cell(200, 10, txt=clean(f"Platforma: {platform}"), ln=True)
                    pdf.cell(200, 10, txt=clean(f"Profil sledzony: @{target_profile}"), ln=True)
                    pdf.line(10, 50, 200, 50) 
                    pdf.ln(5)
                    
                    # Wyniki
                    pdf.cell(200, 10, txt=clean(f"Srednie zaangazowanie (10 postow): {int(avg_engagement)}"), ln=True)
                    pdf.cell(200, 10, txt=clean(f"Ostatnie zaangazowanie: {int(latest_post['engagement'])}"), ln=True)
                    pdf.cell(200, 10, txt=clean(f"Wskaznik V-Score: {v_score:.2f}x"), ln=True)
                    
                    # Wniosek i alerty
                    pdf.ln(5)
                    pdf.set_font("Arial", 'B', 12)
                    if v_score > 1.5:
                        pdf.set_text_color(220, 53, 69) 
                        pdf.cell(200, 10, txt=clean("WYKRYTO VIRAL! Post rosnie znacznie szybciej niz zwykle."), ln=True)
                    else:
                        pdf.set_text_color(40, 167, 69) 
                        pdf.cell(200, 10, txt=clean("Brak anomalii. Wzrost stabilny."), ln=True)
                    
                    pdf.set_text_color(0, 0, 0)
                    pdf.set_font("Arial", size=10)
                    pdf.cell(200, 10, txt=clean(f"Link do posta: {latest_post['url']}"), ln=True)

                    # Stopka
                    pdf.ln(10)
                    pdf.set_font("Arial", 'I', size=8)
                    pdf.cell(200, 10, txt=clean("Wygenerowano automatycznie przez Viral Detector by Wiktoria Cedro"), ln=True)
                    
                    return pdf.output(dest='S').encode('latin-1', 'replace')

                # Eksport do pdf
                pdf_data = generate_pdf()
                st.download_button(
                    label="📄 Pobierz raport w PDF",
                    data=pdf_data,
                    file_name=f"raport_{target_profile}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )

        except Exception as e:
            st.error(f"Błąd: {e}. Upewnij się, że profil jest publiczny i wpisano poprawną nazwę.")

else: 
    st.info("Wpisz nazwę publicznego profilu w panelu bocznym i kliknij przycisk, aby rozpocząć automatyczną analizę.")
