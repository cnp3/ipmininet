from ipmininet.iptopo import IPTopo
from ipmininet.router.config import RouterConfig, BGP, ebgp_session, set_local_pref, new_access_list, AF_INET6
import ipmininet.router.config.bgp as _bgp


class BGPTopoLocalPref(IPTopo):
    """This topology is composed of two AS connected in dual homing with different local pref"""

    def build(self, *args, **kwargs):
        """
    TODO
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
        as4r1.addDaemon(BGP, address_families=(AF_INET6(networks=('dead:beef::/32',)),))
        as4r2 = self.addRouter('as4r2')
        as4r2.addDaemon(BGP, address_families=(AF_INET6(networks=('dead:beef::/32',)),))
        as4h1 = self.addHost("as4h1")

        # Add Links
        self.addLink(as1r1, as1r6)
        self.addLink(as1r1, as1r3)
        self.addLink(as1r3, as1r2)
        self.addLink(as1r3, as1r6)
        self.addLink(as1r2, as1r4)
        self.addLink(as1r4, as1r5)
        self.addLink(as1r5, as1r6)
        self.addLink(as4r1, as1r6)
        self.addLink(as4r2, as1r5)
        self.addLink(as4r1, as4h1)
        self.addLink(as4r2, as4h1)
        self.addSubnet((as4r1, as4h1), subnets=('dead:beef::/32',))
        self.addSubnet((as4h1, as4r2), subnets=('dead:beef::/32',))

        al = new_access_list(name='all', entries=('any',))
        set_local_pref(self, as1r6, as4r1, 99, filter_list=(al, ))
        set_local_pref(self, as1r5, as4r2, 50, filter_list=(al, ))

        # Add full mesh
        self.addAS(4, (as4r1, as4r2))
        self.addiBGPFullMesh(1, (as1r1, as1r2, as1r3, as1r4, as1r5, as1r6))

        # Add eBGP session
        ebgp_session(self, as1r6, as4r1)
        ebgp_session(self, as1r5, as4r2)

        super(BGPTopoLocalPref, self).build(*args, **kwargs)

