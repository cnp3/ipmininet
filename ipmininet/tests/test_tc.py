"""This module tests the delay and bandwidth allocation"""
import json
import re
import subprocess
import time

import pytest

from ipmininet.clean import cleanup
from ipmininet.examples.tc_advanced_network import TCAdvancedNet
from ipmininet.examples.tc_network import TCNet
from ipmininet.ipnet import IPNet
from ipmininet.link import TCIntf
from ipmininet.router import IPNode
from ipmininet.tests.utils import assert_connectivity
from . import require_root
from .utils import require_cmd

delay_regex = re.compile(r"time=(\d+\.?\d*) ms")


def assert_delay(src: IPNode, dst: IPNode, delay_target: float, tolerance=1.5,
                 v6=False):
    executable = "ping{v6}".format(v6="6" if v6 else "")
    require_cmd(executable, help_str="{executable} is required to run "
                                     "tests".format(executable=executable))

    cmd = "{executable} -c 10 {dst}".format(executable=executable,
                                            dst=dst.intf().ip6 if v6
                                            else dst.intf().ip)
    out, err, exitcode = src.pexec(cmd)

    assert exitcode == 0, "Cannot ping between {src} and {dst}: " \
                          "{err}".format(src=src, dst=dst, err=err)

    delays = []
    for line in out.split("\n"):
        match = delay_regex.search(line)
        if match is not None:
            delay = float(match.group(1))
            if delay_target - tolerance <= delay <= delay_target + tolerance:
                delays.append(delay)
    assert len(delays) >= 5, \
        "Less than half of the pings between {src} and {dst}" \
        " had the desired latency".format(src=src, dst=dst)


def assert_bw(src: IPNode, dst: IPNode, bw_target: float, tolerance=1,
              v6=False):
    require_cmd("iperf3", help_str="iperf3 is required to run tests")

    iperf = dst.popen("iperf3 -s -J --one-off", universal_newlines=True)
    time.sleep(1)
    dst_ip = dst.intf().ip6 if v6 else dst.intf().ip
    src.popen("iperf3 -c {}".format(dst_ip), stdout=subprocess.DEVNULL,
              stderr=subprocess.DEVNULL)
    out, err = iperf.communicate()

    assert iperf.poll() == 0, "Cannot use iperf3 between {src} and {dst}: " \
                              "{err}".format(src=src, dst=dst, err=err)

    bws = []
    data = json.loads(out)
    for sample in data["intervals"]:
        bw = int(sample["sum"]["bits_per_second"]) / 10 ** 6
        if bw_target - tolerance <= bw <= bw_target + tolerance:
            bws.append(bw)
    assert len(bws) >= 5, \
        "Less than half of the pings between {src} and {dst}" \
        " had the desired latency".format(src=src, dst=dst)


@require_root
@pytest.mark.parametrize("topo,delay,bw", [
    (TCNet, 32, 100),
    (TCAdvancedNet, 49, 10),
])
def test_tc_example(topo, delay, bw):
    """
    :param topo: The topology class
    :param delay: The delay between host h1 and h2 in ms
    :param bw: The bandwidth between h1 and h2 in Mbps
    """
    try:
        net = IPNet(topo=topo(), intf=TCIntf)
        net.start()

        # Check connectivity
        assert_connectivity(net, v6=False)
        assert_connectivity(net, v6=True)

        # Check delay
        assert_delay(net["h1"], net["h2"], delay, v6=False)
        assert_delay(net["h1"], net["h2"], delay, v6=True)

        # Check bandwidth
        assert_bw(net["h1"], net["h2"], bw, v6=False, tolerance=bw // 10)
        assert_bw(net["h1"], net["h2"], bw, v6=True, tolerance=bw // 10)

        net.stop()
    finally:
        cleanup()
