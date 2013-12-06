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
from flask import current_app, url_for
from .blueprint import compressor_blueprint
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

        # register the blueprint
        app.register_blueprint(compressor_blueprint, url_prefix='/_compressor')

    def register_asset(self, asset, replace=False):
        """ Add an asset in the list of available assets.

        Args:
            asset : the :class:`Asset` to register
            replace: If `False` and a asset is already registered with the
                same name, raises an exception. Use `True` to replace an
                existing asset. (default `False`)

        Raise:
            CompressorException: If an asset with the same name is already
                registered.
        """
        if asset.name in self._assets and not replace:
            raise CompressorException("An asset named '{}' is already "
                                      "registered. Use `replace=True` to "
                                      "replace an existing asset."
                                      "".format(asset.name))

        self._assets[asset.name] = asset

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
        properties.

        An asset instance can have none or several processors. Each processor
        is called to alter the content of the asset (for example, you can add
        a processor to compile `SASS <http://sass-lang.com>`_ files into
        regular CSS).

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
    default_inline_template = "{content}"
    default_linked_template = "<link ref='external' href='{url}' "\
                              "type='{mimetype}'>"
    default_mimetype = "text/plain"

    def __init__(self, name, sources=None, contents=None, processors=None,
                 inline_template=None, linked_template=None, mimetype=None):
        """ Initializes an :class:`Asset` instance.

        Args:
            name: the name of the asset, used to uniquely identify it
            sources: a list of filenames from wich the content will be loaded.
                Filenames will be appended to the static folder of the Flask
                application to find to file. (default: `[]`)
            contents: the content of the asset, or `None`
            processors: a list a processor registered in the
                :class:`Compressor` extension (default: `[]`)
            inline_template: A string used to build a string representation of
                the processed content. The template is a regular Python string
                used with the "new" Python 3 `format` syntax, and must
                contains a `content` placeholder. (default: `{content}`)
            linked_template: A string used to build a link to an external
                version of the processed content. The template is a regular
                Python string used with the "new" Python 3 `format` syntax.
                Available placeholders are `url` and `mimetype`. (default:
                `<link ref='external' href='{url}' type='{mimetype}'>`)
            mimetype: the mimetype corresponding to the final content of the
                asset (default: `text/plain`)
        """
        self.name = name
        self.sources = sources or []
        self.contents = contents
        self.processors = processors or []
        self.inline_template = inline_template or self.default_inline_template
        self.linked_template = linked_template or self.default_linked_template
        self.mimetype = mimetype or self.default_mimetype

    def apply_processors(self, data):
        """ Apply all processors of this asset to data.

        Args:
            data: can be either a string or a list of strings

        Returns:
            Modified data with all processors applied. Returns the same
            type as `data` (a string or a list of strings).
        """
        contents = data

        if isinstance(data, basestring):
            contents = [data]

        # apply all processors
        compressor = current_app.extensions['compressor']
        for name in self.processors:
            processor = compressor.get_processor(name)
            contents = [processor(content) for content in contents]

        if isinstance(data, basestring):
            return contents[0]

        return contents

    def get_contents(self, apply_processors=True):
        """ Returns a list of all contents in this asset.

        Args:
            apply_processors: indicate if processors from the asset should
                be applied to all contents (default `True`)

        Returns:
            a list of strings, each string corresponding to a source of
            content in the asset
        """
        contents = []

        for filename in self.sources:
            contents.append(self.load_contents_from_file(filename))

        if self.contents is not None:
            contents.append(self.contents)

        # apply processors
        if apply_processors:
            contents = self.apply_processors(contents)

        return contents

    def get_content(self, apply_processors=True):
        """ Concatenate all contents from the asset in a single string.

        Args:
            apply_processors: indicate if processors from the asset should
                be applied to the content (default `True`)

        Returns:
            a string
        """
        content = '\n'.join(self.get_contents(apply_processors=False))

        # apply processors
        if apply_processors:
            content = self.apply_processors(content)

        return content

    def get_inline_content(self):
        """ Return the content of the asset formatted with the
            `inline_template` template. Available placeholders are `content`
            and `mimetype`. """
        content = self.get_content()
        return self.inline_template.format(content=content,
                                           mimetype=self.mimetype)

    def get_inline_contents(self):
        """ Similar to :meth:`get_inline_content`, except that all sources
            from the asset are in their own `inline_template`. """
        contents = self.get_contents()
        return '\n'.join(
            [self.inline_template.format(content=content,
                                         mimetype=self.mimetype)
             for content in contents]
        )

    def get_linked_content(self):
        """ Return a link to the content of the asset, the link is formatted
            with the`linked_template` template. Available placeholders are
            `url` and `mimetype`. """
        url = url_for('compressor.render_asset', asset_name=self.name)
        return self.linked_template.format(url=url, mimetype=self.mimetype)

    def get_linked_contents(self):
        """ Similar to :meth:`get_linked_content`, except that all sources
            from the asset are in their own `linked_template`. """
        urls = []

        for filename in self.sources:
            urls.append(url_for('compressor.render_asset_source',
                                asset_name=self.name, filename=filename))

        if self.contents is not None:
            urls.append(url_for('compressor.render_asset_contents',
                                asset_name=self.name))

        return '\n'.join(
            [self.linked_template.format(url=url, mimetype=self.mimetype)
             for url in urls]
        )

    def load_contents_from_file(self, filename):
        """ Load the content from a file.

            Args:
                filename: A path to the file to load contents from. The file
                    will be searched in the static folder of the Flask app.
        """
        abs_path = os.path.join(current_app.static_folder, filename)
        return open(abs_path).read()


class CSSAsset(Asset):
    """ A helper class to use a :class:`Asset` objects with CSS assets. """
    default_inline_template = '<style type="{mimetype}">{content}</style>'
    default_linked_template = '<link type="{mimetype}" rel="stylesheet" ' \
                              'href="{url}">'
    default_mimetype = 'text/css'


class JSAsset(Asset):
    """ A helper class to use a :class:`Asset` objects with Javascript assets.
    """
    default_inline_template = '<script type="{mimetype}">{content}</script>'
    default_linked_tempalte = '<script type="{mimetype}" src="{url}">' \
                              '</script>'
    default_mimetype = 'text/javascript'
