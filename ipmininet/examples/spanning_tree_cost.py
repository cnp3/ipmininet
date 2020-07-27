from ipmininet.iptopo import IPTopo


class SpanningTreeCost(IPTopo):

    def build(self, *args, **kwargs):
        r"""
                        +-----+
                        | s1  |
                        +-----+
                        |      \
                        |       \ 10
                        |        \
                     +--+--+   +--+--+
                     | s2  +---+ s3  |
                     +-----+   +-----+
        """
        s1 = self.addSwitch("s1", stp=True, prio=1)
        s2 = self.addSwitch("s2", stp=True, prio=2)
        s3 = self.addSwitch("s3", stp=True, prio=3)

        self.addLinks((s1, s2), (s2, s3))
        self.addLink(s3, s1, stp_cost=10)

        for s in self.switches():
            self.addLink(s, self.addHost('h%s' % s))

        super().build(*args, **kwargs)
