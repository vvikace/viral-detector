from dash import dcc, html
import dash_bootstrap_components as dbc

def get_app_layout():
    return dbc.Container([
        html.H1("🕵️‍♂️ VIRAL DETECTOR", className="text-center mt-5 mb-3", style={'fontWeight': '900', 'background': 'linear-gradient(45deg, #00f2fe, #fe0979)', 'WebkitBackgroundClip': 'text', 'WebkitTextFillColor': 'transparent'}),
        html.P("Monitoruj zasięgi. Wyłapuj odchylenia.", className="text-center text-muted mb-5"),
        
        dbc.Card([
            dbc.CardBody([
                dbc.InputGroup([
                    dbc.Select(
                        id='platform-select',
                        options=[
                            {'label': 'TikTok', 'value': 'Tiktok'},
                            {'label': 'YouTube Shorts', 'value': 'Youtube'}
                        ],
                        value='Tiktok',
                        className="bg-dark text-white border-info",
                        style={'maxWidth': '200px', 'cursor': 'pointer'}
                    ),
                    dbc.InputGroupText("@", className="bg-dark text-info border-info fw-bold"),
                    dbc.Input(id='profile-input', type='text', placeholder='np. wersow', className="bg-dark text-white border-info"),
                    dbc.Button('ANALIZUJ', id='analyze-button', n_clicks=0, color="info", className="fw-bold"),
                    dbc.Button('ODŚWIEŻ', id='btn-force-refresh', n_clicks=0, color="warning", className="fw-bold")
                ], size="lg", className="shadow-sm")
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
        dcc.Store(id='store-data')
        
    ], fluid=True, style={'maxWidth': '1100px'})
