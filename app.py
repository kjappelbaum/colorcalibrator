# -*- coding: utf-8 -*-
"""Runs the app"""
from __future__ import absolute_import

from colorcalibrator import app, server  # pylint:disable=unused-import

if __name__ == '__main__':

    app.run_server(debug=True)
