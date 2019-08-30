"""Base classes to configure a BGP daemon"""
from builtins import str

import itertools

from ipaddress import ip_network, ip_address

from ipmininet.overlay import Overlay
from ipmininet.utils import realIntfList
from .zebra import QuaggaDaemon, Zebra, RouteMap, AccessList, AccessListEntry, RouteMapMatchCond, CommunityList, \
    RouteMapSetAction, PERMIT, DENY

BGP_DEFAULT_PORT = 179
SHARE = "Share"
CLIENT_PROVIDER = "Client-Provider"


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


def ebgp_session(topo, a, b, link_type=None):
    """Register an eBGP peering between two nodes, and disable IGP adjacencies
    between them.
    :param topo: The current topology
    :param a: Local router
    :param b: Peer router
    :param link_type: Can be set to SHARE or CLIENT_PROVIDER. In this case ebgp_session will create import and export
    filter and set local pref based on the link type
    """
    if link_type:
        all_al = new_access_list('All', ('any',))
        # Create the community filter for the export policy
        for router in [a, b]:
            peers_link = new_community_list('from-peers', 1, action=PERMIT)
            up_link = new_community_list('from-up', 3, action=PERMIT)
            community_lists = topo.getNodeInfo(router, 'bgp_community_lists', list)
            for f in [peers_link, up_link]:
                if f not in community_lists:
                    community_lists.append(f)
        route_maps_a = topo.getNodeInfo(a, 'bgp_route_maps', list)
        route_maps_b = topo.getNodeInfo(b, 'bgp_route_maps', list)

        if link_type == SHARE:
            # Set the community and local pref for the import policy
            set_community(topo, a, b, 1, (all_al,), direction='in')
            set_community(topo, b, a, 1, (all_al,), direction='in')
            set_local_pref(topo, a, b, 150, (all_al,))
            set_local_pref(topo, b, a, 150, (all_al,))

            # Create route maps to filter exported route
            route_maps_a.append(
                {'match_policy': DENY, 'peer': b, 'match_cond': (
                    RouteMapMatchCond('community', 'from-up'),),
                 'direction': 'out', 'name': 'export-to-peer-' + b, })
            route_maps_b.append(
                {'match_policy': DENY, 'peer': a, 'match_cond': (
                    RouteMapMatchCond('community', 'from-up'),),
                 'direction': 'out', 'name': 'export-to-peer-' + a, })
            route_maps_a.append(
                {'match_policy': DENY, 'peer': b, 'match_cond': (
                    RouteMapMatchCond('community', 'from-peers'),),
                 'direction': 'out', 'name': 'export-to-peer-' + b, 'order': 15})
            route_maps_b.append(
                {'match_policy': DENY, 'peer': a, 'match_cond': (
                    RouteMapMatchCond('community', 'from-peers'),),
                 'direction': 'out', 'name': 'export-to-peer-' + a, 'order': 15})
            route_maps_a.append(
                {'match_policy': PERMIT, 'peer': b,
                 'direction': 'out', 'name': 'export-to-peer-' + b, 'order': 20})
            route_maps_b.append(
                {'match_policy': PERMIT, 'peer': a,
                 'direction': 'out', 'name': 'export-to-peer-' + a, 'order': 20})
        elif link_type == CLIENT_PROVIDER:
            # Set the community and local pref for the import policy
            set_community(topo, a, b, 3, (all_al,), direction='in')
            set_community(topo, b, a, 2, (all_al,), direction='in')
            set_local_pref(topo, a, b, 100, (all_al,), )
            set_local_pref(topo, b, a, 200, (all_al,), )

            # Create route maps to filter exported route
            route_maps_a.append(
                {'match_policy': DENY, 'peer': b, 'match_cond': (
                    RouteMapMatchCond('community', 'from-up'),),
                 'direction': 'out', 'name': 'export-to-up-' + b, 'order': 10})
            route_maps_a.append(
                {'match_policy': DENY, 'peer': b, 'match_cond': (
                    RouteMapMatchCond('community', 'from-peers'),),
                 'direction': 'out', 'name': 'export-to-up-' + b, 'order': 15})
            route_maps_a.append(
                {'match_policy': PERMIT, 'peer': b,
                 'direction': 'out', 'name': 'export-to-up-' + b, 'order': 20})

    bgp_peering(topo, a, b)
    topo.linkInfo(a, b)['igp_passive'] = True


def set_local_pref(topo, router, peer, value, filter_list):
    """Set a local pref on a link between two nodes

    :param topo: The current topology
    :param router: The router that apply the routemap
    :param peer: The peer to which the routemap is applied
    :param value: The local pref value to set
    :param filter_list: A list of filter, can be empty
    """
    match_cond = []
    set_actions = []
    access_lists = topo.getNodeInfo(router, 'bgp_access_lists', list)
    community_lists = topo.getNodeInfo(router, 'bgp_community_lists', list)

    # Create match_conditions based on the provided filters
    for f in filter_list:
        if isinstance(f, CommunityList):
            match_cond.append(RouteMapMatchCond('community', f.name))
            if f not in community_lists:
                community_lists.append(f)
        elif isinstance(f, AccessList):
            match_cond.append(RouteMapMatchCond('access-list', f.name))
            if f not in access_lists:
                access_lists.append(f)
        else:
            raise Exception("Filter not yet implemented")

    # Create set action based on the provided value
    set_actions.append(RouteMapSetAction('local-preference', value))
    route_maps = topo.getNodeInfo(router, 'bgp_route_maps', list)
    route_maps.append(
        {'peer': peer, 'match_cond': match_cond, 'set_actions': set_actions, 'direction': 'in'})


