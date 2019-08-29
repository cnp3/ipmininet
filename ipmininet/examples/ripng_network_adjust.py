"""This file contains a simple crash test for RIPng topology"""

from ipmininet.iptopo import IPTopo
from ipmininet.router.config.ripng import RIPng
from ipmininet.router.config import RouterConfig


class RIPngNetworkAdjust(IPTopo):

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
                / a       \ b       c /         \ d
               /           \         /           \ 
              /             \       /             \ 
       +-----+      e        +-----+     f         +-----+
       | r1  +---------------+ r2  +---------------+ r5  |
       +--+--+               +-----+               +--+--+
          |   \                                   /   |
       +--+--+ \              g                  / +--+--+
       | h1  |  +-------------------------------+  | h5  |
       +-----+                                     +-----+
        """

        weights = input("""The goal of this exercise is to play with the weight of the links between the routers to 
        get the following paths: h1 -> r1 -> r5 -> r4 -> h4 and h3 -> r3 -> r2 -> r4 -> h4 \nusing RIP for IPv6 (
        distance vector routing).\nEnter all the weights of the links, from 'a' to 'g', separated only by a space. 
        \nRecall: the valid weights in RIP are [1, 16]\n""")

        while(True):
            try:
                w = self.check_correct_weights(weights)
                break
            except Exception as e:
                weights = input('Error: {}\n Try again:\n'.format(str(e)))

        r1 = self.addRouter_v6('r1')
        r2 = self.addRouter_v6('r2')
        r3 = self.addRouter_v6('r3')
        r4 = self.addRouter_v6('r4')
        r5 = self.addRouter_v6('r5')
        r1.addDaemon(RIPng)
        r2.addDaemon(RIPng)
        r3.addDaemon(RIPng)
        r4.addDaemon(RIPng)
        r5.addDaemon(RIPng)

        h1 = self.addHost('h1')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')
        h5 = self.addHost('h5')

        self.addLink(h1, r1)
        self.addLink(h3, r3)
        self.addLink(h4, r4)
        self.addLink(h5, r5)

        lr1r2 = self.addLink(r1, r2, igp_metric=w[4])
        lr1r2[r1].addParams(ip="2042:12::1/64")
        lr1r2[r2].addParams(ip="2042:12::2/64")
        lr1r3 = self.addLink(r1, r3, igp_metric=w[0])
        lr1r3[r1].addParams(ip="2042:13::1/64")
        lr1r3[r3].addParams(ip="2042:13::3/64")
        lr1r5 = self.addLink(r1, r5, igp_metric=w[6])
        lr1r5[r1].addParams(ip="2042:15::1/64")
        lr1r5[r5].addParams(ip="2042:15::5/64")
        lr2r3 = self.addLink(r2, r3, igp_metric=w[1])
        lr2r3[r2].addParams(ip="2042:23::2/64")
        lr2r3[r3].addParams(ip="2042:23::3/64")
        lr2r4 = self.addLink(r2, r4, igp_metric=w[2])
        lr2r4[r2].addParams(ip="2042:24::2/64")
        lr2r4[r4].addParams(ip="2042:24::4/64")
        lr2r5 = self.addLink(r2, r5, igp_metric=w[5])
        lr2r5[r2].addParams(ip="2042:25::2/64")
        lr2r5[r5].addParams(ip="2042:25::5/64")
        lr4r5 = self.addLink(r4, r5, igp_metric=w[3])
        lr4r5[r4].addParams(ip="2042:45::4/64")
        lr4r5[r5].addParams(ip="2042:45::5/64")

        self.addSubnet(nodes=[r1, h1], subnets=["2042:11::/64"])
        self.addSubnet(nodes=[r3, h3], subnets=["2042:33::/64"])
        self.addSubnet(nodes=[r4, h4], subnets=["2042:44::/64"])
        self.addSubnet(nodes=[r5, h5], subnets=["2042:55::/64"])

        super(RIPngNetworkAdjust, self).build(*args, **kwargs)

    def addRouter_v6(self, name):
        return self.addRouter(name, use_v4=False, use_v6=True, config=RouterConfig)
    
    def check_correct_weights(self, w):
        weights = w.split()
        if len(weights) != 7:
            raise IndexError('You did not enter a valid number of weights: {}'.format(len(weights)))
        try:
            wint = list(map(int, weights))
        except ValueError:
            raise ValueError('You did not enter integers')
        for i in wint:
            if i < 1 or i > 16:
                raise ValueError('You did not enter a valid weight: {}'.format(i))
        return wint
        

