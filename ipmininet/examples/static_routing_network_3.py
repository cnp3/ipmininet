"""This file contains a more complex example of static routing."""

from ipmininet.iptopo import IPTopo
from ipmininet.router.config import RouterConfig, STATIC, StaticRoute


class StaticRoutingNet3(IPTopo):

    def build(self, *args, **kwargs):
        """
            +-----+     +-----+     +-----+     +-----+     +-----+
            | h1  +-----+ r1  +-----+ r2  +-----+ r3  +-----+ h3  |
            +-----+     +--+--+     +--+--+     +--+--+     +-----+
                           |           |           |
            +-----+     +--+--+     +--+--+     +--+--+     +-----+
            | h6  +-----+ r6  +-----+ r5  +-----+ r4  +-----+ h4  |
            +-----+     +-----+     +-----+     +-----+     +-----+

        """
        r1 = self.addRouter('r1', use_v6=True)
        r2 = self.addRouter('r2', use_v6=True)
        r3 = self.addRouter('r3', use_v6=True)
        r4 = self.addRouter('r4', use_v6=True)
        r5 = self.addRouter('r5', use_v6=True)
        r6 = self.addRouter('r6', use_v6=True)

        h1 = self.addHost('h1', use_v6=True)
        h3 = self.addHost('h3', use_v6=True)
        h4 = self.addHost('h4', use_v6=True)
        h6 = self.addHost('h6', use_v6=True)

        self.addLink(h1, r1)
        self.addLink(h3, r3)
        self.addLink(h4, r4)
        self.addLink(h6, r6)

        self.addLink(r1, r2)
        self.addLink(r1, r6)
        self.addLink(r2, r5)
        self.addLink(r2, r3)
        self.addLink(r3, r4)
        self.addLink(r4, r5)
        self.addLink(r5, r6)

        self.addSubnet(nodes=[r1, h1], subnets=["10.11.0.0/24", "2042:11::/64"])
        self.addSubnet(nodes=[r3, h3], subnets=["10.33.0.0/24", "2042:33::/64"])
        self.addSubnet(nodes=[r4, h4], subnets=["10.44.0.0/24", "2042:44::/64"])
        self.addSubnet(nodes=[r6, h6], subnets=["10.66.0.0/24", "2042:66::/64"])

        self.addSubnet(nodes=[r1, r2], subnets=["10.12.0.0/24", "2042:11::/64"])
        self.addSubnet(nodes=[r1, r6], subnets=["10.16.0.0/24", "2042:16::/64"])
        self.addSubnet(nodes=[r2, r5], subnets=["10.25.0.0/24", "2042:25::/64"])
        self.addSubnet(nodes=[r2, r3], subnets=["10.23.0.0/24", "2042:23::/64"])
        self.addSubnet(nodes=[r3, r4], subnets=["10.34.0.0/24", "2042:34::/64"])
        self.addSubnet(nodes=[r4, r5], subnets=["10.45.0.0/24", "2042:45::/64"])
        self.addSubnet(nodes=[r5, r6], subnets=["10.56.0.0/24", "2042:56::/64"])

        
        r1.addDaemon(STATIC, static_routes=[
                                            StaticRoute("10.33.0.2/32", "10.12.0.2"),
                                            StaticRoute("10.66.0.2/32", "10.12.0.2"),
                                            StaticRoute("10.44.0.2/32", "10.12.0.2"),

                                            StaticRoute("2042:33::2", "2042:12::2"),
                                            StaticRoute("2042:66::2", "2042:12::2"),
                                            StaticRoute("2042:44::2", "2042:12::2"),
                                           ])
        r2.addDaemon(STATIC, static_routes=[
                                            StaticRoute("10.11.0.2/32", "10.12.0.1"),
                                            StaticRoute("10.33.0.2/32", "10.23.0.2"),
                                            StaticRoute("10.44.0.2/32", "10.23.0.2"),
                                            StaticRoute("10.66.0.2/32", "10.25.0.2"),

                                            StaticRoute("2042:11::2", "2042:12::1"),
                                            StaticRoute("2042:33::2", "2042:23::2"),
                                            StaticRoute("2042:44::2", "2042:23::2"),
                                            StaticRoute("2042:66::2", "2042:23::2")
                                           ])
        r3.addDaemon(STATIC, static_routes=[
                                            StaticRoute("10.11.0.2/32", "10.23.0.1"),
                                            StaticRoute("10.66.0.2/32", "10.23.0.1"),
                                            StaticRoute("10.44.0.2/32", "10.34.0.2"),

                                            StaticRoute("2042:11::2", "2042:23::1"),
                                            StaticRoute("2042:66::2", "2042:23::1"),
                                            StaticRoute("2042:44::2", "2042:23::2"),
                                           ])
        r4.addDaemon(STATIC, static_routes=[
                                            StaticRoute("10.11.0.2/32", "10.34.0.1"),
                                            StaticRoute("10.66.0.2/32", "10.34.0.1"),
                                            StaticRoute("10.33.0.2/32", "10.34.0.1"),

                                            StaticRoute("2042:11::2", "2042:34::1"),
                                            StaticRoute("2042:66::2", "2042:34::1"),
                                            StaticRoute("2042:33::2", "2042:34::1")
                                           ])
        r5.addDaemon(STATIC, static_routes=[
                                            StaticRoute("10.11.0.2/32", "10.25.0.1"),
                                            StaticRoute("10.33.0.2/32", "10.25.0.1"),
                                            StaticRoute("10.44.0.2/32", "10.25.0.1"),
                                            StaticRoute("10.66.0.2/32", "10.56.0.2"),

                                            StaticRoute("2042:11::2", "2042:25::1"),
                                            StaticRoute("2042:33::2", "2042:25::1"),
                                            StaticRoute("2042:44::2", "2042:25::1"),
                                            StaticRoute("2042:66::2", "2042:56::2"),
                                           ])
        r6.addDaemon(STATIC, static_routes=[
                                            StaticRoute("10.11.0.2/32", "10.56.0.1"),
                                            StaticRoute("10.33.0.2/32", "10.56.0.1"),
                                            StaticRoute("10.44.0.2/32", "10.56.0.1"),

                                            StaticRoute("2042:11::2", "2042:56::1"),
                                            StaticRoute("2042:33::2", "2042:56::1"),
                                            StaticRoute("2042:44::2", "2042:56::1"),
                                           ])
        
        
        super(StaticRoutingNet3, self).build(*args, **kwargs)

