"""Base classes to configure a BGP daemon"""
import heapq
from typing import Sequence, TYPE_CHECKING, Optional, Union, Tuple, List, Set

import itertools

from ipaddress import ip_network, ip_address, IPv4Network, IPv6Network

from ipmininet.link import IPIntf
from ipmininet.overlay import Overlay
from ipmininet.utils import realIntfList
from .zebra import QuaggaDaemon, Zebra, RouteMap, AccessList, \
    RouteMapMatchCond, CommunityList, RouteMapSetAction, PERMIT, DENY

if TYPE_CHECKING:
    from ipmininet.iptopo import IPTopo
    from ipmininet.node_description import RouterDescription
    from ipmininet.router import Router


BGP_DEFAULT_PORT = 179
SHARE = "Share"
CLIENT_PROVIDER = "Client-Provider"


class AS(Overlay):
    """An overlay class that groups routers by AS number"""

    def __init__(self, asn: int, routers=(), **props):
        """:param asn: The number for this AS
        :param routers: an initial set of routers to add to this AS
        :param props: key-values to set on all routers of this AS"""
        super().__init__(nodes=routers, nprops=props)
        self.asn = asn

    @property
    def asn(self) -> int:
        return self.nodes_properties['asn']

    @asn.setter
    def asn(self, x: int):
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
        super().apply(topo)

    def __str__(self):
        return '<iBGPMesh %s>' % self.asn


def bgp_fullmesh(topo, routers: Sequence[str]):
    """Establish a full-mesh set of BGP peerings between routers

    :param topo: The current topology
    :param routers: The set of routers peering within each other"""
    def _set_peering(x):
        bgp_peering(topo, x[0], x[1])

    for peering in itertools.combinations(routers, 2):
        _set_peering(peering)


def bgp_peering(topo: 'IPTopo', a: str, b: str):
    """Register a BGP peering between two nodes"""
    topo.getNodeInfo(a, 'bgp_peers', list).append(b)
    topo.getNodeInfo(b, 'bgp_peers', list).append(a)


def ebgp_session(topo: 'IPTopo', a: 'RouterDescription', b: 'RouterDescription',
                 link_type: Optional[str] = None):
    """Register an eBGP peering between two nodes, and disable IGP adjacencies
    between them.

    :param topo: The current topology
    :param a: Local router
    :param b: Peer router
    :param link_type: Can be set to SHARE or CLIENT_PROVIDER. In this case
                      ebgp_session will create import and export
                      filter and set local pref based on the link type
    """
    if link_type:
        all_al = AccessList('All', ('any',))
        # Create the community filter for the export policy
        peers_link = CommunityList(name='from-peers', community=1,
                                   action=PERMIT)
        up_link = CommunityList(name='from-up', community=3, action=PERMIT)

        if link_type == SHARE:
            # Set the community and local pref for the import policy
            a.get_config(BGP)\
                .set_community(1, from_peer=b, matching=(all_al,)) \
                .set_local_pref(150, from_peer=b, matching=(all_al,))
            b.get_config(BGP)\
                .set_community(1, from_peer=a, matching=(all_al,))\
                .set_local_pref(150, from_peer=a, matching=(all_al,))

            # Create route maps to filter exported route
            a.get_config(BGP)\
                .deny('export-to-peer-' + b, to_peer=b, matching=(up_link,),
                      order=10)\
                .deny('export-to-peer-' + b, to_peer=b, matching=(peers_link,),
                      order=15)\
                .permit('export-to-peer-' + b, to_peer=b, order=20)

            b.get_config(BGP)\
                .deny('export-to-peer-' + a, to_peer=a, matching=(up_link,),
                      order=10)\
                .deny('export-to-peer-' + a, to_peer=a, matching=(peers_link,),
                      order=15)\
                .permit('export-to-peer-' + a, to_peer=a, order=20)

        elif link_type == CLIENT_PROVIDER:
            # Set the community and local pref for the import policy
            a.get_config(BGP)\
                .set_community(3, from_peer=b, matching=(all_al,)) \
                .set_local_pref(100, from_peer=b, matching=(all_al,))
            b.get_config(BGP)\
                .set_community(2, from_peer=a, matching=(all_al,))\
                .set_local_pref(200, from_peer=a, matching=(all_al,))

            # Create route maps to filter exported route
            a.get_config(BGP)\
                .deny('export-to-up-' + b, to_peer=b, matching=(up_link,),
                      order=10)\
                .deny('export-to-up-' + b, to_peer=b, matching=(peers_link,),
                      order=15)\
                .permit('export-to-up-' + b, to_peer=b, order=20)

    bgp_peering(topo, a, b)
    topo.linkInfo(a, b)['igp_passive'] = True


