import webbrowser
from multiprocessing import freeze_support

import matplotlib

from dash import html
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

from dash_app import app
from layout.navbar import navbar
from layout.display import display
from callbacks import load_all  # Register all callbacks
from data.cache import clean_cache
import config

load_figure_template('LITERA')

matplotlib.use(backend='Agg')

app.layout = html.Div(dbc.Container(fluid=True, children=[
    dbc.Row([
        navbar.navbar,
        display.display,
    ]),
]))

server = app.server  # Expose server for Gunicorn

if __name__ == '__main__':
    if config.bundled_mode:
        freeze_support()
        webbrowser.open('http://127.0.0.1:8050')
        
    try:
        app.run_server(debug=config.debug_mode)
    finally:
        clean_cache()