def set_med(topo, router, peer, value, filter_list):
    """Set bgp med on an exported route

    :param topo: The current topology
    :param router: The router that apply the routemap
    :param peer: The peer to which the routemap is applied
    :param value: The med value to set
    :param filter_list: A list of filter, can be empty
    """
    match_cond = []
    set_actions = []
    access_lists = topo.getNodeInfo(router, 'bgp_access_lists', list)
    community_lists = topo.getNodeInfo(router, 'bgp_community_lists', list)

    # Create match_conditions based on the provided filters
    for f in filter_list:
        if isinstance(f, CommunityList):
            match_cond.append(RouteMapMatchCond('community', f.name))
            if f not in community_lists:
                community_lists.append(f)
        elif isinstance(f, AccessList):
            match_cond.append(RouteMapMatchCond('access-list', f.name))
            if f not in access_lists:
                access_lists.append(f)
        else:
            raise Exception("Filter not yet implemented")

    # Create set action based on the provided value
    set_actions.append(RouteMapSetAction('metric', value))
    route_maps = topo.getNodeInfo(router, 'bgp_route_maps', list)
    route_maps.append(
        {'peer': peer, 'match_cond': match_cond, 'set_actions': set_actions, 'direction': 'out'})


def set_community(topo, router, peer, value, filter_list, direction):
    """
    Set community on imported or exported route

    :param topo: The current topology
    :param router: The router that apply the routemap
    :param peer: The peer to which the routemap is applied
    :param value: The value of the community as:com, if you only specify com the asn of the router will be automatically set
    :param filter_list: A lise of filter, can be empty
    :param direction: direction of the route map(in, out, both)
    """
    match_cond = []
    set_actions = []
    access_lists = topo.getNodeInfo(router, 'bgp_access_lists', list)
    community_list = topo.getNodeInfo(router, 'bgp_community_lists', list)

    # Create match_conditions based on the provided filters
    for f in filter_list:
        if isinstance(f, CommunityList):
            match_cond.append(RouteMapMatchCond('community', f.name))
            if f not in community_list:
                community_list.append(f)
        elif isinstance(f, AccessList):
            match_cond.append(RouteMapMatchCond('access-list', f.name))
            if f not in access_lists:
                access_lists.append(f)
        else:
            raise Exception("Filter not yet implemented")

    # Create set action based on the provided value
    set_actions.append(RouteMapSetAction('community', value))
    route_maps = topo.getNodeInfo(router, 'bgp_route_maps', list)
    route_maps.append(
        {'peer': peer, 'match_cond': match_cond, 'set_actions': set_actions, 'direction': direction})


def new_access_list(name, entries=()):
    """
    Create and return new access list to be used as a filter for RouteMap

    :param name: Name of the access list
    :param entries: List of prefix to filter
    """
    return AccessList(name=name, entries=entries)


def new_community_list(name, community, action=PERMIT):
    """
    Create a new community list to be used as a filter for RouteMap

    :param name: Name of the community list
    :param community: Community to filter
    :param action:
    """
    return CommunityList(name=name, community=community, action=action)


def set_rr(topo, rr, peers=()):
    """
    Set rr as route reflector for all router r

    :param topo: The current topology
    :param rr: The route reflector
    :param peers: Clients of the route reflector
    """
    for r in peers:
        bgp_peering(topo, rr, r)
    router_is_rr = topo.getNodeInfo(rr, 'bgp_rr_info', list)
    router_is_rr.append(True)


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
        cfg.address_families = self._address_families(
            self.options.address_families, cfg.neighbors)
        cfg.access_lists = self.build_access_list()
        cfg.community_lists = self.build_community_list()
        cfg.route_maps = self.build_route_map(cfg.neighbors)
        cfg.rr = self._node.get('bgp_rr_info')

        return cfg

    def build_community_list(self):
        """
        Build and return a list of community_filter
        """
        node_community_lists = self._node.get('bgp_community_lists')
        if node_community_lists:
            for list in node_community_lists:
                # If community is an int change it to the right format asn:community by adding node asn
                if isinstance(list.community, int):
                    list.community = '%s:%d' % (self._node.asn, list.community)
            return node_community_lists
        else:
            return []

    def build_access_list(self):
        """
        Build and return a list of acess_filter
        :return:
        """
        node_access_lists = self._node.get('bgp_access_lists')
        access_lists = []
        if node_access_lists is not None:
            for acl_entries in node_access_lists:
                access_lists.append(AccessList(name=acl_entries.name, entries=acl_entries.entries))
        return access_lists

    def build_route_map(self, neigbors):
        """
        Build and return a list of route map for the current node
        """
        node_route_maps = self._node.get('bgp_route_maps')
        route_maps = []
        if node_route_maps is not None:
            for kwargs in node_route_maps:
                remote_peer = kwargs.pop('peer')
                peers = []
                for neighbor in neigbors:
                    if neighbor.node == remote_peer:
                        peers.append(neighbor)
                for peer in peers:
                    kwargs['neighbor'] = peer
                    rm = RouteMap(**kwargs)
                    # If route map already exist, add conditions and actions to it
                    try:
                        index = route_maps.index(rm)
                        tmp_rm = route_maps.pop(index)
                        rm.append_match_cond(tmp_rm.match_cond)
                        rm.append_set_action(tmp_rm.set_actions)
                    except ValueError:
                        pass
                    route_maps.append(rm)
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
        self.node = node
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
            i = to_visit.pop()
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
