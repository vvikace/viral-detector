import dash
from dash import Input, Output, State, html, dcc, ctx
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import os
from dotenv import load_dotenv
from supabase import create_client
from fpdf import FPDF
import threading
import time
from update_db import run_update 
from datetime import datetime

def bot_loop():
    while True:
        try:
            print("Bot: Rozpoczynam aktualizację...")
            run_update()
            print("Bot: Aktualizacja zakończona. Śpię godzinę.")
        except Exception as e:
            print(f"Bot: Błąd w trakcie aktualizacji: {e}")
        time.sleep(3600) 

# Bota w tle przy starcie aplikacji
thread = threading.Thread(target=bot_loop, daemon=True)
thread.start()
# ----------------------------

# Import komponentów z własnych plików
from layout import get_app_layout
from api_scraper import get_tiktok_posts

load_dotenv()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
server = app.server
app.title = "Viral Detector"

# 1. Interfejs z pliku layout.py
app.layout = get_app_layout()

# 2. Logika
@app.callback(
    [Output('metrics-output', 'children'),
     Output('engagement-graph', 'figure'),
     Output('engagement-graph', 'style'),
     Output('error-message', 'children'),
     Output('success-message', 'children'),
     Output('store-data', 'data'),
     Output('btn-download-pdf', 'style')],
    [Input('analyze-button', 'n_clicks'),
     Input('btn-force-refresh', 'n_clicks')], # DODAJEMY DRUGI INPUT
    [State('profile-input', 'value'),
     State('platform-select', 'value')]
)
def update_dashboard(n1, n2, target_profile, platform):
    if not target_profile or (n1 == 0 and n2 == 0):
        return "", {}, {'display': 'none'}, "", "", None, {'display': 'none'}
    
    # SPRAWDZAMY KTÓRY PRZYCISK KLIKNIĘTO
    trigger_id = ctx.triggered_id
    
    posts_data = []
    error_msg = ""
    
    if trigger_id == 'btn-force-refresh':
        # ŚWIEŻE DANE Z SIECI - zawsze TikTok
        posts_data, error_msg = get_tiktok_posts(target_profile)
    else:
        # DANE Z BAZY (Szybkie)
        supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
        response = supabase.table("historia_analiz").select("*").eq("profil", target_profile).order("data", desc=True).limit(10).execute()
        
        # TU JEST KLUCZ: Uzupełniamy listę danymi z response.data
        posts_data = []
        for item in response.data:
            posts_data.append({
                "date": item.get('timestamp'), 
                "engagement": item.get('ostatni_post', 0) 
            })
            
        if not posts_data:
            error_msg = "Brak danych w bazie. Kliknij Odśwież."
    
    if error_msg:
            return "", {}, {'display': 'none'}, error_msg, "", None, {'display': 'none'}
        
    if not posts_data:
        return "", {}, {'display': 'none'}, f"Nie udało się pobrać danych.", "", None, {'display': 'none'}
        
    # Obliczenia analityczne vscore
    df = pd.DataFrame(posts_data)
    if len(df) >= 2:
        pierwszy = df.iloc[-1]["engagement"]  # Najstarszy w bazie (z listy 10)
        ostatni = df.iloc[0]["engagement"]    # Najnowszy
        
        procentowa_zmiana = ((ostatni - pierwszy) / pierwszy) * 100
        trend_text = f"{procentowa_zmiana:+.1f}%"
        trend_color = "#00f2fe" if procentowa_zmiana >= 0 else "#fe0979"
    else:
        trend_text = "Brak danych do trendu"
        trend_color = "white"
    avg_engagement = df["engagement"].mean()
    latest_post = df.iloc[0]
    v_score = latest_post["engagement"] / avg_engagement if avg_engagement > 0 else 0
    
    # Supabase
    db_message = ""
    try:
        db_url = os.environ.get("SUPABASE_URL")
        db_key = os.environ.get("SUPABASE_KEY")
        if db_url and db_key:
            supabase = create_client(db_url, db_key)
            data_to_save = {
                "profil": target_profile, 
                "platforma": platform, 
                "srednia": int(avg_engagement), 
                "ostatni_post": int(latest_post["engagement"]), 
                "v_score": float(v_score)
            }
            supabase.table("historia_analiz").insert(data_to_save).execute()
            db_message = "Zapisano w bazie!"
    except Exception as e:
        db_message = f"(Błąd zapisu DB: {e})"
        
    # Metryki i wykresy
    metrics_html = [
        html.Div(className='text-center', children=[
            html.H4(["Średnie zaangażowanie ", html.Span("ℹ️", id="tooltip-avg", style={'cursor': 'help', 'fontSize': '0.8em'})]),
            dbc.Tooltip("Średnia suma lajków i komentarzy z ostatnich 10 postów.", target="tooltip-avg", placement="top"),
            html.H2(f"{int(avg_engagement):,}")
        ]),
        html.Div(className='text-center', children=[
            html.H4(["Ostatni post ", html.Span("ℹ️", id="tooltip-latest", style={'cursor': 'help', 'fontSize': '0.8em'})]),
            dbc.Tooltip("Liczba interakcji pod najnowszym opublikowanym materiałem.", target="tooltip-latest", placement="top"),
            html.H2(f"{int(latest_post['engagement']):,}")
        ]),
        html.Div(className='text-center', children=[
            html.H4(["V-Score ", html.Span("ℹ️", id="tooltip-vscore", style={'cursor': 'help', 'fontSize': '0.8em'})]),
            dbc.Tooltip("Wskaźnik wiralności. Wynik powyżej 1.5x oznacza wykrycie viralu!", target="tooltip-vscore", placement="top"),
            html.H2(f"{v_score:.2f}x", style={'color': '#fe0979' if v_score > 1.5 else '#00f2fe'})
        ])
    ]
    
    fig = px.bar(df, x="date", y="engagement", title=f"Zaangażowanie: @{target_profile} ({platform})", template="plotly_dark", color_discrete_sequence=["#00f2fe"])
    fig.add_hline(y=avg_engagement, line_dash="dash", line_color="#fe0979", annotation_text="Średnia")
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    
    # Czyste dane do pamięci przeglądarki na potrzeby PDF
    stored_data = {
        "profile": target_profile,
        "platform": platform,
        "avg": int(avg_engagement),
        "latest": int(latest_post["engagement"]),
        "vscore": v_score
    }
    
    return metrics_html, fig, {'display': 'block'}, "", db_message, stored_data, {'display': 'inline-block'}

