"""This modules provides a config object for a host,
that is able to provide configurations for a set of daemons.
It also defines the base class for a host daemon, as well as a minimalistic
configuration for a host."""
from future.utils import with_metaclass

import abc
import os

from mako.lookup import TemplateLookup

from ipmininet.router.config.base import NodeConfig, Daemon


__TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')
host_template_lookup = TemplateLookup(directories=[__TEMPLATES_DIR])


class HostDaemon(with_metaclass(abc.ABCMeta, Daemon)):
    def __init__(self, node, template_lookup=host_template_lookup, **kwargs):
        super(HostDaemon, self).__init__(node, template_lookup=template_lookup,
                                         **kwargs)


class HostConfig(NodeConfig):
    pass
