import dash_table as dt
import dash_html_components as html
from dash.dependencies import Input, Output

##
## Used by Callbacks
##

LOCATION_TABLE_COLUMNS = [
    'fire_id', 'id', 'start', 'end', 'lat', 'lng', 'area',
    'total_consumption', 'total_emissions', 'PM2.5'
]

def flatten_location(fire, aa, loc):
    return {
        "fire_id": fire['flat_summary']['id'],
        "id": loc["id"],
        "start": aa["start"],
        "end": aa["end"],
        "lat": loc["lat"],
        "lng": loc["lng"],
        "area": loc["area"],
        "total_consumption": sum(loc['consumption_by_category'].values()),
        "total_emissions": sum([v for d in loc['emissions'].values() for v in d.values()]),
        "PM2.5": sum(loc['emissions'].get('PM2.5',{}).values())
    }

def get_locations_table(summarized_fires):
    # Note: We need to return a table, even if `data` is empty, to trigger
    #   callbacks that clear out the location header and graphs. This happens
    #   after loading an output file.  We'll just hide the table if `data`
    #   is empty

    # TODO: handle multple selected fires ?
    data = []
    for f in (summarized_fires or []):
        for aa in f['active_areas']:
            for l in aa['locations']:
                data.append(flatten_location(f, aa, l))

    locations_table = dt.DataTable(
        id='locations-table',
        data=data,
        columns=[{'id': c, 'name': c} for c in LOCATION_TABLE_COLUMNS],
        style_table={
            'maxHeight': '400px',
            'overflowY': 'scroll'
        },
        sort_action='native',
        filter_action='native',
        row_selectable='single',  #'multi',
        # editable=False,
    )

    return [
        html.Div(className="hidden" if not data else "", children=[
            html.Div("Select a location to see emissions and plumerise graphs below",
                className="caption"),
            locations_table
        ])
    ]