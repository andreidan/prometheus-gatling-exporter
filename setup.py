#!/usr/bin/env python

import functools
from setuptools import setup


def read(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except IOError:
        return ''


readme = functools.partial(read, 'README.rst')


setup(
    name='prometheus-gatling-exporter',
    author='Andrei Dan',
    author_email='andrei@crate.io',
    url='https://github.com/andreidan/prometheus-gatling-exporter',
    description='A tool that parses Gatling live logs and exports metrics for\
            Prometheus to scrape.',
    long_description=readme(),
    entry_points={
        'console_scripts': [
            'gatling_exporter = gatling.gatling_exporter:main'
        ]
    },
    package_dir={'': 'src'},
    packages=['gatling'],
    install_requires=[
        'prometheus_client>=0.2.0'
    ],
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    use_scm_version=True,
    setup_requires=['setuptools_scm']
)
