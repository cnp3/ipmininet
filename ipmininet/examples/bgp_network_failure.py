from ipmininet.iptopo import IPTopo
from ipmininet.router.config import RouterConfig, BGP, ebgp_session, CLIENT_PROVIDER, SHARE, AF_INET6
import ipmininet.router.config.bgp as _bgp


class BGPFailure(IPTopo):
    """This topology builds a 5-AS network exchanging BGP reachability
    information. Links failure are used to show the evolution of the active topology
    of the network."""
    def build(self, *args, **kwargs):
        """       
    +-----+        =        +-----+
    | as2r+-----------------+ as5r|
    +--+--+                 +--+--+
       |   \               /   |
       |    \             /    |
       |     \$          /=    |
       |      \         /      |
       |       ⅃       /       |
       |        +-----+        | 
       |$       | as3r|        |$
       |        +-----+        |   
       |       /       \       |
       |      /         \      |
       |     /=          \$    |
       |    /             \    |
       v   /               ⅃   v
    +--+--+        $        +--+--+
    | as1r+---------------->+ as4r|
    +-----+                 +-----+
        """
        # Add all routers
        as1r = self.bgp('as1r')
        as2r = self.bgp('as2r')
        as3r = self.bgp('as3r')
        as4r = self.bgp('as4r')
        as5r = self.bgp('as5r')
        
        self.addLink(as1r, as2r, params1={"ip": ("fd00:12::1/64",)},
                                    params2={"ip": ("fd00:12::2/64",)})
        self.addLink(as1r, as3r, params1={"ip": ("fd00:13::1/64",)},
                                    params2={"ip": ("fd00:13::3/64")})
        self.addLink(as1r, as4r, params1={"ip":"fd00:14::1/64"},
                                    params2={"ip":"fd00:14::4/64"})
        self.addLink(as2r, as3r, params1={"ip": ("fd00:23::2/64")},
                                    params2={"ip": ("fd00:23::3/64")})
        self.addLink(as2r, as5r, params1={"ip": ("fd00:25::2/64")},
                                    params2={"ip": ("fd00:25::5/64")})
        self.addLink(as3r, as4r, params1={"ip": ("fd00:34::3/64")},
                                    params2={"ip": ("fd00:34::4/64")})
        self.addLink(as3r, as5r, params1={"ip": ("fd00:35::3/64")},
                                    params2={"ip": ("fd00:35::5/64")})
        self.addLink(as4r, as5r, params1={"ip":"fd00:45::4/64"},
                                    params2={"ip":"fd00:45::5/64"})
        # Set AS-ownerships
        self.addAS(1, (as1r,))
        self.addAS(2, (as2r,))
        self.addAS(3, (as3r,))
        self.addAS(4, (as4r,))
        self.addAS(5, (as5r,))

        # Add eBGP peering
        ebgp_session(self, as1r, as4r, CLIENT_PROVIDER)
        ebgp_session(self, as2r, as1r, CLIENT_PROVIDER)
        ebgp_session(self, as2r, as3r, CLIENT_PROVIDER)
        ebgp_session(self, as3r, as4r, CLIENT_PROVIDER)
        ebgp_session(self, as5r, as4r, CLIENT_PROVIDER)

        ebgp_session(self, as1r, as3r, SHARE)
        ebgp_session(self, as2r, as5r, SHARE)
        ebgp_session(self, as3r, as5r, SHARE)

        # Add test hosts
        for r in self.routers():
            self.addLink(r, self.addHost('h%s' % r))
        super(BGPFailure, self).build(*args, **kwargs)

    def bgp(self, name):
        r = self.addRouter(name, use_v4=False, use_v6=True)
        r.addDaemon(BGP, address_families=(
            _bgp.AF_INET(redistribute=('connected',)),
            _bgp.AF_INET6(redistribute=('connected',))))
        return r