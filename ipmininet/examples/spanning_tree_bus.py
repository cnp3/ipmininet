from ipmininet.iptopo import IPTopo


class SpanningTreeBus(IPTopo):

    def build(self, *args, **kwargs):
        """
                  +-----+
                  | s1  |
                  +--+--+
                     |
                     |
                  +--+--+
            +-----+ BUS +-----+
            |     +-----+     |
            |                 |
         +--+--+           +--+--+
         | s2  |           | s3  |
         +-----+           +-----+
        """
        s1 = self.addSwitch("s1")
        s2 = self.addSwitch("s2")
        s3 = self.addSwitch("s3")
        s99 = self.addHub("s99")

        self.addLink(s1, s99)
        self.addLink(s2, s99)
        self.addLink(s3, s99)

        self.addLink(s1, s2)
        self.addLink(s2, s3)
        self.addLink(s1, s3)

        for s in (s1, s2, s3):
            self.addLink(s, self.addHost('h%s' % s))

        super(SpanningTreeBus, self).build(*args, **kwargs)
