import os

from dash import Dash
import dash_bootstrap_components as dbc

import config


if config.bundled_mode:
    app_directory = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.realpath(__file__)
    )))
    assets_directory = os.path.join(app_directory, 'assets')
else:
    assets_directory = 'assets'

app = Dash(
    __name__,
    title='VCF Observer',
    update_title='VCF Observing...',
    external_stylesheets=[dbc.themes.LITERA],
    url_base_pathname=config.url_base,
    assets_folder=assets_directory
)
