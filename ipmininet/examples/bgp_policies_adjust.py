from ipmininet.iptopo import IPTopo
from ipmininet.router.config import BGP, ebgp_session, AF_INET6,\
    CLIENT_PROVIDER, SHARE


class BGPPoliciesAdjustTopo(IPTopo):
    """This topology builds a 5-AS network exchanging BGP reachability as shown
    in the figure below. Shared cost are described with ' = ',
    client - provider with ' $ '.

    ASes always favor routes received from clients, then routes from shared-cost
    peering, and finally, routes received from providers.
    This is not influenced by the AS path length.

    The user can add another peering between 2 ASes with the constructor
    arguments or to let the network as it is.

    This topology is taken from
    https://www.computer-networking.info/exercises/html/ex-routing-policies.html
    """

    def __init__(self, as_start=None, as_end=None, bgp_policy=SHARE,
                 *args, **kwargs):
        """:param as_start: The AS router at one end of the extra link.
           If the link type is 'Client-Provider', this AS will be the client.
        :param as_end: The AS router at other end of the extra link.
           If the link type is 'Client-Provider', this AS will be the provider.
        :param bgp_policy: The type of peering (either 'Share' or
           'Client-Provider')"""
        self.as_start = as_start
        self.as_end = as_end
        self.bgp_policy = bgp_policy
        super().__init__(*args, **kwargs)

    def build(self, *args, **kwargs):
        r"""
            +-----+       +-----+
        +---+as4r |       |as3r +---+
        |   +--+--+       +--+--+   |
        |      |   \ =   / = | =    | =
        |      |    \   /    |      |
        |      |     \ /     |      |
        | $    | $    \      |      |
        |      |     / \     |      |
        |      |    /   \    |      |
        |      V   /     \   |      |
        |   +-----+       +--+--+   |
        |   |as2r |       |as5r |   |
        |   +--+--+       +-----+   |
        |      | =                  |
        |      |                    |
        |      |                    |
        |      |                    |
        |      |                    |
        |   +--+--+                 |
        +-->+as1r +-----------------+
            +-----+
        """

        # Add all routers
        as1r, as2r, as3r, as4r, as5r = self.addRouters('as1r', 'as2r', 'as3r',
                                                       'as4r', 'as5r')

        routers = self.routers()
        prefix = {routers[i]: '2001:db:%04x::/48' % i
                  for i in range(len(routers))}
        as1r.addDaemon(BGP,
                       address_families=(AF_INET6(networks=(prefix[as1r],)),))
        as2r.addDaemon(BGP,
                       address_families=(AF_INET6(networks=(prefix[as2r],)),))
        as3r.addDaemon(BGP,
                       address_families=(AF_INET6(networks=(prefix[as3r],)),))
        as4r.addDaemon(BGP,
                       address_families=(AF_INET6(networks=(prefix[as4r],)),))
        as5r.addDaemon(BGP,
                       address_families=(AF_INET6(networks=(prefix[as5r],)),))

        # Add links
        self.addLinks((as1r, as2r), (as1r, as3r), (as1r, as4r), (as2r, as3r),
                      (as2r, as4r), (as3r, as5r), (as4r, as5r))

        # Set AS-ownerships
        self.addAS(1, (as1r,))
        self.addAS(2, (as2r,))
        self.addAS(3, (as3r,))
        self.addAS(4, (as4r,))
        self.addAS(5, (as5r,))

        # Add BGP peering
        ebgp_session(self, as1r, as2r, link_type=SHARE)
        ebgp_session(self, as1r, as3r, link_type=SHARE)
        ebgp_session(self, as2r, as3r, link_type=SHARE)
        ebgp_session(self, as3r, as5r, link_type=SHARE)
        ebgp_session(self, as4r, as5r, link_type=SHARE)
        ebgp_session(self, as4r, as1r, link_type=CLIENT_PROVIDER)
        ebgp_session(self, as4r, as2r, link_type=CLIENT_PROVIDER)

        # Check extra link parameters
        self.check_extra_link()

        # Add custom link
        if self.as_start is not None:
            self.addLink(self.as_start, self.as_end)
            ebgp_session(self, self.as_start, self.as_end,
                         link_type=self.bgp_policy)

        # Add test hosts
        for r in self.routers():
            link = self.addLink(r, self.addHost('h%s' % r))
            self.addSubnet(links=[link], subnets=[prefix[r]])
        super().build(*args, **kwargs)

    def check_extra_link(self):
        """
        Checks the validity of the extra link parameters
        """
        if self.as_start is None and self.as_end is None:
            return
        routers = self.routers()
        if self.as_start not in routers:
            raise ValueError("as_start '%s' is not an AS router among %s"
                             % (self.as_start, ", ".join(routers)))
        if self.as_end not in routers:
            raise ValueError("as_end '%s' is not an AS router among %s"
                             % (self.as_end, ", ".join(routers)))
        if self.bgp_policy not in [CLIENT_PROVIDER, SHARE]:
            raise ValueError("bgp_policy '%s' is not a BGP policy among %s"
                             % (self.bgp_policy, ", ".join([CLIENT_PROVIDER,
                                                            SHARE])))

        self.as_start = [r for r in routers if r == self.as_start][0]
        self.as_end = [r for r in routers if r == self.as_end][0]
