import dash_table as dt
import dash_html_components as html
from dash.dependencies import Input, Output

##
## Used by Callbacks
##

FIRE_TABLE_COLUMNS = [
    'id', 'lat', 'lng', 'num_locations', 'start', 'end', 'total_area',
    'total_consumption', 'total_emissions', 'PM2.5'
]
def get_fires_table_data(summarized_fires):
    return [sf['flat_summary'] for sf in summarized_fires]

def get_fires_table(summarized_fires):
    fires_table = dt.DataTable(
        id='fires-table',
        data=get_fires_table_data(summarized_fires),
        columns=[{'id': c, 'name': c} for c in FIRE_TABLE_COLUMNS],
        style_table={
            'maxHeight': '500px',
            'overflowY': 'scroll'
        },
        sort_action='native',
        filter_action='native',
        row_selectable='single',  #'multi',
        style_cell_conditional=[
            {
                'textAlign': 'left'
            }
        ],
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            }
        ],
        style_as_list_view=True,
        # editable=False,
    )

    return [
        html.Div("Select a fire to see emissions and plumerise graphs below",
            className="caption"),
        fires_table
    ]