class BGPConfig:

    def __init__(self, topo: 'IPTopo', router: 'RouterDescription'):
        self.topo = topo
        self.router = router

    def set_local_pref(self, local_pref: int, from_peer: str,
                       matching: Sequence[Union[AccessList, CommunityList]] =
                       ()) -> 'BGPConfig':
        """Set local pref on a peering with 'from_peer' on routes
         matching all of the access and community lists in 'matching'

        :param local_pref: The local pref value to set
        :param from_peer: The peer on which the local pref is applied
        :param matching: A list of AccessList and/or CommunityList
        :return: self
        """
        self.add_set_action(peer=from_peer,
                            set_action=RouteMapSetAction('local-preference',
                                                         local_pref),
                            matching=matching, direction='in')
        return self

    def set_med(self, med: int, to_peer: str,
                matching: Sequence[Union[AccessList, CommunityList]] = ()) \
            -> 'BGPConfig':
        """Set MED on a peering with 'to_peer' on routes
         matching all of the access and community lists in 'matching'

        :param med: The local pref value to set
        :param to_peer: The peer to which the med is applied
        :param matching: A list of AccessList and/or CommunityList
        :return: self
        """
        self.add_set_action(peer=to_peer,
                            set_action=RouteMapSetAction('metric', med),
                            matching=matching, direction='out')
        return self

    def set_community(self, community: Union[str, int],
                      from_peer: Optional[str] = None,
                      to_peer: Optional[str] = None,
                      matching: Sequence[Union[AccessList, CommunityList]] =
                      ()) -> 'BGPConfig':
        """Set community on a routes received from 'from_peer'
         and routes sent to 'to_peer' on routes matching
         all of the access and community lists in 'matching'

        :param community: The community value to set
        :param from_peer: The peer on which received routes have to have
                          the community
        :param to_peer: The peer on which sent routes have to have the community
        :param matching: A list of AccessList and/or CommunityList
        :return: self
        """
        if to_peer is not None:
            self.add_set_action(peer=to_peer,
                                set_action=RouteMapSetAction('community',
                                                             community),
                                matching=matching, direction='out')
        if from_peer is not None:
            self.add_set_action(peer=from_peer,
                                set_action=RouteMapSetAction('community',
                                                             community),
                                matching=matching, direction='in')
        return self

    def filter(self, name: Optional[str] = None, policy=DENY,
               from_peer: Optional[str] = None, to_peer: Optional[str] = None,
               matching: Sequence[Union[AccessList, CommunityList]] = (),
               order=10) -> 'BGPConfig':
        """Either accept or deny all routes received from 'from_peer'
         and routes sent to 'to_peer' matching
         all of the access and community lists in 'matching'

        :param name: The name of the route-map
        :param policy: Either 'deny' or 'permit'
        :param from_peer: The peer on which received routes have to have
                          the community
        :param to_peer: The peer on which sent routes have to have the community
        :param matching: A list of AccessList and/or CommunityList
        :param order: The order in which route-maps are applied,
         i.e., lower order means applied before
        :return: self
        """
        route_maps = self.topo.getNodeInfo(self.router, 'bgp_route_maps', list)
        if from_peer:
            route_maps.append({
                'match_policy': policy,
                'peer': from_peer,
                'match_cond': self.filters_to_match_cond(matching),
                'direction': 'in',
                'name': name,
                'order': order
            })
        if to_peer:
            route_maps.append({
                'match_policy': policy,
                'peer': to_peer,
                'match_cond': self.filters_to_match_cond(matching),
                'direction': 'out',
                'name': name,
                'order': order
            })
        return self

    def deny(self, name: Optional[str] = None, from_peer: Optional[str] = None,
             to_peer: Optional[str] = None,
             matching: Sequence[Union[AccessList, CommunityList]] = (),
             order=10) -> 'BGPConfig':
        """Deny all routes received from 'from_peer'
         and routes sent to 'to_peer' matching
         all of the access and community lists in 'matching'

        :param name: The name of the route-map
        :param from_peer: The peer on which received routes have to have
                          the community
        :param to_peer: The peer on which sent routes have to have the community
        :param matching: A list of AccessList and/or CommunityList
        :param order: The order in which route-maps are applied,
         i.e., lower order means applied before
        :return: self
        """
        return self.filter(name, policy=DENY, from_peer=from_peer,
                           to_peer=to_peer, matching=matching, order=order)

    def permit(self, name: Optional[str] = None,
               from_peer: Optional[str] = None, to_peer: Optional[str] = None,
               matching: Sequence[Union[AccessList, CommunityList]] = (),
               order=10) -> 'BGPConfig':
        """Accept all routes received from 'from_peer'
         and routes sent to 'to_peer' matching
         all of the access and community lists in 'matching'

        :param name: The name of the route-map
        :param from_peer: The peer on which received routes have to have
                          the community
        :param to_peer: The peer on which sent routes have to have the community
        :param matching: A list of AccessList and/or CommunityList
        :param order: The order in which route-maps are applied,
         i.e., lower order means applied before
        :return: self
        """
        return self.filter(name, policy=PERMIT, from_peer=from_peer,
                           to_peer=to_peer, matching=matching, order=order)

    def filters_to_match_cond(self,
                              filter_list: Sequence[Union[AccessList,
                                                          CommunityList]]):
        match_cond = []
        access_lists = self.topo.getNodeInfo(self.router, 'bgp_access_lists',
                                             list)
        community_list = self.topo.getNodeInfo(self.router,
                                               'bgp_community_lists', list)

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
        return match_cond

    def add_set_action(self, peer: str, set_action: RouteMapSetAction,
                       matching: Sequence[Union[AccessList, CommunityList]],
                       direction: str) -> 'BGPConfig':
        """Add a 'RouteMapSetAction' to a BGP peering between two nodes

        :param peer: The peer to which the route map is applied
        :param set_action: The RouteMapSetAction to set
        :param matching: A list of filter, can be empty
        :param direction: direction of the route map: 'in', 'out' or 'both'
        :return: self
        """
        match_cond = self.filters_to_match_cond(matching)
        route_maps = self.topo.getNodeInfo(self.router, 'bgp_route_maps', list)
        route_maps.append(
            {'peer': peer, 'match_cond': match_cond,
             'set_actions': [set_action], 'direction': direction})
        return self


