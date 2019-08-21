import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go


##
## general helpers
##

def get_data_frame(summarized_fires_by_id):
    fires = [sf['flat_summary'] for sf in summarized_fires_by_id.values()]
    df = pd.DataFrame(fires)
    df['text'] = ('<span data-id="' + df['id'] + '">'
        + df['total_area'].astype(str) + ' acre fire</span>')
    return df

def get_mapbox_figure(mapbox_access_token, summarized_fires_by_id):
    px.set_mapbox_access_token(mapbox_access_token)
    df = get_data_frame(summarized_fires_by_id)
    fig = px.scatter_mapbox(df,
        lat="avg_lat",
        lon="avg_lng",
        text='text',
        size="total_area",
        size_max=15,
        zoom=4,
        #color="total_area",
        #color_continuous_scale=px.colors.colorbrewer.YlOrRd
    )

    return fig

COLOR_SCALE = [
    [0,"rgb(5, 10, 172)"],
    [100,"rgb(40, 60, 190)"],
    [250,"rgb(70, 100, 245)"],
    [500,"rgb(90, 120, 245)"],
    [1000,"rgb(106, 137, 247)"],
    [5000,"rgb(220, 220, 220)"]
]

def get_figure(mapbox_access_token, summarized_fires_by_id):
    df = get_data_frame(summarized_fires_by_id)

    return px.scatter_geo(df,
        lat='avg_lat',
        lon='avg_lng',
        text='text',
        #color="total_area",
        #color_continuous_scale=px.colors.colorbrewer.YlOrRd,
        hover_name="text",
        size="total_area",
        projection="natural earth"
    )

##
## Main function
##

def get_fires_map(mapbox_access_token, summarized_fires_by_id):
    if mapbox_access_token:
        fig = get_mapbox_figure(mapbox_access_token, summarized_fires_by_id)

    else:
        fig = get_figure(mapbox_access_token, summarized_fires_by_id)

    return [
        dcc.Graph(id='fires-map', figure=fig),
        html.Div("Select fires to see in the table", className="caption")
    ]
