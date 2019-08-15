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

def get_fires_map_data(mapbox_access_token, summarized_fires_by_id):
    fires = [sf['flat_summary'] for sf in summarized_fires_by_id.values()]
    df = pd.DataFrame(fires)
    df['text'] = ('<span data-id="' + df['id'] + '">'
        + df['total_area'].astype(str) + ' acre fire</span>')

    # TODO: get working when using 'go.Scattermapbox'
    _f = go.Scattermapbox if mapbox_access_token else go.Scattergeo
    return [_f(
        #type='scattergeo',
        #locationmode='USA-states',
        lon=df['avg_lng'],
        lat=df['avg_lat'],
        text=df['text'],
        meta={'id':df['id']},
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
            'colorscale': 'thermal', #COLOR_SCALE,
            'cmin': 0,
            'color': df['total_area'],
            'cmax': df['total_area'].max(),
            'colorbar': {
                'title': "Total Area"
            }
        }
    )]

def get_fires_map_layout(mapbox_access_token):
    # return dict(
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
    return go.Layout(
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
        #title = "Fire Locations"
    )

def get_fires_map_figure(mapbox_access_token, summarized_fires_by_id):
    data = get_fires_map_data(mapbox_access_token, summarized_fires_by_id)
    layout = get_fires_map_layout(mapbox_access_token)
    return {'data':data, 'layout': layout}

def get_fires_map(mapbox_access_token, summarized_fires_by_id):
    fig = get_fires_map_figure(mapbox_access_token, summarized_fires_by_id)
    return dcc.Graph(id='fires-map', figure=fig)
