"""This file contains a simple crash test for RIPng topology"""

from ipmininet.iptopo import IPTopo
from ipmininet.router.config.ripng import RIPng
from ipmininet.router.config import RouterConfig


class MinimalRIPngNetTest(IPTopo):
    """
                 5
    h1 ---- r1 ---- r2 ---- h2
            |        |
            +-- r3 --+
                 |
                h3
    """
    def __init__(self, is_test_flush=True ,*args, **kwargs):
        self.args_test_2 = [100, 1, 1]
        self.is_test_flush = is_test_flush
        super(MinimalRIPngNetTest, self).__init__(*args, **kwargs)

    def build(self, *args, **kwargs):
        r1 = self.addRouter_v6("r1")
        r2 = self.addRouter_v6("r2")
        r3 = self.addRouter_v6("r3")
        h1 = self.addHost("h1")
        h2 = self.addHost("h2")
        h3 = self.addHost("h3")

        lr1r2 = self.addLink(r1, r2, igp_metric=10)
        lr1r2[r1].addParams(ip=("2042:12::1/64"))
        lr1r2[r2].addParams(ip=("2042:12::2/64"))
        lr1r3 = self.addLink(r1, r3)
        lr1r3[r1].addParams(ip=("2042:13::1/64"))
        lr1r3[r3].addParams(ip=("2042:13::3/64"))
        lr2r3 = self.addLink(r2, r3)
        lr2r3[r2].addParams(ip=("2042:23::2/64"))
        lr2r3[r3].addParams(ip=("2042:23::3/64"))

        lr1h1 = self.addLink(r1, h1)
        lr2h2 = self.addLink(r2, h2)
        lr3h3 = self.addLink(r3, h3)

        self.addSubnet(nodes=[r1, h1], subnets=["2042:11::/64"])
        self.addSubnet(nodes=[r2, h2], subnets=["2042:22::/64"])
        self.addSubnet(nodes=[r3, h3], subnets=["2042:33::/64"])
        if self.is_test_flush:
            for i in (r1, r2, r3):
                i.addDaemon(RIPng, update_timer=self.args_test_2[0], timeout_timer=self.args_test_2[1], garbage_timer=self.args_test_2[2])
        else:
            r1.addDaemon(RIPng)
            r2.addDaemon(RIPng)
            r3.addDaemon(RIPng)

        super(MinimalRIPngNetTest, self).build(*args, **kwargs)

    def addRouter_v6(self, name):
        return self.addRouter(name, use_v4=False, use_v6=True, config=RouterConfig)
