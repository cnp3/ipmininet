"""This file contains a simple switch topology using the spanning tree protocol
"""

from ipmininet.iptopo import IPTopo


class SpanningTreeNet(IPTopo):
    """This simple network has a LAN with redundant links.
       The IPSwitch class enables the spanning tree protocol by default
       to prevent loops."""

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
        s1 = self.addSwitch('s1', prio='3')
        s2 = self.addSwitch('s2', prio='2')
        s3 = self.addSwitch('s3', prio='1')
        self.addLinks((s1, s2), (s1, s3), (s3, s2))
        for s in (s1, s2, s3):
            self.addLink(s, self.addHost('h%s' % s))

        super().build(*args, **kwargs)
