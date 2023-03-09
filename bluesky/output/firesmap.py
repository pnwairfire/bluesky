"""bluesky.output.firesmap"""

import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go


def get_data_frame(summarized_fires):
    # preserve original order of fires, so that we can look up selected fires
    fires = [summarized_fires['fires_by_id'][f_id]['flat_summary']
        for f_id in summarized_fires['ids_in_order']]
    df = pd.DataFrame(fires)
    df['text'] = (df['total_area'].astype(str)  + ' acre fire'
        + ' at ' + df['avg_lat'].astype(str) + ', ' + df['avg_lng'].astype(str))
    return df

def get_mapbox_figure(mapbox_access_token, summarized_fires):
    px.set_mapbox_access_token(mapbox_access_token)
    df = get_data_frame(summarized_fires)
    fig = px.scatter_mapbox(df,
        lat="avg_lat",
        lon="avg_lng",
        #text='text',
        size="total_area",
        size_max=15,
        zoom=4,
        #color="total_area",
        #color_continuous_scale=px.colors.colorbrewer.YlOrRd
    )
    fig.update_traces(marker=dict(color='red'))

    return fig

COLOR_SCALE = [
    [0,"rgb(5, 10, 172)"],
    [100,"rgb(40, 60, 190)"],
    [250,"rgb(70, 100, 245)"],
    [500,"rgb(90, 120, 245)"],
    [1000,"rgb(106, 137, 247)"],
    [5000,"rgb(220, 220, 220)"]
]

def get_figure(mapbox_access_token, summarized_fires):
    df = get_data_frame(summarized_fires)

    fig = px.scatter_geo(df,
        lat='avg_lat',
        lon='avg_lng',
        #color="total_area",
        #color_continuous_scale=px.colors.colorbrewer.YlOrRd,
        hover_name="text",
        size="total_area",
        projection="natural earth"
    )
    fig.update_traces(marker=dict(color='red'))

    return fig

def get_fires_map(mapbox_access_token, summarized_fires):
    if mapbox_access_token:
        fig = get_mapbox_figure(mapbox_access_token, summarized_fires)
    else:
        fig = get_figure(mapbox_access_token, summarized_fires)

    return [
        html.Div("Select fires to see in the table", className="caption"),
        dcc.Graph(id='fires-map', figure=fig)
    ]
