from ipmininet.iptopo import IPTopo
from ipmininet.router.config import RouterConfig, BGP, ebgp_session, set_rr, AF_INET6


class BGPTopoRR(IPTopo):
    """This topology is composed of two AS connected in dual homing with different local pref"""

    def build(self, *args, **kwargs):
        """
    TODO slide 42 iBGP RED config
           +----------+                                   +--------+
                      |                                   |
         AS1          |                  AS2              |        AS3
                      |                                   |
                      |                                   |
    +-------+   eBGP  |  +-------+     iBGP    +-------+  |  eBGP   +-------+
    | as1r1 +------------+ as2r1 +-------------+ as2r2 +------------+ as3r1 |
    +-------+         |  +-------+             +-------+  |         +-------+
                      |                                   |
                      |                                   |
                      |                                   |
         +------------+                                   +--------+
        """
        # Add all routers
        as1r1 = self.addRouter('as1r1')
        as1r1.addDaemon(BGP, address_families=(
            AF_INET6(redistribute=('connected',)),))
        as1r2 = self.addRouter('as1r2')
        as1r2.addDaemon(BGP, address_families=(
            AF_INET6(redistribute=('connected',)),))
        as1r3 = self.addRouter('as1r3')
        as1r3.addDaemon(BGP, address_families=(
            AF_INET6(redistribute=('connected',)),))
        as1r4 = self.addRouter('as1r4')
        as1r4.addDaemon(BGP, address_families=(
            AF_INET6(redistribute=('connected',)),))
        as1r5 = self.addRouter('as1r5')
        as1r5.addDaemon(BGP, address_families=(
            AF_INET6(redistribute=('connected',)),))
        as1r6 = self.addRouter('as1r6')
        as1r6.addDaemon(BGP, address_families=(
            AF_INET6(redistribute=('connected',)),))
        as4r1 = self.addRouter('as4r1')
        as4r1.addDaemon(BGP, address_families=(
            AF_INET6(redistribute=('connected',)),))
        as4r2 = self.addRouter('as4r2')
        as4r2.addDaemon(BGP, address_families=(
            AF_INET6(redistribute=('connected',)),))
        as5r1 = self.addRouter('as5r1')
        as5r1.addDaemon(BGP, address_families=(
            AF_INET6(redistribute=('connected',)),))
        as3r1 = self.addRouter('as3r1')
        as3r1.addDaemon(BGP, address_families=(
            AF_INET6(redistribute=('connected',)),))
        as2r1 = self.addRouter('as2r1')
        as2r1.addDaemon(BGP, address_families=(AF_INET6(networks=('dead:beef::/32',)),))
        as2h1 = self.addHost('as21')

        # Add Links
        self.addLink(as1r1, as1r6)
        self.addLink(as1r1, as1r3)
        self.addLink(as1r3, as1r2)
        self.addLink(as1r3, as1r6)
        self.addLink(as1r2, as1r4)
        self.addLink(as1r4, as1r5)
        self.addLink(as1r5, as1r6)
        self.addLink(as4r1, as1r5)
        self.addLink(as4r2, as1r4)
        self.addLink(as3r1, as1r1)
        self.addLink(as5r1, as1r6)
        self.addLink(as3r1, as5r1)
        self.addLink(as5r1, as2r1)
        self.addLink(as2r1, as4r1)
        self.addLink(as4r1, as4r2)
        self.addLink(as2r1, as2h1)
        self.addSubnet((as2r1, as2h1), subnets=('dead:beef::/32',))


        set_rr(self, as1r1, peers=[as1r3, as1r2, as1r4, as1r5, as1r6])
        set_rr(self, as1r5, peers=[as1r1, as1r2, as1r4, as1r3, as1r6])

        # Add full mesh
        self.addAS(2, (as2r1,))
        self.addAS(3, (as3r1,))
        self.addAS(5, (as5r1,))
        self.addiBGPFullMesh(4, routers=[as4r1, as4r2])
        self.addAS(1, (as1r1, as1r2, as1r3, as1r4, as1r5, as1r6))

        # Add eBGP session
        ebgp_session(self, as1r6, as5r1)
        ebgp_session(self, as1r1, as3r1)
        ebgp_session(self, as1r4, as4r2)
        ebgp_session(self, as1r5, as4r1)
        ebgp_session(self, as3r1, as5r1)
        ebgp_session(self, as5r1, as2r1)
        ebgp_session(self, as2r1, as4r1)

        super(BGPTopoRR, self).build(*args, **kwargs)

