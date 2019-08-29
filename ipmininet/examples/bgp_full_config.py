from ipmininet.iptopo import IPTopo
from ipmininet.router.config import BGP, ebgp_session, set_local_pref, set_med, set_rr, new_access_list, \
    set_community, new_community_list, AF_INET6


class BGPTopoFull(IPTopo):
    """This topology is composed of two AS connected in dual homing with different local pref,
     MED and communities. AS1 has one route reflector: as1r3."""

    def build(self, *args, **kwargs):
        """
                                 +
                           AS1   |   AS4
        +-------+                |
        | as1r1 +--------+       |
        +---+---+        |       |
          2 |            |       |
        +---+---+    +---+---+   |   +-------+
        | as1r3 +----+ as1r6 +-------+ as4r1 +--------+
        +---+---+    +---+---+   |   +-------+        |
            |            |       |                    |
        +---+---+        |       |                 +--+--+     +-------+
        | as1r2 |        |       |                 | s4  +-----+ as4h1 |
        +---+---+        |       |                 +--+--+     +-------+
          4 |            |       |                    |
        +---+---+    +---+---+   |   +-------+        |
        | as1r4 +----+ as1r5 +-------+ as4r2 +--------+
        +-------+    +-------+   |   +-------+
                                 |
                                 +
        """

        # Add all routers
        as1r1 = self.bgp('as1r1')
        as1r2 = self.bgp('as1r2')
        as1r3 = self.bgp('as1r3')
        as1r4 = self.bgp('as1r4')
        as1r5 = self.bgp('as1r5', family=AF_INET6(redistribute=('ospf6', 'connected')))
        as1r6 = self.bgp('as1r6', family=AF_INET6(redistribute=('ospf6', 'connected')))
        as4r1 = self.bgp('as4r1', family=AF_INET6(networks=('dead:beef::/32',)))
        as4r2 = self.bgp('as4r2', family=AF_INET6(networks=('dead:beef::/32',)))

        # Add the host and the switch
        as4h1 = self.addHost('as4h1')
        switch = self.addSwitch('s4')

        # Add Links
        self.addLink(as1r1, as1r6)
        self.addLink(as1r1, as1r3, igp_metric=2)
        self.addLink(as1r3, as1r2)
        self.addLink(as1r3, as1r6)
        self.addLink(as1r2, as1r4, igp_metric=4)
        self.addLink(as1r4, as1r5)
        self.addLink(as1r5, as1r6)
        self.addLink(as4r1, as1r6)
        self.addLink(as4r2, as1r5)
        self.addLink(as4r1, switch)
        self.addLink(as4r2, switch)
        self.addLink(switch, as4h1)
        self.addSubnet((as4r1, as4r2, as4h1), subnets=('dead:beef::/32',))

        al = new_access_list(name='all', entries=('any',))
        cl = new_community_list(name='loc-pref', community='1:80')
        set_local_pref(self, as1r6, as4r1, 99, filter_list=(al,))
        set_community(self, as4r1, as1r6, '1:80', filter_list=(al,), direction='in')
        set_med(self, as1r6, as4r1, 50, filter_list=(al,))
        set_med(self, as4r1, as1r6, 50, filter_list=(al,))
        set_local_pref(self, as1r5, as4r2, 50, filter_list=(al,))

        # Add full mesh
        self.addAS(4, (as4r1, as4r2))
        self.addAS(1, (as1r1, as1r2, as1r3, as1r4, as1r5, as1r6))
        set_rr(self, as1r3, (as1r1, as1r2, as1r4, as1r5, as1r6))

        # Add eBGP session
        ebgp_session(self, as1r6, as4r1)
        ebgp_session(self, as1r5, as4r2)

        super(BGPTopoFull, self).build(*args, **kwargs)

    def bgp(self, name, family=AF_INET6()):
        r = self.addRouter(name)
        r.addDaemon(BGP, address_families=(family,))
        return r
