"""Base classes to configure a RIP daemon"""
from ipaddress import ip_interface

from ipmininet.overlay import Overlay
from ipmininet.utils import otherIntf, L3Router, realIntfList
from .utils import ConfigDict
from .zebra import QuaggaDaemon, Zebra

class RIPng(QuaggaDaemon):
    """This class provides a simple configuration for an RIP daemon.
    It advertizes one network per interface (the primary one), (WORK IN PROGRESS) 
    and set interfaces not facing another L3Router to passive"""
    NAME = 'ripng'
    DEPENDS = (Zebra,)
    KILL_PATTERNS = (NAME,)

    def __init__(self, node, *args, **kwargs):
        super(RIPng, self).__init__(node=node, *args, **kwargs)

    def build(self):
        cfg = super(RIPng, self).build()
        #cfg.redistribute = self.options.redistribute
        interfaces = [itf
                      for itf in realIntfList(self._node)]
        cfg.interfaces = self._build_interfaces(interfaces)
        cfg.networks = self._build_networks(interfaces)
        return cfg

    def _build_networks(self, interfaces):
        """Return the list of RIP networks to advertize from the list of
        active RIP interfaces"""
        # Check that we have at least one IPv4 network on that interface ...
        return [RIPNetwork(domain=ip_interface(
            u'%s/%s' % (i.ip, i.prefixLen))) for i in interfaces if i.ip]

    def _build_interfaces(self, interfaces):
        """Return the list of OSPF interface properties from the list of
        active interfaces"""
        return [ConfigDict(description=i.describe,
                           name=i.name,
                           # Is the interface between two routers?
                           active=self.is_active_interface(i),
                           priority=i.get('ospf_priority',
                                          self.options.priority),
                           dead_int=i.get('ospf_dead_int',
                                          self.options.dead_int),
                           hello_int=i.get('ospf_hello_int',
                                           self.options.hello_int),
                           cost=i.igp_metric,
                           # Is the interface forcefully disabled?
                           passive=i.get('igp_passive', False))
                for i in interfaces]
    """
    def set_defaults(self, defaults):
        """""":param debug: the set of debug events that should be logged
        :param dead_int: Dead interval timer
        :param hello_int: Hello interval timer
        :param priority: priority for the interface, used for DR election
        :param redistribute: set of OSPFRedistributedRoute sources""""""
        defaults.dead_int = 'minimal hello-multiplier 5'
        defaults.hello_int = 1
        defaults.priority = 10
        defaults.redistribute = []
        super(RIPng, self).set_defaults(defaults)
    """
    def is_active_interface(self, itf):
        """Return whether an interface is active or not for the OSPF daemon"""
        return L3Router.is_l3router_intf(otherIntf(itf))


class RIPNetwork(object):
    """A class holding an RIP network properties"""

    def __init__(self, domain):
        self.domain = domain

"""
class OSPFRedistributedRoute(object):
    """"""A class representing a redistributed route type in OSPF""""""

    def __init__(self, subtype, metric_type=1, metric=1000):
        self.subtype = subtype
        self.metric_type = metric_type
        self.metric = metric
"""