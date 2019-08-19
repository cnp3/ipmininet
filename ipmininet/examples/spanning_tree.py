"""This file contains a simple switch topology using the spanning tree protocol"""

from ipmininet.iptopo import IPTopo

def int2dpid(dpid):
    try:
        dpid = hex(dpid)[2:]
        dpid = '0' * ( 16 - len(dpid)) + dpid
        return dpid
    except IndexError:
        raise Exception('NULL')

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
        s1 = self.addSwitch('s1', stp=True, prio='3')
        s2 = self.addSwitch('s2', stp=True, prio='2')
        s3 = self.addSwitch('s3', stp=True, prio='1')
        self.addLink(s1, s2)
        self.addLink(s1, s3)
        self.addLink(s3, s2)
        for s in (s1, s2, s3):
            self.addLink(s, self.addHost('h%s' % s))

        super(SpanningTreeNet, self).build(*args, **kwargs)
