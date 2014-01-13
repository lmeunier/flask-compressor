Flask-Compressor
================

.. image:: https://travis-ci.org/lmeunier/flask-compressor.png?branch=master
   :target: https://travis-ci.org/lmeunier/flask-compressor

Overview
--------

Flask-Compressor is a `Flask <http://flask.pocoo.org>`_ extension that helps
you to manage your web assets. For example, Flask-Compressor will concatenate
and minify all your CSS files, or compile CoffeScript files into JavaScript.

The main difference between Flask-Compressor and other extensions doing the
same thing is that Flask-Compressor will never write the final result of an
asset on the file system, all results are kept in memory and served directly
from memory. This behavior can help deployement when the user running the Flask
application don't have the right to write on the local file system (this is the
case with Google App Engine).


Requirements
------------

- Python 2.7 or Python 3.3
- Flask >= 0.10
- scripts or Python modules to process your assets

This extension is not a rewrite of famous web assets processors (like
`CoffeeScript <http://coffeescript.org/>`_ or `LESS <http://lesscss.org>`_).
You must install dependencies required for each processor you want to use.

Installation
------------

- from PyPI:

.. code:: bash

   pip install Flask-Compressor

- from Git:

.. code:: bash

    git clone https://github.com/lmeunier/flask-compressor
    cd flask-compressor
    python setup.py install


Initialize the Flask-Compressor extension
-----------------------------------------

.. code:: python

    from flask import Flask
    from flask.ext.compressor import Compressor

    app = Flask(__name__)
    compressor = Compressor(app)

    # or

    app = Flask(__name__)
    compressor = Compressor()
    compressor.init_app(app)


Working with assets
-------------------

An asset is the equivalent of an external resource like a JavaScript or a CSS
file. You create an asset by instantiating an `Asset` object with content and
processors.

.. code:: python

    from flask.ext.compressor import Asset

    css_content = '''
        html {
            background-color: red;
        }
    '''
    my_asset = Asset(content=css_content, processors=['cssmin'])

The `processors` argument is optional, it defaults to an empty list (no
processors). Processors are used to apply transformations to the content of an
asset. They are applied in the same order as they are declared in the
`processors` argument.

An helper named `FileAsset` is available to load the content from a file. The
`filename` argument is appended to the static folder path of the Flask
application to build the full path to the file.

.. code:: python

    from flask.ext.compressor import FileAsset

    my_asset = FileAsset(filename='css/styles.less', processors=['lesscss'])

If debug is enabled (`current_app.debug == True`), the file is re-read each
time the content of the asset is accessed. If debug is disabled, the file is
read only the first time the content of the asset is accessed, further
modifications to the source file won't alter the content of the asset.


Working with bundles
--------------------

A bundle is a collection of assets. A bundle is identified by a name and must
be registered with the Flask-Compressor extension. You can create a bundle by
instantiating a `Bundle` object with assets and processors.

.. code:: python

    from flask.ext.compressor import Bundle

    my_bundle = Bundle('name_for_my_bundle', assets=[asset1, asset2], processors=['cssmin'])
    compressor.register_bundle(my_bundle)

The content of a bundle is the concatenation of all assets. Assets
are concatenated in the same order as they are declared in the `assets`
argument.

Like for assets, the `processors` argument is optional, it defaults to an empty
list (no processors). Processors are used to apply transformations to the
content of a bundle. They are applied in the same order as they are declared in
the `processors` argument.


Available processors
--------------------

Flask-Compressor is shipped with only two processors. More processors will be
added soon.


cssmin
~~~~~~

`cssmin <https://pypi.python.org/pypi/cssmin>`_ is a Python port of the YUI CSS
compression algorithm. To use it, you must install the `cssmin` Python package.

.. code:: bash

    pip install cssmin

lesscss
~~~~~~~

Use the `lessc` command from `lesscss <http://lesscss.org/>`_ to compile LESS
code into regular CSS content. You need to have the `lessc` command available.
If you already have `node.js <http://nodejs.org>`_ and `npm
<https://npmjs.org>`_ installed, you can install `lessc` with one command line:

.. code:: bash

    npm install -g less

jsmin
~~~~~

Use `jsmin <https://pypi.python.org/pypi/jsmin>`_ to compress JavaScript. You
must manually install jsmin if you want to use this processor.

.. code:: bash

   pip install jsmin


Bundle templates
----------------

When creating a `Bundle` object, you can pass three arguments to control the
output of the bundle in a template: `inline_template`, `linked_template` and
`mimetype`. Inline and linked templates are regular Python string used with the
"new" Python 3 `format` syntax.

Available placeholders are:

- `inline_template`: `{content}` and `{mimetype}`
- `linked_template`: `{url}` and `{mimetype}`

For example, if you want to create a bundle and use it with CSS files, you can
do something like this:

.. code:: python

    my_bundle = Bundle(
        name='my_bundle',
        assets=[Asset('/* some CSS properties */')],
        inline_template='<style type="{mimetype}">{content}</style>',
        linked_template='<link type="{mimetype}" rel="stylesheet" href="{url}">',
        mimetype='text/css',
        extension='css'
    )

You can now render your bundle in your template, and either add the content
inline or linked to an external file.

Two helper classes are provided with Flask-Compressor with defaults values for
templates (inline and linked), the mimetype and the extension:

- `flask.ext.compressor.CSSBundle` (for CSS content)
- `flask.ext.compressor.JSBundle` (for JavaScript code)


Render bundles in templates
---------------------------

A new function `compressor` is added to the Jinja2 environment. The
`compressor` function render the content of a bundle. You can either render the
bundle inline (the content of the bundle is added to the output - this is the
default behavior), or linked.

.. code:: HTML+Django

    {{ compressor('name_for_my_bundle', inline=True) }}

The way the `compressor` function render the content of the bundle is
controlled by the `inline` argument. When `inline` is `True` (default value),
the `inline_template` of the bundle is used. When `inline` is `False`, the
`linked_template` is used.


Blueprint
---------

A blueprint is automaticaly registered at the URL prefix `/_compressor/` when
you add a Flask-Compressor extension instance to your Flask application. This
blueprint is only used when bundles are not inlined in your templates
(i.e., `inline=False` in the `compressor` template function).

An URL to a bundle in build from the name of the bundle, a unique hash (md5
calculated from the content) and the extension of the bundle (for example:
`/_compressor/bundle/my_css_bundle_v836625e5ecabdada6dd84787e0f72a16.css`)


Full example
------------

.. code:: python

    from flask import Flask
    from flask.ext.flatpages import pygments_style_defs
    from flask.ext.compressor import Compressor, Asset, Bundle

    app = Flask(__name__)
    compressor = Compressor(app)

    css_bundle = CSSBundle(
        name='css_bundle',
        assets=[
            Asset(content=pygments_style_defs()),
            FileAsset(filename='styles.less', processors=['lesscss']),
        ],
        processors=['cssmin']
    )


What does this example? We have created a CSS bundle with two assets. The
content of the first asset comes from the `FlatPages extension
<http://pythonhosted.org/Flask-FlatPages/>`_: CSS styles for pygments
highlight. The second asset is a `LESS <http://lesscss.org/>`_ file with a
processor to compile the file content into regular CSS properties. And finally,
contents from the two assets are concatenated and minified using the `cssmin`
processor.


Credits
-------

The Flask-Compressor extension is maintained by `Laurent Meunier
<http://www.deltalima.net/>`_.


Licenses
--------

Flask-Compressor is Copyright (c) 2013 Laurent Meunier. It is free software,
and may be redistributed under the terms specified in the LICENSE file (a
3-clause BSD License).
