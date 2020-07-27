"""This file contains another example of static routing."""

from ipmininet.iptopo import IPTopo
from ipmininet.router.config import RouterConfig, STATIC, StaticRoute


class StaticRoutingNetBasic(IPTopo):
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
        r1, r2, r3, r4 = \
            self.addRouters('r1', 'r2', 'r3', 'r4',
                            use_v4=False, use_v6=True, config=RouterConfig)

        # Hosts
        h1 = self.addHost("h1")
        h2 = self.addHost("h2")
        h3 = self.addHost("h3")
        h4 = self.addHost("h4")

        # Link between r1 and r2
        lr1r2 = self.addLink(r1, r2)
        lr1r2[r1].addParams(ip="2042:12::1/64")
        lr1r2[r2].addParams(ip="2042:12::2/64")

        # Link between r1 and r3
        lr1r3 = self.addLink(r1, r3)
        lr1r3[r1].addParams(ip="2042:13::1/64")
        lr1r3[r3].addParams(ip="2042:13::3/64")

        # Link between r1 and r4
        lr1r4 = self.addLink(r1, r4)
        lr1r4[r1].addParams(ip="2042:14::1/64")
        lr1r4[r4].addParams(ip="2042:14::4/64")

        # Link between r2 and r4
        lr2r4 = self.addLink(r2, r4)
        lr2r4[r2].addParams(ip="2042:24::2/64")
        lr2r4[r4].addParams(ip="2042:24::4/64")

        # Link between r3 and r4
        lr3r4 = self.addLink(r3, r4)
        lr3r4[r3].addParams(ip="2042:34::3/64")
        lr3r4[r4].addParams(ip="2042:34::4/64")

        # Link between r1 and h1
        lr1h1 = self.addLink(r1, h1)
        lr1h1[r1].addParams(ip="2042:1a::1/64")
        lr1h1[h1].addParams(ip="2042:1a::a/64")

        # Link between r2 and h2
        lr2h2 = self.addLink(r2, h2)
        lr2h2[r2].addParams(ip="2042:2b::2/64")
        lr2h2[h2].addParams(ip="2042:2b::b/64")

        # Link between r3 and h3
        lr3h3 = self.addLink(r3, h3)
        lr3h3[r3].addParams(ip="2042:3c::3/64")
        lr3h3[h3].addParams(ip="2042:3c::c/64")

        # Link between r4 and h4
        lr4h4 = self.addLink(r4, h4)
        lr4h4[r4].addParams(ip="2042:4d::4/64")
        lr4h4[h4].addParams(ip="2042:4d::d/64")

        # Add static routes
        r1.addDaemon(STATIC, static_routes=[
            StaticRoute(prefix="2042:2b::/64", nexthop="2042:12::2"),  # h2->r2
            StaticRoute(prefix="2042:3c::/64", nexthop="2042:13::3"),  # h3->r3
            StaticRoute(prefix="2042:4d::/64", nexthop="2042:13::3"),  # h4->r3
        ])
        r2.addDaemon(STATIC, static_routes=[
            StaticRoute(prefix="2042:1a::/64", nexthop="2042:12::1"),  # h1->r1
            StaticRoute(prefix="2042:3c::/64", nexthop="2042:24::4"),  # h3->r4
            StaticRoute(prefix="2042:4d::/64", nexthop="2042:24::4"),  # h4->r4
        ])
        r3.addDaemon(STATIC, static_routes=[
            StaticRoute(prefix="2042::/16", nexthop="2042:34::4"),  # /->r4
        ])
        r4.addDaemon(STATIC, static_routes=[
            StaticRoute(prefix="2042:1a::/64", nexthop="2042:14::1"),  # h1->r1
            StaticRoute(prefix="2042:2b::/64", nexthop="2042:24::2"),  # h2->r2
            StaticRoute(prefix="2042:3c::/64", nexthop="2042:14::1"),  # h3->r1
        ])

        super().build(*args, **kwargs)
