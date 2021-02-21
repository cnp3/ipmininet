#!/usr/bin/env python

"Setuptools params"

import os
import shutil
import sys

from pkg_resources import parse_version, require
from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install

VERSION = '0.9'

modname = distname = 'ipmininet'

MININET_VERSION = "2.3.0"
install_requires = [
    'setuptools',
    'mako>=1.1,<1.2'
]
dependency_links = []

# Version after which we use another method to install
# dependencies from github
SPIN_PIP_VER = parse_version("18.1")


# Get back Pip version
try:
    version = parse_version(require("pip")[0].version)
except IndexError:
    version = parse_version("0")
    print("We cannot find the version of pip."
          "We assume that is it inferior to %s." % SPIN_PIP_VER)

if version >= SPIN_PIP_VER:
    install_requires.append('mininet @ git+https://github.com/mininet/mininet@{ver}'
                            .format(ver=MININET_VERSION))
else:
    print("You should run pip with --process-dependency-links to install all the dependencies")
    install_requires.append('mininet=={ver}'.format(ver=MININET_VERSION))
    dependency_links.append('git+https://github.com/mininet/mininet@{ver}#egg=mininet-{ver}'
                            .format(ver=MININET_VERSION))


def setup_mininet_dep():
    """
    Install the Mininet dependencies
    """
    mn_dir = "mininet_dependencies"
    if not os.path.exists(os.path.join("/opt", mn_dir)):
        tmp_dir = os.path.dirname(__file__)
        sys.path.insert(0, os.path.join(tmp_dir, "ipmininet/install"))
        from install import install_mininet

        mininet_dir = os.path.join(tmp_dir, "mininet_dependencies")
        os.mkdir(mininet_dir)

        install_mininet(mininet_dir, pip_install=False)
        shutil.move(mininet_dir, "/opt")


class PostDevelopCommand(develop):
    """Post-installation for development mode."""
    def run(self):
        setup_mininet_dep()
        develop.run(self)


class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        setup_mininet_dep()
        install.run(self)


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
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: System :: Networking",
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9'
        ],
    keywords='networking OSPF IP BGP quagga mininet',
    license='GPLv2',
    install_requires=install_requires,
    dependency_links=dependency_links,
    tests_require=['pytest'],
    setup_requires=['pytest-runner'],
    url='https://github.com/cnp3/ipmininet',
    cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand,
    },
)
