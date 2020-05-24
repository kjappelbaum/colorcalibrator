# -*- coding: utf-8 -*-
# pylint:disable=logging-format-interpolation
"""Calling the layout of the app as a function of the path"""
from __future__ import absolute_import

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from flask import session

from . import layout
from ._version import get_versions
from .app import app, server

__version__ = get_versions()['version']
del get_versions

app.layout = html.Div([dcc.Location(id='url', refresh=False), html.Div(id='page-content')])


@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')],
)
def display_page(pathname):
    """Display the layout as function of the url"""
    session.clear()

    app.logger.info('Pathname is {}'.format(pathname))
    if pathname == '/':
        return layout.serve_layout()

    return layout.serve_layout()


if __name__ == '__main__':
    app.run_server(debug=True)
