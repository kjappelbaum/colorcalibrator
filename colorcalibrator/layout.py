# -*- coding: utf-8 -*-
# pylint:disable=line-too-long
"""Setting up the layout and the main callbacks"""
from __future__ import absolute_import, print_function

import json
import uuid

import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output, State
from flask import session
from six.moves import range

from . import dash_reusable_components as drc
from .app import app
from .utils import (GRAPH_PLACEHOLDER, STORAGE_PLACEHOLDER, calibrate_image, flip_image, get_average_color,
                    mirror_image, plot_parity, rotate_image)

SESSION_ID = str(uuid.uuid4())


def serve_layout():
    """create the layout"""
    layout = html.Div([
        # Session ID
        html.Div(SESSION_ID, id='session-id', style={'display': 'none'}),
        # Banner display
        html.Div(
            [
                html.H2('Color calibration app', id='title'),
            ],
            className='banner',
        ),
        html.Div(
            className='container',
            children=[
                html.Div([
                    html.
                    P('Upload your image and ensure that the black batch is in the top left corner (flip and rotation buttons will be added in the next releaese).'
                     ),
                    html.
                    P("Please make sure that there are no spotlights, this will make the color calibration fail. In case there are issues with spotlights, you will notice this in the partity plot, in which no longer all points fall on a line. If some points don't fall on a line, you can exclude those patches from the calibration."
                     ),
                    html.P('For now, it is limited to .jpg (which is a constrain to make debugging easier'),
                ]),
                html.Div(
                    className='row',
                    children=[
                        html.Div(
                            className='five columns',
                            children=[
                                drc.Card([
                                    dcc.Upload(
                                        id='upload-image',
                                        children=[
                                            'Drag and Drop or ',
                                            html.A('Select an Image'),
                                        ],
                                        style={
                                            'width': '100%',
                                            'height': '50px',
                                            'lineHeight': '50px',
                                            'borderWidth': '1px',
                                            'borderStyle': 'dashed',
                                            'borderRadius': '5px',
                                            'textAlign': 'center',
                                        },
                                        accept='image/*',
                                    ),
                                ]),
                                drc.Card([
                                    html.Button(
                                        'rotate clockwise by 90°',
                                        id='rotate90',
                                        style={
                                            'margin-right': '10px',
                                            'margin-top': '5px',
                                        },
                                    ),
                                    html.Button(
                                        'flip vertically',
                                        id='flip',
                                        style={
                                            'margin-right': '10px',
                                            'margin-top': '5px',
                                        },
                                    ),
                                    html.Button(
                                        'flip horizontally',
                                        id='mirror',
                                        style={
                                            'margin-right': '10px',
                                            'margin-top': '5px',
                                        },
                                    ),
                                ]),
                                drc.Card([
                                    html.Label('Calibration card'),
                                    dcc.Dropdown(
                                        id='calibration_card',
                                        options=[
                                            {
                                                'label': 'Spyderchecker 24',
                                                'value': 'spyder24',
                                            },
                                        ],
                                        value='spyder24',
                                    ),
                                    html.Label('Number of visible rows'),
                                    dcc.Dropdown(
                                        id='rows',
                                        options=[
                                            {
                                                'label': '4',
                                                'value': 4,
                                            },
                                            {
                                                'label': '6',
                                                'value': 6,
                                            },
                                        ],
                                        value=4,
                                    ),
                                    html.Label('Number of visible columns'),
                                    dcc.Dropdown(
                                        id='columns',
                                        options=[
                                            {
                                                'label': '4',
                                                'value': 4,
                                            },
                                            {
                                                'label': '6',
                                                'value': 6,
                                            },
                                        ],
                                        value=6,
                                    ),
                                    html.Label(
                                        'Patches to exclude (you can get the numbers from the hover in the parity plot)'
                                    ),
                                    dcc.Dropdown(id='exclude_dropdown', multi=True),
                                    html.Button(
                                        'Run Calibration',
                                        id='button-run-operation',
                                        style={
                                            'margin-right': '10px',
                                            'margin-top': '5px',
                                        },
                                    ),
                                    html.Button(
                                        'Measure Color',
                                        id='measure-operation',
                                        style={
                                            'margin-right': '10px',
                                            'margin-top': '5px',
                                        },
                                    ),
                                ]),
                                drc.Card([
                                    html.P('The average color in the selected region is'),
                                    html.Div(id='color_res'),
                                ]),
                                drc.Card([
                                    html.H4('Calibration quality'),
                                    html.
                                    P('Ideally, all points fall on the diagonal. If this is not the case, use the hoover tool to find the patches for which it went wrong.'
                                     ),
                                    dcc.Graph(
                                        id='graph-parity',
                                        config={'displayModeBar': False},
                                    ),
                                ]),
                            ],
                        ),
                        html.Div(
                            className='seven columns',
                            style={'float': 'right'},
                            children=[
                                # The Interactive Image Div contains the dcc Graph
                                # showing the image, as well as the hidden div storing
                                # the true image
                                html.Div(
                                    id='div-interactive-image',
                                    children=[
                                        GRAPH_PLACEHOLDER,
                                        html.Div(
                                            id='div-storage',
                                            children=STORAGE_PLACEHOLDER,
                                            style={'display': 'none'},
                                        ),
                                    ],
                                )
                            ],
                        ),
                    ],
                ),
            ],
        ),
        html.Div(
            [
                html.Hr(),
                html.Div('Built with Dash and plantcv.'),
                html.Footer(
                    '© Laboratory of Molecular Simulation (LSMO), École polytechnique fédérale de Lausanne (EPFL)'),
            ],
            className='container',
        ),
    ])
    return layout


