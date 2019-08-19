from ipmininet.iptopo import IPTopo


class SpanningTreeSimple(IPTopo):

    def build(self, *args, **kwargs):
        """
                        +-----+
                        | s1  |
                        +-----+
                        |      \
                        |       \
                        |        \
                     +--+--+   +--+--+
                     | s2  +---+ s3  |
                     +-----+   +-----+
        """
        s1 = self.addSwitch("s1", stp=True, prio=1)
        s2 = self.addSwitch("s2", stp=True, prio=2)
        s3 = self.addSwitch("s3", stp=True, prio=3)

        self.addLink(s1, s2)
        self.addLink(s2, s3)
        self.addLink(s3, s1, cost=10)

        super(SpanningTreeSimple, self).build(*args, **kwargs)
