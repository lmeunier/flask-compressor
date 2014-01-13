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
import functools
import hashlib
from flask import current_app, url_for
from .exceptions import CompressorException
from .blueprint import blueprint as compressor_blueprint
from .templating import compressor as compressor_template_helper
from .processors import DEFAULT_PROCESSORS


class memoized(object):
    """ Decorator. Caches a function or method return value only if the current
    Flask application is *not* in debug mode. """

    def __init__(self, func):
        """ Initialize the decorator with a function (or method) """
        self.func = func
        self.cache = {}

    def __call__(self, *args, **kwargs):
        """ Call the decorated function (or method) if the Flask application is
        not in debug mode, or the return value is not yet cached. """
        if current_app.debug:
            # always reevaluate the return value when debug is enabled
            return self.func(*args, **kwargs)

        # compute the key to store the retur value in a dict
        key = (args, frozenset(kwargs.items()))

        if key in self.cache:
            # the return value is already evaluated, return it
            return self.cache[key]

        # evaluate the return value (call the decorated function)
        value = self.func(*args, **kwargs)

        # store and return the return value
        self.cache[key] = value
        return value

    def __repr__(self):
        """ Return a representation of the decorated function (or method) """
        return "<Memoized function '{}'>".format(self.func.__name__)

    def __get__(self, obj, objtype):
        """ Support instance method """
        return functools.partial(self.__call__, obj)


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

        Raises:
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

        for processor in DEFAULT_PROCESSORS:
            self.register_processor(processor)

    def register_processor(self, processor, name=None, replace=False):
        """ Add a processor in the list of available processors.

        A processor is a Python function that accepts one argument (usually
        the content of an :class:`Asset` object), and returns the processed
        content.

        Args:
            processor: the function used to process contents
            name: The name to identify the processor, must be unique. If
                `None`, use `processor.__name__`.
            replace: If `False` and a processor is already registered with the
                same name, raises an exception. Use `True` to replace an
                existing processor. (default `False`)

        Raises:
            CompressorException: If a processor with the same name is already
                registered.
        """
        if name is None:
            name = processor.__name__

        if name in self._processors and not replace:
            raise CompressorException("A processor named '{}' is already "
                                      "registered. Use `replace=True` to "
                                      "replace an existing processor."
                                      "".format(name))

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
    default_inline_template = '{content}'
    default_linked_template = '<link ref="external" href="{url}" '\
                              'type="{mimetype}">'
    default_mimetype = 'text/plain'
    default_extension = 'txt'

    def __init__(self, name, assets=None, processors=None,
                 inline_template=None, linked_template=None, mimetype=None,
                 extension=None):
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
            extension: the file extension associated with the mimetype
                (default: `txt`)
        """
        self.name = name
        self.assets = assets or []
        self.processors = processors or []
        self.inline_template = inline_template or self.default_inline_template
        self.linked_template = linked_template or self.default_linked_template
        self.mimetype = mimetype or self.default_mimetype
        self.extension = extension or self.default_extension

        for asset in self.assets:
            asset.bundle = self

    def apply_processors(self, contents):
        """ Apply all processors to the provided data.

        Args:
            data: a list of strings

        Returns:
            A list of modified strings with all processors applied.
        """
        compressor = current_app.extensions['compressor']
        for name in self.processors:
            processor = compressor.get_processor(name)
            contents = [processor(content) for content in contents]

        return contents

    @memoized
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

    @memoized
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
            content = self.apply_processors([content])[0]

        return content

    @memoized
    def get_inline_content(self, concatenate=True):
        """ Return the content of the bundle formatted with the
            `inline_template` template. Available placeholders for the
            template are `content` and `mimetype`.

            Args:
                concatenate: If `True`, all contents from assets are
                    concatenated before applying the inline template. If
                    `False`, the inline template is applied to each asset
                    content. (default: `True`)
        """
        if concatenate:
            content = self.get_content()
            return self.inline_template.format(content=content,
                                               mimetype=self.mimetype)
        else:
            contents = self.get_contents()
            return '\n'.join(
                [self.inline_template.format(content=content,
                                             mimetype=self.mimetype)
                 for content in contents]
            )

    @memoized
    def get_linked_content(self, concatenate=True):
        """ Return a link to the content of the bundle, the link is formatted
            with the`linked_template` template. Available placeholders for the
            template are `url` and `mimetype`.

            Args:
                concatenate: If `True`, all contents from assets are
                    concatenated before applying the linked template. If
                    `False`, the linked template is applied to each asset
                    content. (default: `True`)
        """
        if concatenate:
            return self.linked_template.format(url=self.url, mimetype=self.mimetype)
        else:
            urls = [asset.url for asset in self.assets]
            return '\n'.join(
                [self.linked_template.format(url=url, mimetype=self.mimetype)
                 for url in urls]
            )

    @property
    @memoized
    def url(self):
        return url_for(
            'compressor.render_bundle',
            bundle_name=self.name,
            bundle_hash=self.hash,
            bundle_extension=self.extension,
        )

    @property
    @memoized
    def hash(self):
        content = self.get_content()
        return hashlib.md5(content.encode('utf-8')).hexdigest()


class CSSBundle(Bundle):
    """ A helper class to use a :class:`Bundle` objects with CSS assets. """
    default_inline_template = '<style type="{mimetype}">{content}</style>'
    default_linked_template = '<link type="{mimetype}" rel="stylesheet" ' \
                              'href="{url}">'
    default_mimetype = 'text/css'
    default_extension = 'css'


class JSBundle(Bundle):
    """ A helper class to use a :class:`Bundle` objects with Javascript assets.
    """
    default_inline_template = '<script type="{mimetype}">{content}</script>'
    default_linked_template = '<script type="{mimetype}" src="{url}">' \
                              '</script>'
    default_mimetype = 'text/javascript'
    default_extension = 'js'


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
        self._raw_content = content
        self.processors = processors or []
        self.bundle = None

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
    @memoized
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
        return self._raw_content

    @property
    @memoized
    def url(self):
        return url_for(
            'compressor.render_asset',
            bundle_name=self.bundle.name,
            bundle_extension=self.bundle.extension,
            asset_index=self.bundle.assets.index(self),
            asset_hash=self.hash,
            name=self.name
        )

    @property
    @memoized
    def hash(self):
        return hashlib.md5(self.content.encode('utf-8')).hexdigest()


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
        if os.path.isabs(filename):
            raise CompressorException("Absolute filename are not supported: "
                                      "{}. Use a relative path from the static"
                                      "folder of your Flask app."
                                      "".format(filename))
        self.filename = filename
        super(FileAsset, self).__init__(None, *args, **kwargs)

    @property
    @memoized
    def raw_content(self):
        """ Return the content of the file `self.filename`. """
        abs_path = os.path.join(current_app.static_folder, self.filename)
        with open(abs_path) as handle:
            self._raw_content = handle.read()
        return self._raw_content

    @property
    def name(self):
        """ The asset is identified by the filename """
        return self.filename
