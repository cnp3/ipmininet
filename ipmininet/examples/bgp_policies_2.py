import ipmininet.router.config.bgp as _bgp
from ipmininet.iptopo import IPTopo
from ipmininet.router.config import BGP, ebgp_session, CLIENT_PROVIDER, SHARE


class BGPPoliciesTopo2(IPTopo):
    """This topology builds a 4-AS network exchanging BGP reachability as shown
    in the figure below. Shared cost are described with ' = ',
    client - provider with ' $ '.

    ASes always favor routes received from clients, then routes from shared-cost
    peering, and finally, routes received from providers.
    This is not influenced by the AS path length.

    This topology is taken from
    https://www.computer-networking.info/exercises/html/ex-routing-policies.html
    """
    def build(self, *args, **kwargs):
        """
                      =
           +----------------------+
        +--+--+                   |
        | as4 +-------+           |
        +-----+  $    |           |
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
        as1r1 = self.bgp('as1')
        as2r1 = self.bgp('as2')
        as3r1 = self.bgp('as3')
        as4r1 = self.bgp('as4')

        # Add links
        las12 = self.addLink(as1r1, as2r1)
        las12[as1r1].addParams(ip=("fd00:12::1/64",))
        las12[as2r1].addParams(ip=("fd00:12::2/64",))

        las23 = self.addLink(as2r1, as3r1)
        las23[as2r1].addParams(ip=("fd00:23::2/64",))
        las23[as3r1].addParams(ip=("fd00:23::3/64",))

        las13 = self.addLink(as1r1, as3r1)
        las13[as1r1].addParams(ip=("fd00:13::1/64",))
        las13[as3r1].addParams(ip=("fd00:13::3/64",))

        las34 = self.addLink(as3r1, as4r1)
        las34[as3r1].addParams(ip=("fd00:34::3/64",))
        las34[as4r1].addParams(ip=("fd00:34::4/64",))

        las24 = self.addLink(as2r1, as4r1)
        las24[as2r1].addParams(ip=("fd00:24::2/64",))
        las24[as4r1].addParams(ip=("fd00:24::4/64",))

        # Set AS-ownerships
        self.addAS(1, (as1r1,))
        self.addAS(2, (as2r1,))
        self.addAS(3, (as3r1,))
        self.addAS(4, (as4r1,))
        # Add eBGP peering
        ebgp_session(self, as1r1, as2r1, link_type=CLIENT_PROVIDER)
        ebgp_session(self, as3r1, as2r1, link_type=SHARE)
        ebgp_session(self, as4r1, as2r1, link_type=CLIENT_PROVIDER)
        ebgp_session(self, as1r1, as3r1, link_type=CLIENT_PROVIDER)
        ebgp_session(self, as4r1, as3r1, link_type=SHARE)
        # Add test hosts
        for r in self.routers():
            self.addLink(r, self.addHost('h%s' % r))
        super(BGPPoliciesTopo2, self).build(*args, **kwargs)

    def bgp(self, name):
        r = self.addRouter(name, use_v4=False, use_v6=True)
        r.addDaemon(BGP, address_families=(
            _bgp.AF_INET(redistribute=('connected',)),
            _bgp.AF_INET6(redistribute=('connected',))))
        return r
