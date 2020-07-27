import ipmininet.router.config.bgp as _bgp
from ipmininet.iptopo import IPTopo
from ipmininet.router.config import BGP, ebgp_session, CLIENT_PROVIDER, SHARE


class BGPPoliciesTopo1(IPTopo):
    """This topology builds a 5-AS network exchanging BGP reachability
    information. Peering between AS1, AS2, AS3 and AS4 are declared as
    'shared-cost' while AS5 is declared as their provider. ASes always favor
    routes received from clients, then routes from shared-cost peering,
    and finally, routes received from providers. This is not influenced by
    the AS path length."""
    def build(self, *args, **kwargs):
        """
              +-------+      $
              | as1r1 +-------------+
              +---+---+             |
                  | =               |
          +-------|--------+        |
                  |    AS2 |        v
              +---+---+    | $  +---+---+
              | as2r1 +-------->+ as5r1 |
              +---+---+    |    +--++---+
                  |        |       ^^
              +---+---+    |       ||
              | as2r2 |    |       ||
              +---+---+    |       ||
                  |        |     $ || $
          +-------|--------+       ||
                  | =              ||
              +---+---+            ||
              | as3r1 +------------+|
              +---+---+             |
                  | =               |
              +---+---+             |
              | as4r1 +-------------+
              +-------+
        """
        # Add all routers
        as1r1 = self.bgp('as1r1')
        as2r1 = self.bgp('as2r1')
        as2r2 = self.bgp('as2r2')
        as3r1 = self.bgp('as3r1')
        as4r1 = self.bgp('as4r1')
        as5r1 = self.bgp('as5r1')
        self.addLinks((as1r1, as2r1), (as2r1, as2r2), (as3r1, as2r2),
                      (as3r1, as4r1), (as5r1, as1r1), (as5r1, as2r1),
                      (as5r1, as3r1), (as5r1, as4r1))
        # Set AS-ownerships
        self.addAS(1, (as1r1,))
        self.addiBGPFullMesh(2, (as2r1, as2r2))
        self.addAS(3, (as3r1,))
        self.addAS(4, (as4r1,))
        self.addAS(5, (as5r1,))
        # Add eBGP peering
        ebgp_session(self, as1r1, as2r1, link_type=SHARE)
        ebgp_session(self, as3r1, as2r2, link_type=SHARE)
        ebgp_session(self, as3r1, as4r1, link_type=SHARE)
        ebgp_session(self, as1r1, as5r1, link_type=CLIENT_PROVIDER)
        ebgp_session(self, as2r1, as5r1, link_type=CLIENT_PROVIDER)
        ebgp_session(self, as3r1, as5r1, link_type=CLIENT_PROVIDER)
        ebgp_session(self, as4r1, as5r1, link_type=CLIENT_PROVIDER)
        # Add test hosts
        for r in self.routers():
            self.addLink(r, self.addHost('h%s' % r))
        super().build(*args, **kwargs)

    def bgp(self, name):
        r = self.addRouter(name)
        r.addDaemon(BGP, address_families=(
            _bgp.AF_INET(redistribute=('connected',)),
            _bgp.AF_INET6(redistribute=('connected',))))
        return r
