# -*- coding: utf-8 -*-

"""
    Flask-Compressor test suite
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

from __future__ import unicode_literals, absolute_import, division, \
    print_function
import os
import unittest
import flask
import tempfile
from flask.ext.compressor import Compressor, Bundle, Asset, FileAsset, \
    CompressorException
from flask.ext.compressor.processors import DEFAULT_PROCESSORS


class ProcessorsTestCase(unittest.TestCase):
    def setUp(self):
        # initialize the flask app
        app = flask.Flask(__name__)
        app.config['TESTING'] = True
        compressor = Compressor(app)
        self.app = app
        self.compressor = compressor

        # our processor function
        def test_processor(content):
            return "FOOBAR" + str(content)
        self.test_processor = test_processor

    def test_default_processors(self):
        for processor in DEFAULT_PROCESSORS:
            self.compressor.get_processor(processor.__name__)

    def test_register_processor(self):
        self.compressor.register_processor(self.test_processor)
        self.compressor.get_processor(self.test_processor.__name__)
        self.assertRaises(
            CompressorException,
            self.compressor.register_processor,
            self.test_processor
        )
        self.compressor.register_processor(self.test_processor, replace=True)
        self.compressor.get_processor(self.test_processor.__name__)

    def test_register_named_processor(self):
        self.compressor.register_processor(self.test_processor)
        self.compressor.register_processor(self.test_processor, 'test1')
        self.compressor.register_processor(self.test_processor, 'test2')
        self.assertRaises(
            CompressorException,
            self.compressor.register_processor,
            self.test_processor,
            'test1'
        )
        self.compressor.register_processor(
            self.test_processor,
            'test1',
            replace=True
        )
        self.compressor.get_processor(self.test_processor.__name__)
        self.compressor.get_processor('test1')
        self.compressor.get_processor('test2')

    def test_get_processor(self):
        self.compressor.register_processor(self.test_processor)
        self.compressor.register_processor(self.test_processor, 'test1')
        self.assertEqual(
            self.test_processor,
            self.compressor.get_processor('test1')
        )
        self.assertEqual(
            self.test_processor,
            self.compressor.get_processor(self.test_processor.__name__)
        )

    def test_processor_not_found(self):
        self.assertRaises(
            CompressorException,
            self.compressor.get_processor,
            self.test_processor.__name__,
        )
        self.compressor.register_processor(self.test_processor)
        self.compressor.get_processor(self.test_processor.__name__)

    def test_apply_processor(self):
        self.compressor.register_processor(self.test_processor, 'test')
        processor = self.compressor.get_processor('test')
        processed_content = processor('some garbage')
        self.assertEqual(processed_content, 'FOOBARsome garbage')


class CssminProcessorTestCase(unittest.TestCase):
    def setUp(self):
        # initialize the flask app
        app = flask.Flask(__name__)
        app.config['TESTING'] = True
        compressor = Compressor(app)
        self.app = app
        self.compressor = compressor

    def test_cssmin_is_present(self):
        self.compressor.get_processor('cssmin')

    def test_apply_cssmin(self):
        css_content = '''
            html {
                background-color: red;
            }
        '''
        processor = self.compressor.get_processor('cssmin')

        with self.app.test_request_context():
            processed_content = processor(css_content)
            self.assertEqual(processed_content, 'html{background-color:red}')


class BundlesTestCase(unittest.TestCase):
    def setUp(self):
        # initialize the flask app
        app = flask.Flask(__name__)
        app.config['TESTING'] = True
        compressor = Compressor(app)
        self.app = app
        self.compressor = compressor

        # our bundle
        bundle = Bundle(name='test_bundle')
        self.bundle = bundle

    def test_register_bundle(self):
        self.compressor.register_bundle(self.bundle)
        self.assertRaises(CompressorException, self.compressor.register_bundle,
                          self.bundle)
        self.compressor.register_bundle(self.bundle, replace=True)

    def test_get_bundle(self):
        self.compressor.register_bundle(self.bundle)
        bundle = self.compressor.get_bundle('test_bundle')
        self.assertEqual(bundle, self.bundle)

    def test_replace_bundle(self):
        self.compressor.register_bundle(self.bundle)
        self.compressor.register_bundle(self.bundle, replace=True)
        bundle = self.compressor.get_bundle('test_bundle')
        self.assertEqual(bundle, self.bundle)

    def test_bundle_not_found(self):
        self.assertRaises(CompressorException, self.compressor.get_bundle,
                          'test_bundle')
        self.compressor.register_bundle(self.bundle)
        self.compressor.get_bundle('test_bundle')
        self.assertRaises(CompressorException, self.compressor.get_bundle,
                          'WTF!')


class BundleWithAssetsTestCase(unittest.TestCase):
    def setUp(self):
        # initialize the flask app
        app = flask.Flask(__name__)
        app.config['TESTING'] = True
        compressor = Compressor(app)
        self.app = app
        self.compressor = compressor

        # some simple processors
        def test1(content):
            return "FOOBAR" + str(content)

        def test2(content):
            return str(content) + "BARFOO"

        compressor.register_processor(test1)
        compressor.register_processor(test2)

        # our bundle
        bundle = Bundle(
            name='test_bundle',
            assets=[
                Asset(content='first asset', processors=['test1']),
                Asset(content='second asset')
            ],
            processors=['test2']
        )
        self.bundle = bundle

        compressor.register_bundle(bundle)

    def test_get_content(self):
        bundle_content = 'FOOBARfirst asset\nsecond assetBARFOO'
        with self.app.test_request_context():
            content = self.bundle.get_content()
            self.assertEqual(content, bundle_content)

        bundle_content = 'FOOBARfirst asset\nsecond asset'
        with self.app.test_request_context():
            content = self.bundle.get_content(apply_processors=False)
            self.assertEqual(content, bundle_content)

    def test_get_contents(self):
        bundle_contents = ['FOOBARfirst assetBARFOO', 'second assetBARFOO']
        with self.app.test_request_context():
            contents = self.bundle.get_contents()
            self.assertEqual(contents, bundle_contents)

        bundle_contents = ['FOOBARfirst asset', 'second asset']
        with self.app.test_request_context():
            contents = self.bundle.get_contents(apply_processors=False)
            self.assertEqual(contents, bundle_contents)

    def test_get_inline_content(self):
        inline_content = 'FOOBARfirst asset\nsecond assetBARFOO'
        with self.app.test_request_context():
            content = self.bundle.get_inline_content()
            self.assertEqual(content, inline_content)

        inline_content = 'FOOBARfirst assetBARFOO\nsecond assetBARFOO'
        with self.app.test_request_context():
            contents = self.bundle.get_inline_content(concatenate=False)
            self.assertEqual(contents, inline_content)

    def test_get_linked_content(self):
        linked_content = "<link ref='external' href='/_compressor/bundle/tes" \
            "t_bundle' type='text/plain'>"
        with self.app.test_request_context():
            content = self.bundle.get_linked_content()
            self.assertEqual(content, linked_content)

        linked_content = "<link ref='external' href='/_compressor/bundle/tes" \
            "t_bundle/asset/0/' type='text/plain'>\n<link ref='external' hre" \
            "f='/_compressor/bundle/test_bundle/asset/1/' type='text/plain'>"
        with self.app.test_request_context():
            contents = self.bundle.get_linked_content(concatenate=False)
            self.assertEqual(contents, linked_content)

    def test_blueprint_urls(self):
        get = self.app.test_client().get

        rv = get('/_compressor/bundle/test_bundle')
        self.assertEqual('FOOBARfirst asset\nsecond assetBARFOO', rv.data.decode('utf8'))

        rv = get('/_compressor/bundle/bundle_not_found')
        self.assertEqual(rv.status_code, 404)

        rv = get('/_compressor/bundle/test_bundle/asset/0/')
        self.assertEqual('FOOBARfirst asset', rv.data.decode('utf8'))

        rv = get('/_compressor/bundle/test_bundle/asset/1/')
        self.assertEqual('second asset', rv.data.decode('utf8'))

        rv = get('/_compressor/bundle/test_bundle/asset/2/')
        self.assertEqual(rv.status_code, 404)

        rv = get('/_compressor/bundle/test_bundle/asset/1/not_found.css')
        self.assertEqual(rv.status_code, 404)

        rv = get('/_compressor/bundle/bundle_not_found/asset/0/')
        self.assertEqual(rv.status_code, 404)

class AssetTestCase(unittest.TestCase):
    def setUp(self):
        # initialize the flask app
        app = flask.Flask(__name__)
        app.config['TESTING'] = True
        compressor = Compressor(app)
        self.app = app
        self.compressor = compressor

        self.css_content = '''
            html {
                background-color: red;
            }
        '''
        self.asset_processors = ['cssmin']
        self.asset = Asset(self.css_content, self.asset_processors)

    def test_raw_content(self):
        with self.app.test_request_context():
            self.assertEqual(self.asset.raw_content, self.css_content)

    def test_content(self):
        with self.app.test_request_context():
            self.assertEqual(self.asset.content, 'html{background-color:red}')


class FileAssetTestCase(AssetTestCase):
    def setUp(self):
        super(FileAssetTestCase, self).setUp()

        # create a temporary file
        fd, filename = tempfile.mkstemp()
        os.write(fd, self.css_content.encode('utf-8'))
        os.close(fd)

        # create a FileAsset object
        self.asset = FileAsset(filename, self.asset_processors)

    def tearDown(self):
        os.remove(self.asset.filename)


class MultipleProcessorsTestCase(unittest.TestCase):
    def setUp(self):
        # initialize the flask app
        app = flask.Flask(__name__)
        app.config['TESTING'] = True
        compressor = Compressor(app)
        self.app = app
        self.compressor = compressor

        def processor1(content):
            return content.replace('html', ' body ')

        def processor2(content):
            return content.replace(' body ', 'p ')

        def processor3(content):
            return content.replace(':red}', ':blue}')

        self.compressor.register_processor(processor1)
        self.compressor.register_processor(processor2)
        self.compressor.register_processor(processor3)

        css_content = 'html { background-color: red; } '
        self.asset1 = Asset(css_content, processors=['processor1', 'processor2'])
        self.asset2 = Asset(css_content, processors=['processor2', 'processor1'])
        self.bundle = Bundle(
            'test_bundle',
            assets=[self.asset1, self.asset2],
            processors=['cssmin', 'processor3'],
        )

    def test_asset_content(self):
        asset_content = 'p  { background-color: red; } '
        with self.app.test_request_context():
            self.assertEqual(asset_content, self.asset1.content)

        asset_content = ' body  { background-color: red; } '
        with self.app.test_request_context():
            self.assertEqual(asset_content, self.asset2.content)

    def test_bundle_content(self):
        bundle_content = 'p{background-color:blue}body{background-color:blue}'
        with self.app.test_request_context():
            self.assertEqual(bundle_content, self.bundle.get_content())


if __name__ == '__main__':
    unittest.main()
