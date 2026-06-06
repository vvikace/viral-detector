import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import pandas as pd
import yt_dlp
from datetime import datetime
import os
from dotenv import load_dotenv
from supabase import create_client

# Wczytanie haseł z pliku .env
load_dotenv()

# 1. Inicjalizacja aplikacji
app = dash.Dash(__name__)
server = app.server 
app.title = "Viral Detector"

# 2. LAYOUT (Wygląd strony)
app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'padding': '30px', 'maxWidth': '1000px', 'margin': '0 auto'}, children=[
    
    html.H1("🕵️‍♂️ Viral Detector", style={'textAlign': 'center', 'color': '#333'}),
    html.P("Analiza wiralności profili na platformie TikTok.", style={'textAlign': 'center', 'color': '#666'}),
    
    # Panel wyszukiwania
    html.Div(style={'backgroundColor': '#f8f9fa', 'padding': '20px', 'borderRadius': '10px', 'textAlign': 'center', 'marginBottom': '30px'}, children=[
        html.Label("Nazwa profilu: ", style={'fontWeight': 'bold', 'marginRight': '10px'}),
        dcc.Input(id='profile-input', type='text', placeholder='np. wersow', style={'padding': '8px', 'width': '200px', 'borderRadius': '5px', 'border': '1px solid #ccc'}),
        html.Button('Analizuj', id='analyze-button', n_clicks=0, style={'padding': '8px 20px', 'marginLeft': '10px', 'backgroundColor': '#000000', 'color': 'white', 'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer'})
    ]),
    
    html.Div(id='error-message', style={'color': 'red', 'fontWeight': 'bold', 'textAlign': 'center'}),
    html.Div(id='success-message', style={'color': 'green', 'fontWeight': 'bold', 'textAlign': 'center'}),
    
    # Animacja ładowania i wyniki
    dcc.Loading(
        id="loading",
        type="circle",
        color="#000000",
        children=[
            # Metryki
            html.Div(id='metrics-output', style={'display': 'flex', 'justifyContent': 'space-around', 'marginTop': '30px'}),
            # Wykres
            dcc.Graph(id='engagement-graph', style={'display': 'none', 'marginTop': '30px'})
        ]
    )
])

# 3. CALLBACKS (Logika aplikacji)
@app.callback(
    [Output('metrics-output', 'children'),
     Output('engagement-graph', 'figure'),
     Output('engagement-graph', 'style'),
     Output('error-message', 'children'),
     Output('success-message', 'children')],
    [Input('analyze-button', 'n_clicks')],
    [State('profile-input', 'value')]
)
def update_dashboard(n_clicks, target_profile):
    if n_clicks == 0 or not target_profile:
        return "", {}, {'display': 'none'}, "", ""
    
    posts_data = []
    
    try:
        # Pobieranie danych (TikTok)
        ydl_opts = {'skip_download': True, 'playlist_items': '1-10', 'quiet': True, 'extract_flat': False}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.tiktok.com/@{target_profile}", download=False)
            for entry in info.get('entries', []):
                if not entry: continue
                likes = entry.get('like_count') or 0
                comments = entry.get('comment_count') or 0
                date_str = entry.get('upload_date')
                dt = datetime.strptime(date_str, '%Y%m%d') if date_str else datetime.now()
                posts_data.append({"date": dt, "engagement": likes + comments})
                
        if not posts_data:
            return "", {}, {'display': 'none'}, f"Nie udało się pobrać danych dla @{target_profile}.", ""
            
        # Obliczenia
        df = pd.DataFrame(posts_data)
        avg_engagement = df["engagement"].mean()
        latest_post = df.iloc[0]
        v_score = latest_post["engagement"] / avg_engagement if avg_engagement > 0 else 0
        
        # Zapis do Supabase
        db_message = ""
        try:
            url = os.environ.get("SUPABASE_URL")
            key = os.environ.get("SUPABASE_KEY")
            if url and key:
                supabase = create_client(url, key)
                data_to_save = {"profil": target_profile, "platforma": "Tiktok", "srednia": int(avg_engagement), "ostatni_post": int(latest_post["engagement"]), "v_score": float(v_score)}
                supabase.table("historia_analiz").insert(data_to_save).execute()
                db_message = "Zapisano w bazie!"
        except Exception as e:
            db_message = f"(Błąd zapisu DB: {e})"
        
        # Budowanie wyglądu metryk (HTML)
        metrics_html = [
            html.Div(style={'textAlign': 'center'}, children=[html.H4("Średnie zaangażowanie"), html.H2(f"{int(avg_engagement):,}")]),
            html.Div(style={'textAlign': 'center'}, children=[html.H4("Ostatni post"), html.H2(f"{int(latest_post['engagement']):,}")]),
            html.Div(style={'textAlign': 'center'}, children=[html.H4("V-Score"), html.H2(f"{v_score:.2f}x", style={'color': 'red' if v_score > 1.5 else 'green'})])
        ]
        
        # Budowanie wykresu
        fig = px.bar(df, x="date", y="engagement", title=f"Zaangażowanie pod ostatnimi 10 postami (@{target_profile})")
        fig.add_hline(y=avg_engagement, line_dash="dash", line_color="red", annotation_text="Średnia")
        
        return metrics_html, fig, {'display': 'block'}, "", db_message

    except Exception as e:
        return "", {}, {'display': 'none'}, f"Wystąpił błąd: {str(e)}", ""

# 4. Start serwera
if __name__ == '__main__':
    app.run_server(debug=True)
