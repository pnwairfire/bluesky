import re

import dash_table as dt
from dash.dependencies import Input, Output

FIRE_TABLE_COLUMNS = [
    'id', 'lat', 'lng', 'num_locations', 'start', 'end', 'total_area',
    'total_consumption', 'total_emissions', 'PM2.5'
]
def process_fires(summarized_fires):
    return [sf['flat_summary'] for sf in summarized_fires]

def get_fires_data_table(summarized_fires_by_id):
    return dt.DataTable(
        id='fires-table',
        data=process_fires(summarized_fires_by_id.values()),
        columns=[{'id': c, 'name': c} for c in FIRE_TABLE_COLUMNS],
        style_table={
            'maxHeight': '500px',
            'overflowY': 'scroll'
        },
        sort_action='native',
        filter_action='native',
        row_selectable='single',  #'multi',
        # editable=False,
    )

ID_EXTRACTOR = re.compile('data-id="([^"]+)"')

def define_callbacks(app):

    # Update fires table
    @app.callback(
        Output("fires-table", "data"),
        [
            Input("fires-map", "selectedData"),
        ],
    )
    def update_bar(map_selected_data):
        if map_selected_data:
            selected_fires = []
            for p in  map_selected_data['points']:
                fire_id = ID_EXTRACTOR.findall(p['text'])[0]
                selected_fires.append(app.summarized_fires_by_id[fire_id])
        else:
            selected_fires = app.summarized_fires_by_id.values()

        return process_fires(selected_fires)
