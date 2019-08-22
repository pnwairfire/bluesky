import base64
import json
import re

import dash

import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from . import analysis, firesmap, firestable, locationstable, graphs, layout


def define_callbacks(app, mapbox_access_token,
        initial_summarized_fires, initial_bluesky_output_file_name):
    # Suppress errors because some callbacks are are assigned to
    # components that will be genreated by other callbacks
    # (and thus aren't in the initial layout)
    app.config.suppress_callback_exceptions=True

    @app.callback(
        [
            Output('summarized-fires-state', 'value'),
            Output('bluesky-output-file-name', 'value')
        ],
        [
            Input("upload-data", "filename"),
            Input("upload-data", "contents")
        ]
    )
    def load_output(uploaded_filenames, uploaded_file_contents):
        """Loads data from an uploaded output file, processes the fire
        data to create summarized data, and saves the summary data and
        output file name to browser text fields.
        """
        if uploaded_file_contents is None:
            if not initial_summarized_fires:
                # Initial app load, and '-i' wasn't specified
                raise PreventUpdate
            summarized_fires_json = analysis.SummarizedFiresEncoder().encode(
                initial_summarized_fires)
            bluesky_output_file_name = initial_bluesky_output_file_name

        else:
            bluesky_output_file_name = uploaded_filenames
            content_type, content_string = uploaded_file_contents.split(',')
            decoded = base64.b64decode(content_string).decode()
            data = json.loads(decoded)
            summarized_fires_json = analysis.SummarizedFiresEncoder().encode(
                analysis.summarized_fires(data.get('fires', [])))

        return summarized_fires_json, bluesky_output_file_name

    @app.callback(
        [
            Output('navbar-upload-box', 'children'),
            Output('top-header', 'children'),
            Output('fires-map-container', 'children'),
            Output("fires-table-container", "children")
        ],
        [
            Input('summarized-fires-state', 'value'),
            Input('bluesky-output-file-name', 'value')
        ]
    )
    def update_fires_map_and_table_from_loaded_output(summarized_fires_json,
            bluesky_output_file_name):
        """Updates the fires map and table when new summarized data
        are generated and recroded.
        """
        summarized_fires = json.loads(summarized_fires_json)

        if not summarized_fires['fires_by_id']:
            return [
                [],
                [
                    html.Div(className="main-body-upload-box-container",
                        children=[layout.get_upload_box_layout()])
                ],
                [],
                []
            ]
        return [
            [layout.get_upload_box_layout()],
            [
                dbc.Alert(children=[
                        "Output File:",
                        html.Span(bluesky_output_file_name)
                    ],
                    color="secondary"
                )
            ],
            firesmap.get_fires_map(mapbox_access_token, summarized_fires),
            firestable.get_fires_table(summarized_fires)
        ]

    @app.callback(
        [
            Output('fires-table', "selected_rows")
        ],
        [
            Input('fires-table', "data"),
            Input("fires-map", "selectedData"),
            Input("fires-map", "clickData")
        ],
        [
            State('summarized-fires-state', 'value')
        ]
    )
    def select_table_row_from_clicked_map_marker(table_rows, selected_data,
            clickData, summarized_fires_json):
        summarized_fires = json.loads(summarized_fires_json)

        ctx = dash.callback_context
        row_ids = []
        if ctx.triggered:
            prop_id = ctx.triggered[0]['prop_id']
            data = ctx.triggered[0]['value']
            if prop_id in ('fires-map.clickData', 'fires-map.selectedData'):
                # create dict for fast lookup in determining row ids
                fire_ids = {summarized_fires['ids_in_order'][p['pointIndex']]:1
                    for p in data['points']}
                row_ids = [i for i,r in enumerate(table_rows)
                    if r['id'] in fire_ids]

        return [row_ids]


    @app.callback(
        [
            Output('fire-header', "children"),
            Output('fire-fuelbeds-container', "children"),
            Output('fire-consumption-container', "children"),
            Output('fire-emissions-container', "children"),
            Output('locations-table-container', "children")
        ],
        [
            Input('fires-table', "derived_virtual_data"),
            Input('fires-table', "derived_virtual_selected_rows")
        ],
        [
            State('summarized-fires-state', 'value')
        ]
    )
    def update_fire_graphs_and_locations_table(table_rows, selected_rows,
            summarized_fires_json):
        """Generates fire graphs and locations table when a fire is
        selected in the fires table.
        """
        summarized_fires = json.loads(summarized_fires_json)

        ctx = dash.callback_context
        fire_ids = []
        if ctx.triggered:
            prop_id = ctx.triggered[0]['prop_id']
            data = ctx.triggered[0]['value']
            if prop_id == 'fires-table.derived_virtual_selected_rows':
                fire_ids = [table_rows[i]['id'] for i in data]

        selected_fires = [summarized_fires['fires_by_id'][i] for i in fire_ids]

        def get_fire_header(selected_fires):
            # TODO: handle multiple fires ?
            if len(selected_fires) >= 1:
                return [
                    dbc.Alert(children=[
                            html.Div("Fire{} represented in the graphs below:".format(
                                "s" if len(selected_fires) > 1 else "")),
                            html.Ul(children=[
                                html.Li(children=[html.Span(sf['flat_summary']['id'])])
                                     for sf in selected_fires
                            ])

                        ],
                        color="secondary"
                    )
                ]
            return []

        return [
            get_fire_header(selected_fires),
            graphs.get_fire_fuelbeds_graph_elements(selected_fires),
            graphs.get_fire_consumption_graph_elements(selected_fires),
            graphs.get_fire_emissions_graph_elements(selected_fires),
            locationstable.get_locations_table(selected_fires),
            # graphs.get_plumerise_graph_elements(selected_fires),
            # graphs.get_fuelbeds_graph_elements(selected_fires)
        ]

    @app.callback(
        [
            Output('location-header', "children"),
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
            State('summarized-fires-state', 'value')
        ]
    )
    def update_location_graphs(rows, selected_rows, summarized_fires_json):
        """Generates location graphs when a location is selected in the
        locations table.
        """
        if not selected_rows:
            return [[]] * 5 # list of 4 empty lists

        summarized_fires = json.loads(summarized_fires_json)

        # if not selected_rows:
        #     raise PreventUpdate
        selected_rows = selected_rows or []

        fire_ids = [rows[i]['fire_id'] for i in selected_rows]
        location_ids = [rows[i]['id'] for i in selected_rows]

        selected_fires = [summarized_fires['fires_by_id'][fid] for fid in fire_ids]
        selected_locations = []
        for f in selected_fires:
            for aa in f['active_areas']:
                selected_locations.extend([l for l in aa['locations']
                    if l['id'] in location_ids])

        def get_location_header(selected_locations):
            # TODO: handle multiple locations ?
            if len(selected_locations) == 1:
                l = selected_locations[0]
                return [
                    dbc.Alert(children=[
                            "Location:",
                            html.Span("{}, {}".format(
                                l["lat"], l["lng"])),
                            html.Span("{} - {}".format(
                                l["start"], l["end"]))
                        ],
                        color="secondary"
                    )
                ]
            return []


        return [
            get_location_header(selected_locations),
            graphs.get_location_fuelbeds_graph_elements(selected_locations),
            graphs.get_location_consumption_graph_elements(selected_locations),
            graphs.get_location_emissions_graph_elements(selected_locations),
            graphs.get_location_plumerise_graph_elements(selected_locations)
        ]
