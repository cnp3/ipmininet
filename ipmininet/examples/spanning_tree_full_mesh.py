from ipmininet.iptopo import IPTopo


class SpanningTreeFullMesh(IPTopo):

    def build(self, *args, **kwargs):
        r"""
        +-----+     +-----+
        | s10 |     | s11 |
        +--+--+     +--+--+
           |   \   /   |
           |    \ /    |
           |     \     |
           |    / \    |
           |   /   \   |
        +--+--+     +--+--+
        | s1  +-----+ s2  |
        +--+--+     +--+--+
           |   \   /   |
           |    \ /    |
           |     \     |
           |    / \    |
           |   /   \   |
        +--+--+     +--+--+
        | S3  +-----+ S4  |
        +--+--+     +--+--+
           |   \   /   |
           |    \ /    |
           |     \     |
           |    / \    |
           |   /   \   |
        +--+--+     +--+--+
        | S12 |     | S17 |
        +-----+     +-----+
        """
        s10 = self.addSwitch("s10", prio=10)
        s11 = self.addSwitch("s11", prio=11)
        s1 = self.addSwitch("s1", prio=1)
        s2 = self.addSwitch("s2", prio=2)
        s3 = self.addSwitch("s3", prio=3)
        s4 = self.addSwitch("s4", prio=4)
        s12 = self.addSwitch("s12", prio=12)
        s17 = self.addSwitch("s17", prio=17)

        self.addLinks((s10, s1), (s10, s2), (s11, s1), (s11, s2), (s1, s2),
                      (s1, s3), (s1, s4), (s2, s3), (s2, s4), (s3, s4),
                      (s3, s12), (s3, s17), (s4, s12), (s4, s17))

        for s in (s10, s11, s1, s2, s3, s4, s12, s17):
            self.addLink(s, self.addHost('h%s' % s))

        super().build(*args, **kwargs)
