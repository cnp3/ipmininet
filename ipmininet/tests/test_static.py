"""This module tests the static address and route allocations"""
import pytest

from ipmininet.clean import cleanup
from ipmininet.examples.partial_static_address_network import \
    PartialStaticAddressNet
from ipmininet.examples.static_address_network import StaticAddressNet
from ipmininet.examples.static_routing import StaticRoutingNet
from ipmininet.examples.static_routing_failure import StaticRoutingNetFailure
from ipmininet.examples.static_routing_network_basic import \
    StaticRoutingNetBasic
from ipmininet.examples.static_routing_network_complex import \
    StaticRoutingNetComplex
from ipmininet.ipnet import IPNet
from ipmininet.tests.utils import assert_connectivity, assert_path
from . import require_root


@require_root
def test_static_example():
    try:
        net = IPNet(topo=StaticAddressNet())
        net.start()

        # Check allocated addresses
        assert net["h1"].intf("h1-eth0").ip == "10.0.0.2"
        assert net["h1"].intf("h1-eth0").ip6 == "2001:1a::2"

        assert net["h2"].intf("h2-eth0").ip == "10.2.0.2"
        assert net["h2"].intf("h2-eth0").ip6 == "2001:12b::2"

        assert net["h3"].intf("h3-eth0").ip == "10.0.3.2"
        assert net["h3"].intf("h3-eth0").ip6 == "2001:3c::2"

        assert net["h4"].intf("h4-eth0").ip == "10.2.0.3"
        assert net["h4"].intf("h4-eth0").ip6 == "2001:12b::3"

        assert net["r1"].intf("lo").ip == "10.1.1.1"
        assert net["r1"].intf("lo").ip6 == "2042:1::1"
        assert net["r1"].intf("r1-eth0").ip == "10.0.0.1"
        assert net["r1"].intf("r1-eth0").ip6 == "2001:1a::1"
        assert net["r1"].intf("r1-eth1").ip == "10.1.0.1"
        assert net["r1"].intf("r1-eth1").ip6 == "2001:12::1"
        assert net["r1"].intf("r1-eth2").ip == "10.2.0.1"
        assert net["r1"].intf("r1-eth2").ip6 == "2001:12b::1"

        assert net["r2"].intf("lo").ip == "10.2.2.1"
        assert net["r2"].intf("lo").ip6 == "2042:2::1"
        assert net["r2"].intf("r2-eth0").ip == "10.1.0.2"
        assert net["r2"].intf("r2-eth0").ip6 == "2001:12::2"
        assert net["r2"].intf("r2-eth1").ip == "10.0.3.1"
        assert net["r2"].intf("r2-eth1").ip6 == "2001:3c::1"

        # Check connectivity
        assert_connectivity(net, v6=False)
        assert_connectivity(net, v6=True)

        net.stop()
    finally:
        cleanup()


@require_root
def test_partial_static_example():
    try:
        net = IPNet(topo=PartialStaticAddressNet())
        net.start()

        # Check allocated addresses
        assert net["h3"].intf("h3-eth0").ip == "192.168.1.2"
        assert net["h3"].intf("h3-eth0").ip6 == "fc00:1::2"

        assert net["r1"].intf("lo").ip6 == "2042:1::1"
        assert net["r1"].intf("r1-eth1").ip == "192.168.0.1"
        assert net["r1"].intf("r1-eth1").ip6 == "fc00::1"

        assert net["r2"].intf("r2-eth0").ip == "192.168.0.2"
        assert net["r2"].intf("r2-eth0").ip6 == "fc00::2"
        assert net["r2"].intf("r2-eth1").ip == "192.168.1.1"
        assert net["r2"].intf("r2-eth1").ip6 == "fc00:1::1"

        # Check connectivity
        assert_connectivity(net, v6=False)
        assert_connectivity(net, v6=True)

        net.stop()
    finally:
        cleanup()


static_paths = {

    StaticRoutingNet.__name__: [
        ["h1", "r1", "r2", "h2"],
        ["h2", "r2", "r1", "h1"]
    ],
    StaticRoutingNetFailure.__name__: [
        ["h4", "r4", "r3", "h3"]
    ],
    StaticRoutingNetBasic.__name__: [
        ["h1", "r1", "r2", "h2"],
        ["h1", "r1", "r3", "h3"],
        ["h1", "r1", "r3", "r4", "h4"],

        ["h2", "r2", "r1", "h1"],
        ["h2", "r2", "r4", "r1", "r3", "h3"],
        ["h2", "r2", "r4", "h4"],

        ["h3", "r3", "r4", "r1", "h1"],
        ["h3", "r3", "r4", "r2", "h2"],
        ["h3", "r3", "r4", "h4"],

        ["h4", "r4", "r1", "h1"],
        ["h4", "r4", "r2", "h2"],
        ["h4", "r4", "r1", "r3", "h3"]
    ],
    StaticRoutingNetComplex.__name__: [
        ["h1", "r1", "r2", "r5", "r4", "r3", "h3"],
        ["h1", "r1", "r2", "r5", "r4", "h4"],
        ["h1", "r1", "r2", "r5", "r6", "h6"],

        ["h3", "r3", "r2", "r1", "h1"],
        ["h3", "r3", "r2", "r5", "r4", "h4"],
        ["h3", "r3", "r2", "r5", "r6", "h6"],

        ["h4", "r4", "r3", "r2", "r1", "h1"],
        ["h4", "r4", "r3", "h3"],
        ["h4", "r4", "r3", "r2", "r5", "r6", "h6"],

        ["h6", "r6", "r1", "h1"],
        ["h6", "r6", "r5", "r4", "r3", "h3"],
        ["h6", "r6", "r5", "r4", "h4"],
    ]
}


@require_root
@pytest.mark.parametrize("topo,connected,v4,v6", [
    (StaticRoutingNet, True, True, True),
    (StaticRoutingNetFailure, False, False, True),
    (StaticRoutingNetBasic, True, False, True),
    (StaticRoutingNetComplex, True, False, True),
])
def test_static_examples(topo, connected, v4, v6):
    try:
        net = IPNet(topo=topo())
        net.start()

        if connected and v4:
            assert_connectivity(net, v6=False)
        if connected and v6:
            assert_connectivity(net, v6=True)

        for p in static_paths[topo.__name__]:
            if v4:
                assert_path(net, p, v6=False)
            if v6:
                assert_path(net, p, v6=True)

        net.stop()
    finally:
        cleanup()
