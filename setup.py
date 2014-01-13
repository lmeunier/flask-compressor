# -*- coding: utf-8 -*-

"""
    Flask-Compressor
    ~~~~~~~~~~~~~~~~

    Flask-Compressor is a Flask extension that helps you to concatenate and
    minify your Javascript and CSS files.

"""

from setuptools import setup


setup(
    name='Flask-Compressor',
    version='0.2.0',
    description='Compress your CSS and JS files.',
    long_description=__doc__,
    author='Laurent Meunier',
    author_email='laurent@deltalima.net',
    url='https://github.com/lmeunier/flask-compressor',
    packages=['flask_compressor'],
    include_package_data=True,
    zip_safe=False,
    install_requires=['Flask'],
    test_suite="tests",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
