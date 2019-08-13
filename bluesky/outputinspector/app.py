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

from bluesky import analysis
from . import firesmap

def get_navbar():
    return dbc.NavbarSimple(
        children=[
            dbc.NavItem(get_upload_box()),
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

def get_upload_box():
    return dcc.Upload(
        id="upload-data",
        children=html.Div(
            ["Drag and drop or click to select a Bluesky output JSON file to upload."]
        ),
        style={
            "width": "100%",
            "height": "60px",
            "lineHeight": "60px",
            "borderWidth": "1px",
            "borderStyle": "dashed",
            "borderRadius": "5px",
            "textAlign": "center",
            "margin": "10px",
        },
        multiple=False
    )

FIRE_TABLE_COLUMNS = [
    'id', 'lat', 'lng', 'num_locations', 'start', 'end', 'total_area',
    'total_consumption', 'total_emissions', 'PM2.5'
]




def get_fires_data_table(data, summarized_fires):

    return dt.DataTable(
        id='fires-table',
        data=[sf['flat_summary'] for sf in summarized_fires],
        columns=[{'id': c, 'name': c} for c in FIRE_TABLE_COLUMNS],
        style_table={
            'maxHeight': '250px',
            'overflowY': 'scroll'
        },
        sort_action='native',
        filter_action='native',
        row_selectable='single',  #'multi',
        # editable=False,
    )

def get_body(data, summarized_fires):
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            firesmap.get_fires_map(data, summarized_fires)
                        ],
                        md=4,
                    ),
                    dbc.Col(
                        [
                            html.Div("Fires Table"),
                            get_fires_data_table(data, summarized_fires)
                        ],
                        md=8
                    )
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H2("Emissions"),
                            dcc.Graph(
                                figure={"data": []}
                            ),
                        ],
                        md=4,
                    ),
                    dbc.Col(
                        [
                            html.H2("Plumerise"),
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

def create_app(bluesky_output_file):
    data = {}
    if bluesky_output_file:
        with open(os.path.abspath(bluesky_output_file)) as f:
            data = json.load(f)
    summarized_fires = [analysis.SummarizedFire(f) for f in data.get('fires')]

    app = dash.Dash(__name__, external_stylesheets=EXTERNAL_STYLESHEETS)
    app.title = "Bluesky Output Inspector"
    app.layout = html.Div([get_navbar(), get_body(data, summarized_fires)])


    ##
    ## Callbacks
    ##

    # @app.callback(
    #     Output("", ""),
    #     [Input("upload-data", "filename"), Input("upload-data", "contents")],
    # )
    # def update_output(uploaded_filenames, uploaded_file_contents):
    #     """Save uploaded files and regenerate the file list."""

    #     if uploaded_filenames is not None and uploaded_file_contents is not None:
    #         data = json.load(uploaded_file_contents)


    return app