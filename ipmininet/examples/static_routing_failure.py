"""This file contains an example of topology using static routing.
   There is no connectivity between all the routers.
   Changing one routing table would ensure connectivity."""

from ipmininet.iptopo import IPTopo
from ipmininet.router.config import RouterConfig, STATIC, StaticRoute


class StaticRoutingNetFailure(IPTopo):

    def build(self, *args, **kwargs):
        r"""
            +-----+     +-----+     +-----+     +-----+     +-----+
            | h1  +-----+ r1  +-----+ r2  +-----+ r3  +-----+ h3  |
            +-----+     +--+--+     +--+--+     +--+--+     +-----+
                           |           |   \   /   |
                           |           |    \ /    |
                           |           |     \     |
                           |           |    / \    |
                           |           |   /   \   |
            +-----+     +--+--+     +--+--+     +--+--+     +-----+
            | h6  +-----+ r6  +-----+ r5  +-----+ r4  +-----+ h4  |
            +-----+     +-----+     +-----+     +-----+     +-----+

        """

        r1, r2, r3, r4, r5, r6 = \
            self.addRouters('r1', 'r2', 'r3', 'r4', 'r5', 'r6',
                            use_v4=False, use_v6=True, config=RouterConfig)

        h1 = self.addHost('h1', use_v4=False, use_v6=True)
        h3 = self.addHost('h3', use_v4=False, use_v6=True)
        h4 = self.addHost('h4', use_v4=False, use_v6=True)
        h6 = self.addHost('h6', use_v4=False, use_v6=True)

        self.addLinks((h1, r1), (h3, r3), (h4, r4), (h6, r6))

        lr1r2 = self.addLink(r1, r2)
        lr1r2[r1].addParams(ip=("2042:12::1/64",))
        lr1r2[r2].addParams(ip=("2042:12::2/64",))
        lr1r6 = self.addLink(r1, r6)
        lr1r6[r1].addParams(ip=("2042:16::1/64",))
        lr1r6[r6].addParams(ip=("2042:16::2/64",))
        lr2r4 = self.addLink(r2, r4)
        lr2r4[r2].addParams(ip=("2042:24::1/64",))
        lr2r4[r4].addParams(ip=("2042:24::2/64",))
        lr2r5 = self.addLink(r2, r5)
        lr2r5[r2].addParams(ip=("2042:25::1/64",))
        lr2r5[r5].addParams(ip=("2042:25::2/64",))
        lr2r3 = self.addLink(r2, r3)
        lr2r3[r2].addParams(ip=("2042:23::1/64",))
        lr2r3[r3].addParams(ip=("2042:23::2/64",))
        lr3r4 = self.addLink(r3, r4)
        lr3r4[r3].addParams(ip=("2042:34::1/64",))
        lr3r4[r4].addParams(ip=("2042:34::2/64",))
        lr3r5 = self.addLink(r3, r5)
        lr3r5[r3].addParams(ip=("2042:35::1/64",))
        lr3r5[r5].addParams(ip=("2042:35::2/64",))
        lr4r5 = self.addLink(r4, r5)
        lr4r5[r4].addParams(ip=("2042:45::1/64",))
        lr4r5[r5].addParams(ip=("2042:45::2/64",))
        lr5r6 = self.addLink(r5, r6)
        lr5r6[r5].addParams(ip=("2042:56::1/64",))
        lr5r6[r6].addParams(ip=("2042:56::2/64",))

        self.addSubnet(nodes=[r1, h1], subnets=["2042:11::/64"])
        self.addSubnet(nodes=[r3, h3], subnets=["2042:33::/64"])
        self.addSubnet(nodes=[r4, h4], subnets=["2042:44::/64"])
        self.addSubnet(nodes=[r6, h6], subnets=["2042:66::/64"])

        r1.addDaemon(STATIC, static_routes=[
            StaticRoute(prefix="2042:33::2", nexthop="2042:12::2"),
            StaticRoute(prefix="2042:66::2", nexthop="2042:16::2"),
            StaticRoute(prefix="2042:44::2", nexthop="2042:12::2"),
        ])
        r2.addDaemon(STATIC, static_routes=[
            StaticRoute(prefix="2042:11::2", nexthop="2042:25::2"),
            StaticRoute(prefix="2042:33::2", nexthop="2042:25::2"),
            StaticRoute(prefix="2042:44::2", nexthop="2042:24::2"),
            StaticRoute(prefix="2042:66::2", nexthop="2042:12::1")
        ])
        r3.addDaemon(STATIC, static_routes=[
            StaticRoute(prefix="2042:11::2", nexthop="2042:23::1"),
            StaticRoute(prefix="2042:66::2", nexthop="2042:23::1"),
            StaticRoute(prefix="2042:44::2", nexthop="2042:23::1"),
        ])
        r4.addDaemon(STATIC, static_routes=[
            StaticRoute(prefix="2042:11::2", nexthop="2042:34::1"),
            StaticRoute(prefix="2042:66::2", nexthop="2042:45::2"),
            StaticRoute(prefix="2042:33::2", nexthop="2042:34::1")
        ])
        r5.addDaemon(STATIC, static_routes=[
            StaticRoute(prefix="2042:11::2", nexthop="2042:23::2"),
            StaticRoute(prefix="2042:33::2", nexthop="2042:56::1"),
            StaticRoute(prefix="2042:44::2", nexthop="2042:56::1"),
            StaticRoute(prefix="2042:66::2", nexthop="2042:45::1"),
        ])
        r6.addDaemon(STATIC, static_routes=[
            StaticRoute(prefix="2042:11::2", nexthop="2042:16::1"),
            StaticRoute(prefix="2042:33::2", nexthop="2042:56::1"),
            StaticRoute(prefix="2042:44::2", nexthop="2042:16::1"),
        ])

        super().build(*args, **kwargs)
