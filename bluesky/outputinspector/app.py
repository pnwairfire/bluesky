import os

import dash
import dash_core_components as dcc
import dash_html_components as html
import flask
import plotly.express as px

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Bluesky Output Inspector"

app.layout = html.Div(children=[
    html.H3(children='Bluesky Output Inspector'),

    html.Div("Upload ."),
    dcc.Upload(
        id="upload-data",
        children=html.Div(
            ["Drag and drop or click to select a Bluesky output JSON file to upload."]
        ),
        style={
            "width": "100%",
            "height": "60px",
            "lineHeight": "60px",
            "borderWidth": "1px",
            "borderStyle": "dashed",
            "borderRadius": "5px",
            "textAlign": "center",
            "margin": "10px",
        },
        multiple=False
    )
])

