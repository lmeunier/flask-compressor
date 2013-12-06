# -*- coding: utf-8 -*-

"""
    Blueprints for the Flask-Compressor extension.
"""

from __future__ import unicode_literals, absolute_import, division, \
    print_function
from flask import Blueprint, current_app, abort, Response


compressor_blueprint = Blueprint('compressor', __name__)


@compressor_blueprint.route('/asset/<asset_name>')
def render_asset(asset_name):
    """ Render the complete asset content.

    Args:
        asset_name: name of the asset to render
    """
    compressor = current_app.extensions['compressor']
    asset = compressor.get_asset(asset_name)
    content = asset.get_content()
    return Response(content, mimetype=asset.mimetype)


@compressor_blueprint.route('/asset/<asset_name>/sources/<path:filename>')
def render_asset_source(asset_name, filename):
    """ Render a single source from an asset.

    Args:
        asset_name: name of the asset to render
        filename: One of the filenames in asset.sources. If the filename is
            found in the asset, returns a 404 error.
    """
    compressor = current_app.extensions['compressor']
    asset = compressor.get_asset(asset_name)

    if not filename in asset.sources:
        abort(404)

    content = asset.load_contents_from_file(filename)
    content = asset.apply_processors(content)
    return Response(content, mimetype=asset.mimetype)


@compressor_blueprint.route('/asset/<asset_name>/contents.css')
def render_asset_contents(asset_name):
    """ Render the content from an asset.

    Args:
        asset_name: name of the asset to render
    """
    compressor = current_app.extensions['compressor']
    asset = compressor.get_asset(asset_name)

    content = asset.contents
    content = asset.apply_processors(content)
    return Response(content, mimetype=asset.mimetype)
