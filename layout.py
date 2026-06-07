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
                            options=[
                                {'label': 'TikTok', 'value': 'Tiktok'},
                                {'label': 'YouTube Shorts', 'value': 'Youtube'}
                            ],
                            value='Tiktok', 
                            clearable=False
                        )
                    ], md=3), 
                    dbc.Col([
                        html.Label("Nazwa profilu", className="fw-bold text-info"),
                        dcc.Input(id='profile-input', type='text', placeholder='np. wersow', className="form-control bg-dark text-white border-info")
                    ], md=4),
                    dbc.Col([
                        html.Button('ANALIZUJ', id='analyze-button', n_clicks=0, className="btn btn-info w-100 fw-bold mt-4"),
                    ], md=2),
                    dbc.Col([
                        html.Button('ODŚWIEŻ', id='btn-force-refresh', n_clicks=0, className="btn btn-warning w-100 fw-bold mt-4"),
                    ], md=3)
                ], className="g-3 align-items-center"),
                
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            dbc.RadioItems(
                                id="history-toggle",
                                className="btn-group",
                                inputClassName="btn-check",
                                labelClassName="btn btn-outline-info fw-bold",
                                labelCheckedClassName="active",
                                options=[
                                    {"label": "Ostatnie 10 pomiarów", "value": "short"},
                                    {"label": "Cała historia (Trend)", "value": "long"},
                                ],
                                value="short",
                            )
                        ], className="text-center mt-4")
                    ])
                ])
            ])
        ], className="border-info mb-4 shadow", style={'backgroundColor': '#111', 'borderRadius': '15px'}),
        
        html.Div(id='error-message', className="text-danger text-center fw-bold mb-3"),
        html.Div(id='success-message', className="text-success text-center fw-bold mb-3"),
        
        dcc.Loading(id="loading", type="cube", color="#00f2fe", children=[
            html.Div(id='metrics-output', className='d-flex justify-content-between mt-4'),
            dcc.Graph(id='engagement-graph', style={'display': 'none'}, className="mt-5"),
        ]),
        
        html.Div(
            dbc.Button("📄 POBIERZ RAPORT PDF", id="btn-download-pdf", color="danger", className="mt-4 fw-bold shadow-lg", style={'display': 'none'}),
            className="text-center"
        ),
        
        dcc.Download(id="download-dataframe-pdf"),
        dcc.Store(id='store-data'),
        
        # EKRAN POWITALNY
        html.Div(id="welcome-screen", className="mt-5", children=[
            
            # 1. Szybki Start
            html.Div(className="text-center mb-5", children=[
                html.P("Nie masz pomysłu? Sprawdź popularnych twórców:", style={'color': '#aaa', 'fontSize': '1.1em'}),
                html.Div(className="d-flex justify-content-center gap-3 flex-wrap", children=[
                    dbc.Button("@wersow", id="btn-wersow", outline=True, color="info", className="rounded-pill"),
                    dbc.Button("@friz", id="btn-friz", outline=True, color="info", className="rounded-pill"),
                    dbc.Button("@hi_hania", id="btn-hania", outline=True, color="info", className="rounded-pill"),
                    dbc.Button("@przemek.pro", id="btn-przemek", outline=True, color="info", className="rounded-pill"),
                ])
            ]),

            # 2. Infografiki
            dbc.Row(className="text-center mt-5", children=[
                dbc.Col(md=4, children=[
                    html.Div("📡", style={'fontSize': '3.5rem', 'marginBottom': '15px'}),
                    html.H5("Skanowanie Sieci", style={'color': '#00f2fe', 'fontWeight': 'bold'}),
                    html.P("Pobieraj najświeższe dane o zasięgach prosto z TikToka i YouTube w czasie rzeczywistym!", style={'color': '#888', 'fontSize': '0.9em'})
                ]),
                dbc.Col(md=4, children=[
                    html.Div("🗄️", style={'fontSize': '3.5rem', 'marginBottom': '15px'}),
                    html.H5("Historia i Trendy", style={'color': '#fe0979', 'fontWeight': 'bold'}),
                    html.P("Narzędzie w tle buduje bazę danych dla analizowanych profili, pozwalając wyłapać długoterminowe wzorce.", style={'color': '#888', 'fontSize': '0.9em'})
                ]),
                dbc.Col(md=4, children=[
                    html.Div("🔥", style={'fontSize': '3.5rem', 'marginBottom': '15px'}),
                    html.H5("Wykrywanie Anomalii", style={'color': '#00f2fe', 'fontWeight': 'bold'}),
                    html.P("Autorski wskaźnik V-Score automatycznie identyfikuje materiały, które zyskują status viralu.", style={'color': '#888', 'fontSize': '0.9em'})
                ])
            ])
        ])
        html.Footer([
            html.Hr(style={'borderColor': '#fe0979', 'opacity': '0.3'}),
            html.P([
                "Stworzone przez ", 
                html.Span("Wiktorię Cedro", style={'color': '#00f2fe', 'fontWeight': 'bold', 'textShadow': '0 0 5px #00f2fe'}),
                " | Viral Detector 2026"
            ], className="text-center text-muted mt-3 mb-4", style={'fontSize': '0.9em'})
        ])
        
    ], fluid=True, style={'maxWidth': '1100px'})
