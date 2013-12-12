# -*- coding: utf-8 -*-

"""
    Blueprints for the Flask-Compressor extension.
"""

from __future__ import unicode_literals, absolute_import, division, \
    print_function
from flask import Blueprint, current_app, abort, Response


blueprint = Blueprint('compressor', __name__)


@blueprint.route('/bundle/<bundle_name>')
def render_bundle(bundle_name):
    """ Render the complete bundle content.

    Args:
        bundle_name: name of the bundle to render
    """
    compressor = current_app.extensions['compressor']

    from . import CompressorException
    try:
        bundle = compressor.get_bundle(bundle_name)
    except CompressorException:
        abort(404)

    content = bundle.get_content()
    return Response(content, mimetype=bundle.mimetype)


@blueprint.route('/bundle/<bundle_name>/asset/<int:asset_index>/',
                 defaults={'asset_name': None})
@blueprint.route('/bundle/<bundle_name>/asset/<int:asset_index>/'
                 '<path:asset_name>')
def render_asset(bundle_name, asset_index, asset_name):
    """ Render a single source from an asset.

    Args:
        asset_name: name of the asset to render
        filename: One of the filenames in asset.sources. If the filename is
            found in the asset, returns a 404 error.
    """
    compressor = current_app.extensions['compressor']

    from . import CompressorException
    try:
        bundle = compressor.get_bundle(bundle_name)
    except CompressorException:
        abort(404)

    try:
        asset = bundle.assets[asset_index]
    except IndexError:
        # asset not found
        abort(404)

    # check the asset name
    if asset_name is not None and asset_name != asset.name:
        abort(404)

    content = asset.content
    return Response(content, mimetype=bundle.mimetype)
