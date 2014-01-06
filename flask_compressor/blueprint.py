# -*- coding: utf-8 -*-

"""
    Blueprints for the Flask-Compressor extension.
"""

from __future__ import unicode_literals, absolute_import, division, \
    print_function
from flask import Blueprint, current_app, abort, Response


blueprint = Blueprint('compressor', __name__)


@blueprint.route('/bundle/<bundle_name>.<extension>')
def render_bundle(bundle_name, extension):
    """ Render the complete bundle content.

    Args:
        bundle_name: name of the bundle to render
        extension: file extension for the bundle
    """
    compressor = current_app.extensions['compressor']

    from . import CompressorException
    try:
        bundle = compressor.get_bundle(bundle_name)
    except CompressorException:
        # bundle not found
        abort(404)

    # check the extension
    if bundle.extension != extension:
        abort(404)

    content = bundle.get_content()
    return Response(content, mimetype=bundle.mimetype)


@blueprint.route('/bundle/<bundle_name>/asset/<int:asset_index>.<extension>')
def render_asset(bundle_name, asset_index, extension):
    """ Render a single source from an asset.

    Args:
        bundle_name: name of the bundle to render
        asset_index: index of the asset in `Bundle.assets`
        extension: file extension for the bundle
    """
    compressor = current_app.extensions['compressor']

    from . import CompressorException
    try:
        bundle = compressor.get_bundle(bundle_name)
    except CompressorException:
        # bundle not found
        abort(404)

    try:
        asset = bundle.assets[asset_index]
    except IndexError:
        # asset not found
        abort(404)

    # check the extension
    if bundle.extension != extension:
        abort(404)

    content = asset.content
    return Response(content, mimetype=bundle.mimetype)
