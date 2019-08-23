"""This file contains a simple crash test for RIPng topology"""

from ipmininet.iptopo import IPTopo
from ipmininet.router.config.ripng import RIPng


class SimpleCrashRIPng(IPTopo):

    def build(self, *args, **kwargs):
        """
        +-----+     +-----+     +-----+     +-----+
        | h1  +-----+ r1  +-----+ r2  +-----+ h2  |
        +-----+     +-----+     +-----+     +-----+
        """
        r1, r2 = self.addRouter_v6('r1'), self.addRouter_v6('r2')
        h1, h2 = self.addHost('h1'), self.addHost('h2')

        self.addLink(h1, r1)
        self.addLink(h2, r2)
        lr1r2 = self.addLink(r1, r2)
        lr1r2[r1].addParams(ip=("2042:12::1/64"))
        lr1r2[r2].addParams(ip=("2042:12::2/64"))

        self.addSubnet(nodes=[r1, h1], subnets=["2042:11::/64"])
        self.addSubnet(nodes=[r2, h2], subnets=["2042:22::/64"])

        r1.addDaemon(RIPng)
        r2.addDaemon(RIPng)

        super(SimpleCrashRIPng, self).build(*args, **kwargs)

    def addRouter_v6(self, name):
        return self.addRouter(name, use_v4=False, use_v6=True)
