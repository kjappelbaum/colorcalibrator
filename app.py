# -*- coding: utf-8 -*-
"""Runs the app"""
from __future__ import absolute_import

import os

from colorcalibrator import app, server  # pylint:disable=unused-import

app.server.secret_key = os.urandom(24)

if __name__ == '__main__':
    app.server.secret_key = os.urandom(24)
    app.run_server(debug=True)
