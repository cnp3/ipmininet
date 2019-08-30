from ipmininet.iptopo import IPTopo
from ipmininet.router.config import RouterConfig, BGP, ebgp_session, CLIENT_PROVIDER, SHARE, AF_INET6
import ipmininet.router.config.bgp as _bgp


class BGPCentralized(IPTopo):
    """This topology builds a 4-AS network exchanging BGP reachability
    information"""
    def build(self, *args, **kwargs):
        """       
       +----------------------+
    +--+--+  $         =      |
    | as4 +-------+           |
    +-----+       |           |
                  v           |
               +--+--+     +--+--+
               | as2 +-----+ as3 |
               +--+--+  =  +--+--+
                  ^           ^
    +-----+  $    |           |
    | as1 +-------+           |
    +--+--+           $       |
       +----------------------+
        """
        # Add all routers
        as1r1 = self.bgp('as1r1')
        as2r1 = self.bgp('as2r1')
        as3r1 = self.bgp('as3r1')
        as4r1 = self.bgp('as4r1')
        self.addLink(as1r1, as2r1, params1={"ip": ("fd00:12::1/64",)},
                                    params2={"ip": ("fd00:12::2/64",)})
        self.addLink(as2r1, as3r1, params1={"ip": ("fd00:23::2/64")},
                                    params2={"ip": ("fd00:23::3/64")})
        self.addLink(as1r1, as3r1, params1={"ip": ("fd00:13::1/64",)},
                                    params2={"ip": ("fd00:13::3/64")})
        self.addLink(as3r1, as4r1, params1={"ip": ("fd00:34::3/64")},
                                    params2={"ip": ("fd00:34::4/64")})
        self.addLink(as2r1, as4r1, params1={"ip": ("fd00:24::2/64")},
                                    params2={"ip": ("fd00:24::4/64")})
        # Set AS-ownerships
        self.addAS(1, (as1r1,))
        self.addAS(2, (as2r1,))
        self.addAS(3, (as3r1,))
        self.addAS(4, (as4r1,))
        # Add eBGP peering
        ebgp_session(self, as1r1, as2r1, CLIENT_PROVIDER)
        ebgp_session(self, as3r1, as2r1, SHARE)
        ebgp_session(self, as4r1, as2r1, CLIENT_PROVIDER)
        ebgp_session(self, as1r1, as3r1, CLIENT_PROVIDER)
        ebgp_session(self, as4r1, as3r1, SHARE)
        # Add test hosts
        for r in self.routers():
            self.addLink(r, self.addHost('h%s' % r))
        super(BGPCentralized, self).build(*args, **kwargs)

    def bgp(self, name):
        r = self.addRouter(name, use_v4=False, use_v6=True)
        r.addDaemon(BGP, address_families=(
            _bgp.AF_INET(redistribute=('connected',)),
            _bgp.AF_INET6(redistribute=('connected',))))
        return r