import dash_html_components as html

def get_emissions_graph(summarized_fires):
    if not summarized_fires:
        return html.Div("")

    return html.Div("TODO: create emissions graph")


def get_plumerise_graph(summarized_fires):
    if not summarized_fires:
        return html.Div("")

    return html.Div("TODO: create plumerise graph")
