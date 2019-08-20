import dash_html_components as html
import dash_core_components as dcc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def get_fire_label(fire):
    return ('fire ' + fire['flat_summary']['id'][0:5] + '...'
        + fire['flat_summary']['id'][-5:])

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

##
## Summary fire graphs
##

def get_summary_fuelbeds_graph_elements(summarized_fires):
    if not summarized_fires:
        return [html.Div("")]

    # TODO: make sure this handles multple selected fires
    graphs = []
    for f in summarized_fires:
        df = pd.DataFrame(f['fuelbeds'])
        if not df.empty:
            graphs.append(dcc.Graph(
                id='summary-fuelbeds-graph-'+f['flat_summary']['id'],
                figure=go.Figure(data=[go.Pie(
                    labels='FCCS ' + df['fccs_id'], values=df['pct'])])
            ))

    if not graphs:
        return [html.Div("(no fuelbeds for fire)", className="empty-graph")]

    return [html.H4("Fuelbeds")] + graphs + [html.Div("Fuelbeds by Fire", className="caption")]

def get_summary_consumption_graph_elements(summarized_fires):
    if not summarized_fires:
        return [html.Div("")]

    # TODO: make sure this handles multple selected fires
    data = []
    for f in summarized_fires:
        df = pd.DataFrame([dict(c=c, v=v) for c,v in f['consumption_by_category'].items()])
        if not df.empty:
            data.append(go.Bar(name=get_fire_label(f), x=df['c'], y=df['v']))

    if not data:
        return [html.Div("(no consumption for fire)", className="empty-graph")]

    return generate_bar_graph_elements('summary-consumption-graph', data, "Consumption")

def get_summary_emissions_graph_elements(summarized_fires):
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
        html.H5("Timeprofiled Emissions"),
        dcc.Graph(
            id='summary-emissions-graph',
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
## Per-location graphs
##


def get_location_fuelbeds_graph_elements(locations):
    if not locations:
        return [html.Div("")]

    # TODO: make sure this handles multple selected fires
    graphs = []
    for l in locations:
        df = pd.DataFrame(l['fuelbeds'])
        if not df.empty:
            graphs.append(dcc.Graph(
                id='location-fuelbeds-graph-'+l['id'],
                figure=go.Figure(data=[go.Pie(
                    labels='FCCS ' + df['fccs_id'], values=df['pct'])])
            ))

    if not graphs:
        return [html.Div("(no fuelbeds for location)", className="empty-graph")]

    return [html.H4("Location Fuelbeds")] + graphs + [html.Div("Fuelbeds by location", className="caption")]

def get_location_consumption_graph_elements(locations):
    return [html.Div("(emissions graph to come")]

def get_location_emissions_graph_elements(locations):
    return [html.Div("(emissions graph to come")]

def get_location_plumerise_graph_elements(summarized_fires):
    if not summarized_fires:
        return [html.Div("")]

    # TODO: handle multple selected fires ?
    graphs = []
    # for f in summarized_fires:
    #     def create_rows(aa,loc,d):
    #         return [{
    #                 'time': d['t'],
    #                 'level': i,
    #                 'height': h,
    #                 'aa': aa['id'],
    #                 'loc':loc['id']
    #             } for i, h in enumerate(d['heights'])]
    #     flat_plumerise = flatten(f, 'plumerise', create_rows)

    #     df = pd.DataFrame(flat_plumerise)
    #     if not df.empty:
    #         # df.set_index('level')
    #         graphs.append(
    #             dcc.Graph(id='plumerise-graph',
    #                 figure=px.scatter(df, x="time", y="height", color="level")
    #                 # figure=px.bar(df, x="time", y="height", color="loc",
    #                 #     barmode="group", #facet_col="aa", #facet_row="day",
    #                 #     # category_orders={"day": ["Thur", "Fri", "Sat", "Sun"],
    #                 #     #       "time": ["Lunch", "Dinner"]}
    #                 #     #height=400
    #                 # )
    #             )
    #         )


    if not graphs:
        graphs = [html.Div("(no plumerise information)", className="empty-graph")]

    return [html.H4("Plumerise")] + graphs + [html.Div("Plumerise by activity collection, by location", className="caption")]
