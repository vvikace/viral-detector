from dash import dcc, html
import dash_bootstrap_components as dbc

def get_app_layout():
    return dbc.Container([
        html.H1("🕵️‍♂️ VIRAL DETECTOR", className="text-center mt-5 mb-3", style={'fontWeight': '900', 'background': 'linear-gradient(45deg, #00f2fe, #fe0979)', 'WebkitBackgroundClip': 'text', 'WebkitTextFillColor': 'transparent'}),
        html.P("Monitoruj zasięgi. Wyłapuj odchylenia.", className="text-center text-muted mb-5"),
        
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Platforma", className="fw-bold text-info"),
                        dcc.Dropdown(
                            id='platform-select',
                            options=[{'label': 'TikTok', 'value': 'Tiktok'}],
                            value='Tiktok', 
                            clearable=False
                        )
                        ], md=3), 
                    dbc.Col([
                        html.Label("Nazwa profilu", className="fw-bold text-info"),
                        dcc.Input(id='profile-input', type='text', placeholder='np. wersow', className="form-control bg-dark text-white border-info")
                        ], md=4),
                    dbc.Col([
                        html.Button('🔥 ANALIZUJ', id='analyze-button', n_clicks=0, className="btn btn-info w-100 fw-bold mt-4"),
                        ], md=2),
                    dbc.Col([
                        html.Button('🔄 ODŚWIEŻ', id='btn-force-refresh', n_clicks=0, className="btn btn-warning w-100 fw-bold mt-4"),
                        ], md=3)
                    ], className="g-3 align-items-center")
                ])
            ], className="border-info mb-4", style={'backgroundColor': '#111'}),
        
        html.Div(id='error-message', className="text-danger text-center fw-bold mb-3"),
        html.Div(id='success-message', className="text-success text-center fw-bold mb-3"),
        
        dcc.Loading(id="loading", type="cube", color="#00f2fe", children=[
        html.Div(id='metrics-output', className='d-flex justify-content-around mt-4'),
        dcc.Graph(id='engagement-graph', style={'display': 'none'}, className="mt-4"),
        
        ]),
        
        html.Div(
                dbc.Button("📄 POBIERZ RAPORT PDF", id="btn-download-pdf", color="danger", className="mt-4 fw-bold", style={'display': 'none'}),
                className="text-center"
            )
        ]),
        
        # NOWE: Techniczne komponenty Dasha do pobierania plików i zapamiętywania danych
        dcc.Download(id="download-dataframe-pdf"),
        dcc.Store(id='store-data')
        
    ], fluid=True, style={'maxWidth': '1000px'})
