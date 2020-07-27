from ipmininet.iptopo import IPTopo


class SpanningTreeHub(IPTopo):

    def build(self, *args, **kwargs):
        """
          +-----+s3.2   ||   s17.1+-----+s17.2  ||  s10.1+-----+
          | s3  +-------||--------+ s17 +-------||-------+ s10 |
          +-----+       ||        +-----+       ||       +--+--+
             |s3.1      ||                                  | s10.2
             |          ||                                  |
             |          ||[hub s99]                      =======
             |          ||                                  |
             |          ||                                  |s11.1
             |          ||    s6.2+-----+ s6.3  ||  s11.3+--+--+
          =======       ||--------+ s6  +-------||-------+ s11 |
             |          ||        +--+--+       ||       +--+--+
             |                       |s6.1                  |s11.2
             |                       |                      |
             |                ===================================[hub s100]
             |s12.1             |
          +--+--+               |
          | s12 +---------------+
          +-----+s12.2
        """
        # adding switches
        s3 = self.addSwitch("s3", prio=3)
        s6 = self.addSwitch("s6", prio=6)
        s10 = self.addSwitch("s10", prio=10)
        s11 = self.addSwitch("s11", prio=11)
        s12 = self.addSwitch("s12", prio=12)
        s17 = self.addSwitch("s17", prio=17)
        # hubs
        s99 = self.addHub("s99")
        s100 = self.addHub("s100")

        # links
        self.addLinks((s3, s12), (s3, s99), (s12, s100), (s6, s100), (s17, s99),
                      (s10, s17), (s11, s10), (s11, s100), (s6, s99), (s6, s11))

        for s in self.switches():
            self.addLink(s, self.addHost('h%s' % s))

        super().build(*args, **kwargs)
