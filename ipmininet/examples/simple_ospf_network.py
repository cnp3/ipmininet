"""This file contains a simple OSPF topology"""

from ipmininet.iptopo import IPTopo

HOSTS_PER_ROUTER = 2


class SimpleOSPFNet(IPTopo):
    """This simple network has multiple areas, as well as some passive
    interfaces in a management network"""

    def build(self, *args, **kwargs):
        """
                                                     +----+
                        +-------+--------------+-----+ S1 +--------+-----------------+---------+
                        |       |              |     +--+-+        |                 |         |
                        |       |              |        |          |                 |         |
Management Network (OOB)|       |              |        |          |                 |         |
+---------------------------------------------------------------------------------------------------+
                        |       |              |        |          |                 |         |
                        |       |              |      +-+--+ 5     |                 |         |
          Area 0.0.0.0  |       |              | +----+ R1 +-----+ |                 |         |
                        |       |              | |    +----+     | |                 |         |
                   +---------------------------------+    +------------------------------------------+
                        |       |             +----+ |     |  +----+                 |         |
                        |    +--+-+           | R2 +----------+ R3 |           +-----+         |
                        |    | R5 +-----------++---+ |     |  +-+--+-----------+ R6 ++         |
                        |    +----+            |     |     |    |              +--+-+          |
                        |       |10            |     |     |    |                 |            |
                        |       |              |     |     |    |                 |            |
                        |    +--+-+            |     |     |    |    5         +--+-+          |
                        +----+ R4 +------------+     |     |    +--------------+ R7 +----------+
                             +----+                  |     |                   +----+
                                                     |     |
                      Area 1.1.1.1                   |     |        Area 2.2.2.2
                                                     +     +
        Two hosts are attached to each router, named as hXY where x is the
        host number attached to that router, and Y the router name.
        """
        # Build backbone
        r1, r2, r3 = self.addRouters('r1', 'r2', 'r3', use_v4=True,
                                     use_v6=False)
        self.addLink(r1, r2)
        self.addLink(r1, r3, igp_metric=5)
        self.addLink(r3, r2)
        for r in (r1, r2, r3):
            for i in range(HOSTS_PER_ROUTER):
                self.addLink(r, self.addHost('h%s%s' % (i, r)),
                             params2={'v4_width': 5})

        # Area 1.1.1.1 is delimited by an OSPFArea overlay
        r4, r5 = self.addRouters('r4', 'r5', use_v4=True, use_v6=False)
        self.addLink(r2, r5)
        self.addLink(r2, r4)
        self.addLink(r4, r5, igp_metric=10)
        for r in (r4, r5):
            for i in range(HOSTS_PER_ROUTER):
                self.addLink(r, self.addHost('h%s%s' % (i, r)))
        self.addOSPFArea(routers=(r4, r5), area='1.1.1.1')

        # Area 2.2.2.2 is delimited by the igp_area parameter of addLink()
        r6, r7 = self.addRouters('r6', 'r7', use_v4=True, use_v6=False)
        self.addLink(r3, r6, igp_area='2.2.2.2')
        self.addLink(r3, r7, igp_area='2.2.2.2', igp_metric=5)
        self.addLink(r6, r7, igp_area='2.2.2.2')
        for r in (r6, r7):
            for i in range(HOSTS_PER_ROUTER):
                self.addLink(r, self.addHost('h%s%s' % (i, r)),
                             igp_area='2.2.2.2')

        # Management network
        s1 = self.addSwitch('s1')
        for r in self.routers():
            self.addLink(s1, r, igp_passive=True)

        super().build(*args, **kwargs)