def set_rr(topo: 'IPTopo', rr: str, peers: Sequence[str] = ()):
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
        super().__init__(node=node, *args, **kwargs)
        self.port = port

    def build(self):
        cfg = super().build()
        cfg.asn = self._node.asn
        cfg.neighbors = self._build_neighbors()
        cfg.address_families = self._address_families(
            self.options.address_families, cfg.neighbors)
        cfg.access_lists = self.build_access_list()
        cfg.community_lists = self.build_community_list()
        cfg.route_maps = self.build_route_map(cfg.neighbors)
        cfg.rr = self._node.get('bgp_rr_info')

        return cfg

    def build_community_list(self) -> List[CommunityList]:
        """
        Build and return a list of community_filter
        """
        node_community_lists = self._node.get('bgp_community_lists')
        community_lists = []
        if node_community_lists:
            for node_cl in node_community_lists:
                # If community is an int change it to the right format
                # asn:community by adding node asn
                cl = CommunityList(name=node_cl.name,
                                   community=node_cl.community,
                                   action=node_cl.action)
                community_lists.append(cl)
                if isinstance(node_cl.community, int):
                    cl.community = '%s:%d' % (self._node.asn, node_cl.community)
        return community_lists

    def build_access_list(self) -> List[AccessList]:
        """
        Build and return a list of access_filter
        :return:
        """
        node_access_lists = self._node.get('bgp_access_lists')
        access_lists = []
        if node_access_lists is not None:
            for acl_entries in node_access_lists:
                access_lists.append(AccessList(name=acl_entries.name,
                                               entries=acl_entries.entries))
        return access_lists

    def build_route_map(self, neighbors: Sequence['Peer']) -> List[RouteMap]:
        """
        Build and return a list of route map for the current node
        """
        node_route_maps = self._node.get('bgp_route_maps')
        route_maps = []  # type: List[RouteMap]
        if node_route_maps is not None:
            for kwargs in node_route_maps:
                remote_peer = kwargs.pop('peer')
                peers = []
                for neighbor in neighbors:
                    if neighbor.node == remote_peer:
                        peers.append(neighbor)
                for peer in peers:
                    kwargs['neighbor'] = peer
                    rm = RouteMap(**kwargs)
                    # If route map already exist, add conditions and actions
                    # to it
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
        super().set_defaults(defaults)

    def _build_neighbors(self) -> List['Peer']:
        """Compute the set of BGP peers for this BGP router
        :return: set of neighbors"""
        neighbors = []
        for x in self._node.get('bgp_peers', []):
            for v6 in [True, False]:
                peer = Peer(self._node, x, v6=v6)
                if peer.peer:
                    neighbors.append(peer)
        return neighbors

    @staticmethod
    def _address_families(af: List['AddressFamily'], nei: List['Peer']) \
            -> List['AddressFamily']:
        """Complete the address families: add extra networks, or activate
        neighbors. The default is to activate all given neighbors"""
        for a in af:
            a.neighbors.extend(nei)
        return af

    @classmethod
    def get_config(cls, topo: 'IPTopo', node: 'RouterDescription', **kwargs):
        return BGPConfig(topo=topo, router=node)


