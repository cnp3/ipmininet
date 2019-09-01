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
    NAME = 'ripngd'
    DEPENDS = (Zebra,)
    KILL_PATTERNS = (NAME,)

    def __init__(self, node, *args, **kwargs):
        super(RIPng, self).__init__(node=node, *args, **kwargs)

    def build(self):
        cfg = super(RIPng, self).build()
        cfg.redistribute = self.options.redistribute
        cfg.split_horizon = self.options.split_horizon
        cfg.split_horizon_with_poison = self.options.split_horizon_with_poison
        cfg.timers = self._build_timers(self.options.update_timer, self.options.timeout_timer, self.options.garbage_timer)
        interfaces = [itf
                      for itf in realIntfList(self._node)]
        cfg.interfaces = self._build_interfaces(interfaces)
        cfg.networks = self._build_networks(interfaces)
        return cfg

    def _build_networks(self, interfaces):
        """Return the list of RIP networks to advertize from the list of
        active RIP interfaces"""
        return [RIPNetwork(domain=ip_interface(
            u'%s/%s' % (i.ip6, i.prefixLen6))) for i in interfaces if i.ip6]

    def _build_interfaces(self, interfaces):
        """Return the list of RIP interface properties from the list of
        active interfaces"""
        return [ConfigDict(description=i.describe,
                           name=i.name,
                           # Is the interface between two routers?
                           active=self.is_active_interface(i),
                           cost=i.igp_metric-1,
                           domain=ip_interface(u'%s/%s' % (i.ip6, i.prefixLen6)))
                for i in interfaces]
    
    def _build_timers(self, update, timeout, garbage):
        """Return a list of timer values for RIP for the router
        :param update: routing table timer value in second (default value:30)
        :param timeout: routing information timeout timer (default value:180)
        :param garbage: garbage collection timer (default value:120)"""
        t = []
        t.append(update) if update else t.append(30)
        t.append(timeout) if timeout else t.append(180)
        t.append(garbage) if garbage else t.append(120)
        return ' '.join([str(e) for e in t])
    
    def set_defaults(self, defaults):
        """:param debug: the set of debug events that should be logged
        :param redistribute: set of RIPngRedistributedRoute sources"""
        defaults.redistribute = []
        super(RIPng, self).set_defaults(defaults)
    
    def is_active_interface(self, itf):
        """Return whether an interface is active or not for the OSPF daemon"""
        return L3Router.is_l3router_intf(otherIntf(itf))


class RIPNetwork(object):
    """A class holding an RIP network properties"""

    def __init__(self, domain):
        self.domain = domain

class RIPRedistributedRoute(object):
    """A class representing a redistributed route type in RIP"""

    def __init__(self, subtype, metric_type=1, metric=1000):
        self.subtype = subtype
        self.metric_type = metric_type
        self.metric = metric