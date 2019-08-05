"""This module tests the static address and route allocations"""

from ipmininet.clean import cleanup
from ipmininet.examples.partial_static_address_network import PartialStaticAddressNet
from ipmininet.examples.static_address_network import StaticAddressNet
from ipmininet.examples.static_routing import StaticRoutingNet
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

        assert net["r1"].intf("r1-eth0").ip == "10.0.0.1"
        assert net["r1"].intf("r1-eth0").ip6 == "2001:1a::1"
        assert net["r1"].intf("r1-eth1").ip == "10.1.0.1"
        assert net["r1"].intf("r1-eth1").ip6 == "2001:12::1"
        assert net["r1"].intf("r1-eth2").ip == "10.2.0.1"
        assert net["r1"].intf("r1-eth2").ip6 == "2001:12b::1"

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


@require_root
def test_staticd_example():
    try:
        net = IPNet(topo=StaticRoutingNet())
        net.start()

        assert_connectivity(net, v6=False)
        assert_connectivity(net, v6=True)

        paths = [
            ["h1", "r1", "r2", "h2"],
            ["h2", "r2", "r1", "h1"]
        ]
        for p in paths:
            assert_path(net, p, v6=False)
            assert_path(net, p, v6=True)

        net.stop()
    finally:
        cleanup()
