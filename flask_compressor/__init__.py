# -*- coding: utf-8 -*-

"""
    Flask-Compressor
    ~~~~~~~~~~~~~~~~

    Flask-Compressor is a Flask extension that helps you to concatenate and
    minify your Javascript and CSS files.

"""

from __future__ import unicode_literals, absolute_import, division, \
    print_function
import os
from flask import current_app
from .templating import compressor as compressor_template_helper


class CompressorException(Exception):
    """ Base exception for all exceptions raised by the Flask-Compressor
    extension. """
    pass


class Compressor(object):
    """
        The Flask extension object used by Flask-Compressor.
    """

    def __init__(self, app=None):
        """ Initializes the Compressor extension.

        Args:
            app: your Flask application or `None` if you use :meth:`init_app`
        """
        self._assets = {}
        self._processors = {}

        self.app = app
        if app is not None:
            self.init_app(app)

        self.register_default_processors()

    def init_app(self, app):
        """ Initilize an application.

        Used to initilize an application, useful to instantiate a Compressor
        object without requiring an app object.

        Args:
            app: your Flask application
        """
        # add `compressor\ functions in jinja templates
        app.jinja_env.globals['compressor'] = compressor_template_helper

        # register the Compressor extension in the Flask app
        app.extensions['compressor'] = self

    def register_asset(self, name, asset):
        """ Add an asset in the list of available assets.

        Args:
            name: the name to identify the asset, must be unique
            asset (:class:`Asset`): the asset to register
        """
        self._assets[name] = asset

    def get_asset(self, name):
        """ Get the asset identified by its `name`.

        Args:
            name: the name of the asset

        Returns:
            An :class:`Asset` object.

        Raises:
            CompressorException: If no asset are associated to the `name`.
        """
        if not name in self._assets:
            raise CompressorException("asset '{}' not found.".format(name))

        return self._assets[name]

    def register_default_processors(self):
        """ Register default processors.

        Flask-Compressor comes with some usefull processors in
        :mod:`flask_compressor.processors`. This function will load processors
        listed in `flask_compressor.processors.DEFAULT_PROCESSORS`.
        """

        from .processors import DEFAULT_PROCESSORS
        for processor in DEFAULT_PROCESSORS:
            name = processor.__name__
            self.register_processor(name, processor)
            self._processors[name] = processor

    def register_processor(self, name, processor):
        """ Add a processor in the list of available processors.

        A processor is a Python function that accepts one argument (usually
        the content of an :class:`Asset` object), and returns the processed
        content.

        Args:
            name: the name to identify the processor, must be unique
            processor: the function used to process contents
        """
        self._processors[name] = processor

    def get_processor(self, name):
        """ Get the processor identified by its `name`.

        Args:
            name: the name of the processor

        Returns:
            A processor (a Python function).

        Raises:
            CompressorException: If no processor are associated the the
                `name`.
        """
        if not name in self._processors:
            raise CompressorException("Processor '{}' not found.".format(name))

        return self._processors[name]


class Asset(object):
    """
        An `Asset` object is a Python representation of a web asset used in
        your web application. An asset could be a Javascript file or some CSS
        properties, or a collection of one or sereval assets.

        An asset instance can have none or several processors. Each processor
        is called to alter the content of the asset (for example, you can add
        a processor to compile `SASS <http://sass-lang.com>`_ files into
        regular CSS).

        An asset have a template used to build a string representation of
        processed contents from assets. The template is usually used to add
        `<style></style>` or `<script></script>` html tag to the final result.

        >>> from flask.ext.compressor import Asset
        >>> css_content = '''
        ... html {
        ...     background-color: red;
        ... }
        ... '''
        >>> my_asset = Asset(contents=css_content, processors=['cssmin'])
        >>> print my_asset
        'html{background-color:red}'
    """
    default_template = "{content}"

    def __init__(self, assets=None, sources=None, contents=None,
                 processors=None, template=None):
        """ Initializes an :class:`Asset` instance.

        The content of an asset can be loaded from zero or several child assets
        (with the `assets` argument), a file (with the `source` argument) or
        passed directly as a string (with the `contents` argument).

        Args:
            assets: a list of :class:`Asset` objects (default: `[]`)
            sources: a list of filenames from wich the content will be loaded.
                Filenames will be appended to the static folder of the Flask
                application to find to file. (default: `[]`)
            contents: the content of the asset, or `None`
            processors: a list a processor registered in the
                :class:`Compressor` extension (default: `[]`)
            template: A string used to build a string representation of the
                processed content. The template is a regular Python string
                used with the "new" Python 3 `format` syntax, and must
                contains a `content` placeholder. (default: `{content}`)
        """
        self.assets = assets or []
        self.sources = sources or []
        self.contents = contents
        self.processors = processors or []
        self.template = template or self.default_template

    def get_content(self):
        """ Returns the processed content of the asset. """
        content = ''

        for asset in self.assets:
            content = content + asset.get_content()

        for filename in self.sources:
            content = content + self._load_contents_from_file(filename)

        if self.contents is not None:
            content = content + self.contents

        # apply processors
        compressor = current_app.extensions['compressor']
        for name in self.processors:
            content = compressor.get_processor(name)(content)

        return self.template.format(content=content)

    def _load_contents_from_file(self, filename):
        """ Load the content from a file.

            Args:
                filename: A path to the file to load contents from. The file
                    will be searched in the static folder of the Flask app.
        """
        abs_path = os.path.join(current_app.static_folder, filename)
        return open(abs_path).read()


class CSSAsset(Asset):
    """ A helper class to use a :class:`Asset` objects with CSS assets. """
    default_template = '<style type="text/css">{content}</style>'


class JSAsset(Asset):
    """ A helper class to use a :class:`Asset` objects with Javascript assets.
    """
    default_template = '<script type="text/javascript">{content}</script>'
