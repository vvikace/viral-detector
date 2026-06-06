from dash import dcc, html

def get_app_layout():
    return html.Div(style={'fontFamily': 'Arial, sans-serif', 'padding': '30px', 'maxWidth': '1000px', 'margin': '0 auto'}, children=[
        
        html.H1("🕵️‍♂️ Viral Detector", style={'textAlign': 'center', 'color': '#333'}),
        html.P("Analiza viralności profili na platformach TikTok oraz Instagram.", style={'textAlign': 'center', 'color': '#666'}),
        
        # Panel wyszukiwania
        html.Div(style={'backgroundColor': '#f8f9fa', 'padding': '20px', 'borderRadius': '10px', 'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'gap': '15px', 'marginBottom': '30px', 'flexWrap': 'wrap'}, children=[
            html.Label("Platforma: ", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='platform-select',
                options=[
                    {'label': 'TikTok', 'value': 'Tiktok'},
                    {'label': 'Instagram', 'value': 'Instagram'}
                ],
                value='Tiktok',
                clearable=False,
                style={'width': '150px'}
            ),
            html.Label("Nazwa profilu: ", style={'fontWeight': 'bold'}),
            dcc.Input(id='profile-input', type='text', placeholder='np. wersow', style={'padding': '8px', 'width': '200px', 'borderRadius': '5px', 'border': '1px solid #ccc'}),
            html.Button('Analizuj', id='analyze-button', n_clicks=0, style={'padding': '8px 20px', 'backgroundColor': '#000000', 'color': 'white', 'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer'})
        ]),
        
        html.Div(id='error-message', style={'color': 'red', 'fontWeight': 'bold', 'textAlign': 'center'}),
        html.Div(id='success-message', style={'color': 'green', 'fontWeight': 'bold', 'textAlign': 'center'}),
        
        # Animacja ładowania i wyniki
        dcc.Loading(
            id="loading",
            type="circle",
            color="#000000",
            children=[
                html.Div(id='metrics-output', style={'display': 'flex', 'justifyContent': 'space-around', 'marginTop': '30px'}),
                dcc.Graph(id='engagement-graph', style={'display': 'none', 'marginTop': '30px'})
            ]
        )
    ])
