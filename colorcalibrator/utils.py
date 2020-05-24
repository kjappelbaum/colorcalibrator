# -*- coding: utf-8 -*-
"""Some utility functions"""
from __future__ import absolute_import, print_function

import json
import tempfile

import cv2
import dash_core_components as dcc
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from PIL import Image, ImageOps
from plantcv import plantcv as pcv
from plotly.subplots import make_subplots
from six.moves import map, range

# [filename, image_signature, action_stack]
STORAGE_PLACEHOLDER = json.dumps({'filename': None, 'image_signature': None, 'action_stack': []})


GRAPH_PLACEHOLDER = dcc.Graph(id='interactive-image', style={'height': '80vh'})

TARGET_IMG_SPYDER24 = np.load('./data/target_img.npy')
TARGET_MASK_SPYDER24 = np.load('./data/target_mask.npy')


def pil_to_array(pil):
    return np.asarray(pil)

def array_to_pil(array):
    return Image.fromarray(array)

def calibrate_image(image, nrows, ncols, card, excluded=None, radius=20):  # pylint:disable=too-many-locals
    """Use plantcv to automatically calibrate the image"""
    if excluded is None:
        excluded = []
    opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    _, start, space = pcv.transform.find_color_card(rgb_img=opencv_image)

    source_mask = pcv.transform.create_color_card_mask(
        opencv_image,
        radius=radius,
        start_coord=start,
        spacing=space,
        nrows=nrows,
        ncols=ncols,
        exclude=excluded,
    )

    if card == 'spyder24':
        target_img = TARGET_IMG_SPYDER24
        target_mask = TARGET_MASK_SPYDER24
    else:
        raise NotImplementedError

    with tempfile.TemporaryDirectory() as dirpath:
        tm, sm, _, corrected_img = pcv.transform.correct_color(  #pylint:disable=invalid-name
            target_img=target_img,
            target_mask=target_mask,
            source_img=opencv_image,
            source_mask=source_mask,
            output_directory=dirpath,
        )

    img = cv2.cvtColor(corrected_img, cv2.COLOR_BGR2RGB)
    im_pil = Image.fromarray(img)

    df_sm = pd.DataFrame(sm, columns=['label', 'r', 'g', 'b'])
    df_tm = pd.DataFrame(tm, columns=['label', 'r', 'g', 'b'])

    merged_df = pd.merge(df_sm, df_tm, left_on='label', right_on='label', suffixes=('_source', '_target'))
    merged_df['label'] = merged_df['label'] / 10

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

    return fig


def show_histogram(image):
    """Show the RGB channels as histogram"""

    def hg_trace(name, color, hg):  # pylint:disable=invalid-name
        line = go.Scatter(
            x=list(range(0, 256)),
            y=hg,
            name=name,
            line=dict(color=(color)),
            mode='lines',
            showlegend=False,
        )
        fill = go.Scatter(
            x=list(range(0, 256)),
            y=hg,
            mode='fill',
            name=name,
            line=dict(color=(color)),
            fill='tozeroy',
            hoverinfo='none',
        )

        return line, fill

    hg = image.histogram()  # pylint:disable=invalid-name

    if image.mode == 'RGBA':
        rhg = hg[0:256]
        ghg = hg[256:512]
        bhg = hg[512:768]
        ahg = hg[768:]

        data = [
            *hg_trace('Red', '#FF4136', rhg),
            *hg_trace('Green', '#2ECC40', ghg),
            *hg_trace('Blue', '#0074D9', bhg),
            *hg_trace('Alpha', 'gray', ahg),
        ]

        title = 'RGBA Histogram'

    elif image.mode == 'RGB':
        # Returns a 768 member array with counts of R, G, B values
        rhg = hg[0:256]
        ghg = hg[256:512]
        bhg = hg[512:768]

        data = [
            *hg_trace('Red', '#FF4136', rhg),
            *hg_trace('Green', '#2ECC40', ghg),
            *hg_trace('Blue', '#0074D9', bhg),
        ]

        title = 'RGB Histogram'

    else:
        data = [*hg_trace('Gray', 'gray', hg)]

        title = 'Grayscale Histogram'

    layout = go.Layout(
        title=title,
        margin=go.Margin(l=35, r=35),
        legend=dict(x=0, y=1.15, orientation='h'),
    )

    return go.Figure(data=data, layout=layout)


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
