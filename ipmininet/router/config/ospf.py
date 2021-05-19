"""Base classes to configure an OSPF daemon"""
from ipaddress import ip_interface, IPv4Network
from typing import Sequence, List

from ipmininet.link import IPIntf
from ipmininet.overlay import Overlay
from ipmininet.utils import L3Router
from .utils import ConfigDict
from .zebra import QuaggaDaemon, Zebra


class OSPFArea(Overlay):
    """An overlay to group OSPF links and routers by area"""

    def __init__(self, area: str, routers: Sequence[str] = (),
                 links: Sequence[str] = (), **props):
        """:param area: the area for this overlay
        :param routers: the set of routers for which all their interfaces
                        belong to that area
        :param links: individual links belonging to this area"""
        super().__init__(nodes=routers, links=links, nprops=props)
        self.area = area

    @property
    def area(self) -> str:
        return self.links_properties['igp_area']

    @area.setter
    def area(self, x: str):
        self.links_properties['igp_area'] = x
        # Also set node property so we can use it for the loopback interface
        self.nodes_properties['igp_area'] = x

    def apply(self, topo):
        # Add all links for the routers
        for r in self.nodes:
            self.add_link(*[(r, x) for x in topo.g[r].keys()])
        super().apply(topo)

    def __str__(self):
        return '<OSPF area %s>' % self.area


class OSPF(QuaggaDaemon):
    """This class provides a simple configuration for an OSPF daemon.
    It advertizes one network per interface (the primary one), and set
    interfaces not facing another L3Router to passive"""
    NAME = 'ospfd'
    DEPENDS = (Zebra,)
    KILL_PATTERNS = (NAME,)

    def __init__(self, node, *args, **kwargs):
        super().__init__(node=node, *args, **kwargs)

    def build(self):
        cfg = super().build()
        cfg.redistribute = self.options.redistribute
        interfaces = self._node.intfList()
        cfg.interfaces = self._build_interfaces(interfaces)
        cfg.networks = self._build_networks(interfaces)
        return cfg

    @staticmethod
    def _build_networks(interfaces: List[IPIntf]) -> List['OSPFNetwork']:
        """Return the list of OSPF networks to advertize from the list of
        active OSPF interfaces"""
        # Check that we have at least one IPv4 network on that interface ...
        return [OSPFNetwork(domain=ip_interface('%s/%s' % (i.ip, i.prefixLen)),
                            area=i.igp_area) for i in interfaces if i.ip]

    def _build_interfaces(self, interfaces: List[IPIntf]) -> List[ConfigDict]:
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

    def set_defaults(self, defaults):
        """:param debug: the set of debug events that should be logged
        :param dead_int: Dead interval timer
        :param hello_int: Hello interval timer
        :param priority: priority for the interface, used for DR election
        :param redistribute: set of OSPFRedistributedRoute sources"""
        defaults.dead_int = 'minimal hello-multiplier 5'
        defaults.hello_int = 1
        defaults.priority = 10
        defaults.redistribute = []
        super().set_defaults(defaults)

    @staticmethod
    def is_active_interface(itf) -> bool:
        """Return whether an interface is active or not for the OSPF daemon"""
        if itf.broadcast_domain is None:
            return False
        return any(L3Router.is_l3router_intf(i) for i in itf.broadcast_domain
                   if i != itf)


class OSPFNetwork:
    """A class holding an OSPF network properties"""

    def __init__(self, domain: IPv4Network, area: str):
        self.domain = domain
        self.area = area


class OSPFRedistributedRoute:
    """A class representing a redistributed route type in OSPF"""

    def __init__(self, subtype: str, metric_type=1, metric=1000):
        self.subtype = subtype
        self.metric_type = metric_type
        self.metric = metric
