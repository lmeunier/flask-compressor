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
from .blueprint import blueprint as compressor_blueprint
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
        self._bundles = {}
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

    def register_bundle(self, bundle, replace=False):
        """ Add a bundle in the list of available bundles.

        Args:
            bundle : the :class:`Bundle` to register
            replace: If `False` and a bundle is already registered with the
                same name, raises an exception. Use `True` to replace an
                existing bundle. (default `False`)

        Raise:
            CompressorException: If a bundle with the same name is already
                registered.
        """
        if bundle.name in self._bundles and not replace:
            raise CompressorException("A bundle named '{}' is already "
                                      "registered. Use `replace=True` to "
                                      "replace an existing bundle."
                                      "".format(bundle.name))

        self._bundles[bundle.name] = bundle

    def get_bundle(self, name):
        """ Get the bundle identified by its `name`.

        Args:
            name: the name of the bundle

        Returns:
            A :class:`Bundle` object.

        Raises:
            CompressorException: If no bundle are associated to the `name`.
        """
        if not name in self._bundles:
            raise CompressorException("Bundle '{}' not found.".format(name))

        return self._bundles[name]

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


class Bundle(object):
    """
        A `Bundle` object is a collection of a web assets used in your web
        application. An asset could be a Javascript file or some CSS
        properties.

        A bundle instance can have none or several processors. Each processor
        is called to alter the content of the concatenation of all assets in
        the bundle.
    """
    default_inline_template = "{content}"
    default_linked_template = "<link ref='external' href='{url}' "\
                              "type='{mimetype}'>"
    default_mimetype = "text/plain"

    def __init__(self, name, assets=None, processors=None,
                 inline_template=None, linked_template=None, mimetype=None):
        """ Initializes a :class:`Bundle` instance.

        Args:
            name: the name of the bundle, used to uniquely identify it
            assets: a list of :class:`Asset` objects (default: `[]`)
            processors: a list a processor registered in the
                :class:`Compressor` extension (default: `[]`)
            inline_template: A string used to build a string representation of
                the processed content. The template is a regular Python string
                used with the "new" Python 3 `format` syntax. AVailable
                placeholders are `content` and `mimetype`. (default:
                `{content}`)
            linked_template: A string used to build a link to an external
                version of the bundle content. The template is a regular
                Python string used with the "new" Python 3 `format` syntax.
                Available placeholders are `url` and `mimetype`. (default:
                `<link ref='external' href='{url}' type='{mimetype}'>`)
            mimetype: the mimetype corresponding to the final content of the
                bundle (default: `text/plain`)
        """
        self.name = name
        self.assets = assets or []
        self.processors = processors or []
        self.inline_template = inline_template or self.default_inline_template
        self.linked_template = linked_template or self.default_linked_template
        self.mimetype = mimetype or self.default_mimetype

    def apply_processors(self, data):
        """ Apply all processors to the provided data.

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
        """ Returns a list with the content of each assets.

        Args:
            apply_processors: indicate if processors from the bundle should
                be applied to each contents (default `True`)

        Returns:
            a list of strings, each string corresponding to the content of an
            asset
        """
        contents = []

        for asset in self.assets:
            contents.append(asset.content)

        # apply processors
        if apply_processors:
            contents = self.apply_processors(contents)

        return contents

    def get_content(self, apply_processors=True):
        """ Concatenate the content from each assets in a single string.

        Args:
            apply_processors: indicate if processors from the bundle should
                be applied to the final content (default `True`)

        Returns:
            a string
        """
        content = '\n'.join(self.get_contents(apply_processors=False))

        # apply processors
        if apply_processors:
            content = self.apply_processors(content)

        return content

    def get_inline_content(self):
        """ Return the content of the bundle formatted with the
            `inline_template` template. Available placeholders for the
            tempalte are `content` and `mimetype`. """
        content = self.get_content()
        return self.inline_template.format(content=content,
                                           mimetype=self.mimetype)

    def get_inline_contents(self):
        """ Similar to :meth:`get_inline_content`, except that all assets
            from the bundle are in their own `inline_template`. """
        contents = self.get_contents()
        return '\n'.join(
            [self.inline_template.format(content=content,
                                         mimetype=self.mimetype)
             for content in contents]
        )

    def get_linked_content(self):
        """ Return a link to the content of the bundle, the link is formatted
            with the`linked_template` template. Available placeholders for the
            template are `url` and `mimetype`. """
        url = url_for('compressor.render_bundle', bundle_name=self.name)
        return self.linked_template.format(url=url, mimetype=self.mimetype)

    def get_linked_contents(self):
        """ Similar to :meth:`get_linked_content`, except that all assets
            from the bundle are in their own `linked_template`. """
        urls = []

        for index, asset in enumerate(self.assets):
            urls.append(url_for('compressor.render_asset',
                                bundle_name=self.name,
                                asset_index=index,
                                asset_name=asset.name))

        return '\n'.join(
            [self.linked_template.format(url=url, mimetype=self.mimetype)
             for url in urls]
        )


class CSSBundle(Bundle):
    """ A helper class to use a :class:`Bundle` objects with CSS assets. """
    default_inline_template = '<style type="{mimetype}">{content}</style>'
    default_linked_template = '<link type="{mimetype}" rel="stylesheet" ' \
                              'href="{url}">'
    default_mimetype = 'text/css'


class JSBundle(Bundle):
    """ A helper class to use a :class:`Bundle` objects with Javascript assets.
    """
    default_inline_template = '<script type="{mimetype}">{content}</script>'
    default_linked_tempalte = '<script type="{mimetype}" src="{url}">' \
                              '</script>'
    default_mimetype = 'text/javascript'


class Asset(object):
    """
        An asset is the equivalent of an external ressource like a Javascript
        or a CSS file.

        Processors can be applied to the content of an asset. For exemple,
        your asset can point to a `SASS <http://sass-lang.com>`_ file and use
        a processor to convert it to regular CSS content.
    """
    def __init__(self, content='', processors=None):
        """ Initializes an :class:`Asset` instance.

        Args:
            content: the content of the asset (default: empty string)
            processors: a list a processor registered in the
                :class:`Compressor` extension (default: `[]`)
        """
        self._content = content
        self.processors = processors or []

    def apply_processors(self, content):
        """ Apply all processors to the provided content.

        Args:
            content: the content to be processed

        Returns:
            Modified content with all processors applied
        """
        # apply all processors
        compressor = current_app.extensions['compressor']
        for name in self.processors:
            processor = compressor.get_processor(name)
            content = processor(content)

        return content

    @property
    def content(self):
        """ Return the content of the asset after being altered by the
        processors. """
        return self.apply_processors(self.raw_content)

    @property
    def name(self):
        """ Return (if available) a name to identify the asset. """
        return None

    @property
    def raw_content(self):
        """ Return the raw content of the asset, without any modification. """
        return self._content


class FileAsset(Asset):
    """
        A specialized :class:`Asset` class that allow to load the content from
        a file. The file must be presents in the static folder of the Flask
        application.
    """
    def __init__(self, filename, *args, **kwargs):
        """ Initializes a :class:`FileAsset` instance.

        Args:
            filename: load content from the file identified by `filename`,
                `filename` is a path relative to the static folder of the
                Flask application
        """
        self.filename = filename
        super(FileAsset, self).__init__(None, *args, **kwargs)

    @property
    def raw_content(self):
        """ Return the content of the file `self.filename`. """

        # do not reload file on each call if app is not in debug mode and the
        # file is already loaded
        if not current_app.debug and self._content is not None:
            return self._content

        # if debug mode is enabled, reload the file on each call
        abs_path = os.path.join(current_app.static_folder, self.filename)
        self._content = open(abs_path).read()
        return self._content

    @property
    def name(self):
        return self.filename