class AddressFamily:
    """An address family that is exchanged through BGP"""

    def __init__(self, af_name: str, redistribute: Sequence[str] = (),
                 networks: Sequence[Union[str, IPv4Network, IPv6Network]] = ()):
        self.name = af_name
        self.networks = [ip_network(str(n)) for n in networks]
        self.redistribute = redistribute
        self.neighbors = []  # type: List[Peer]


def AF_INET(*args, **kwargs):
    """The ipv4 (unicast) address family"""
    return AddressFamily('ipv4', *args, **kwargs)


def AF_INET6(*args, **kwargs):
    """The ipv6 (unicast) address family"""
    return AddressFamily('ipv6', *args, **kwargs)


class Peer:
    """A BGP peer"""
    def __init__(self, base: 'Router', node: str, v6=False):
        """:param base: The base router that has this peer
        :param node: The actual peer"""
        self.peer, other = self._find_peer_address(base, node, v6=v6)
        if not self.peer or not other:
            return
        self.node = node
        self.asn = other.asn
        self.family = 'ipv4' if not v6 else 'ipv6'
        try:
            self.port = other.nconfig.daemon(BGP).port
        except KeyError:  # No configured daemon - yet - use default
            self.port = BGP_DEFAULT_PORT
        # We default to nexthop self for eBGP routes only
        self.nh_self = 'next-hop-self'
        # We enable eBGP multihop if eBGP is in use
        ebgp = self.asn != base.asn
        self.ebgp_multihop = ebgp
        self.description = '%s (%sBGP)' % (node, 'e' if ebgp else 'i')

    @staticmethod
    def _find_peer_address(base: 'Router', peer: str, v6=False) \
            -> Tuple[Optional[str], Optional['Router']]:
        """Return the IP address that base should try to contact to establish
        a peering"""
        visited = set()  # type: Set[IPIntf]
        to_visit = {i.name: i for i in realIntfList(base)}
        prio_queue = [(0, i) for i in to_visit.keys()]
        heapq.heapify(prio_queue)
        # Explore all interfaces in base ASN recursively, until we find one
        # connected to the peer
        while to_visit:
            path_cost, i = heapq.heappop(prio_queue)
            if i in visited:
                continue
            i = to_visit.pop(i)
            visited.add(i)
            for n in i.broadcast_domain.routers:
                if n.node.name == peer:
                    if not v6:
                        return n.ip, n.node
                    if n.ip6 and not ip_address(n.ip6).is_link_local:
                        return n.ip6, n.node
                    return None, None
                if n.node.asn == base.asn or not n.node.asn:
                    for i in realIntfList(n.node):
                        to_visit[i.name] = i
                        heapq.heappush(prio_queue, (path_cost + i.igp_metric,
                                                    i.name))
        return None, None
