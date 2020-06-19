# -*- coding: utf-8 -*-
# pylint:disable=logging-format-interpolation
"""Calling the layout of the app as a function of the path"""
from __future__ import absolute_import

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from flask import session
from PIL import Image

from . import layout
from .app import app, server
from .dash_reusable_components import pil_to_b64

app.layout = html.Div([dcc.Location(id='url', refresh=False), html.Div(id='page-content')])


@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')],
)
def display_page(pathname):
    """Display the layout as function of the url"""
    session.clear()
    IM_PLACEHOLDER = pil_to_b64(Image.open('./images/default.jpg'))
    session['image_string'] = IM_PLACEHOLDER
    del IM_PLACEHOLDER

    return layout.serve_layout()


if __name__ == '__main__':
    app.run_server(debug=True)
