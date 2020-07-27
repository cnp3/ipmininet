from ipmininet.iptopo import IPTopo
from ipmininet.router.config import BGP, ebgp_session, AF_INET6,\
    CLIENT_PROVIDER, SHARE


class BGPPoliciesTopo5(IPTopo):
    """This topology builds a 8-AS network exchanging BGP reachability as shown
    in the figure below. Shared cost are described with ' = ',
    client - provider with ' $ '.

    ASes always favor routes received from clients, then routes from shared-cost
    peering, and finally, routes received from providers.
    This is not influenced by the AS path length.

    This topology is taken from
    https://www.computer-networking.info/exercises/html/ex-bgp.html
    """
    def build(self, *args, **kwargs):
        """
                    +-----+
             +----->+as2r +<----------------+
             |      +-----+                 |
             | $                          $ |
             |                              |
          +--+--+      =      +--+--+       |
          |as1r +-------------+ as3r|       |
          +--+--+             +--+--+       |
             ^                   ^          |
             | $               $ |          |
             |                   |          |
          +--+--+      =      +--+--+       |
          |as4r +-------------+as8r |       |
          +--+--+             +--+--+       |
             ^                   ^          |
             | $               $ |          |
             |                   |          |
          +--+--+      =      +--+--+       |
          |as6r +-------------+as5r +-------+
          +--+--+             +--+--+
             ^                   |
             | $               $ |
             |      +------+     |
             +------+ as7r +<----+
                    +------+
        """
        # Add all routers
        as1r, as2r, as3r, as4r, as5r, as6r, as7r, as8r = \
            self.addRouters('as1r', 'as2r', 'as3r', 'as4r', 'as5r', 'as6r',
                            'as7r', 'as8r')

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
        as6r.addDaemon(BGP,
                       address_families=(AF_INET6(networks=(prefix[as6r],)),))
        as7r.addDaemon(BGP,
                       address_families=(AF_INET6(networks=(prefix[as7r],)),))
        as8r.addDaemon(BGP,
                       address_families=(AF_INET6(networks=(prefix[as8r],)),))

        # Add links
        self.addLinks((as1r, as2r), (as1r, as3r), (as1r, as4r), (as2r, as5r),
                      (as3r, as8r), (as4r, as6r), (as4r, as8r), (as5r, as6r),
                      (as5r, as7r), (as5r, as8r), (as6r, as7r))

        # Set AS-ownerships
        self.addAS(1, (as1r,))
        self.addAS(2, (as2r,))
        self.addAS(3, (as3r,))
        self.addAS(4, (as4r,))
        self.addAS(5, (as5r,))
        self.addAS(6, (as6r,))
        self.addAS(7, (as7r,))
        self.addAS(8, (as8r,))

        # Add BGP peering
        ebgp_session(self, as1r, as3r, link_type=SHARE)
        ebgp_session(self, as4r, as8r, link_type=SHARE)
        ebgp_session(self, as6r, as5r, link_type=SHARE)
        ebgp_session(self, as1r, as2r, link_type=CLIENT_PROVIDER)
        ebgp_session(self, as4r, as1r, link_type=CLIENT_PROVIDER)
        ebgp_session(self, as5r, as2r, link_type=CLIENT_PROVIDER)
        ebgp_session(self, as5r, as7r, link_type=CLIENT_PROVIDER)
        ebgp_session(self, as5r, as8r, link_type=CLIENT_PROVIDER)
        ebgp_session(self, as6r, as4r, link_type=CLIENT_PROVIDER)
        ebgp_session(self, as7r, as6r, link_type=CLIENT_PROVIDER)
        ebgp_session(self, as8r, as3r, link_type=CLIENT_PROVIDER)

        # Add test hosts
        for r in self.routers():
            link = self.addLink(r, self.addHost('h%s' % r))
            self.addSubnet(links=[link], subnets=[prefix[r]])
        super().build(*args, **kwargs)