app.layout = serve_layout


@app.callback(
    Output('graph-parity', 'figure'),
    [Input('interactive-image', 'figure')],
    [State('div-storage', 'children')],
)
def update_histogram(_, storage):
    """Check if the parity plot can be updated when the image changes"""
    storage = json.loads(storage)
    try:
        df = json.loads(storage['merged_df'])  # pylint:disable=invalid-name
        if df is None:
            raise Exception('Will return empty df')

        merged_df = pd.DataFrame.from_dict(df)
    except Exception:  # pylint:disable=broad-except
        merged_df = pd.DataFrame([{
            'r_source': 1,
            'g_source': 1,
            'b_source': 1,
            'r_target': 1,
            'g_target': 1,
            'b_target': 1,
            'label': 'dummy',
        }])

    return plot_parity(merged_df)


@app.callback(
    Output('exclude_dropdown', 'options'),
    [Input('columns', 'value'), Input('rows', 'value')],
)
def update_exlude_options(rows, columns):
    """Dropdown for exclude is dynamic as function of the selected number of rows and columns"""
    total_columns = rows * columns
    options = [{'label': str(v), 'value': v} for v in range(1, total_columns)]
    return options


@app.callback(
    Output('color_res', 'children'),
    [Input('measure-operation', 'n_clicks')],
    [State('interactive-image', 'selectedData'),
     State('div-storage', 'children')],
)
def update_rgb_result(_, selected_data, storage):  # pylint:disable=unused-argument
    """Print the result of the RGB measurement"""
    rgb = get_average_color(
        selected_data['range']['x'],
        selected_data['range']['y'],
        session.get('image_pil'),
    )
    return html.Div(['Red {}, green {}, blue {}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))])


@app.callback(
    Output('div-interactive-image', 'children'),
    [
        Input('upload-image', 'contents'),
        Input('button-run-operation', 'n_clicks_timestamp'),
        Input('rotate', 'n_clicks_timestamp'),
        Input('flip', 'n_clicks_timestamp'),
        Input('mirror', 'n_clicks_timestamp'),
    ],
    [
        State('interactive-image', 'selectedData'),
        State('upload-image', 'filename'),
        State('div-storage', 'children'),
        State('session-id', 'children'),
        State('calibration_card', 'value'),
        State('columns', 'value'),
        State('rows', 'value'),
        State('exclude_dropdown', 'value'),
    ],
)
def update_graph_interactive_image(  # pylint:disable=too-many-arguments
    content,
    run_timestamp,
    rotate_timestamp,
    flip_timestamp,
    mirror_timestamp,
    selected_data,  # pylint:disable=unused-argument
    new_filename,
    storage,
    session_id,  # pylint:disable=unused-argument
    calibration_card,
    columns,
    rows,
    excluded,
):
    """main callback that updates the image
    """

    # Retrieve information saved in storage, which is a dict containing
    # information about the image and its action stack
    storage = json.loads(storage)
    filename = storage['filename']  # Filename is the name of the image file.

    # # Runs the undo function if the undo button was clicked. Storage stays
    # # the same otherwise.
    # storage = undo_last_action(undo_clicks, storage)

    # If a new file was uploaded (new file name changed)
    if new_filename and new_filename != filename:
        # Replace filename

        print((filename, 'replaced by', new_filename))

        # Update the storage dict
        storage['filename'] = new_filename

        # Parse the string and convert to pil
        string = content.split(';base64,')[-1]
        im_pil = drc.b64_to_pil(string)

        session['image_string'] = string
        session['filename'] = new_filename
        session['image_pil'] = im_pil

        # Resets the action stack
        storage['action_stack'] = []
        storage['merged_df'] = None

    # we want to run colorcalibration as name wasn't changed
    else:
        # https://community.plotly.com/t/input-two-or-more-button-how-to-tell-which-button-is-pressed/5788/29
        run_timestamp = int(run_timestamp)
        rotate_timestamp = int(rotate_timestamp)
        flip_timestamp = int(flip_timestamp)
        mirror_timestamp = int(mirror_timestamp)

        # run calibration
        if (run_timestamp > rotate_timestamp and run_timestamp > flip_timestamp and run_timestamp > mirror_timestamp):
            img, merged_df = calibrate_image(session['image_pil'], rows, columns, calibration_card, excluded)
            session['image_pil'] = img
            storage['merged_df'] = merged_df.to_json()

        # mirror the image
        elif (mirror_timestamp > rotate_timestamp and mirror_timestamp > flip_timestamp and
              mirror_timestamp > run_timestamp):
            img = mirror_image(session['image_pil'])
            session['image_pil'] = img

        # flip the image
        elif (flip_timestamp > rotate_timestamp and flip_timestamp > mirror_timestamp and
              flip_timestamp > run_timestamp):
            img = flip_image(session['image_pil'])
            session['image_pil'] = img

        # rotate the image by 90 degree
        elif (rotate_timestamp > flip_timestamp and rotate_timestamp > mirror_timestamp and
              rotate_timestamp > run_timestamp):
            img = rotate_image(session['image_pil'])
            session['image_pil'] = img

    return [
        drc.InteractiveImagePIL(
            image_id='interactive-image',
            image=session.get('image_pil'),
            enc_format='jpeg',
            display_mode='fixed',
            dragmode='select',
            verbose=True,
        ),
        html.Div(id='div-storage', children=json.dumps(storage), style={'display': 'none'}),
    ]
