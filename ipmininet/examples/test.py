
from ipmininet.clean import cleanup
from ipmininet.ipnet import IPNet
from ipmininet.iptopo import IPTopo
from ipmininet.router.config import RIPng
from ipmininet.router.config.base import RouterConfig
from ipmininet.router.config.ripng import RIPRedistributedRoute
from ipmininet.tests.utils import assert_connectivity, assert_path


class MinimalRIPngNet(IPTopo):
    """
                 5
    h1 ---- r1 ---- r2 ---- h2
            |        |
            +-- r3 --+
                 |
                h3
    """
    def __init__(self, *args, **kwargs):
        super(MinimalRIPngNet, self).__init__(*args, **kwargs)

    def build(self, *args, **kwargs):
        r1 = self.addRouter_v6("r1")
        r2 = self.addRouter_v6("r2")
        r3 = self.addRouter_v6("r3")
        self.addLink(r1, r2, igp_metric=5)
        self.addLink(r1, r3)
        self.addLink(r2, r3)

        h1 = self.addHost("h1")
        self.addLink(r1, h1)
        h2 = self.addHost("h2")
        self.addLink(r2, h2)
        h3 = self.addHost("h3")
        self.addLink(r3, h3)

        r1.addDaemon(RIPng)
        r2.addDaemon(RIPng)
        r3.addDaemon(RIPng)
        super(MinimalRIPngNet, self).build(*args, **kwargs)

    def addRouter_v6(self, name):
        return self.addRouter(name, use_v4=False, use_v6=True, config=RouterConfig)