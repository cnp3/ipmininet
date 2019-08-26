"""Base classes to configure a BGP daemon"""
from builtins import str

import itertools

from ipaddress import ip_network, ip_address

from ipmininet.overlay import Overlay
from ipmininet.utils import realIntfList
from .zebra import QuaggaDaemon, Zebra, RouteMap, AccessList, AccessListEntry, RouteMapMatchCond, CommunityList, \
    RouteMapSetAction

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

    for peering in itertools.combinations(routers, 2):
        _set_peering(peering)


def bgp_peering(topo, a, b):
    """Register a BGP peering between two nodes"""
    topo.getNodeInfo(a, 'bgp_peers', list).append(b)
    topo.getNodeInfo(b, 'bgp_peers', list).append(a)


def ebgp_session(topo, a, b):
    """Register an eBGP peering between two nodes, and disable IGP adjacencies
    between them."""
    bgp_peering(topo, a, b)
    topo.linkInfo(a, b)['igp_passive'] = True


def set_local_pref(topo, local, remote, value, filter_names, filter_type):
    """Set a local pref on a link between two nodes

    :param topo: The current topology
    :param local: The router that apply the routemap
    :param remote: The peer to which the routemap is applied
    :param filter_names: Name of the filter
    :param filter_type: Type of filter (Access or Community list)"""
    match_cond = []
    for filter_name in filter_names:
        match_cond.append(RouteMapMatchCond(filter_type, filter_name))
    route_maps = topo.getNodeInfo(local, 'bgp_route_maps', list)
    route_maps.append((value, remote, match_cond, 'local-preference', 'in'))


def set_med(topo, local, remote, value, filter_names, filter_type):
    """Set bgp med on an exported route

    :param topo: The current topology
    :param local: The router that apply the routemap
    :param remote: The peer to which the routemap is applied
    :param filter_names: Name of the filter
    :param filter_type: Type of filter (Access or Community list)
    """
    match_cond = []
    for filter_name in filter_names:
        match_cond.append(RouteMapMatchCond(filter_type, filter_name))
    route_maps = topo.getNodeInfo(local, 'bgp_route_maps', list)
    route_maps.append((value, remote, match_cond, 'metric', 'out'))


def new_access_list(topo, locals, name, entries=()):
    """
    Create a new access list for the router local

    :param topo: The current topology
    :param locals: List of routers that need the access list
    :param name: Name of the access list
    :param entries: List of prefix to filter
    """
    for local in locals:
        access_lists = topo.getNodeInfo(local, 'bgp_access_lists', list)
        access_lists.append(AccessList(name=name, entries=entries))


def new_community_list(topo, locals, name, community):
    """
    Create a new community list for the router local

    :param topo: The current topology
    :param local: List of routers that need the community list
    :param name: Name of the community list
    :param community: Community to filter
    """
    for local in locals:
        community_lists = topo.getNodeInfo(local, 'bgp_community_lists', list)
        community_lists.append(CommunityList(name=name, community=community))


def set_community(topo, local, remote, value, filter_names, filter_type, direction='out'):
    """
    Set community on imported or exported route

    :param topo: The current topology
    :param local: The router that apply the routemap
    :param remote: The peer to which the routemap is applied
    :param filter_names: Name of the filter
    :param filter_type: Type of filter (Access or Community list)
    """
    match_cond = []
    for filter_name in filter_names:
        match_cond.append(RouteMapMatchCond(filter_type, filter_name))
    route_maps = topo.getNodeInfo(local, 'bgp_route_maps', list)
    route_maps.append((value, remote, match_cond, 'community', direction))


def set_rr(topo, rr, peers=()):
    """
    Set rr as route reflector for all router r

    :param topo: The current topology
    :param rr: The route reflector
    :param routers: List of peers for the rr
    """
    for r in peers:
        rr_client = topo.getNodeInfo(rr, 'bgp_rr_info', list)
        bgp_peering(topo, rr, r)
        rr_client.append(r)


