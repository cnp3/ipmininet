"""Base classes to configure a BGP daemon"""
import itertools

from ipaddress import ip_network

from ipmininet.overlay import Overlay
from ipmininet.utils import realIntfList
from .zebra import QuaggaDaemon, Zebra


BGP_DEFAULT_PORT = 179


class AS(Overlay):
    """An overlay class that groups routers by AS number"""

    def __init__(self, asn, routers=(), **props):
        """:param asn: The number for this AS
        :param routers: an initial set of routers to add to this AS
        :param props: key-vals to set on all routers of this AS"""
        super(AS, self).__init__(nodes=routers, nprops=props)
        self.asn = asn

    @property
    def asn(self):
        return self.nodes_properties['asn']

    @asn.setter
    def asn(self, x):
        x = int(x)
        self.nodes_properties['asn'] = x

    def __str__(self):
        return '<AS %s>' % self.asn


class iBGPFullMesh(AS):
    """An overlay class to establish iBGP sessions in full mesh between BGP
    routers."""

    def apply(self, topo):
        # Quagga auto-detect whether to use iBGP or eBGP depending on ASN
        # So we simply make a full mesh with everyone
        bgp_fullmesh(topo, self.nodes)
        super(iBGPFullMesh, self).apply(topo)

    def __str__(self):
        return '<iBGPMesh %s>' % self.asn


def bgp_fullmesh(topo, routers):
    """Establish a full-mesh set of BGP peerings between routers

    :param routers: The set of routers peering within each other"""
    def _set_peering(x):
        bgp_peering(topo, x[0], x[1])
    map(_set_peering, itertools.combinations(routers, 2))


def bgp_peering(topo, a, b):
    """Register a BGP peering between two nodes"""
    topo.getNodeInfo(a, 'bgp_peers', list).append(b)
    topo.getNodeInfo(b, 'bgp_peers', list).append(a)


def ebgp_session(topo, a, b):
    """Register an eBGP peering between two nodes, and disable IGP adjacencies
    between them."""
    bgp_peering(topo, a, b)
    topo.linkInfo(a, b)['igp_passive'] = True


class BGP(QuaggaDaemon):
    """This class provides the configuration skeletons for BGP routers."""
    NAME = 'bgpd'
    DEPENDS = (Zebra,)
    KILL_PATTERNS = (NAME,)

    @property
    def STARTUP_LINE_EXTRA(self):
        # We add the port to the standard startup line
        return '-p %s' % self.port

    def __init__(self, node, port=BGP_DEFAULT_PORT,
                 *args, **kwargs):
        super(BGP, self).__init__(node=node, *args, **kwargs)
        self.port = port

    def build(self):
        cfg = super(BGP, self).build()
        cfg.asn = self._node.asn
        cfg.neighbors = self._build_neighbors()
        cfg.address_families = self._address_families(
            self.options.address_families, cfg.neighbors)
        return cfg

    def set_defaults(self, defaults):
        """:param address_families: The set of AddressFamily to use"""
        defaults.address_families = []
        super(BGP, self).set_defaults(defaults)

    def _build_neighbors(self):
        """Compute the set of BGP peers for this BGP router
        :return: set of neighbors"""
        return [Peer(self._node, x) for x in self._node.get('bgp_peers', [])]

    def _address_families(self, af, nei):
        """Complete the address families: add extra networks, or activate
        neighbors. The default is to activate all given neighbors"""
        for a in af:
            a.neighbors.extend(nei)
        return af


class AddressFamily(object):
    """An address family that is exchanged through BGP"""

    def __init__(self, af_name, redistribute=(), networks=(),
                 *args, **kwargs):
        self.name = af_name
        self.networks = map(ip_network, map(unicode, networks))
        self.redistribute = redistribute
        self.neighbors = []
        super(AddressFamily, self).__init__()


def AF_INET(*args, **kwargs):
    """The ipv4 (unicast) address family"""
    return AddressFamily('ipv4', *args, **kwargs)


def AF_INET6(*args, **kwargs):
    """The ipv6 (unicast) address family"""
    return AddressFamily('ipv6', *args, **kwargs)


class Peer(object):
    """A BGP peer"""
    def __init__(self, base, node):
        """:param base: The base router that has this peer
        :param node: The actual peer"""
        self.peer, other = self._find_peer_address(base, node)
        self.asn = other.asn
        try:
            self.port = other.config.daemon(BGP).port
        except KeyError:  # No configured daemon - yet - use default
            self.port = BGP_DEFAULT_PORT
        # We default to nexthop self for all peering type
        self.nh_self = 'next-hop-self all'
        # We enable eBGP multihop if eBGP is in use
        ebgp = self.asn != base.asn
        self.ebgp_multihop = ebgp
        self.description = '%s (%sBGP)' % (node, 'e' if ebgp else 'i')

    @staticmethod
    def _find_peer_address(base, peer):
        """Return the IP address that base should try to contact to establish
        a peering"""
        visited = set()
        to_visit = realIntfList(base)
        # Explore all interfaces in base ASN recursively, until we find one
        # connected to the peer
        while to_visit:
            i = to_visit.pop()
            if i in visited:
                continue
            visited.add(i)
            for n in i.broadcast_domain.routers:
                if n.node.name == peer:
                    ip = n.ip
                    return (ip, n.node) if ip else (
                        n.ip6, n.node)
                elif n.node.asn == base.asn or not n.node.asn:
                    to_visit.extend(realIntfList(n.node))
        return None, None
