from ipmininet.iptopo import IPTopo


class SpanningTreeAdjust(IPTopo):

    def __init__(self, l1_start=None, l1_end=None, l1_cost=1,
                 l2_start=None, l2_end=None, l2_cost=1, *args, **kwargs):
        """
        :param l1_start: Endpoint interface of the 1st link
                         on which we want to change the cost
        :param l1_end: Endpoint interface of the 1st link
                       on which we want to change the cost
        :param l1_cost: Cost to set on the first link
        :param l2_start: Endpoint interface of the 2nd link
                         on which we want to change the cost
        :param l2_end: Endpoint interface of the 2nd link
                       on which we want to change the cost
        :param l2_cost: Cost to set on the second link
        """

        self.l1_start = l1_start
        self.l1_end = l1_end
        self.l1_cost = int(l1_cost)

        self.l2_start = l2_start
        self.l2_end = l2_end
        self.l2_cost = int(l2_cost)

        super().__init__(*args, **kwargs)

    def build(self, *args, **kwargs):
        r"""
        === Full topology ===

           +------------------------+
           |s6.2                    |
        +--+--+          +-----+    |
        | s6  +          | s2  |    |
        +--+--+          ++---++    |
           |s6.1      s2.1|   |s2.2 |
           |              |   |     |
           |s3.4      s1.1|   |s4.2 |
        +--+--+s3.1  s1.3++---++    |
        | s3  +----------+ s1  |    |
        +--+--+          +--+--+    |
       s3.2|   \s3.3        |s1.4   |
           |    \           |       |
           |     \          |       |
           |      \         |       |
           |       \        |       |
           |        \       |       |
           |         \      |       |
           |          \     |       |
           |           \    |       |
           |s4.1    s5.2\   |s5.1   |
        +--+--+          +--+--+    |
        | s4  +----------+ s5  +----+
        +-----+s4.2  s5.3+-----+ s5.4

        === Spanning tree ===

        +--+--+          +-----+
        | s6  +          | s2  |
        +--+--+          ++---++
           |s6.1      s2.1|
           |              |
           |s3.4      s1.1|
        +--+--+s3.1  s1.3++---++
        | s3  +----------+ s1  |
        +--+--+          +--+--+
       s3.2|                |s1.4
           |                |
           |                |
           |                |
           |                |
           |                |
           |                |
           |                |
           |                |
           |s4.1            |s5.1
        +--+--+          +--+--+
        | s4  +          + s5  +
        +-----+          +-----+

        === Adjust 2 weights to get ===

           +------------------------+
           |s6.2                    |
        +--+--+          +-----+    |
        | s6  +          | s2  |    |
        +--+--+          ++---++    |
                              |s2.2 |
                              |     |
                              |s4.2 |
        +--+--+          ++---++    |
        | s3  +          + s1  |    |
        +--+--+          +--+--+    |
               \s3.3        |s1.4   |
                \           |       |
                 \          |       |
                  \         |       |
                   \        |       |
                    \       |       |
                     \      |       |
                      \     |       |
                       \    |       |
                    s5.2\   |s5.1   |
        +--+--+          +--+--+    |
        | s4  +----------+ s5  +----+
        +-----+s4.2  s5.3+-----+ s5.4
        """
        # adding switches
        s1 = self.addSwitch("s1", prio=1)
        s2 = self.addSwitch("s2", prio=2)
        s3 = self.addSwitch("s3", prio=3)
        s4 = self.addSwitch("s4", prio=4)
        s5 = self.addSwitch("s5", prio=5)
        s6 = self.addSwitch("s6", prio=6)

        # adding links
        self.addLinks((s1, s2), (s1, s2), (s1, s3), (s1, s5), (s3, s4),
                      (s3, s5), (s3, s6), (s4, s5), (s5, s6))

        for s in self.switches():
            self.addLink(s, self.addHost('h%s' % s))

        super().build(*args, **kwargs)

    def addLink(self, node1, node2, port1=None, port2=None,
                key=None, **opts):

        link = super().addLink(node1, node2, port1=port1, port2=port2,
                               key=key, **opts)

        # Adjust STP cost if the link was in the parameters
        itfs = ["%s-eth%d" % (node1, link.link_attrs["port1"]),
                "%s-eth%d" % (node2, link.link_attrs["port2"])]
        if self.l1_start in itfs and self.l1_end in itfs:
            link[0].addParams(stp_cost=self.l1_cost)
            link[1].addParams(stp_cost=self.l1_cost)
        if self.l2_start in itfs and self.l2_end in itfs:
            link[0].addParams(stp_cost=self.l2_cost)
            link[1].addParams(stp_cost=self.l2_cost)