class BGP(QuaggaDaemon):
    """This class provides the configuration skeletons for BGP routers."""
    NAME = 'bgpd'
    DEPENDS = (Zebra,)
    KILL_PATTERNS = (NAME,)

    @property
    def STARTUP_LINE_EXTRA(self):
        """We add the port to the standard startup line"""
        return '-p %s' % self.port

    def __init__(self, node, port=BGP_DEFAULT_PORT,
                 *args, **kwargs):
        super(BGP, self).__init__(node=node, *args, **kwargs)
        self.port = port

    def build(self):
        cfg = super(BGP, self).build()
        cfg.asn = self._node.asn
        cfg.neighbors = self._build_neighbors()
        cfg.debug = self.options.debug
        cfg.address_families = self._address_families(
            self.options.address_families, cfg.neighbors)
        cfg.access_lists = self.build_access_list()
        cfg.community_lists = self._node.get('bgp_community_lists') if self._node.get('bgp_community_lists') else []
        cfg.route_maps = self.build_route_map()
        cfg.rr = self._build_rr()
        return cfg

    def _build_rr(self):
        rr_info = self._node.get('bgp_rr_info')
        rr_peers = []
        if rr_info is not None:
            for rr in rr_info:
                for v6 in [True, False]:
                    peer = Peer(self._node, rr, v6)
                    if peer.peer:
                        rr_peers.append(peer)
        return rr_peers

    def build_access_list(self):
        node_access_lists = self._node.get('bgp_access_lists')
        access_lists = []
        if node_access_lists is not None:
            for acl_entries in node_access_lists:
                access_lists.append(AccessList(name=acl_entries.name, entries=acl_entries.entries))
        return access_lists

    def build_route_map(self):
        node_route_maps = self._node.get('bgp_route_maps')
        route_maps = []
        if node_route_maps is not None:
            for (value, node, match_cond, action, direction) in node_route_maps:
                peer = Peer(self._node, node, True)
                if not route_maps:
                    route_maps.append(
                        RouteMap(neighbor=peer, direction=direction,  match_cond=match_cond,
                                 set_actions=((action, value),)))
                else:
                    for route_map in route_maps:
                        if route_map.neighbor.peer == peer.peer and route_map.direction == direction:
                            route_map.append_match_cond(match_cond)
                            route_map.append_set_action((RouteMapSetAction(action, value),))
                        else:
                            route_maps.append(
                                RouteMap(neighbor=peer, direction=direction,  match_cond=match_cond,
                                         set_actions=((action, value),)))
        return route_maps

    def set_defaults(self, defaults):
        """:param debug: the set of debug events that should be logged
        :param address_families: The set of AddressFamily to use"""
        defaults.address_families = [AF_INET(), AF_INET6()]
        super(BGP, self).set_defaults(defaults)

    def _build_neighbors(self):
        """Compute the set of BGP peers for this BGP router
        :return: set of neighbors"""
        neighbors = []
        for x in self._node.get('bgp_peers', []):
            for v6 in [True, False]:
                peer = Peer(self._node, x, v6=v6)
                if peer.peer:
                    neighbors.append(peer)
        return neighbors

    # Define a function that deal wtih the route map function
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
        self.networks = [ip_network(str(n)) for n in networks]
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

    def __init__(self, base, node, v6=False):
        """:param base: The base router that has this peer
        :param node: The actual peer"""
        self.peer, other = self._find_peer_address(base, node, v6=v6)
        if not self.peer:
            return
        self.asn = other.asn
        self.family = 'ipv4' if not v6 else 'ipv6'
        try:
            self.port = other.config.daemon(BGP).port
        except KeyError:  # No configured daemon - yet - use default
            self.port = BGP_DEFAULT_PORT
        # We default to nexthop self for all peering type
        self.nh_self = 'next-hop-self force'
        # We enable eBGP multihop if eBGP is in use
        ebgp = self.asn != base.asn
        self.ebgp_multihop = ebgp
        self.description = '%s (%sBGP)' % (node, 'e' if ebgp else 'i')

    @staticmethod
    def _find_peer_address(base, peer, v6=False):
        """Return the IP address that base should try to contact to establish
        a peering"""
        visited = set()
        to_visit = realIntfList(base)
        # Explore all interfaces in base ASN recursively, until we find one
        # connected to the peer
        while to_visit:
            i = to_visit.pop(0)
            if i in visited:
                continue
            visited.add(i)
            for n in i.broadcast_domain.routers:
                if n.node.name == peer:
                    if not v6:
                        return n.ip, n.node
                    elif n.ip6 and not ip_address(n.ip6).is_link_local:
                        return n.ip6, n.node
                    else:
                        return None, None
                elif n.node.asn == base.asn or not n.node.asn:
                    to_visit.extend(realIntfList(n.node))
        return None, None