# CALLBACK 2: Generowanie raportu PDF (po kliknięciu POBIERZ)
@app.callback(
    Output("download-dataframe-pdf", "data"),
    Input("btn-download-pdf", "n_clicks"),
    State("store-data", "data"),
    prevent_initial_call=True
)
def generate_pdf(n_clicks, stored_data):
    print(f"DEBUG: Stored data to PDF: {stored_data}") 
    if not stored_data:
        print("DEBUG: Brak danych w store!")
        return dash.no_update

    def clean(text):
        text = str(text)
        replacements = {'ą':'a', 'ć':'c', 'ę':'e', 'ł':'l', 'ń':'n', 'ó':'o', 'ś':'s', 'ź':'z', 'ż':'z', 'Ą':'A', 'Ć':'C', 'Ę':'E', 'Ł':'L', 'Ń':'N', 'Ó':'O', 'Ś':'S', 'Ź':'Z', 'Ż':'Z'}
        for pl, asc in replacements.items(): text = text.replace(pl, asc)
        return text

    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=clean("RAPORT ANALIZY KONKURENCJI"), ln=True, align='C')
    
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=clean(f"Data wygenerowania: {datetime.now().strftime('%Y-%m-%d %H:%M')}"), ln=True)
    pdf.cell(200, 10, txt=clean(f"Platforma: {stored_data['platform']}"), ln=True)
    pdf.cell(200, 10, txt=clean(f"Profil sledzony: @{stored_data['profile']}"), ln=True)
    pdf.line(10, 45, 200, 45) 
    pdf.ln(5)
    
    pdf.cell(200, 10, txt=clean(f"Srednie zaangazowanie (10 postow): {stored_data['avg']}"), ln=True)
    pdf.cell(200, 10, txt=clean(f"Ostatnie zaangazowanie: {stored_data['latest']}"), ln=True)
    pdf.cell(200, 10, txt=clean(f"Wskaznik V-Score: {stored_data['vscore']:.2f}x"), ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    if stored_data['vscore'] > 1.5:
        pdf.set_text_color(220, 53, 69) 
        pdf.cell(200, 10, txt=clean("WYKRYTO VIRAL! Post rosnie znacznie szybciej niz zwykle."), ln=True)
    else:
        pdf.set_text_color(40, 167, 69) 
        pdf.cell(200, 10, txt=clean("Brak anomalii. Wzrost stabilny."), ln=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    pdf.set_font("Arial", 'I', size=8)
    pdf.cell(200, 10, txt=clean("Wygenerowano automatycznie przez Viral Detector by Wiktoria Cedro"), ln=True)
    
    # Kodowanie pliku do pobrania bezpośrednio przez przeglądarkę
    return dcc.send_bytes(pdf.output(dest='S').encode('latin-1', 'replace'), f"raport_{stored_data['profile']}.pdf")

if __name__ == '__main__':
    app.run_server(debug=True)
    
