# -*- coding: utf-8 -*-

"""
    Jinja2 helpers to use the Flask-Compressor features in templates.
"""

from __future__ import unicode_literals, absolute_import, division, \
    print_function
from jinja2 import Markup
from flask import current_app


def compressor(bundle_name, inline=True):
    """ Returns the processed content of a bundle.

            {{ compressor('bundle_name') }}

        Args:
            bundle_name: the name of the bundle
            inline: If `True`, the bundle content is added directly in the
                output. If `False`, the bundle content is linked to a
                downloadable ressource. (default: `True`)

        Returns:
            the processed content of the bundle
    """
    compressor_ext = current_app.extensions['compressor']
    bundle = compressor_ext.get_bundle(bundle_name)

    if inline:
        content = bundle.get_inline_content(concatenate=current_app.debug)
    else:
        if current_app.debug:
            content = bundle.get_linked_contents()
        else:
            content = bundle.get_linked_content()

    # mark the string as safe, so HTML tags won't be escaped
    return Markup(content)
