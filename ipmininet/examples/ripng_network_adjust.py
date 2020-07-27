"""This file contains a topology controlled by RIPng daemons.
   The weight can be customized."""

from ipmininet.iptopo import IPTopo
from ipmininet.router.config.ripng import RIPng
from ipmininet.router.config import RouterConfig


class RIPngNetworkAdjust(IPTopo):

    def __init__(self, lr1r2_cost=1, lr1r3_cost=1, lr1r5_cost=1, lr2r3_cost=1,
                 lr2r4_cost=1, lr2r5_cost=1, lr4r5_cost=1, *args, **kwargs):
        """
        :param lr1r2_cost: Cost of link between R1 and R2
        :param lr1r3_cost: Cost of link between R1 and R3
        :param lr1r5_cost: Cost of link between R1 and R5
        :param lr2r3_cost: Cost of link between R2 and R3
        :param lr2r4_cost: Cost of link between R2 and R4
        :param lr2r5_cost: Cost of link between R2 and R5
        :param lr4r5_cost: Cost of link between R4 and R5
        """

        self.lr1r2_cost = int(lr1r2_cost)
        self.lr1r3_cost = int(lr1r3_cost)
        self.lr1r5_cost = int(lr1r5_cost)
        self.lr2r3_cost = int(lr2r3_cost)
        self.lr2r4_cost = int(lr2r4_cost)
        self.lr2r5_cost = int(lr2r5_cost)
        self.lr4r5_cost = int(lr4r5_cost)
        super().__init__(*args, **kwargs)

    def build(self, *args, **kwargs):
        r"""
                  +-----+               +-----+
                  | h3  |               | h4  |
                  +--+--+               +--+--+
                     |                     |
                  +--+--+               +--+--+
                  | r3  |               | r4  |
                  +--+--+               +--+--+
                    / \                   / \
                   /   \                 /   \
                  /     \               /     \
                 /       \             /       \
                /         \           /         \
               /           \         /           \
              /             \       /             \
       +-----+               +-----+               +-----+
       | r1  +---------------+ r2  +---------------+ r5  |
       +--+--+               +-----+               +--+--+
          |   \                                   /   |
       +--+--+ \                                 / +--+--+
       | h1  |  +-------------------------------+  | h5  |
       +-----+                                     +-----+
        """

        r1, r2, r3, r4, r5 = self.addRouters('r1', 'r2', 'r3', 'r4', 'r5',
                                             use_v4=False, use_v6=True,
                                             config=RouterConfig)
        r1.addDaemon(RIPng)
        r2.addDaemon(RIPng)
        r3.addDaemon(RIPng)
        r4.addDaemon(RIPng)
        r5.addDaemon(RIPng)

        h1 = self.addHost('h1')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')
        h5 = self.addHost('h5')

        self.addLinks((h1, r1), (h3, r3), (h4, r4), (h5, r5))

        lr1r2 = self.addLink(r1, r2, igp_metric=self.lr1r2_cost)
        lr1r2[r1].addParams(ip="2042:12::1/64")
        lr1r2[r2].addParams(ip="2042:12::2/64")
        lr1r3 = self.addLink(r1, r3, igp_metric=self.lr1r3_cost)
        lr1r3[r1].addParams(ip="2042:13::1/64")
        lr1r3[r3].addParams(ip="2042:13::3/64")
        lr1r5 = self.addLink(r1, r5, igp_metric=self.lr1r5_cost)
        lr1r5[r1].addParams(ip="2042:15::1/64")
        lr1r5[r5].addParams(ip="2042:15::5/64")
        lr2r3 = self.addLink(r2, r3, igp_metric=self.lr2r3_cost)
        lr2r3[r2].addParams(ip="2042:23::2/64")
        lr2r3[r3].addParams(ip="2042:23::3/64")
        lr2r4 = self.addLink(r2, r4, igp_metric=self.lr2r4_cost)
        lr2r4[r2].addParams(ip="2042:24::2/64")
        lr2r4[r4].addParams(ip="2042:24::4/64")
        lr2r5 = self.addLink(r2, r5, igp_metric=self.lr2r5_cost)
        lr2r5[r2].addParams(ip="2042:25::2/64")
        lr2r5[r5].addParams(ip="2042:25::5/64")
        lr4r5 = self.addLink(r4, r5, igp_metric=self.lr4r5_cost)
        lr4r5[r4].addParams(ip="2042:45::4/64")
        lr4r5[r5].addParams(ip="2042:45::5/64")

        self.addSubnet(nodes=[r1, h1], subnets=["2042:11::/64"])
        self.addSubnet(nodes=[r3, h3], subnets=["2042:33::/64"])
        self.addSubnet(nodes=[r4, h4], subnets=["2042:44::/64"])
        self.addSubnet(nodes=[r5, h5], subnets=["2042:55::/64"])

        super().build(*args, **kwargs)
