"""Base classes to configure an OpenR daemon"""
from ipaddress import ip_interface

from ipmininet.overlay import Overlay
from ipmininet.utils import L3Router, realIntfList
from .utils import ConfigDict
from .openrd import OpenrDaemon


class OpenrDomain(Overlay):
    """An overlay to group OpenR links and routers by domain"""

    def __init__(self, domain, routers=(), links=(), **props):
        """:param domain: the domain for this overlay
        :param routers: the set of routers for which all their interfaces
                        belong to that area
        :param links: individual links belonging to this area"""
        super().__init__(nodes=routers, links=links, nprops=props)
        self.domain = domain

    @property
    def domain(self):
        return self.links_properties['openr_domain']

    @domain.setter
    def domain(self, x):
        self.links_properties['openr_domain'] = x

    def apply(self, topo):
        # Add all links for the routers
        for r in self.nodes:
            self.add_link(*topo.g[r])
        super().apply(topo)

    def __str__(self):
        return '<OpenR domain %s>' % self.domain


class Openr(OpenrDaemon):
    """This class provides a simple configuration for an OpenR daemon."""
    NAME = 'openr'
    DEPENDS = (OpenrDaemon,)
    KILL_PATTERNS = (NAME,)

    def __init__(self, node, *args, **kwargs):
        super().__init__(node=node, *args, **kwargs)

    def build(self):
        cfg = super().build()
        cfg.update(self.options)
        cfg.node_name = self._node.name
        interfaces = realIntfList(self._node)
        cfg.interfaces = self._build_interfaces(interfaces)
        cfg.networks = self._build_networks(interfaces)
        cfg.prefixes = self._build_prefixes(interfaces)
        return cfg

    @staticmethod
    def _build_networks(interfaces):
        """Return the list of OpenR networks to advertize from the list of
        active OpenR interfaces"""
        # Check that we have at least one IPv4 network on that interface ...
        return [OpenrNetwork(domain=ip_interface('%s/%s' % (i.ip, i.prefixLen)))
                for i in interfaces if i.ip]

    def _build_interfaces(self, interfaces):
        """Return the list of OpenR interface properties from the list of
        active interfaces"""
        return [ConfigDict(description=i.describe,
                           name=i.name,
                           # Is the interface between two routers?
                           active=self.is_active_interface(i),
                           ) for i in interfaces]

    @staticmethod
    def _build_prefixes(interfaces):
        ipv6_addresses = []
        for itf in interfaces:
            ipv6_addresses += itf.addresses[6]
        ipv6_addresses = filter(lambda x: not x.is_link_local, ipv6_addresses)
        return ",".join(map(lambda x: x.with_prefixlen, ipv6_addresses))

    def set_defaults(self, defaults):
        """Updates some options of the OpenR daemon to run a network of
        routers in mininet. For a full list of parameters see
        OpenrDaemon:_defaults in openrd.py"""
        defaults.ifname_prefix = "r"
        defaults.iface_regex_include = "r.*"
        defaults.log_dir = "/var/log"
        super().set_defaults(defaults)

    @staticmethod
    def is_active_interface(itf):
        """Return whether an interface is active or not for the OpenR daemon"""
        if itf.broadcast_domain is None:
            return False
        return any(L3Router.is_l3router_intf(i) for i in itf.broadcast_domain
                   if i != itf)


class OpenrNetwork:
    """A class holding an OpenR network properties"""

    def __init__(self, domain):
        self.domain = domain


class OpenrPrefixes:
    """A class representing a prefix type in OpenR"""

    def __init__(self, prefixes):
        self.prefixes = prefixes
