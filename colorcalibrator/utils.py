# -*- coding: utf-8 -*-
"""Some utility functions"""
from __future__ import absolute_import, print_function

import json

import colour
import cv2
import dash_core_components as dcc
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from PIL import Image, ImageOps
from plantcv import plantcv as pcv
from plotly.subplots import make_subplots
from six.moves import map, range

pcv.params.debug = None

# [filename, image_signature, action_stack]
STORAGE_PLACEHOLDER = json.dumps({'filename': None, 'image_signature': None, 'action_stack': []})

GRAPH_PLACEHOLDER = dcc.Graph(id='interactive-image', style={'height': '80vh'})

TARGET_SPYDER24 = np.array([[43, 41, 43], [80, 80, 78], [122, 118, 116], [161, 157, 14], [202, 198, 195],
                            [249, 242, 238], [25, 55, 135], [57, 146, 64], [186, 26, 51], [245, 205, 0], [192, 75, 145],
                            [0, 127, 159], [238, 158, 25], [157, 188, 54], [83, 58, 106], [195, 79, 95], [58, 88, 159],
                            [222, 118, 32], [112, 76, 60], [197, 145, 125], [87, 120, 155], [82, 106, 60],
                            [126, 125, 174], [98, 187, 166]])


def pil_to_array(pil):
    return np.asarray(pil)


def array_to_pil(array):
    return Image.fromarray(array)


def calibrate_image(image, nrows, ncols, card, excluded=None, algorithm='finlayson', radius=20):  # pylint:disable=too-many-locals, too-many-arguments
    """Use plantcv to automatically calibrate the image"""

    opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    _, start, space = pcv.transform.find_color_card(rgb_img=opencv_image)
    del image
    source_mask = pcv.transform.create_color_card_mask(
        opencv_image,
        radius=radius,
        start_coord=start,
        spacing=space,
        nrows=nrows,
        ncols=ncols,
    )
    _, source_matrix = pcv.transform.get_color_matrix(opencv_image, source_mask)

    if card == 'spyder24':
        reference = TARGET_SPYDER24
    else:
        raise NotImplementedError

    corrected_img = opencv_image.copy()

    if algorithm == 'finlayson':
        algorithm_ = 'Finlayson 2015'
    elif algorithm == 'cheung':
        algorithm_ = 'Cheung 2004'
    elif algorithm == 'vandermonde':
        algorithm_ = 'Vandermonde'
    else:
        # log this case
        algorithm_ = 'Finlayson 2015'

    if isinstance(excluded, list):
        source_matrix = np.delete(source_matrix, excluded, axis=0)
        reference = np.delete(reference, excluded, axis=0)

    corrected_img[:] = colour.colour_correction(opencv_image[:], source_matrix[:, 1:], reference, algorithm_)
    del opencv_image
    _, corrected_matrix = pcv.transform.get_color_matrix(corrected_img, source_mask)
    del source_mask
    target_matrix = corrected_matrix.copy()
    target_matrix[:, 1:] = TARGET_SPYDER24

    label = np.arange(0, len(target_matrix))
    corrected_matrix[:, 0] = label
    target_matrix[:, 0] = label

    img = cv2.cvtColor(corrected_img, cv2.COLOR_BGR2RGB)
    im_pil = Image.fromarray(img)
    del img

    df_sm = pd.DataFrame(corrected_matrix, columns=['label', 'r', 'g', 'b'])
    df_tm = pd.DataFrame(target_matrix, columns=['label', 'r', 'g', 'b'])

    merged_df = pd.merge(df_sm, df_tm, left_on='label', right_on='label', suffixes=('_source', '_target'))
    merged_df['label'] = merged_df['label']

    return im_pil, merged_df


def plot_parity(merged_df):
    """Make a partiy plot indicating the quality of the calibration"""
    fig = make_subplots(rows=1, cols=3)

    fig.add_trace(
        go.Scatter(
            x=merged_df['r_source'],
            y=merged_df['r_target'],
            hovertext=merged_df['label'],
            mode='markers',
            marker={'color': 'red'},
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=merged_df['g_source'],
            y=merged_df['g_target'],
            hovertext=merged_df['label'],
            mode='markers',
            marker={'color': 'green'},
        ),
        row=1,
        col=2,
    )

    fig.add_trace(
        go.Scatter(
            x=merged_df['b_source'],
            y=merged_df['b_target'],
            hovertext=merged_df['label'],
            mode='markers',
            marker={'color': 'blue'},
        ),
        row=1,
        col=3,
    )

    fig.update_layout(showlegend=False)
    fig['layout'].update(margin=dict(l=0, r=0, b=0, t=0))

    return fig


def get_average_color(x, y, image):  # pylint:disable=too-many-locals, invalid-name
    """ Returns a 3-tuple containing the RGB value of the average color of the
    given square bounded area of length = n whose origin (top left corner)
    is (x, y) in the given image"""

    height = image.size[1]

    lower, upper = list(map(int, y))
    left, right = list(map(int, x))
    # Adjust height difference

    upper = height - upper
    lower = height - lower

    x_0 = min([left, right])
    x_1 = max([left, right])

    y_0 = min([lower, upper])
    y_1 = max([lower, upper])

    # ugly because numpy somehow flips the axis
    reds = 0
    greens = 0
    blues = 0
    counter = 0

    for i in range(x_0, x_1):
        for j in range(y_0, y_1):
            red, green, blue = image.getpixel((i, j))
            reds += red
            greens += green
            blues += blue

            counter += 1

    return reds / counter, greens / counter, blues / counter


def rotate_image(image):
    return image.rotate(90)


def flip_image(image):
    return ImageOps.flip(image)


def mirror_image(image):
    return ImageOps.mirror(image)
