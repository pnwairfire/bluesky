import base64
import json
import re

import dash

import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from . import analysis, firesmap, firestable, locationstable, graphs


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
            Output('summary-fuelbeds-container', "children"),
            Output('summary-consumption-container', "children"),
            Output('summary-emissions-container', "children"),
            Output('locations-table-container', "children")
        ],
        [
            Input('fires-table', "derived_virtual_data"),
            Input('fires-table', "derived_virtual_selected_rows")
        ],
        [
            State('summarized-fires-by-id-state', 'value')
        ]
    )
    def update_fire_graphs_and_table(rows, selected_rows, summarized_fires_by_id_json):
        summarized_fires_by_id = json.loads(summarized_fires_by_id_json)

        # if not selected_rows:
        #     raise PreventUpdate
        selected_rows = selected_rows or []

        fire_ids = [rows[i]['id'] for i in selected_rows]
        selected_fires = [summarized_fires_by_id[fid] for fid in fire_ids]

        return [
            graphs.get_summary_fuelbeds_graph_elements(selected_fires),
            graphs.get_summary_consumption_graph_elements(selected_fires),
            graphs.get_summary_emissions_graph_elements(selected_fires),
            locationstable.get_locations_table(selected_fires),
            # graphs.get_plumerise_graph_elements(selected_fires),
            # graphs.get_fuelbeds_graph_elements(selected_fires)
        ]

    @app.callback(
        [
            Output('location-fuelbeds-container', "children"),
            Output('location-consumption-container', "children"),
            Output('location-emissions-container', "children"),
            Output('location-plumerise-container', "children")
        ],
        [
            Input('locations-table', "derived_virtual_data"),
            Input('locations-table', "derived_virtual_selected_rows")
        ],
        [
            State('summarized-fires-by-id-state', 'value')
        ]
    )
    def update_location_graphs(rows, selected_rows, summarized_fires_by_id_json):
        if not selected_rows:
            return [html.Div("")]* 4

        summarized_fires_by_id = json.loads(summarized_fires_by_id_json)

        # if not selected_rows:
        #     raise PreventUpdate
        selected_rows = selected_rows or []

        fire_ids = [rows[i]['fire_id'] for i in selected_rows]
        location_ids = [rows[i]['id'] for i in selected_rows]

        selected_fires = [summarized_fires_by_id[fid] for fid in fire_ids]
        selected_locations = []
        for f in selected_fires:
            for aa in f['active_areas']:
                selected_locations.extend([l for l in aa['locations']
                    if l['id'] in location_ids])

        return [
            graphs.get_location_fuelbeds_graph_elements(selected_locations),
            graphs.get_location_consumption_graph_elements(selected_locations),
            graphs.get_location_emissions_graph_elements(selected_locations),
            graphs.get_location_plumerise_graph_elements(selected_locations)
        ]
