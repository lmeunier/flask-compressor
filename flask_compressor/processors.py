# -*- coding: utf-8 -*-

"""
    Default processors for the Flask-Compressor extension.
"""

from __future__ import unicode_literals, absolute_import, division, \
    print_function
from flask import current_app
from . import CompressorException


class CompressorProcessorException(CompressorException):
    """ Base exception for all exceptions raised by processors. """
    pass


def cssmin(content):
    """ Minify your CSS assets.

    Use `cssmin <https://pypi.python.org/pypi/cssmin>`_ (A Python port of the
    YUI CSS compression algorithm) to compress CSS.  You must manually install
    cssmin if you want to use this processor.

    Args:
        content: your CSS content

    Returns:
        the minified version of your CSS content, or the original content if
        the Flask application is in Debug mode

    Raises:
        CompressorProcessorException: if cssmin is not installed.
    """
    try:
        from cssmin import cssmin as cssmin_processor
    except ImportError:
        raise CompressorProcessorException("'cssmin' is not installed. Please"
                                           " install it if you want to use "
                                           "the 'cssmin' processor.")

    if current_app.debug is True:
        # do not minify
        return content

    return cssmin_processor(content)


# processors that should be registered for every app
DEFAULT_PROCESSORS = [cssmin]
