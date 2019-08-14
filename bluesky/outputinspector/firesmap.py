import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go

COLOR_SCALE = [
    [0,"rgb(5, 10, 172)"],
    [100,"rgb(40, 60, 190)"],
    [250,"rgb(70, 100, 245)"],
    [500,"rgb(90, 120, 245)"],
    [1000,"rgb(106, 137, 247)"],
    [5000,"rgb(220, 220, 220)"]
]

def generate_map(mapbox_access_token, summarized_fires):
    fires = [sf['flat_summary'] for sf in summarized_fires]
    df = pd.DataFrame(fires)
    df['text'] = df['total_area'].astype(str) + ' acre fire'

    # TODO: get working when using 'go.Scattermapbox'
    _f = go.Scattermapbox if mapbox_access_token else go.Scattergeo
    data = [_f(
        #type='scattergeo',
        #locationmode='USA-states',
        lon=df['avg_lng'],
        lat=df['avg_lat'],
        text=df['text'],
        mode='markers',
        marker={
            'size': 8,
            'opacity': 0.8,
            #'reversescale': True,
            #'autocolorscale': False,
            'symbol': 'circle',
            # 'line': {
            #     'width': 1,
            #     'color': 'rgba(102, 102, 102)'
            # },
            #'colorscale': COLOR_SCALE,
            'cmin': 0,
            'color': df['total_area'],
            'cmax': df['total_area'].max(),
            'colorbar': {
                'title': "Total Area"
            }
        }
    )]

    # layout = dict(
    #         colorbar = True,
    #         geo = dict(
    #             scope='usa',
    #             projection=dict( type='albers usa' ),
    #             showland = True,
    #             landcolor = "rgb(250, 250, 250)",
    #             subunitcolor = "rgb(217, 217, 217)",
    #             countrycolor = "rgb(217, 217, 217)",
    #             countrywidth = 0.5,
    #             subunitwidth = 0.5
    #         ),
    #     )
    layout = go.Layout(
        autosize=True,
        mapbox=go.layout.Mapbox(
            accesstoken=mapbox_access_token,
            bearing=10,
            pitch=60,
            zoom=13,
            center=  {
                'lat':40.721319,
                'lon':-73.987130
            },
            style="mapbox://styles/mapbox/streets-v11"
        ),
        title = "Pick up Locations in NewYork"
    )

    fig = {'data':data, 'layout': layout}


    return dcc.Graph(id='graph', figure=fig)


def get_fires_map(app, mapbox_access_token, data, summarized_fires):

    map = html.Div(
        id="well-map-container",
        children=[
            # dcc.RadioItems(
            #     id="mapbox-view-selector",
            #     options=[
            #         {"label": "basic", "value": "basic"},
            #         {"label": "satellite", "value": "satellite"},
            #         {"label": "outdoors", "value": "outdoors"},
            #         {
            #             "label": "satellite-street",
            #             "value": "mapbox://styles/mapbox/satellite-streets-v9",
            #         },
            #     ],
            #     value="basic",
            # ),
            generate_map(mapbox_access_token, summarized_fires)
        ]
    )



    return map