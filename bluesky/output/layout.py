import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

from . import analysis

def get_upload_box_layout():
    return dcc.Upload(
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

def get_navbar():
    return dbc.NavbarSimple(
        children=[
            html.Div("", id="run-id"),
            dbc.NavItem(get_upload_box_layout()),
            # dbc.DropdownMenu(
            #     nav=True,
            #     in_navbar=True,
            #     label="Menu",
            #     children=[
            #         dbc.DropdownMenuItem("Entry 1")
            #     ]
            # )
        ],
        brand="BlueSky Output Visualizer",
        brand_href="#",
        sticky="top",
        fluid=True
    )

def get_body():
    return dbc.Container(
        [
            dbc.Row([
                dbc.Col([html.Div(id="fires-map-container")], lg=5),
                dbc.Col([html.Div(id='fires-table-container')], lg=7)
            ]),
            dbc.Row([
                dbc.Col([html.Div(id='fuelbeds-container')], lg=4),
                dbc.Col([html.Div(id='consumption-container')], lg=4),
                dbc.Col([html.Div(id='emissions-container')], lg=4),
            ]),
            dbc.Row([
                dbc.Col([html.Div(id='plumerise-container')], lg=6)
            ])
        ],
        fluid=True,
        className="mt-4",
    )

def get_layout(initial_summarized_fires_by_id):
    init_state = analysis.SummarizedFiresEncoder().encode(
        initial_summarized_fires_by_id)
    return html.Div([
        dcc.Input(id='summarized-fires-by-id-state', type='text',
            value=init_state, style={'display': 'none'}),
        get_navbar(),
        get_body()
    ])
