#!/usr/bin/env python

"Setuptools params"

from setuptools import setup, find_packages

VERSION = '0.5'

modname = distname = 'ipmininet'

setup(
    name=distname,
    version=VERSION,
    description='A mininet extension providing components to emulate IP'
                'networks running multiple protocols.',
    author='Olivier Tilmans',
    author_email='olivier.tilmans@uclouvain.be',
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Programming Language :: Python",
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Topic :: System :: Networking",
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7'
        ],
    keywords='networking OSPF IP BGP quagga mininet',
    license='GPLv2',
    install_requires=[
        'setuptools',
        'mako',
        'ipaddress',
        'mininet'
    ],
    scripts=['util/install.py', 'util/utils.py', 'util/build_vm.sh'],
    tests_require=['pytest'],
    setup_requires=['pytest-runner'],
    url='https://github.com/oliviertilmans/ipmininet'
)
