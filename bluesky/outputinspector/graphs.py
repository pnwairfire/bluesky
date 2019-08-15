import dash_html_components as html
import dash_core_components as dcc
import pandas as pd

def get_emissions_graph_elements(summarized_fires):
    if not summarized_fires:
        return [html.Div("")]

    # timeprofiled emissions are summed across all locations, and
    # each species is graphed
    # Note that there should only be one fire
    data = []
    for f in summarized_fires:
        df = pd.DataFrame(f['timeprofiled_emissions'])
        if not df.empty:
            species = [k for k in df.keys() if k != 'dt']
            for s in species:
                data.append({
                    'x': df['dt'],
                    'y': df[s],
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
