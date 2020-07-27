from ipmininet.iptopo import IPTopo
from ipmininet.router.config import RouterConfig, STATIC, StaticRoute


class StaticRoutingNet(IPTopo):

    def build(self, *args, **kwargs):

        # Change the config object for RouterConfig
        # because it does not add by default OSPF or OSPF6
        r1 = self.addRouter("r1", config=RouterConfig,
                            lo_addresses=["2042:1::1/64", "10.1.1.1/24"])
        r2 = self.addRouter("r2", config=RouterConfig,
                            lo_addresses=["2042:2::1/64", "10.2.2.1/24"])
        h1 = self.addHost("h1")
        h2 = self.addHost("h2")

        lr1r2, lr1h1, lr2h2 = self.addLinks((r1, r2), (r1, h1), (r2, h2))

        lr1r2[r1].addParams(ip=("2042:12::1/64", "10.12.0.1/24"))
        lr1r2[r2].addParams(ip=("2042:12::2/64", "10.12.0.2/24"))

        lr1h1[r1].addParams(ip=("2042:1a::1/64", "10.51.0.1/24"))
        lr1h1[h1].addParams(ip=("2042:1a::a/64", "10.51.0.5/24"))

        lr2h2[r2].addParams(ip=("2042:2b::2/64", "10.62.0.2/24"))
        lr2h2[h2].addParams(ip=("2042:2b::b/64", "10.62.0.6/24"))

        # Add static routes
        r1.addDaemon(STATIC,
                     static_routes=[StaticRoute("2042:2b::/64", "2042:12::2"),
                                    StaticRoute("10.62.0.0/24", "10.12.0.2")])
        r2.addDaemon(STATIC,
                     static_routes=[StaticRoute("2042:1a::/64", "2042:12::1"),
                                    StaticRoute("10.51.0.0/24", "10.12.0.1")])

        super().build(*args, **kwargs)
