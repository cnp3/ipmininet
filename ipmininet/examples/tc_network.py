"""This network emulates delay and bandwidth constraints on the links.

Note that this topology has to be run in an IPNet object that set its 'intf'
parameter to the class ipmininet.link.TCIntf or a subclass
"""

from ipmininet.iptopo import IPTopo


class TCNet(IPTopo):

    def build(self, *args, **kw):
        h1 = self.addHost("h1")
        r1, r2 = self.addRouters("r1", "r2")
        h2 = self.addHost("h2")

        # Set maximum bandwidth on the link to 100 Mbps
        self.addLink(h1, r1, bw=100)

        # Sets delay in both directions to 15 ms
        self.addLink(r1, r2, delay="15ms")

        # Set delay only for packets going from r2 to h2
        self.addLink(r2, h2, params1={"delay": "2ms"})

        super().build(*args, **kw)
