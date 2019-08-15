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
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from . import analysis, firesmap, firestable, graphs, layout


EXTERNAL_STYLESHEETS = [
    dbc.themes.BOOTSTRAP
    #, 'https://codepen.io/chriddyp/pen/bWLwgP.css'
]

def create_app(bluesky_output_file=None, mapbox_access_token=None):
    initial_data = {}
    if bluesky_output_file:
        with open(os.path.abspath(bluesky_output_file)) as f:
            initial_data = json.load(f)
    initial_summarized_fires_by_id = analysis.summarized_fires_by_id(
        initial_data.get('fires', []))

    def serve_layout():
        return layout.get_layout(initial_summarized_fires_by_id)

    app = dash.Dash(__name__, external_stylesheets=EXTERNAL_STYLESHEETS)
    app.title = "Bluesky Output Inspector"
    app.layout = serve_layout
    define_callbacks(app, mapbox_access_token,
        initial_summarized_fires_by_id)

    return app


##
## Callbacks
##

ID_EXTRACTOR = re.compile('data-id="([^"]+)"')

def define_callbacks(app, mapbox_access_token,
        initial_summarized_fires_by_id):
    # Suppress errors because some callbacks are are assigned to
    # components that will be genreated by other callbacks
    # (and thus aren't in the initial layout)
    app.config.suppress_callback_exceptions=True

    # Load data from uploaded output

    @app.callback(
        Output('summarized-fires-by-id-state', 'value'),
        [
            Input("upload-data", "filename"),
            Input("upload-data", "contents")
        ]
    )
    def update_output(uploaded_filenames, uploaded_file_contents):
        if uploaded_file_contents is None:
            if not initial_summarized_fires_by_id:
                # Initial app load, and '-i' wasn't specified
                raise PreventUpdate
            summarized_fires_by_id_json = analysis.SummarizedFiresEncoder().encode(
                initial_summarized_fires_by_id)

        else:
            content_type, content_string = uploaded_file_contents.split(',')
            decoded = base64.b64decode(content_string).decode()
            data = json.loads(decoded)
            summarized_fires_by_id_json = analysis.SummarizedFiresEncoder().encode(
                analysis.summarized_fires_by_id(data.get('fires', [])))

        return summarized_fires_by_id_json

    # Update map when new output data is loaded
    @app.callback(
        Output('fires-map-container', 'children'),
        [
            Input('summarized-fires-by-id-state', 'value')
        ]
    )
    def update_fires_map_from_loaded_output(summarized_fires_by_id_json):
        return firesmap.get_fires_map(mapbox_access_token,
            json.loads(summarized_fires_by_id_json))

    # Update fires table when fires are selected on map

    @app.callback(
        Output("fires-table-container", "children"),
        [
            Input("fires-map", "selectedData"),
            Input("fires-map", "clickData"),
            Input("fires-map", "figure")
        ],
        [
            State('summarized-fires-by-id-state', 'value')
        ]
    )
    def update_fires_table_from_map(selected_data, click_data, figure,
            summarized_fires_by_id_json):
        summarized_fires_by_id = json.loads(summarized_fires_by_id_json)

        def get_selected_fires(points):
            selected_fires = []
            for p in  points:
                fire_id = ID_EXTRACTOR.findall(p['text'])[0]
                selected_fires.append(summarized_fires_by_id[fire_id])
            return selected_fires

        ctx = dash.callback_context
        selected_fires = summarized_fires_by_id.values()
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
        ],
        [
            State('summarized-fires-by-id-state', 'value')
        ]
    )
    def update_graphs(rows, selected_rows, summarized_fires_by_id_json):
        summarized_fires_by_id = json.loads(summarized_fires_by_id_json)

        # if not selected_rows:
        #     raise PreventUpdate
        selected_rows = selected_rows or []

        fire_ids = [rows[i]['id'] for i in selected_rows]
        selected_fires = [summarized_fires_by_id[fid] for fid in fire_ids]

        emissions_graph = graphs.get_emissions_graph_elements(selected_fires)
        plumerise_graph = graphs.get_plumerise_graph_elements(selected_fires)

        return [
            emissions_graph,
            plumerise_graph
        ]
