import dash_core_components as dcc
import dash_html_components as html

def get_upload_box():
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

def define_callbacks(app):

    # @app.callback(
    #     Output("", ""),
    #     [Input("upload-data", "filename"), Input("upload-data", "contents")],
    # )
    # def update_output(uploaded_filenames, uploaded_file_contents):
    #     """Save uploaded files and regenerate the file list."""

    #     if uploaded_filenames is not None and uploaded_file_contents is not None:
    #         data = json.load(uploaded_file_contents)

    pass
