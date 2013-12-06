# -*- coding: utf-8 -*-

"""
    Jinja2 helpers to use the Flask-Compressor features in templates.
"""

from __future__ import unicode_literals, absolute_import, division, \
    print_function
from jinja2 import Markup
from flask import current_app


def compressor(asset_name, **extra):
    """ Returns the processed content of an asset.

            {{ compressor('asset_name') }}

        Args:
            asset_name: the name of the asset
            extra: extra parameters passed to :func:`Asset.get_content`

        Returns:
            the processed content of an asset
    """
    compressor_ext = current_app.extensions['compressor']
    asset = compressor_ext.get_asset(asset_name)
    return Markup(asset.get_content(**extra))
