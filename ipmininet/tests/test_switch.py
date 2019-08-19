"""This module tests the switches"""

from ipmininet.clean import cleanup
from ipmininet.examples.spanning_tree import SpanningTreeNet
from ipmininet.ipnet import IPNet
from ipmininet.tests import require_root
from ipmininet.tests.utils import assert_connectivity


@require_root
def test_stp_example():
    try:
        net = IPNet(topo=SpanningTreeNet())
        net.start()

        assert_connectivity(net, v6=False)
        assert_connectivity(net, v6=True)

        net.stop()
    finally:
        cleanup()
