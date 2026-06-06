import dash
from dash import Input, Output, State, html
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import os
from dotenv import load_dotenv
from supabase import create_client
from fpdf import FPDF

# Importujemy komponenty z naszych własnych plików
from layout import get_app_layout
from api_scraper import get_instagram_posts, get_tiktok_posts

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
    [Input('analyze-button', 'n_clicks')],
    [State('profile-input', 'value'),
     State('platform-select', 'value')]
)
def update_dashboard(n_clicks, target_profile, platform):
    if n_clicks == 0 or not target_profile:
        return "", {}, {'display': 'none'}, "", ""
    
    posts_data = []
    error_msg = ""
    
    # Skryptów pobierania z pliku api_scraper.py
    if platform == "Instagram":
        posts_data, error_msg = get_instagram_posts(target_profile)
    elif platform == "Tiktok":
        posts_data, error_msg = get_tiktok_posts(target_profile)
        
    if error_msg:
        return "", {}, {'display': 'none'}, error_msg, ""
        
    if not posts_data:
        return "", {}, {'display': 'none'}, f"Nie udało się pobrać danych dla @{target_profile} ({platform}).", ""
        
    # Obliczenia analityczne vscore
    df = pd.DataFrame(posts_data)
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
    if not stored_data:
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
    
