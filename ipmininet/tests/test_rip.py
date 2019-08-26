"""This module tests the RIPng daemon
    This test requires the deamon OSPF6 to be disabled"""
import pytest

from ipmininet.clean import cleanup
from ipmininet.ipnet import IPNet
from ipmininet.iptopo import IPTopo
from ipmininet.router.config import RIPng
from ipmininet.router.config.base import RouterConfig
from ipmininet.router.config.ripng import RIPRedistributedRoute
from ipmininet.tests.utils import assert_connectivity, assert_path
from . import require_root


class MinimalRIPngNet(IPTopo):
    """
                 3
    h1 ---- r1 ---- r2 ---- h2
            |        |
            +-- r3 --+
                 |
                h3
    """
    def __init__(self, *args, **kwargs):
        super(MinimalRIPngNet, self).__init__(*args, **kwargs)

    def build(self, *args, **kwargs):
        r1 = self.addRouter("r1", config=RouterConfig)
        r1.addDaemon(RIPng)
        r2 = self.addRouter("r2", config=RouterConfig)
        r2.addDaemon(RIPng)
        r3 = self.addRouter("r3", config=RouterConfig)
        r3.addDaemon(RIPng)
        self.addLink(r1, r2, igp_metric=3, params1={"ip":"2042:12::1/64"}, params2={"ip":"2042:12::2/64"})
        self.addLink(r1, r3,               params1={"ip":"2042:13::1/64"}, params2={"ip":"2042:13::3/64"})
        self.addLink(r2, r3,               params1={"ip":"2042:23::2/64"}, params2={"ip":"2042:23::3/64"})

        h1 = self.addHost("h1")
        self.addLink(r1, h1, params1={"ip":"2042:11::1/64"}, params2={"ip":"2042:11::2/64"})
        h2 = self.addHost("h2")
        self.addLink(r2, h2, params1={"ip":"2042:22::1/64"}, params2={"ip":"2042:22::2/64"})
        h3 = self.addHost("h3")
        self.addLink(r3, h3, params1={"ip":"2042:33::1/64"}, params2={"ip":"2042:33::2/64"})
        super(MinimalRIPngNet, self).build(*args, **kwargs)



@require_root
def test_ripng():
    try:
        net = IPNet(topo=MinimalRIPngNet())
        net.start()
        assert_connectivity(net, v6=True)
        
        net.stop()
    finally:
        cleanup()