import dash_html_components as html
import dash_core_components as dcc
import pandas as pd
import plotly.graph_objects as go

def get_fuelbeds_graph_elements(summarized_fires):
    if not summarized_fires:
        return [html.Div("")]

    # Note that there should only be one fire
    # TODO: handle multple selected fires
    data = []
    for f in summarized_fires:
        df = pd.DataFrame(f['fuelbeds'])
        if not df.empty:
            data.append(go.Bar(
                name='fire ' + f['flat_summary']['id'][0:5]+'...'+f['flat_summary']['id'][-5:],
                x='fccs ' + df['fccs_id'], y=df['pct']
            ))

    if not data:
        return [html.Div("(no fuelbeds for fire)", className="empty-graph")]

    return [
        dcc.Graph(
            id='fuelbeds-graph',
            figure={
                'data': data,
                'layout': {
                    'clickmode': 'event+select',
                    'barmode':'group'
                }
            }
        ),
        html.Div("Fuelbeds", className="caption")
    ]


def get_consumption_graph_elements(summarized_fires):
    if not summarized_fires:
        return [html.Div("")]

    return [html.Div("(consumption graph coming soon)", className="empty-graph")]


def get_emissions_graph_elements(summarized_fires):
    if not summarized_fires:
        return [html.Div("")]

    # timeprofiled emissions are summed across all locations, and
    # each species is graphed
    # Note that there should only be one fire
    # TODO: handle multple selected fires
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
        return [html.Div("(no emissions for fire)", className="empty-graph")]

    return [
        dcc.Graph(
            id='emissions-graph',
            figure={
                'data': data,
                'layout': {
                    # 'title': 'Emissions from fire(s) {}'.format(','.join(
                    #     f['flat_summary']['id'] for f in summarized_fires)),
                    'clickmode': 'event+select'
                }
            }
        ),
        html.Div("Timeprofiled Emissions", className="caption")
    ]

def get_plumerise_graph_elements(summarized_fires):
    if not summarized_fires:
        return [html.Div("")]

    return [html.Div("(plumerise graph coming soon)", className="empty-graph")]  # TEMP
