"""This file contains a simple switch topology using the spanning tree protocol"""

from ipmininet.iptopo import IPTopo


class SpanningTreeNet(IPTopo):
    """This simple network has a LAN with redundant links.
       It enables the spanning tree protocol to prevent loops."""

    def build(self, *args, **kwargs):
        """
                            +-----+
                            | hs1 |
                            +--+--+
                               |
                            +--+-+
                      +-----+ s1 +-----+
                      |     +----+     |
        +-----+     +-+--+          +--+-+     +-----+
        | hs2 +-----+ s2 +----------+ s3 +-----+ hs3 |
        +-----+     +----+          +----+     +-----+
        """
        # 'stp' option enables the spanning tree protocol to resolve loops in LAN
        s1 = self.addSwitch('s1', stp=True)
        s2 = self.addSwitch('s2', stp=True)
        s3 = self.addSwitch('s3', stp=True)
        self.addLink(s1, s2)
        self.addLink(s1, s3)
        self.addLink(s3, s2)
        for s in (s1, s2, s3):
            self.addLink(s, self.addHost('h%s' % s))

        super(SpanningTreeNet, self).build(*args, **kwargs)
