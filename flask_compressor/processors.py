# -*- coding: utf-8 -*-

"""
    Default processors for the Flask-Compressor extension.
"""

from __future__ import unicode_literals, absolute_import, division, \
    print_function
import subprocess
from flask import current_app
from .exceptions import CompressorProcessorException


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


def lesscss(content):
    """ Compile your LESS code to CSS.

    Use the `lessc` command to compile LESS code to regular CSS content. The
    `lessc` command is not installed with Flask-Compressor, you need to install
    it separatly. Go to the `homepage of LESS <http://lesscss.org>`_ for
    installation instructions.

    If you already have `node.js <http://nodejs.org>`_ and `npm
    <https://npmjs.org>`_ installed, you can install `lessc` with this command
    line:

        npm install -g less

    Args:
        content: your LESS content

    Returns:
        the LESS content compiled to regular CSS content
    """
    try:
        process = subprocess.Popen(
            ['lessc', '--no-color', '-'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except OSError as e:
        # error when invoking the lessc command
        raise CompressorProcessorException("Error when invoking the 'lessc' "
                                           "command: " + e.strerror)

    stdout, stderr = process.communicate(input=content)

    if process.wait() != 0:
        raise CompressorProcessorException("Error with 'lesscss': " + stderr)

    return stdout


def jsmin(content):
    """ Minify your JavaScript code.

    Use `jsmin <https://pypi.python.org/pypi/jsmin>`_ to compress JavaScript.
    You must manually install jsmin if you want to use this processor.

    Args:
        content: your JavaScript code

    Returns:
        the minified version of your JavaScript code, or the original content
        if the Flask application is in Debug mode

    Raises:
        CompressorProcessorException: if jsmin is not installed.
    """
    try:
        from jsmin import jsmin as jsmin_processor
    except ImportError:
        raise CompressorProcessorException("'jsmin' is not installed. Please"
                                           " install it if you want to use "
                                           "the 'jsmin' processor.")

    if current_app.debug is True:
        # do not minify
        return content

    return jsmin_processor(content)


# processors that should be registered for every app
DEFAULT_PROCESSORS = [cssmin, lesscss, jsmin]
