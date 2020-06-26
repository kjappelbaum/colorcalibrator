# -*- coding: utf-8 -*-
"""Some utility functions"""
from __future__ import absolute_import, print_function

import json

import colour
import dash_core_components as dcc
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from colour_checker_detection import detect_colour_checkers_segmentation
from PIL import Image, ImageOps
from plotly.subplots import make_subplots
from six.moves import map, range

# [filename, image_signature, action_stack]
STORAGE_PLACEHOLDER = json.dumps({'filename': None, 'image_signature': None, 'action_stack': [], 'image_string': ''})

GRAPH_PLACEHOLDER = dcc.Graph(id='interactive-image', style={'height': '80vh'})

# https://www.datacolor.com/wp-content/uploads/2018/01/SpyderCheckr_Color_Data_V2.pdf
TARGET_SPYDER24 = np.array([
    [43, 41, 43],  # 6E
    [80, 80, 78],  # 5E
    [122, 118, 116],  # 4E
    [161, 157, 154],  # 3E
    [202, 198, 195],  # 2E
    [249, 242, 238],  # 1E
    [25, 55, 135],  # 6F
    [57, 146, 64],  # 5F
    [186, 26, 51],  # 4F
    [245, 205, 0],  # 3F
    [192, 75, 145],  # 2F
    [0, 127, 159],  # 1F
    [238, 158, 25],  # 6G
    [157, 188, 54],  # 5G
    [83, 58, 106],  # 4G
    [195, 79, 95],  # 3G
    [58, 88, 159],  # 2G
    [222, 118, 32],  # 1G
    [112, 76, 60],  # 6H
    [197, 145, 125],  # 5H
    [87, 120, 155],  # 4H
    [82, 106, 60],  # 3H
    [126, 125, 174],  # 2H
    [98, 187, 166]  # 1H
]) / 255


def pil_to_array(pil):
    return np.asarray(pil)


def array_to_pil(array):
    return Image.fromarray(array)


def calibrate_image(image, card, excluded=None, algorithm='finlayson'):  # pylint:disable=too-many-locals, too-many-arguments
    """Use colour to automatically calibrate the image"""
    if card == 'spyder24':
        reference = TARGET_SPYDER24
    else:
        raise NotImplementedError

    linear_image = colour.cctf_decoding(image)  # decode to linear RGB

    try:
        swatches = detect_colour_checkers_segmentation(linear_image)[0][::-1]  # black first
    except Exception as e:  # pylint:disable=invalid-name
        raise ValueError(e)

    # neutralization (white balance) based on # 3E
    im = linear_image / swatches[3]  # pylint:disable=invalid-name
    im *= colour.cctf_decoding(reference[3])  # pylint:disable=invalid-name

    swatches_wb = detect_colour_checkers_segmentation(im)[0][::-1]  # black first

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
        swatches_wb = np.delete(swatches_wb, excluded, axis=0)
        reference = np.delete(reference, excluded, axis=0)

    im_cal_linear = colour.colour_correction(im, swatches_wb, colour.cctf_decoding(reference), method=algorithm_)

    im_cal_non_linear = colour.cctf_encoding(im_cal_linear)
    im_pil = Image.fromarray((np.clip(im_cal_non_linear, 0, 1) * 255).astype(np.uint8))
    swatches_calibrated = detect_colour_checkers_segmentation(im_cal_non_linear)[0][::-1]

    label = np.arange(0, len(swatches_wb))
    target_matrix = np.zeros((len(label), 4))
    measured_matrix = np.zeros((len(label), 4))

    target_matrix[:, 0] = label
    measured_matrix[:, 0] = label

    measured_matrix[:, 1:] = swatches_calibrated
    target_matrix[:, 1:] = reference

    df_sm = pd.DataFrame(measured_matrix, columns=['label', 'r', 'g', 'b'])
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
