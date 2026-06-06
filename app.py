import dash
from dash import Input, Output, State, html
import plotly.express as px
import pandas as pd
import os
from dotenv import load_dotenv
from supabase import create_client

# Importujemy komponenty z naszych własnych plików!
from layout import get_app_layout
from api_scraper import get_instagram_posts, get_tiktok_posts

load_dotenv()

app = dash.Dash(__name__)
server = app.server
app.title = "Viral Detector"

# 1. Podpinamy interfejs z pliku layout.py
app.layout = get_app_layout()

# 2. Logika
@app.callback(
    [Output('metrics-output', 'children'),
     Output('engagement-graph', 'figure'),
     Output('engagement-graph', 'style'),
     Output('error-message', 'children'),
     Output('success-message', 'children')],
    [Input('analyze-button', 'n_clicks')],
    [State('profile-input', 'value'),
     State('platform-select', 'value')]
)
def update_dashboard(n_clicks, target_profile, platform):
    if n_clicks == 0 or not target_profile:
        return "", {}, {'display': 'none'}, "", ""
    
    posts_data = []
    error_msg = ""
    
    # Wywołanie skryptów pobierania z pliku api_scraper.py
    if platform == "Instagram":
        posts_data, error_msg = get_instagram_posts(target_profile)
    elif platform == "Tiktok":
        posts_data, error_msg = get_tiktok_posts(target_profile)
        
    if error_msg:
        return "", {}, {'display': 'none'}, error_msg, ""
        
    if not posts_data:
        return "", {}, {'display': 'none'}, f"Nie udało się pobrać danych dla @{target_profile} ({platform}).", ""
        
    # Obliczenia analityczne
    df = pd.DataFrame(posts_data)
    avg_engagement = df["engagement"].mean()
    latest_post = df.iloc[0]
    v_score = latest_post["engagement"] / avg_engagement if avg_engagement > 0 else 0
    
    # Zapis do Supabase
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
    
    # Przygotowanie metryk i wykresów
    metrics_html = [
        html.Div(style={'textAlign': 'center'}, children=[html.H4("Średnie zaangażowanie"), html.H2(f"{int(avg_engagement):,}")]),
        html.Div(style={'textAlign': 'center'}, children=[html.H4("Ostatni post"), html.H2(f"{int(latest_post['engagement']):,}")]),
        html.Div(style={'textAlign': 'center'}, children=[html.H4("V-Score"), html.H2(f"{v_score:.2f}x", style={'color': 'red' if v_score > 1.5 else 'green'})])
    ]
    
    fig = px.bar(df, x="date", y="engagement", title=f"Zaangażowanie pod ostatnimi 10 postami (@{target_profile} - {platform})")
    fig.add_hline(y=avg_engagement, line_dash="dash", line_color="red", annotation_text="Średnia")
    
    return metrics_html, fig, {'display': 'block'}, "", db_message

if __name__ == '__main__':
    app.run_server(debug=True)
