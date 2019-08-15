import dash_html_components as html
import dash_core_components as dcc

def get_emissions_graph_elements(summarized_fires):
    if not summarized_fires:
        return [html.Div("")]

    # timeprofiled emissions are summed across all locations, and
    # each species is graphed
    # Note that there should only be one fire
    data = []
    for f in summarized_fires:
        tes_df = f.get_timeprofiled_emissions()
        if tes_df is not None and not tes_df.empty:
            species = [k for k in tes_df.keys() if k != 'dt']
            for s in species:
                data.append({
                    'x': tes_df['dt'],
                    'y': tes_df[s],
                    'text': ['a', 'b', 'c', 'd'],
                    'customdata': ['c.a', 'c.b', 'c.c', 'c.d'],
                    'name': s,
                    'mode': 'lines+markers',
                    'marker': {'size': 5}
                })

    if not data:
        return [html.Div("(no emissions for fire)")]

    return [
        dcc.Graph(
            id='emissions-graph',
            figure={
                'data': data,
                'layout': {
                    'title': 'Emissions from fire(s) {}'.format(','.join(
                        f['flat_summary']['id'] for f in summarized_fires)),
                    'clickmode': 'event+select'
                }
            }
        ),
        html.Div("Timeprofiled Emissions")
    ]

def get_plumerise_graph_elements(summarized_fires):
    if not summarized_fires:
        return [html.Div("")]

    return [html.Div("")]  # TEMP
