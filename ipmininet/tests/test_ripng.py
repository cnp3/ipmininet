"""This module tests the RIPng daemon"""
import time

import pytest

from ipmininet.clean import cleanup
from ipmininet.examples.ripng_network import RIPngNetwork
from ipmininet.examples.ripng_network_adjust import RIPngNetworkAdjust
from ipmininet.ipnet import IPNet
from ipmininet.iptopo import IPTopo
from ipmininet.router.config import RIPng
from ipmininet.router.config.base import RouterConfig
from ipmininet.tests.utils import assert_connectivity, assert_path,\
    assert_routing_table
from . import require_root


class MinimalRIPngNet(IPTopo):
    """
                 5
    h1 ---- r1 ---- r2 ---- h2
            |        |
            +-- r3 --+
                 |
                h3
    """

    def __init__(self, is_test_flush=False, *args, **kwargs):
        self.args_test_2 = [100, 1, 1]
        self.is_test_flush = is_test_flush
        super(MinimalRIPngNet, self).__init__(*args, **kwargs)

    def build(self, *args, **kwargs):
        r1 = self.addRouter_v6("r1")
        r2 = self.addRouter_v6("r2")
        r3 = self.addRouter_v6("r3")
        h1 = self.addHost("h1")
        h2 = self.addHost("h2")
        h3 = self.addHost("h3")

        lr1r2 = self.addLink(r1, r2, igp_metric=10)
        lr1r2[r1].addParams(ip="2042:12::1/64")
        lr1r2[r2].addParams(ip="2042:12::2/64")
        lr1r3 = self.addLink(r1, r3)
        lr1r3[r1].addParams(ip="2042:13::1/64")
        lr1r3[r3].addParams(ip="2042:13::3/64")
        lr2r3 = self.addLink(r2, r3)
        lr2r3[r2].addParams(ip="2042:23::2/64")
        lr2r3[r3].addParams(ip="2042:23::3/64")

        self.addLink(r1, h1)
        self.addLink(r2, h2)
        self.addLink(r3, h3)

        self.addSubnet(nodes=[r1, h1], subnets=["2042:11::/64"])
        self.addSubnet(nodes=[r2, h2], subnets=["2042:22::/64"])
        self.addSubnet(nodes=[r3, h3], subnets=["2042:33::/64"])
        if self.is_test_flush:
            for i in (r1, r2, r3):
                i.addDaemon(RIPng, update_timer=self.args_test_2[0],
                            timeout_timer=self.args_test_2[1],
                            garbage_timer=self.args_test_2[2])
        else:
            r1.addDaemon(RIPng)
            r2.addDaemon(RIPng)
            r3.addDaemon(RIPng)

        super(MinimalRIPngNet, self).build(*args, **kwargs)

    def addRouter_v6(self, name):
        return self.addRouter(name, use_v4=False, use_v6=True,
                              config=RouterConfig)


expected_paths = {
    MinimalRIPngNet.__name__: [
        ['h1', 'r1', 'r3', 'r2', 'h2'],
        ['h1', 'r1', 'r3', 'h3'],
        ['h2', 'r2', 'r3', 'r1', 'h1'],
        ['h2', 'r2', 'r3', 'h3'],
        ['h3', 'r3', 'r1', 'h1'],
        ['h3', 'r3', 'r2', 'h2']
    ],
    RIPngNetwork.__name__: [
        ['h1', 'r1', 'r2', 'r3', 'h3'],
        ['h1', 'r1', 'r4', 'h4'],
        ['h1', 'r1', 'r4', 'r5', 'h5'],

        ['h3', 'r3', 'r2', 'r1', 'h1'],
        ['h3', 'r3', 'r2', 'r5', 'r4', 'h4'],
        ['h3', 'r3', 'r2', 'r5', 'h5'],

        ['h4', 'r4', 'r1', 'h1'],
        ['h4', 'r4', 'r5', 'r2', 'r3', 'h3'],
        ['h4', 'r4', 'r5', 'h5'],

        ['h5', 'r5', 'r4', 'r1', 'h1'],
        ['h5', 'r5', 'r2', 'r3', 'h3'],
        ['h5', 'r5', 'r4', 'h4']
    ],
    RIPngNetworkAdjust.__name__: [
        ['h1', 'r1', 'r3', 'h3'],
        ['h1', 'r1', 'r5', 'h5'],

        ['h3', 'r3', 'r1', 'h1'],
        ['h3', 'r3', 'r2', 'r4', 'h4'],

        ['h4', 'r4', 'r2', 'r3', 'h3'],
        ['h4', 'r4', 'r5', 'h5'],

        ['h5', 'r5', 'r1', 'h1'],
        ['h5', 'r5', 'r4', 'h4']
    ],
    "RIPngNetworkAdjust-mod": [
        ['h1', 'r1', 'r3', 'h3'],
        ['h1', 'r1', 'r2', 'r4', 'h4'],
        ['h1', 'r1', 'r2', 'r5', 'h5'],

        ['h3', 'r3', 'r1', 'h1'],
        ['h3', 'r3', 'r2', 'r4', 'h4'],
        ['h3', 'r3', 'r2', 'r5', 'h5'],

        ['h4', 'r4', 'r2', 'r3', 'h3'],
        ['h4', 'r4', 'r2', 'r3', 'h3'],
        ['h4', 'r4', 'r5', 'h5'],

        ['h5', 'r5', 'r2', 'r1', 'h1'],
        ['h5', 'r5', 'r2', 'r3', 'h3'],
        ['h5', 'r5', 'r4', 'h4']
    ]
}


@require_root
@pytest.mark.parametrize("topo", [
    MinimalRIPngNet,
    RIPngNetwork,
    RIPngNetworkAdjust
])
def test_ripng_examples(topo):
    try:
        net = IPNet(topo=topo())
        net.start()
        assert_connectivity(net, v6=True)
        for path in expected_paths[topo.__name__]:
            assert_path(net, path, v6=True)

        net.stop()
    finally:
        cleanup()


@require_root
def test_ripng_adjust():
    try:
        net = IPNet(topo=RIPngNetworkAdjust(lr1r5_cost=5))
        net.start()
        assert_connectivity(net, v6=True)
        for path in expected_paths["RIPngNetworkAdjust-mod"]:
            assert_path(net, path, v6=True)

        net.stop()
    finally:
        cleanup()


@require_root
def test_ripng_flush_routing_tables():
    try:
        net = IPNet(topo=MinimalRIPngNet(is_test_flush=True))
        net.start()
        time.sleep(10)

        routing_tables = {
            "r1": ["2042:22::/64", "2042:33::/64", "2042:23::/64"],
            "r2": ["2042:11::/64", "2042:33::/64", "2042:13::/64"],
            "r3": ["2042:11::/64", "2042:22::/64", "2042:12::/64"]
        }
        for router, expected_ipv6 in routing_tables.items():
            assert_routing_table(net[router], expected_ipv6)
        net.stop()
    finally:
        cleanup()
