import json
import os

import dash
import dash_table as dt
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import flask
import plotly.express as px
from dash.dependencies import Input, Output

from . import analysis, firesmap, firestable, upload

def get_navbar(data):
    return dbc.NavbarSimple(
        children=[
            html.Div("run: {}".format(data.get('run_id')), id="run-id"),
            dbc.NavItem(upload.get_upload_box()),
            # dbc.DropdownMenu(
            #     nav=True,
            #     in_navbar=True,
            #     label="Menu",
            #     children=[
            #         dbc.DropdownMenuItem("Entry 1")
            #     ]
            # )
        ],
        brand="BlueSky Output Inspector",
        brand_href="#",
        sticky="top",
        fluid=True
    )

def get_body(mapbox_access_token, data, summarized_fires_by_id):
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H4("Fires Map"),
                            firesmap.get_fires_map(mapbox_access_token,
                                data, summarized_fires_by_id)
                        ],
                        md=4,
                    ),
                    dbc.Col(
                        [
                            html.H4("Fires Table"),
                            firestable.get_fires_data_table(
                                summarized_fires_by_id)
                        ],
                        md=8
                    )
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H4("Emissions"),
                            dcc.Graph(
                                figure={"data": []}
                            ),
                        ],
                        md=4,
                    ),
                    dbc.Col(
                        [
                            html.H4("Plumerise"),
                            dcc.Graph(
                                figure={"data": []}
                            ),
                        ],
                        md=4,
                    )
                ]
            )
        ],
        fluid=True,
        className="mt-4",
    )


EXTERNAL_STYLESHEETS = [
    dbc.themes.BOOTSTRAP
    #, 'https://codepen.io/chriddyp/pen/bWLwgP.css'
]

def create_app(bluesky_output_file, mapbox_access_token=None):
    data = {}
    if bluesky_output_file:
        with open(os.path.abspath(bluesky_output_file)) as f:
            data = json.load(f)

    summarized_fires_by_id = analysis.summarized_fires_by_id(data.get('fires'))

    app = dash.Dash(__name__, external_stylesheets=EXTERNAL_STYLESHEETS)
    app.title = "Bluesky Output Inspector"
    app.layout = html.Div([
        get_navbar(data),
        get_body(mapbox_access_token, data, summarized_fires_by_id)
    ])
    app.summarized_fires_by_id = summarized_fires_by_id

    firesmap.define_callbacks(app)
    firestable.define_callbacks(app)
    upload.define_callbacks(app)

    return app