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

thread = threading.Thread(target=bot_loop, daemon=True)
thread.start()

from layout import get_app_layout
from api_scraper import get_tiktok_posts, get_youtube_posts

load_dotenv()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
server = app.server
app.title = "Viral Detector"

app.layout = get_app_layout()

@app.callback(
    Output('profile-input', 'value'),
    [Input('btn-wersow', 'n_clicks'),
     Input('btn-friz', 'n_clicks'),
     Input('btn-hania', 'n_clicks'),
     Input('btn-przemek', 'n_clicks')],
    prevent_initial_call=True
)
def set_quick_profile(n1, n2, n3, n4):
    trigger = ctx.triggered_id
    if trigger == 'btn-wersow': return 'wersow'
    if trigger == 'btn-friz': return 'tojafriz'
    if trigger == 'btn-hania': return 'tojahania'
    if trigger == 'btn-przemek': return 'przemek.pro'
    return dash.no_update


@app.callback(
    [Output('metrics-output', 'children'),
     Output('engagement-graph', 'figure'),
     Output('engagement-graph', 'style'),
     Output('error-message', 'children'),
     Output('success-message', 'children'),
     Output('store-data', 'data'),
     Output('btn-download-pdf', 'style'),
     Output('welcome-screen', 'style')],
    [Input('analyze-button', 'n_clicks'),
     Input('btn-force-refresh', 'n_clicks'),
     Input('history-toggle', 'value')],
    [State('profile-input', 'value'),
     State('platform-select', 'value')]
)
def update_dashboard(n1, n2, history_mode, target_profile, platform):
    if not target_profile or (n1 == 0 and n2 == 0 and ctx.triggered_id is None):
        return "", {}, {'display': 'none'}, "", "", None, {'display': 'none'}, {'display': 'block'}
    
    trigger_id = ctx.triggered_id
    supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
    posts_data = []
    error_msg = ""
    db_message = ""

    if trigger_id == 'btn-force-refresh':
        if platform.lower() == 'tiktok':
            fresh_data, refresh_error = get_tiktok_posts(target_profile)
        else:
            fresh_data, refresh_error = get_youtube_posts(target_profile)
            
        if fresh_data and not refresh_error:
            try:
                df_scraped = pd.DataFrame(fresh_data)
                avg_scraped = df_scraped["engagement"].mean()
                latest_scraped = df_scraped.iloc[0]
                v_score_scraped = latest_scraped["engagement"] / avg_scraped if avg_scraped > 0 else 0
                
                data_to_save = {
                    "profil": target_profile, 
                    "platforma": platform, 
                    "srednia": int(avg_scraped), 
                    "ostatni_post": int(latest_scraped["engagement"]), 
                    "v_score": float(v_score_scraped),
                    "url_posta": latest_scraped.get("url", "Brak linku"),
                    "tytul": latest_scraped.get("title", "Brak tytułu"),
                    "miniaturka": latest_scraped.get("thumbnail", "")
                }
                supabase.table("historia_analiz").insert(data_to_save).execute()
                db_message = "Zapisano w bazie!"
            except Exception as e:
                db_message = f"(Błąd zapisu nowej historii: {e})"

    if history_mode == "short":
        if platform.lower() == 'tiktok':
            posts_data, error_msg = get_tiktok_posts(target_profile)
        else:
            posts_data, error_msg = get_youtube_posts(target_profile)
            
        if error_msg:
            return "", {}, {'display': 'none'}, error_msg, "", None, {'display': 'none'}, {'display': 'block'}
            
    else:
        response = supabase.table("historia_analiz").select("*").eq("profil", target_profile).eq("platforma", platform).order("data", desc=True).limit(100).execute()
        
        for item in response.data:
            posts_data.append({
                "date": item.get('data'), 
                "engagement": item.get('ostatni_post', 0),
                "url": item.get('url_posta', 'Brak linku'),
                "title": item.get('tytul', 'Brak tytułu'),
                "thumbnail": item.get('miniaturka', '')
            })
            
        if not posts_data:
            return "", {}, {'display': 'none'}, f"Brak danych w bazie dla @{target_profile}. Kliknij Odśwież.", "", None, {'display': 'none'}, {'display': 'block'}

    df = pd.DataFrame(posts_data)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.sort_values(by='date', ascending=True).reset_index(drop=True)
        df['date_label'] = df['date'].dt.strftime('%m-%d %H:%M').str.replace(' 00:00', '')
        
    df_labels = df.iloc[::10].copy()
    
    avg_engagement = df["engagement"].mean()
    latest_post = df.iloc[-1]
    
    latest_url = latest_post.get("url", "Brak linku")
    latest_title = latest_post.get("title", "Brak tytułu")
    latest_thumb = latest_post.get("thumbnail", "")
    v_score = latest_post["engagement"] / avg_engagement if avg_engagement > 0 else 0
    
    badge = html.Div(
        "VIRAL!",
        style={
            'position': 'absolute', 'top': '10px', 'right': '10px',
            'backgroundColor': '#fe0979', 'color': 'white', 'padding': '5px 10px',
            'borderRadius': '8px', 'fontWeight': 'bold', 'boxShadow': '0 0 15px rgba(254, 9, 121, 0.8)',
            'zIndex': '10', 'fontSize': '0.85em', 'letterSpacing': '1px'
        }
    ) if v_score > 1.5 else None
    
    metrics_html = [
        html.Div(className='metric-card text-center', children=[
            html.H4(["Średnia " + ("z 10 postów " if history_mode == 'short' else "historyczna "), html.Span("ℹ️", id="tooltip-avg", style={'cursor': 'help', 'fontSize': '0.8em'})]),
            dbc.Tooltip("Średnie zaangażowanie z widocznych publikacji.", target="tooltip-avg", placement="top"),
            html.H2(f"{int(avg_engagement):,}", className="mt-4")
        ]),
        
        html.Div(className='metric-card text-center', children=[
            html.H4("Najnowszy Post", className="mb-3"),
            html.Div(style={'position': 'relative', 'display': 'inline-block', 'width': '100%'}, children=[
                html.Img(src=latest_thumb, style={'height': '140px', 'width': '100%', 'objectFit': 'cover', 'borderRadius': '10px', 'marginBottom': '10px', 'boxShadow': '0 4px 8px rgba(0,242,254,0.2)'}) if latest_thumb else html.Div(),
                badge
            ]),
            html.P(latest_title[:45] + "..." if len(latest_title) > 45 else latest_title, style={'fontSize': '0.85em', 'fontStyle': 'italic', 'color': '#aaa'}),
            html.H3(f"{int(latest_post['engagement']):,}"),
            html.A("🔗 Otwórz post", href=latest_url, target="_blank", className="btn btn-outline-info btn-sm mt-2 w-100 fw-bold") if latest_url != "Brak linku" else html.Span()
        ]),
        
        html.Div(className='metric-card text-center', children=[
            html.H4(["V-Score ", html.Span("ℹ️", id="tooltip-vscore", style={'cursor': 'help', 'fontSize': '0.8em'})]),
            dbc.Tooltip("Wskaźnik wiralności. Wynik powyżej 1.5x oznacza wykrycie viralu!", target="tooltip-vscore", placement="top"),
            html.H2(f"{v_score:.2f}x", className="mt-4", style={'color': '#fe0979' if v_score > 1.5 else '#00f2fe', 'fontSize': '3.5em', 'fontWeight': '900'})
        ])
    ]
    
    fig = px.bar(df, x=df.index, y="engagement", title=f"Historia dla: @{target_profile} ({platform})",
                 template="plotly_dark", color_discrete_sequence=["#00f2fe"], custom_data=["url", "title"])
    fig.update_traces(
        hovertemplate=(
            "<b>%{customdata[1]}</b><br><br>" +  
            "<b>Wynik:</b> %{y}<br>" +            
            "<b>Link:</b> %{customdata[0]}" +      
            "<extra></extra>"                      
        ),
        selector=dict(type='bar')
    )
    
    if history_mode == 'long' and len(df) > 5:
        df['trend'] = df['engagement'].rolling(window=5, min_periods=1).mean()
        fig.add_scatter(x=df.index, y=df['trend'], mode='lines', name='Linia trendu', line=dict(color='#fe0979', width=4))
    else:
        fig.add_hline(y=avg_engagement, line_dash="dash", line_color="#fe0979", annotation_text="Średnia")
        
    if 'date_label' in df.columns:
        fig.update_xaxes(tickvals=df_labels.index, ticktext=df_labels['date_label'], title="Data (co 10-ty pomiar)")
    
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
    
    stored_data = {
        "profile": target_profile,
        "platform": platform,
        "avg": int(avg_engagement),
        "latest": int(latest_post["engagement"]),
        "vscore": v_score,
        "latest_url": latest_url  
    }
    
    return metrics_html, fig, {'display': 'block'}, "", db_message, stored_data, {'display': 'inline-block'}, {'display': 'none'}

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
    pdf.ln(5)
    
    pdf.cell(200, 10, txt=clean(f"Srednie zaangazowanie (z wykresu): {stored_data['avg']}"), ln=True)
    pdf.cell(200, 10, txt=clean(f"Ostatnie zaangazowanie: {stored_data['latest']}"), ln=True)
    pdf.cell(200, 10, txt=clean(f"Wskaznik V-Score: {stored_data['vscore']:.2f}x"), ln=True)
    
    url = stored_data.get('latest_url', '')
    if url and url != 'Brak linku':
        pdf.set_font("Arial", 'U', 12)  
        pdf.set_text_color(0, 150, 255) 
        pdf.cell(200, 10, txt=clean("-> Kliknij tutaj, aby otworzyc najnowszy post <-"), ln=True, link=url)
        pdf.set_text_color(0, 0, 0)     
        pdf.set_font("Arial", size=12)
    
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
    
    return dcc.send_bytes(pdf.output(dest='S').encode('latin-1', 'replace'), f"raport_{stored_data['profile']}.pdf")
    
from dash import ClientsideFunction
app.clientside_callback(
    """
    function(profile) {
        document.title = profile ? "Viral Detector | @" + profile : "Viral Detector";
        return "";
    }
    """,
    Output('store-data', 'id'),
    Input('profile-input', 'value')
)
if __name__ == '__main__':
    app.run_server(debug=True)
