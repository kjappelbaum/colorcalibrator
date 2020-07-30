# -*- coding: utf-8 -*-
# pylint:disable=line-too-long
"""Setting up the layout and the main callbacks"""
from __future__ import absolute_import, print_function

import json

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output, State
from six.moves import range

from . import dash_reusable_components as drc
from .app import __version__, app
from .utils import (GRAPH_PLACEHOLDER, STORAGE_PLACEHOLDER, calibrate_image, closest_name, flip_image,
                    get_average_color, mirror_image, plot_parity, rotate_image)


def serve_layout():
    """create the layout"""
    layout = html.Div(
        [
            # Banner display
            html.Div(
                [
                    html.H1('Color calibrator',
                            id='header',
                            style={
                                'color': '#111',
                                'font-family': 'sans-serif',
                                'font-size': '64px',
                                'font-weight': 700,
                                'line-height': '64px',
                                'text-align': 'center',
                                'text-transform': ' uppercase'
                            }),
                ],
                className='container',
            ),
            html.Div(
                className='container',
                children=[
                    html.Div([
                        html.Ol([
                            html.H4('Workflow'),
                            html.
                            Li('Upload image, rotate if needed (black batch in the top left corner and the white one in the top right corner).'
                              ),
                            html.Li('Cick on "Run calibration"'),
                            html.Li('Use mouswheel to zoom, select a rectangle with your substance.'),
                            html.Li('Click on "Measure color"')
                        ])
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
                                            'rotate 90° counterclockwise',
                                            id='rotate',
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
                                        html.Label('Calibration algorithm'),
                                        dcc.Dropdown(id='algorithm',
                                                     options=[{
                                                         'label': 'Cheung 2004',
                                                         'value': 'cheung'
                                                     }, {
                                                         'label': 'Finlayson 2015',
                                                         'value': 'finlayson'
                                                     }, {
                                                         'label': 'Vandermonde',
                                                         'value': 'vandermonde'
                                                     }],
                                                     value='finlayson'),
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
                                    html.Div(id='error'),
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
                                    ),
                                ],
                            ),
                        ],
                    ),
                    html.Div([
                        html.
                        P('Upload your image and ensure that the black batch is in the top left corner and the white one in the top right corner (use the flip or rotation where needed).',
                          style={'font-size': '1.5rem'}),
                        html.
                        P("Please make sure that there are no spotlights, this will make the color calibration fail. In case there are issues with spotlights, you will notice this in the partity plot, in which no longer all points fall on a line. If some points don't fall on a line, you can try to exclude those patches from the calibration. If your whitepoint is completely off, you'll get better results if you perform a manual whitepoint correction (e.g. on the third gray patch) before you use this app.",
                          style={'font-size': '1.5rem'}),
                    ]),
                ],
            ),
            html.Div([
                html.Hr(),
                html.Div([
                    'Built with ',
                    html.A('Dash', href='https://plotly.com/dash/'), ' and ',
                    html.A('colour', href='colour-science.org'), '.'
                ]),
                html.Footer(
                    '© Laboratory of Molecular Simulation (LSMO), École polytechnique fédérale de Lausanne (EPFL). Web app version {}'
                    .format(__version__)),
            ]),
        ],
        className='container')
    return layout


app.layout = serve_layout


def init_timestamp(timestamp):
    """Set the timestamp to zero in case the button has not been clicked, otherwise give an int for the ranking"""
    try:
        timestamp = int(timestamp)
    except TypeError:
        timestamp = 0

    return timestamp


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
    [Input('calibration_card', 'value')],
)
def update_exlude_options(calibration_card):
    """Dropdown for exclude is dynamic as function of the selected number of rows and columns"""
    if calibration_card == 'spyder24':
        options = [{'label': str(v), 'value': v} for v in range(0, 23)]
    return options


@app.callback(
    Output('color_res', 'children'),
    [Input('measure-operation', 'n_clicks')],
    [State('interactive-image', 'selectedData'),
     State('div-storage', 'children')],
)
def update_rgb_result(_, selected_data, storage):  # pylint:disable=unused-argument
    """Print the result of the RGB measurement"""

    storage = json.loads(storage)

    try:
        rgb = get_average_color(
            selected_data['range']['x'],
            selected_data['range']['y'],
            drc.b64_to_pil(storage['image_string']),
        )

        return html.Div([
            'Red {}, green {}, blue {}. Closest name from the xkcd survey is {}.'.format(
                int(rgb[0]), int(rgb[1]), int(rgb[2]), closest_name(rgb))
        ])
    except Exception:  # pylint:disable=broad-except
        return html.Div([''])


