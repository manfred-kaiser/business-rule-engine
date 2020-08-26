# -*- coding: utf-8 -*-

from setuptools import setup, find_packages  # type: ignore

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='business-rule-engine',
    version='0.0.1',
    author='Manfred Kaiser',
    author_email='manfred.kaiser@logfile.at',
    description='Python DSL for setting up business intelligence rules',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords="business rules engine",
    python_requires='>= 3.6',
    packages=find_packages(exclude=("tests",)),  # type: ignore
    url="https://business-rule-engine.readthedocs.io/",
    project_urls={
        'Source': 'https://github.com/logfile-at/business-rule-engine',
        'Tracker': 'https://github.com/logfile-at/business-rule-engine/issues',
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8"
    ],
    install_requires=[
        'formulas'
    ]
)
