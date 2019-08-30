from ipmininet.iptopo import IPTopo
from ipmininet.router.config import RouterConfig, BGP, ebgp_session, set_med, new_access_list, AF_INET6, CLIENT_PROVIDER, SHARE


class BGPMultipleWays(IPTopo):
    """This topology builds a 3-AS network exchanging BGP reachability
    information"""
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
          |as6r+--------------+as5r +-------+
          +--+--+             +--+--+
             ^                   |
             | $               $ |
             |      +------+     |
             +------+ as7r +<----+
                    +------+
        """
        # Add all routers
        as1r = self.addRouter('as1r')
        as2r = self.addRouter('as2r')
        as3r = self.addRouter('as3r')
        as4r = self.addRouter('as4r')
        as5r = self.addRouter('as5r')
        as6r = self.addRouter('as6r')
        as7r = self.addRouter('as7r')
        as8r = self.addRouter('as8r')
        as1r.addDaemon(BGP, address_families=(AF_INET6(networks=('2001:db:1::/48',)),))
        as2r.addDaemon(BGP, address_families=(AF_INET6(networks=('2001:db:2::/48',)),))
        as3r.addDaemon(BGP, address_families=(AF_INET6(networks=('2001:db:3::/48',)),))
        as4r.addDaemon(BGP, address_families=(AF_INET6(networks=('2001:db:4::/48',)),))
        as5r.addDaemon(BGP, address_families=(AF_INET6(networks=('2001:db:5::/48',)),))
        as6r.addDaemon(BGP, address_families=(AF_INET6(networks=('2001:db:6::/48',)),))
        as7r.addDaemon(BGP, address_families=(AF_INET6(networks=('2001:db:7::/48',)),))
        as8r.addDaemon(BGP, address_families=(AF_INET6(networks=('2001:db:8::/48',)),))

        # Add links
        self.addLink(as1r, as2r)
        self.addLink(as1r, as3r)
        self.addLink(as1r, as4r)
        self.addLink(as2r, as5r)
        self.addLink(as3r, as8r)
        self.addLink(as4r, as6r)
        self.addLink(as4r, as8r)
        self.addLink(as5r, as6r)
        self.addLink(as5r, as7r)
        self.addLink(as5r, as8r)
        self.addLink(as6r, as7r)

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
        ebgp_session(self, as1r, as3r, SHARE)
        ebgp_session(self, as4r, as8r, SHARE)
        ebgp_session(self, as6r, as5r, SHARE)
        ebgp_session(self, as1r, as2r, CLIENT_PROVIDER)
        ebgp_session(self, as4r, as1r, CLIENT_PROVIDER)
        ebgp_session(self, as5r, as2r, CLIENT_PROVIDER)
        ebgp_session(self, as5r, as7r, CLIENT_PROVIDER)
        ebgp_session(self, as5r, as8r, CLIENT_PROVIDER)
        ebgp_session(self, as6r, as4r, CLIENT_PROVIDER)
        ebgp_session(self, as7r, as6r, CLIENT_PROVIDER)
        ebgp_session(self, as8r, as3r, CLIENT_PROVIDER)

        # Add test hosts
        for r in self.routers():
            self.addLink(r, self.addHost('h%s' % r))
        super(BGPMultipleWays, self).build(*args, **kwargs)