from ipmininet.iptopo import IPTopo
from ipmininet.router.config import BGP, ebgp_session, AF_INET6,\
    CLIENT_PROVIDER, SHARE


class BGPPoliciesTopo3(IPTopo):
    """This topology builds a 4-AS network exchanging BGP reachability as shown
    in the figure below. Shared cost are described with ' = ',
    client - provider with ' $ '.

    ASes always favor routes received from clients, then routes from shared-cost
    peering, and finally, routes received from providers.
    This is not influenced by the AS path length.

    This topology is taken from
    https://www.computer-networking.info/exercises/html/ex-routing-policies.html
    """
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

        # Add links
        self.addLinks((as1r, as2r), (as1r, as3r), (as1r, as4r), (as2r, as3r),
                      (as3r, as4r))

        # Set AS-ownerships
        self.addAS(1, (as1r,))
        self.addAS(2, (as2r,))
        self.addAS(3, (as3r,))
        self.addAS(4, (as4r,))

        # Add BGP peering
        ebgp_session(self, as1r, as2r, link_type=SHARE)
        ebgp_session(self, as3r, as2r, link_type=SHARE)
        ebgp_session(self, as3r, as1r, link_type=CLIENT_PROVIDER)
        ebgp_session(self, as1r, as4r, link_type=CLIENT_PROVIDER)
        ebgp_session(self, as3r, as4r, link_type=CLIENT_PROVIDER)

        # Add test hosts
        for r in self.routers():
            link = self.addLink(r, self.addHost('h%s' % r))
            self.addSubnet(links=[link], subnets=[prefix[r]])
        super().build(*args, **kwargs)
