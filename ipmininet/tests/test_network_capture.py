""""This module test the Link Failure API"""
import os

from ipmininet.clean import cleanup
from ipmininet.ipnet import IPNet
from . import require_root
from .utils import assert_connectivity
from ..examples.network_capture import NetworkCaptureTopo


@require_root
def test_network_capture_example():
    capture_files = ["/tmp/capture_r1.pcapng", "/tmp/capture_r2-eth0.pcapng",
                     "/tmp/capture_s1.pcapng", "/tmp/capture_s2-eth1.pcapng"]
    try:
        # Delete pre-existing capture files
        for file_name in capture_files:
            if os.path.exists(file_name):
                os.unlink(file_name)

        net = IPNet(topo=NetworkCaptureTopo())
        net.start()

        # Check files existence
        for file_name in capture_files:
            assert os.path.exists(file_name), \
                f"The capture file {file_name} was not created"

        # Check example connectivity
        assert_connectivity(net, v6=False)
        assert_connectivity(net, v6=True)

        net.stop()
    finally:
        cleanup()
