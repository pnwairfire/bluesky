import base64
import json
import os
import re

import dash
import dash_table as dt
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import flask
import plotly.express as px
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate

from . import analysis, firesmap, firestable, upload, graphs

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
                            html.Div(id="fires-map-container", children=[
                                firesmap.get_fires_map(mapbox_access_token,
                                    summarized_fires_by_id),
                                html.Div("Select fires to see in the table",
                                    className="caption")
                            ])
                        ],
                        lg=5,
                    ),
                    dbc.Col(
                        [
                            html.Div(id='fires-table-container', children=[
                                firestable.get_fires_data_table(
                                    summarized_fires_by_id),
                                html.Div("Select a fire to see emissions and plumerise graphs",
                                    className="caption")
                            ])
                        ],
                        lg=7
                    )
                ]
            ),
            dbc.Row([
                dbc.Col([html.Div(id='emissions-container')],lg=6),
                dbc.Col([html.Div(id='plumerise-container')],lg=6)
            ])
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
    define_callbacks(app, mapbox_access_token)

    return app


##
## Callbacks
##

ID_EXTRACTOR = re.compile('data-id="([^"]+)"')

def define_callbacks(app, mapbox_access_token):

    # Update fires table when fires are selected on map

    @app.callback(
        Output("fires-table", "data"),
        [
            Input("fires-map", "selectedData"),
        ],
    )
    def update_fires_table_from_map(map_selected_data):
        if map_selected_data:
            selected_fires = []
            for p in  map_selected_data['points']:
                fire_id = ID_EXTRACTOR.findall(p['text'])[0]
                selected_fires.append(app.summarized_fires_by_id[fire_id])
        else:
            selected_fires = app.summarized_fires_by_id.values()

        return firestable.process_fires(selected_fires)

    # Update graphs when fire is selected in table

    @app.callback([
        Output('emissions-container', "children"),
        Output('plumerise-container', "children")],
        [Input('fires-table', "derived_virtual_data"),
         Input('fires-table', "derived_virtual_selected_rows")])
    def update_graphs(rows, selected_rows):
        # if not selected_rows:
        #     raise PreventUpdate
        selected_rows = selected_rows or []

        fire_ids = [rows[i]['id'] for i in selected_rows]
        selected_fires = [app.summarized_fires_by_id[fid] for fid in fire_ids]

        emissions_graph = graphs.get_emissions_graph_elements(selected_fires)
        plumerise_graph = graphs.get_plumerise_graph_elements(selected_fires)

        return [
            emissions_graph,
            plumerise_graph
        ]

    # Load data from uploaded output

    @app.callback(
        #[Output('fires-map', 'figure'), Output("fires-table", "data")],
        Output('fires-map', 'figure'),
        [Input("upload-data", "filename"), Input("upload-data", "contents")],
    )
    def update_output(uploaded_filenames, uploaded_file_contents):
        if uploaded_file_contents is None:
            raise PreventUpdate

        content_type, content_string = uploaded_file_contents.split(',')
        decoded = base64.b64decode(content_string).decode()
        data = json.loads(decoded)
        app.summarized_fires_by_id = analysis.summarized_fires_by_id(data.get('fires'))

        return {'data': firesmap.get_fires_map_data(
            mapbox_access_token, app.summarized_fires_by_id)}
        # return [
        #     firesmap.get_fires_map_figure(
        #         mapbox_access_token, app.summarized_fires_by_id),
        #     firestable.process_fires(app.summarized_fires_by_id.values())
        # ]
        # return firesmap.get_fires_map_figure(mapbox_access_token,
        #     app.summarized_fires_by_id)