
from ipmininet.iptopo import IPTopo


class NetworkCaptureTopo(IPTopo):
    """
    This topology captures traffic from the network booting.
    This capture the initial messages of the OSPF/OSPFv3 daemons and save the capture
    on /tmp next to the logs.
    """

    def build(self, *args, **kw):
        """
           +----+                 +----+
           | r1 +-----------------+ r2 |
           +--+-+                 +-+--+
              |   +----+   +----+   |
              +---+ s1 +---+ s2 +---+
                  +----+   +----+
        """

        r1, r2 = self.addRouters('r1', 'r2')
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        lr1r2, _, ls1s2, _ = self.addLinks((r1, r2), (r1, s1), (s1, s2), (s2, r2))
        # Capture on all the interfaces of r1 and s1
        self.addNetworkCapture(nodes=[r1, s1],
                               # Capture on two specific interfaces of r2 and s2
                               interfaces=[lr1r2[r2], ls1s2[s2]])
        super().build(*args, **kw)
