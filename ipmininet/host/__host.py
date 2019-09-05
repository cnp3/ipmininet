"""This modules defines a host class,
   with a modulable config system."""
import mininet.node as _m

from ipmininet.router import IPNode
from ipmininet.host.config.base import HostConfig


class IPHost(IPNode):
    """A Host which manages a set of daemons"""

    def __init__(self, name,
                 config=HostConfig,
                 *args, **kwargs):
        super(IPHost, self).__init__(name, config=config, *args, **kwargs)


CPULimitedHost = _m.CPULimitedHost
CPULimitedHost.__bases__ = (IPHost,)
