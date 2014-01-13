# -*- coding: utf-8 -*-

"""
    Blueprints for the Flask-Compressor extension.
"""

from __future__ import unicode_literals, absolute_import, division, \
    print_function
from flask import Blueprint, current_app, abort, Response
from .exceptions import CompressorException


blueprint = Blueprint('compressor', __name__)


@blueprint.route('/bundle/<bundle_name>_v<bundle_hash>.<bundle_extension>')
def render_bundle(bundle_name, bundle_hash, bundle_extension):
    """ Render the complete bundle content.

    Args:
        bundle_name: name of the bundle to render
        bundle_hash: calculated hash from bundle content
        bundle_extension: file extension for the bundle
    """
    compressor = current_app.extensions['compressor']

    try:
        bundle = compressor.get_bundle(bundle_name)
    except CompressorException:
        # bundle not found
        abort(404)

    # check bundle hash
    if bundle.hash != bundle_hash:
        abort(404)

    # check the extension
    if bundle.extension != bundle_extension:
        abort(404)

    content = bundle.get_content()
    return Response(content, mimetype=bundle.mimetype)


@blueprint.route('/bundle/<bundle_name>/asset/<int:asset_index>_v<asset_hash>.<bundle_extension>')
def render_asset(bundle_name, bundle_extension, asset_index, asset_hash):
    """ Render a single source from an asset.

    Args:
        bundle_name: name of the bundle to render
        bundle_extension: file extension for the bundle
        asset_index: index of the asset in `Bundle.assets`
        asset_hash: calculated hash from asset content
    """
    compressor = current_app.extensions['compressor']

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

    # check bundle hash
    if asset.hash != asset_hash:
        abort(404)

    # check the extension
    if bundle.extension != bundle_extension:
        abort(404)

    content = asset.content
    return Response(content, mimetype=bundle.mimetype)
