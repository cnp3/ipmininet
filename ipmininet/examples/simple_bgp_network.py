from ipmininet.iptopo import IPTopo
from ipmininet.router.config import RouterConfig, BGP, iBGPFullMesh, AS,\
                                    bgp_peering
import ipmininet.router.config.bgp as _bgp


class SimpleBGPTopo(IPTopo):
    """This topology builds a 3-AS network exchanging BGP reachability
    information"""
    def build(self, *args, **kwargs):
        """
           +----------+                                   +--------+
                      |                                   |
         AS1          |                  AS2              |        AS3
                      |                                   |
                      |                                   |
    +-------+   eBGP  |  +-------+     iBGP    +-------+  |  eBGP   +-------+
    | as1r1 +------------+ as2r1 +-------------+ as2r2 +------------+ as3r1 |
    +-------+         |  +-------+             +-------+  |         +-------+
                      |                                   |
                      |                                   |
                      |                                   |
         +------------+                                   +--------+
        """
        # Add all routers
        as1r1 = self.bgp('as1r1')
        as2r1 = self.bgp('as2r1')
        as2r2 = self.bgp('as2r2')
        as3r1 = self.bgp('as3r1')
        self.addLink(as1r1, as2r1)
        self.addLink(as2r1, as2r2)
        self.addLink(as3r1, as2r2)
        # Set AS-ownerships
        self.addOverlay(AS(1, (as1r1,)))
        self.addOverlay(iBGPFullMesh(2, (as2r1, as2r2)))
        self.addOverlay(AS(3, (as3r1,)))
        # Add eBGP peering
        bgp_peering(self, as1r1, as2r1)
        bgp_peering(self, as3r1, as2r2)
        # Add test hosts
        for r in self.routers():
            self.addLink(r, self.addHost('h%s' % r))
        super(SimpleBGPTopo, self).build(*args, **kwargs)

    def bgp(self, name):
        r = self.addRouter(name, config=RouterConfig)
        r.addDaemon(BGP, address_families=(
            _bgp.AF_INET(redistribute=('connected',)),
            _bgp.AF_INET6(redistribute=('connected',))))
        return r
