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

def get_navbar():
    return dbc.NavbarSimple(
        children=[
            html.Div("", id="run-id"),
            dbc.NavItem(upload.get_upload_box_layout()),
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

def get_body():
    return dbc.Container(
        [
            dbc.Row([
                dbc.Col([html.Div(id="fires-map-container")], lg=5),
                dbc.Col([html.Div(id='fires-table-container')], lg=7)
            ]),
            dbc.Row([
                dbc.Col([html.Div(id='emissions-container')], lg=6),
                dbc.Col([html.Div(id='plumerise-container')], lg=6)
            ])
        ],
        fluid=True,
        className="mt-4",
    )

def serve_layout():
    return html.Div([
        html.Div(session_id, id='session-id', style={'display': 'none'}),
        get_navbar(),
        get_body()
    ])


EXTERNAL_STYLESHEETS = [
    dbc.themes.BOOTSTRAP
    #, 'https://codepen.io/chriddyp/pen/bWLwgP.css'
]

def create_app(bluesky_output_file=None, mapbox_access_token=None):
    data = {}
    if bluesky_output_file:
        with open(os.path.abspath(bluesky_output_file)) as f:
            data = json.load(f)
    summarized_fires_by_id = analysis.summarized_fires_by_id(
        data.get('fires', []))

    app = dash.Dash(__name__, external_stylesheets=EXTERNAL_STYLESHEETS)
    app.title = "Bluesky Output Inspector"
    app.layout = serve_layout
    app.summarized_fires_by_id = summarized_fires_by_id
    define_callbacks(app, mapbox_access_token)

    return app


##
## Callbacks
##

ID_EXTRACTOR = re.compile('data-id="([^"]+)"')

def define_callbacks(app, mapbox_access_token):
    # Suppress errors because some callbacks are are assigned to
    # components that will be genreated by other callbacks
    # (and thus aren't in the initial layout)
    app.config.suppress_callback_exceptions=True

    # Load data from uploaded output

    @app.callback(
        Output('fires-map-container', 'children'),
        [
            Input("upload-data", "filename"),
            Input("upload-data", "contents")
        ]
    )
    def update_output(uploaded_filenames, uploaded_file_contents):
        if uploaded_file_contents is None:
            if not app.summarized_fires_by_id:
                # Initial app load, and '-i' wasn't specified
                raise PreventUpdate
            # else, leave app.summarized_fires_by_id as is

        else:
            content_type, content_string = uploaded_file_contents.split(',')
            decoded = base64.b64decode(content_string).decode()
            data = json.loads(decoded)
            app.summarized_fires_by_id = analysis.summarized_fires_by_id(
                data.get('fires', []))

        return firesmap.get_fires_map(mapbox_access_token,
            app.summarized_fires_by_id)

    # Update fires table when fires are selected on map

    @app.callback(
        Output("fires-table-container", "children"),
        [
            Input("fires-map", "selectedData"),
            Input("fires-map", "clickData"),
            Input("fires-map", "figure")
        ],
    )
    def update_fires_table_from_map(*args):
        def get_selected_fires(points):
            selected_fires = []
            for p in  points:
                fire_id = ID_EXTRACTOR.findall(p['text'])[0]
                selected_fires.append(app.summarized_fires_by_id[fire_id])
            return selected_fires

        ctx = dash.callback_context
        selected_fires = app.summarized_fires_by_id.values()
        if ctx.triggered:
            prop_id = ctx.triggered[0]['prop_id']
            data = ctx.triggered[0]['value']
            if prop_id in ('fires-map.clickData', 'fires-map.selectedData'):
                selected_fires = get_selected_fires(data['points'])
        # else, leave as complete set of fires

        return firestable.get_fires_table(selected_fires)

    # Update graphs when fire is selected in table

    @app.callback(
        [
            Output('emissions-container', "children"),
            Output('plumerise-container', "children")
        ],
        [
            Input('fires-table', "derived_virtual_data"),
            Input('fires-table', "derived_virtual_selected_rows")
        ]
    )
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
