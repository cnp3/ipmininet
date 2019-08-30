from ipmininet.iptopo import IPTopo
import ipmininet.router.config.bgp as _bgp
from ipmininet.router.config import RouterConfig, BGP, ebgp_session, set_med, new_access_list, AF_INET6, CLIENT_PROVIDER, SHARE


class BGPPrefixConnectedTopo(IPTopo):
    """This topology builds a 3-AS network exchanging BGP reachability
    information"""
    def build(self, *args, **kwargs):
        """
                     +-------+
              +------+ as2r  +-------+
              |      +-------+       |
              | =                  = |
              |                      |
          +---+---+      $       +---+---+
          | as1r  +<-------------+  as3r |
          +---+---+              +---+---+
              |                      |
              | $                  $ |
              |      +-------+       |
              +----->+ as4r  +<------+
                     +-------+
        """
        # Add all routers
        as1r = self.addRouter('as1r')
        as2r = self.addRouter('as2r')
        as3r = self.addRouter('as3r')
        as4r = self.addRouter('as4r')
        as1r.addDaemon(BGP, address_families=(AF_INET6(networks=('2001:db:1::/48',)),))
        as2r.addDaemon(BGP, address_families=(AF_INET6(networks=('2001:db:2::/48',)),))
        as3r.addDaemon(BGP, address_families=(AF_INET6(networks=('2001:db:3::/48',)),))
        as4r.addDaemon(BGP, address_families=(AF_INET6(networks=('2001:db:4::/48',)),))

        # Add links
        self.addLink(as1r, as2r)
        self.addLink(as1r, as3r)
        self.addLink(as1r, as4r)
        self.addLink(as2r, as3r)
        self.addLink(as3r, as4r)

        # Set AS-ownerships
        self.addAS(1, (as1r,))
        self.addAS(2, (as2r,))
        self.addAS(3, (as3r,))
        self.addAS(4, (as4r,))

        # Add BGP peering
        ebgp_session(self, as1r, as2r, SHARE)
        ebgp_session(self, as3r, as2r, SHARE)
        ebgp_session(self, as3r, as1r, CLIENT_PROVIDER)
        ebgp_session(self, as1r, as4r, CLIENT_PROVIDER)
        ebgp_session(self, as3r, as4r, CLIENT_PROVIDER)

        # Add test hosts
        for r in self.routers():
            self.addLink(r, self.addHost('h%s' % r))
        super(BGPPrefixConnectedTopo, self).build(*args, **kwargs)