from ipmininet.iptopo import IPTopo
from ipmininet.router.config import BGP, ebgp_session, set_rr, AF_INET6


class BGPTopoRR(IPTopo):
    """This topology is composed of five AS.
    AS1 uses two router reflectors: as1r1 and as1r5."""

    def build(self, *args, **kwargs):
        """
                                 +
                           AS1   |   AS3
            +----------------------------+
            |                    |       |
        +---+---+                |   +---+---+
        | as1r1 +--------+       |   | as3r1 |
        +---+---+        |       |   +---+---+
            |            |       |       |
          2 |            |       +-------|------------+
            |            |       |       |        AS5
        +---+---+    +---+---+   |   +---+---+
        | as1r3 +----+ as1r6 +-------+ as5r1 +
        +---+---+    +---+---+   |   +---+---+
            |            |       |       |
            |            |       +-------|------------+
            |            |       |       |        AS2
        +---+---+        |       |   +---+---+    +---+---+
        | as1r2 |        |       |   | as2r1 +----+ as2h1 |
        +---+---+        |       |   +---+---+    +---+---+
            |            |       |       |
          4 |            |       +-------|------------+
            |            |       |       |        AS4
        +---+---+    +---+---+   |   +---+---+
        | as1r4 +----+ as1r5 +-------+ as4r1 +
        +---+---+    +-------+   |   +---+---+
            |                    |       |
            |                    |   +---+---+
            +------------------------+ as4r2 +
                                 |   +-------+
                                 |
                                 +
        """

        # Add all routers
        as1r1 = self.bgp('as1r1')
        as1r2 = self.bgp('as1r2')
        as1r3 = self.bgp('as1r3')
        as1r4 = self.bgp('as1r4')
        as1r5 = self.bgp('as1r5',
                         family=AF_INET6(redistribute=('ospf6', 'connected')))
        as1r6 = self.bgp('as1r6',
                         family=AF_INET6(redistribute=('ospf6', 'connected')))
        as4r1 = self.bgp('as4r1',
                         family=AF_INET6(redistribute=('ospf6', 'connected')))
        as4r2 = self.bgp('as4r2',
                         family=AF_INET6(redistribute=('ospf6', 'connected')))
        as5r1 = self.bgp('as5r1',
                         family=AF_INET6(redistribute=('connected',)))
        as3r1 = self.bgp('as3r1',
                         family=AF_INET6(redistribute=('connected',)))
        as2r1 = self.bgp('as2r1',
                         family=AF_INET6(networks=('dead:beef::/32',)))

        # Add host
        as2h1 = self.addHost('as2h1')

        # Add Links
        self.addLink(as1r1, as1r6)
        self.addLink(as1r1, as1r3, igp_metric=2)
        self.addLinks((as1r3, as1r2), (as1r3, as1r6))
        self.addLink(as1r2, as1r4, igp_metric=4)
        self.addLinks((as1r4, as1r5), (as1r5, as1r6), (as4r1, as1r5),
                      (as4r2, as1r4), (as3r1, as1r1), (as5r1, as1r6),
                      (as3r1, as5r1), (as5r1, as2r1), (as2r1, as4r1),
                      (as4r1, as4r2), (as2r1, as2h1))
        self.addSubnet((as2r1, as2h1), subnets=('dead:beef::/32',))

        set_rr(self, rr=as1r1, peers=[as1r3, as1r2, as1r4, as1r5, as1r6])
        set_rr(self, rr=as1r5, peers=[as1r1, as1r2, as1r4, as1r3, as1r6])

        # Add full mesh
        self.addAS(2, (as2r1,))
        self.addAS(3, (as3r1,))
        self.addAS(5, (as5r1,))
        self.addiBGPFullMesh(4, routers=[as4r1, as4r2])
        self.addAS(1, (as1r1, as1r2, as1r3, as1r4, as1r5, as1r6))

        # Add eBGP session
        ebgp_session(self, as1r6, as5r1)
        ebgp_session(self, as1r1, as3r1)
        ebgp_session(self, as1r4, as4r2)
        ebgp_session(self, as1r5, as4r1)
        ebgp_session(self, as3r1, as5r1)
        ebgp_session(self, as5r1, as2r1)
        ebgp_session(self, as2r1, as4r1)

        super().build(*args, **kwargs)

    def bgp(self, name, family=AF_INET6()):
        r = self.addRouter(name)
        r.addDaemon(BGP, address_families=(family,))
        return r
