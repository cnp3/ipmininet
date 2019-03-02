"""This file contains a simple OSPFv3 topology"""

from ipmininet.iptopo import IPTopo

HOSTS_PER_ROUTER = 2


class SimpleOSPFv3Net(IPTopo):

    def build(self, *args, **kwargs):
        """
                                 +----+ 5
                            +----+ R1 +-----+
                            |    +----+     |
                            |               |
                         +--+-+          +--+-+
        +----+           | R2 +----------+ R3 |           +----+
        | R5 +-----------++---+          +-+--+-----------+ R6 |
        +--+-+            |                |              +--+-+
           |10            |                |                 |
           |              |                |                 |
        +--+-+            |                |    5         +--+-+
        | R4 +------------+                +--------------+ R7 |
        +----+                                            +----+

        Two hosts are attached to each router, named as hXY where x is the
        host number attached to that router, and Y the router name.
        """
        r1, r2 = self.addRouter_v6('r1'), self.addRouter_v6('r2')
        r3 = self.addRouter_v6('r3')
        self.addLink(r1, r2)
        self.addLink(r1, r3, igp_metric=5)
        self.addLink(r3, r2)
        for r in (r1, r2, r3):
            for i in range(HOSTS_PER_ROUTER):
                self.addLink(r, self.addHost('h%s%s' % (i, r)))

        r4, r5 = self.addRouter_v6('r4'), self.addRouter_v6('r5')
        self.addLink(r2, r5)
        self.addLink(r2, r4)
        self.addLink(r4, r5, igp_metric=10)
        for r in (r4, r5):
            for i in range(HOSTS_PER_ROUTER):
                self.addLink(r, self.addHost('h%s%s' % (i, r)))

        r6, r7 = self.addRouter_v6('r6'), self.addRouter_v6('r7')
        self.addLink(r3, r6)
        self.addLink(r3, r7, igp_metric=5)
        self.addLink(r6, r7)
        for r in (r6, r7):
            for i in range(HOSTS_PER_ROUTER):
                self.addLink(r, self.addHost('h%s%s' % (i, r)))

        super(SimpleOSPFv3Net, self).build(*args, **kwargs)

    def addRouter_v6(self, name):
        return self.addRouter(name, use_v4=False, use_v6=True)
