from collections import defaultdict

import dash_html_components as html
import dash_core_components as dcc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def generate_bar_graph_elements(graph_id, data, title, caption=''):
    return [
        html.H5(title),
        dcc.Graph(
            id=graph_id,
            figure={
                'data': data,
                'layout': {
                    'clickmode': 'event+select',
                    'barmode':'group'
                }
            }
        ),
        html.Div(caption, className="caption")
    ]

def aggergate_fuelbeds(fires_or_locations):
    fuelbeds = defaultdict(lambda: 0.0)
    total_area = sum([fol['area'] for fol in fires_or_locations])
    for fol in fires_or_locations:
        area_fraction = fol['area'] / total_area
        for fccs_id, pct in fol['fuelbeds'].items():
            fuelbeds[fccs_id] += area_fraction * pct

    # convert to list
    return [
        {'fccs_id': fccs_id, 'pct': pct} for fccs_id, pct in fuelbeds.items()
    ]

def generate_fuelbeds_graph_elements(fires_or_locations, graph_id):
    if not fires_or_locations:
        return []

    fuelbeds = aggergate_fuelbeds(fires_or_locations)
    df = pd.DataFrame(fuelbeds)
    if df.empty:
        return [html.Div("(no fuelbeds)",
            className="empty-graph")]

    data = [
        go.Pie(labels='FCCS ' + df['fccs_id'], values=df['pct'])
    ]
    figure = go.Figure(data=data)
    graph = dcc.Graph(id=graph_id, figure=figure)

    return [html.H5("Fuelbeds"), graph]

def aggregate_consumption(fires_or_locations):
    consumption = defaultdict(lambda: 0.0)
    for fol in fires_or_locations:
        for cat, val in fol['consumption_by_category'].items():
            consumption[cat] += val

    # convert to list
    return [{'c': c, 'v': v} for c,v in consumption.items()]

def generate_consumption_graph_elements(fires_or_locations, graph_id):
    if not fires_or_locations:
        return []

    consumption = aggregate_consumption(fires_or_locations)
    df = pd.DataFrame(consumption)
    if df.empty:
        return [html.Div("(no consumption)",
            className="empty-graph")]
    data = [go.Bar(x=df['c'], y=df['v'])]

    return generate_bar_graph_elements(graph_id, data, "Consumption")

def generate_emissions_graph_elements(fires_or_locations, graph_id):
    if not fires_or_locations:
        return []

    # timeprofiled emissions are summed across all locations, and
    # each species is graphed
    # Note that there should only be one fire
    # TODO: handle multple selected fires
    data = []
    for fol in fires_or_locations:
        timeprofiled_emissions = [
            dict(fol['timeprofiled_emissions'][t], dt=t) for t in sorted(fol['timeprofiled_emissions'].keys())
        ]

        df = pd.DataFrame(timeprofiled_emissions)
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
        return [html.Div("(no emissions)", className="empty-graph")]

    return [
        html.H5("Emissions Profile"),
        dcc.Graph(
            id=graph_id,
            figure={
                'data': data,
                'layout': {
                    # 'title': 'Emissions from fire(s) {}'.format(','.join(
                    #     f['flat_summary']['id'] for f in summarized_fires)),
                    'clickmode': 'event+select'
                }
            }
        ),
        html.Div("", className="caption")
    ]

##
## Summary fire graphs
##

def get_fire_fuelbeds_graph_elements(summarized_fires):
    return generate_fuelbeds_graph_elements(summarized_fires,
        'fire-fuelbeds-graph')

def get_fire_consumption_graph_elements(summarized_fires):
    return generate_consumption_graph_elements(summarized_fires,
        'fire-consumption-graph')

def get_fire_emissions_graph_elements(summarized_fires):
    return generate_emissions_graph_elements(summarized_fires,
        'fire-emissions-graph')


##
## Per-location graphs
##


def get_location_fuelbeds_graph_elements(locations):
    return generate_fuelbeds_graph_elements(locations,
        'location-fuelbeds-graph')

def get_location_consumption_graph_elements(locations):
    return generate_consumption_graph_elements(locations,
        'location-consumption-graph')

def get_location_emissions_graph_elements(locations):
    return generate_emissions_graph_elements(locations,
        'location-emissions-graph')

def get_location_plumerise_graph_elements(locations):
    if not locations:
        return []

    # TODO: handle multple selected locations ?
    graphs = []
    for loc in locations:
        # plumerise_by_level = defaultdict(lambda: [])
        # for p in loc['plumerise']:
        #     for level, h in enumerate(p['heights']):
        #         plumerise_by_level[level].append(dict(height=h, time=p['t']))
        # fig = go.Figure()
        # for level, vals in plumerise_by_level.items():
        #     df = pd.DataFrame(vals)
        #     fig.add_trace(go.Scatter(df, x="time", y="height"))
        # graphs.append(dcc.Graph(id='location-plumerise-graph', figure=fig))
        def plume_hour_dict(p, h, i):
            return dict(
                height=h,
                time=p['t'],
                level=i,
                emissions_fraction=(p['emission_fractions'][i]
                    if i < len(p['emission_fractions']) else None)
            )
        flat_plumerise = [plume_hour_dict(p, h, i)
            for p in loc['plumerise'] for i, h in enumerate(p['heights'])]
        flat_plumerise.sort(key=lambda e: e['time'])
        df = pd.DataFrame(flat_plumerise)
        if not df.empty:
            # df.set_index('level')
            graphs.append(
                dcc.Graph(id='location-plumerise-graph',
                    figure=px.line(df, x="time", y="height", color="level")
                    # figure=px.bar(df, x="time", y="height", color="loc",
                    #     barmode="group", #facet_col="aa", #facet_row="day",
                    #     # category_orders={"day": ["Thur", "Fri", "Sat", "Sun"],
                    #     #       "time": ["Lunch", "Dinner"]}
                    #     #height=400
                    # )
                )
            )


    if not graphs:
        graphs = [html.Div("(no plumerise information)", className="empty-graph")]

    return (
        [html.H4("Location Plumerise")]
        + graphs
        + [html.Div("Plumerise at the specified location", className="caption")]
    )
