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


FIRE_TABLE_COLUMNS = ['id']

def get_fires_data_table(data):
    fire_row_data = []
    for f in data.get('fires'):
        fire_row_data.append({'id': f.get('id')})

    return dt.DataTable(
        id='fires-table',
        data=fire_row_data,
        columns=[{'id': c, 'name': c} for c in FIRE_TABLE_COLUMNS],
        # editable=False,
        # row_selectable=True
    )

def get_body(data):
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            "Show map with points here"
                        ],
                        md=4,
                    ),
                    dbc.Col(
                        [
                            html.H2("Graph"),
                            dcc.Graph(
                                figure={"data": []}
                            ),
                        ]
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div("Fires Table"),
                            get_fires_data_table(data)
                        ]
                    )
                ]
            )
        ],
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

    app = dash.Dash(__name__, external_stylesheets=EXTERNAL_STYLESHEETS)
    app.title = "Bluesky Output Inspector"
    app.layout = html.Div([get_navbar(), get_body(data)])


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