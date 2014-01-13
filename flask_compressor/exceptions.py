# -*- coding: utf-8 -*-

"""
    Exceptions for the Flask-Compressor extension.

"""

from __future__ import unicode_literals, absolute_import, division, \
    print_function


class CompressorException(Exception):
    """ Base exception for all exceptions raised by the Flask-Compressor
    extension. """
    pass


class CompressorProcessorException(CompressorException):
    """ Base exception for all exceptions raised by processors. """
    pass
