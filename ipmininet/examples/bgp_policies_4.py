import ipmininet.router.config.bgp as _bgp
from ipmininet.iptopo import IPTopo
from ipmininet.router.config import BGP, ebgp_session, CLIENT_PROVIDER, SHARE


class BGPPoliciesTopo4(IPTopo):
    """This topology builds a 5-AS network exchanging BGP reachability as shown
    in the figure below. Shared cost are described with ' = ',
    client - provider with ' $ '.

    ASes always favor routes received from clients, then routes from shared-cost
    peering, and finally, routes received from providers.
    This is not influenced by the AS path length.

    This topology is taken from
    https://www.computer-networking.info/exercises/html/ex-bgp.html
    """
    def build(self, *args, **kwargs):
        r"""
        +-----+        =        +-----+
        | as2r+-----------------+ as5r|
        +--+--+                 +--+--+
           |   \               /   |
           |    \             /    |
           |     \$          /=    |
           |      \         /      |
           |       v       /       |
           |        +-----+        |
           |$       | as3r|        |$
           |        +-----+        |
           |       /       \       |
           |      /         \      |
           |     /=          \$    |
           |    /             \    |
           v   /               v   v
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

        # Add links
        las12 = self.addLink(as1r, as2r)
        las12[as1r].addParams(ip=("fd00:12::1/64",))
        las12[as2r].addParams(ip=("fd00:12::2/64",))

        las13 = self.addLink(as1r, as3r)
        las13[as1r].addParams(ip=("fd00:13::1/64",))
        las13[as3r].addParams(ip=("fd00:13::3/64",))

        las14 = self.addLink(as1r, as4r)
        las14[as1r].addParams(ip=("fd00:14::1/64",))
        las14[as4r].addParams(ip=("fd00:14::4/64",))

        las23 = self.addLink(as2r, as3r)
        las23[as2r].addParams(ip=("fd00:23::2/64",))
        las23[as3r].addParams(ip=("fd00:23::3/64",))

        las24 = self.addLink(as2r, as4r)
        las24[as2r].addParams(ip=("fd00:24::2/64",))
        las24[as4r].addParams(ip=("fd00:24::4/64",))

        las25 = self.addLink(as2r, as5r)
        las25[as2r].addParams(ip=("fd00:25::2/64",))
        las25[as5r].addParams(ip=("fd00:25::5/64",))

        las34 = self.addLink(as3r, as4r)
        las34[as3r].addParams(ip=("fd00:34::3/64",))
        las34[as4r].addParams(ip=("fd00:34::4/64",))

        las35 = self.addLink(as3r, as5r)
        las35[as3r].addParams(ip=("fd00:35::3/64",))
        las35[as5r].addParams(ip=("fd00:35::5/64",))

        las45 = self.addLink(as4r, as5r)
        las45[as4r].addParams(ip=("fd00:45::4/64",))
        las45[as5r].addParams(ip=("fd00:45::5/64",))

        # Set AS-ownerships
        self.addAS(1, (as1r,))
        self.addAS(2, (as2r,))
        self.addAS(3, (as3r,))
        self.addAS(4, (as4r,))
        self.addAS(5, (as5r,))

        # Add eBGP peering
        ebgp_session(self, as1r, as4r, link_type=CLIENT_PROVIDER)
        ebgp_session(self, as2r, as1r, link_type=CLIENT_PROVIDER)
        ebgp_session(self, as2r, as3r, link_type=CLIENT_PROVIDER)
        ebgp_session(self, as3r, as4r, link_type=CLIENT_PROVIDER)
        ebgp_session(self, as5r, as4r, link_type=CLIENT_PROVIDER)

        ebgp_session(self, as1r, as3r, link_type=SHARE)
        ebgp_session(self, as2r, as5r, link_type=SHARE)
        ebgp_session(self, as3r, as5r, link_type=SHARE)

        # Add test hosts
        for r in self.routers():
            self.addLink(r, self.addHost('h%s' % r))
        super(BGPPoliciesTopo4, self).build(*args, **kwargs)

    def bgp(self, name):
        r = self.addRouter(name, use_v4=False, use_v6=True)
        r.addDaemon(BGP, address_families=(
            _bgp.AF_INET(redistribute=('connected',)),
            _bgp.AF_INET6(redistribute=('connected',))))
        return r
