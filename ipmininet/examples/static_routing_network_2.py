"""This file contains another example of static routing."""

from ipmininet.iptopo import IPTopo
from ipmininet.router.config import RouterConfig, STATIC, StaticRoute


class StaticRoutingNet2(IPTopo):
    r"""
    +-----+     +-----+    +-----+     +-----+
    | h1  +-----+ r1  +----+ r2  +-----+ h2  |
    +-----+     +--+--+    +--+--+     +-----+
                   |   \      |
                   |    \     |
                   |     \    |
                   |      \   |
    +-----+     +--+--+    +--+--+     +-----+
    | h3  +-----+ r3  +----+ r4  +-----+ h4  |
    +-----+     +-----+    +-----+     +-----+
    """

    def build(self, *args, **kwargs):
        # Change the config object for RouterConfig
        # because it does not add by default OSPF or OSPF6
        r1 = self.addRouter("r1", config=RouterConfig)
        r2 = self.addRouter("r2", config=RouterConfig)
        r3 = self.addRouter("r3", config=RouterConfig)
        r4 = self.addRouter("r4", config=RouterConfig)

        # Hosts
        h1 = self.addHost("h1")
        h2 = self.addHost("h2")
        h3 = self.addHost("h3")
        h4 = self.addHost("h4")

        # Link between r1 and r2
        lr1r2 = self.addLink(r1, r2)
        lr1r2[r1].addParams(ip=("2042:12::1/64", "10.12.0.1/24"))
        lr1r2[r2].addParams(ip=("2042:12::2/64", "10.12.0.2/24"))

        # Link between r1 and r3
        lr1r3 = self.addLink(r1, r3)
        lr1r3[r1].addParams(ip=("2042:13::1/64", "10.13.0.1/24"))
        lr1r3[r3].addParams(ip=("2042:13::3/64", "10.13.0.3/24"))

        # Link between r1 and r4
        lr1r4 = self.addLink(r1, r4)
        lr1r4[r1].addParams(ip=("2042:14::1/64", "10.14.0.1/24"))
        lr1r4[r4].addParams(ip=("2042:14::4/64", "10.14.0.4/24"))

        # Link between r2 and r4
        lr2r4 = self.addLink(r2, r4)
        lr2r4[r2].addParams(ip=("2042:24::2/64", "10.24.0.2/24"))
        lr2r4[r4].addParams(ip=("2042:24::4/64", "10.24.0.4/24"))

        # Link between r3 and r4
        lr3r4 = self.addLink(r3, r4)
        lr3r4[r3].addParams(ip=("2042:34::3/64", "10.34.0.3/24"))
        lr3r4[r4].addParams(ip=("2042:34::4/64", "10.34.0.4/24"))

        # Link between r1 and h1
        lr1h1 = self.addLink(r1, h1)
        lr1h1[r1].addParams(ip=("2042:1a::1/64", "10.51.0.1/24"))
        lr1h1[h1].addParams(ip=("2042:1a::a/64", "10.51.0.5/24"))

        # Link between r2 and h2
        lr2h2 = self.addLink(r2, h2)
        lr2h2[r2].addParams(ip=("2042:2b::2/64", "10.62.0.2/24"))
        lr2h2[h2].addParams(ip=("2042:2b::b/64", "10.62.0.6/24"))

        # Link between r3 and h3
        lr3h3 = self.addLink(r3, h3)
        lr3h3[r3].addParams(ip=("2042:3c::3/64", "10.73.0.3/24"))
        lr3h3[h3].addParams(ip=("2042:3c::c/64", "10.73.0.7/24"))

        # Link between r4 and h4
        lr4h4 = self.addLink(r4, h4)
        lr4h4[r4].addParams(ip=("2042:4d::4/64", "10.84.0.4/24"))
        lr4h4[h4].addParams(ip=("2042:4d::d/64", "10.84.0.8/24"))

        # Add static routes
        r1.addDaemon(STATIC, static_routes=[
            StaticRoute(prefix="2042:2b::/64", nexthop="2042:12::2"),  # h2->r2
            StaticRoute(prefix="10.62.0.0/24", nexthop="10.12.0.2"),
            StaticRoute(prefix="2042::/16", nexthop="2042:13::3"),  # /->r3
            StaticRoute(prefix="10.0.0.0/8", nexthop="10.13.0.3"),
            StaticRoute(prefix="10.73.0.0/24", nexthop="10.13.0.3")
        ])
        r2.addDaemon(STATIC, static_routes=[
            StaticRoute(prefix="2042:1a::/64", nexthop="2042:12::1"),  # h1->r1
            StaticRoute(prefix="10.51.0.0/24", nexthop="10.12.0.1"),
            StaticRoute(prefix="2042:3c::/64", nexthop="2042:24::4"),  # h3->r4
            StaticRoute(prefix="10.73.0.0/24", nexthop="10.24.0.4"),
            StaticRoute(prefix="2042:4d::/64", nexthop="2042:24::4"),  # h4->r4
            StaticRoute(prefix="10.84.0.0/24", nexthop="10.24.0.4")
        ])
        r3.addDaemon(STATIC, static_routes=[
            StaticRoute(prefix="2042::/16", nexthop="2042:34::4"),  # /->r4
            StaticRoute(prefix="10.0.0.0/8", nexthop="10.34.0.4"),
            StaticRoute(prefix="10.62.0.0/24", nexthop="10.34.0.4")
        ])
        r4.addDaemon(STATIC, static_routes=[
            StaticRoute(prefix="2042:1a::/64", nexthop="2042:14::1"),  # h1->r1
            StaticRoute(prefix="10.51.0.0/24", nexthop="10.14.0.1"),
            StaticRoute(prefix="2042:2b::/64", nexthop="2042:24::2"),  # h2->r2
            StaticRoute(prefix="10.62.0.0/24", nexthop="10.24.0.2"),
            StaticRoute(prefix="2042:3c::/64", nexthop="2042:14::1"),  # h3->r1
            StaticRoute(prefix="10.73.0.0/24", nexthop="10.14.0.1")
        ])

        super(StaticRoutingNet2, self).build(*args, **kwargs)
