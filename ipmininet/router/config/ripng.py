"""Base classes to configure a RIP daemon"""
from ipaddress import ip_interface, IPv6Interface
from typing import List

from ipmininet.link import IPIntf
from ipmininet.utils import L3Router
from .utils import ConfigDict
from .zebra import QuaggaDaemon, Zebra

UPDATE_TIMER = 30
TIMEOUT_TIMER = 180
GARBAGE_TIMER = 120


class RIPng(QuaggaDaemon):
    """This class provides a simple configuration for an RIP daemon.
    It advertizes one network per interface (the primary one),
    and set interfaces not facing another L3Router to passive"""
    NAME = 'ripngd'
    DEPENDS = (Zebra,)
    KILL_PATTERNS = (NAME,)

    def build(self):
        cfg = super().build()
        cfg.redistribute = self.options.redistribute
        cfg.split_horizon = self.options.split_horizon
        cfg.split_horizon_with_poison = self.options.split_horizon_with_poison
        cfg.update_timer = self.options.update_timer
        cfg.timeout_timer = self.options.timeout_timer
        cfg.garbage_timer = self.options.garbage_timer
        interfaces = self._node.intfList()
        cfg.interfaces = self._build_interfaces(interfaces)
        cfg.networks = self._build_networks(interfaces)
        return cfg

    @staticmethod
    def _build_networks(interfaces: List[IPIntf]) -> List['RIPNetwork']:
        """Return the list of RIP networks to advertize from the list of
        active RIP interfaces"""
        return [RIPNetwork(domain=ip_interface('%s/%s' % (i.ip6, i.prefixLen6)))
                for i in interfaces if i.ip6]

    def _build_interfaces(self, interfaces: List[IPIntf]) -> List[ConfigDict]:
        """Return the list of RIP interface properties from the list of
        active interfaces"""
        return [ConfigDict(description=i.describe,
                           name=i.name,
                           # Is the interface between two routers?
                           active=self.is_active_interface(i),
                           cost=i.igp_metric - 1,
                           domain=ip_interface('%s/%s'
                                               % (i.ip6, i.prefixLen6)))
                for i in interfaces]

    def set_defaults(self, defaults):
        """:param debug: the set of debug events that should be logged
                         (default: []).
        :param redistribute: set of RIPngRedistributedRoute sources
                             (default: []).
        :param split_horizon: the daemon uses the split-horizon method
                              (default: False).
        :param split_horizon_with_poison: the daemon uses the split-horizon.
         with reversed poison method. If both split_horizon_with_poison
         and split_horizon are set to True, RIPng will use the split-horizon
         with reversed poison method (default: True).
        :param update_timer: routing table timer value in second
                             (default value:30).
        :param timeout_timer: routing information timeout timer
                              (default value:180).
        :param garbage_timer: garbage collection timer
                              (default value:120)."""
        defaults.redistribute = []
        defaults.split_horizon = False
        defaults.split_horizon_with_poison = True
        defaults.update_timer = UPDATE_TIMER
        defaults.timeout_timer = TIMEOUT_TIMER
        defaults.garbage_timer = GARBAGE_TIMER
        super().set_defaults(defaults)

    @staticmethod
    def is_active_interface(itf) -> bool:
        """Return whether an interface is active or not for the RIPng daemon"""
        if itf.broadcast_domain is None:
            return False
        return any(L3Router.is_l3router_intf(i) for i in itf.broadcast_domain
                   if i != itf)


class RIPNetwork:
    """A class holding an RIP network properties"""

    def __init__(self, domain: IPv6Interface):
        self.domain = domain


class RIPRedistributedRoute:
    """A class representing a redistributed route type in RIP"""

    def __init__(self, subtype: str, metric=1000):
        self.subtype = subtype
        self.metric = metric
