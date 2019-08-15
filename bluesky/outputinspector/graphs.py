import dash_html_components as html
import dash_core_components as dcc

def get_emissions_graph_elements(summarized_fires):
    if not summarized_fires:
        return [html.Div("")]

    # if one fire, show timeprofiled emissions per location as well
    # as total; if multiple fires, show only total
    data = []
    for f in summarized_fires:
        for per_loc_te in f.get_timeprofiled_emissions():
            if 'PM2.5' in per_loc_te['timeprofiled_emissions']:
                data.append({
                    'x': per_loc_te['timeprofiled_emissions']['PM2.5']['dt'],
                    'y': per_loc_te['timeprofiled_emissions']['PM2.5']['val'],
                    'text': ['a', 'b', 'c', 'd'],
                    'customdata': ['c.a', 'c.b', 'c.c', 'c.d'],
                    'name': '{}, {} - PM2.5'.format(per_loc_te['lat'], per_loc_te['lng']),
                    'mode': 'markers',
                    'marker': {'size': 12}
                })

    if not data:
        return [html.Div("(no PM2.5 emissions for fire)")]

    return [
        html.Div("Timeprofiled Emissions"),
        dcc.Graph(
            id='emissions-graph',
            figure={
                'data': data,
                'layout': {
                    'clickmode': 'event+select'
                }
            }
        )
    ]


def get_plumerise_graph_elements(summarized_fires):
    if not summarized_fires:
        return [html.Div("")]

    return [html.Div("")]  # TEMP