@app.callback(
    [Output('div-interactive-image', 'children'),
     Output('error', 'children')],
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
        State('calibration_card', 'value'),
        State('exclude_dropdown', 'value'),
        State('algorithm', 'value')
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
        calibration_card,
        excluded,
        algorithm):
    """main callback that updates the image
    """

    # Retrieve information saved in storage, which is a dict containing
    # information about the image and its action stack
    storage = json.loads(storage)
    filename = storage['filename']  # Filename is the name of the image file.

    # # Runs the undo function if the undo button was clicked. Storage stays
    # # the same otherwise.
    # storage = undo_last_action(undo_clicks, storage)
    error_out = html.Div()

    # If a new file was uploaded (new file name changed)
    if new_filename and new_filename != filename:
        # Replace filename

        # Update the storage dict
        storage['filename'] = new_filename

        # Parse the string and convert to pil
        string = content.split(';base64,')[-1]
        #im_pil = drc.b64_to_pil(string)
        storage['image_string'] = string

        del string

    # we want to run colorcalibration as name wasn't changed
    else:
        # https://community.plotly.com/t/input-two-or-more-button-how-to-tell-which-button-is-pressed/5788/29

        run_timestamp = init_timestamp(run_timestamp)
        rotate_timestamp = init_timestamp(rotate_timestamp)
        flip_timestamp = init_timestamp(flip_timestamp)
        mirror_timestamp = init_timestamp(mirror_timestamp)

        # run calibration
        if (run_timestamp > rotate_timestamp and run_timestamp > flip_timestamp and run_timestamp > mirror_timestamp):
            try:
                img, merged_df = calibrate_image(drc.b64_to_numpy(storage['image_string']), calibration_card, excluded,
                                                 algorithm)
                storage['image_string'] = drc.pil_to_b64(img)
                storage['merged_df'] = merged_df.to_json()
                del img
            except Exception as e:  # pylint:disable=broad-except, invalid-name
                error_out = dbc.Alert(
                    'Could not calibrate image, maybe the detection of the color card failed. Try a different image.',
                    color='primary',
                    dismissable=True,
                    style={'font-size': '1.5rem'})
                app.logger.error('Could not calibrate image due to {}'.format(e))  # pylint:disable=logging-format-interpolation
            else:
                app.logger.info('Calibration successfull')

        # mirror the image
        elif (mirror_timestamp > rotate_timestamp and mirror_timestamp > flip_timestamp and
              mirror_timestamp > run_timestamp):
            img = drc.pil_to_b64(mirror_image(drc.b64_to_pil(storage['image_string'])))
            storage['image_string'] = img
            del img
        # flip the image
        elif (flip_timestamp > rotate_timestamp and flip_timestamp > mirror_timestamp and
              flip_timestamp > run_timestamp):
            img = drc.pil_to_b64(flip_image(drc.b64_to_pil(storage['image_string'])))
            storage['image_string'] = img
            del img
        # rotate the image by 90 degree
        elif (rotate_timestamp > flip_timestamp and rotate_timestamp > mirror_timestamp and
              rotate_timestamp > run_timestamp):
            img = drc.pil_to_b64(rotate_image(drc.b64_to_pil(storage['image_string'])))
            storage['image_string'] = img

            del img

    app.logger.info('Returning now')
    if storage['image_string'] == '':  # pylint:disable=no-else-return
        return [
            drc.InteractiveImagePIL(
                image_id='interactive-image',
                image=None,
                enc_format='jpeg',
                display_mode='fixed',
                dragmode='select',
                verbose=False,
            ),
            html.Div(id='div-storage', children=json.dumps(storage), style={'display': 'none'}),
        ], error_out
    else:
        return [
            drc.InteractiveImagePIL(
                image_id='interactive-image',
                image=drc.b64_to_pil(storage['image_string']),
                enc_format='jpeg',
                display_mode='fixed',
                dragmode='select',
                verbose=False,
            ),
            html.Div(id='div-storage', children=json.dumps(storage), style={'display': 'none'}),
        ], error_out
