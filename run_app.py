# -*- coding: utf-8 -*-
"""Runs the app"""

from colorcalibrator import app, server  # pylint:disable=unused-import

if __name__ == '__main__':

    app.run_server(debug=True, host='0.0.0.0')
