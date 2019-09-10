import base64
import json
import os
import re

import dash
import dash_bootstrap_components as dbc

from . import analysis, layout, callbacks


EXTERNAL_STYLESHEETS = [
    dbc.themes.BOOTSTRAP
    #, 'https://codepen.io/chriddyp/pen/bWLwgP.css'
]

def create_app(bluesky_output_file=None, mapbox_access_token=None,
        url_path_prefix=None):
    initial_data = {}
    if bluesky_output_file:
        with open(os.path.abspath(bluesky_output_file)) as f:
            initial_data = json.load(f)
    initial_summarized_fires = analysis.summarized_fires(
        initial_data.get('fires', []))

    def serve_layout():
        return layout.get_layout(bluesky_output_file,
            initial_summarized_fires)

    app = dash.Dash(__name__, url_base_pathname=url_path_prefix,
        external_stylesheets=EXTERNAL_STYLESHEETS)
    app.title = "Bluesky Output Visualizer"
    app.layout = serve_layout
    callbacks.define_callbacks(app, mapbox_access_token,
        initial_summarized_fires, bluesky_output_file)

    return app
