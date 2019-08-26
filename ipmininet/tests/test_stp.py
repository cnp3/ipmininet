import re
import time

import pytest

from ipmininet.iptopo import IPTopo
from ipmininet.clean import cleanup
from ipmininet.ipnet import IPNet
from ipmininet.tests import require_root


class SimpleSpanningTree(IPTopo):

    def build(self, *args, **kwargs):
        """
            +-----+s2.2   s3.2+-----+
            | s2  +-----2-----+ s3  |
            +--+--+           +--+--+
           s2.1|         s3.1/   |s3.3
               |            /    |
               |           /     |
               |          /      |
               |         /       |
               4        2        2
               |       /         |
               |      /          |
               |     /           |
               |    /            |
           s1.1|   /s1.3         |s4.2
            +--+--+           +--+--+
            | s1  +-----5-----+ s4  |
            +-----+s1.2   s4.1+-----+
        """
        # adding switches
        s1 = self.addSwitch("s1", stp=True, prio=1)
        s2 = self.addSwitch("s2", stp=True, prio=2)
        s3 = self.addSwitch("s3", stp=True, prio=3)
        s4 = self.addSwitch("s4", stp=True, prio=4)

        # adding links
        l1 = self.addLink(s1, s2)
        self.addLink(s1, s3)
        l2 = self.addLink(s1, s4)
        self.addLink(s2, s3)
        self.addLink(s3, s4)

        # stp_cost
        l1[0].addParams(stp_cost1=4)
        l1[0].addParams(stp_cost2=4)
        l2[0].addParams(stp_cost1=5)
        l2[0].addParams(stp_cost2=5)

        super(SimpleSpanningTree, self).build(*args, **kwargs)


@require_root
@pytest.mark.parametrize("switch,expected_lines", [
    ("s1", ["forwarding", "forwarding", "forwarding"]),
    ("s2", ["forwarding", "blocking"]),
    ("s3", ["forwarding", "forwarding", "forwarding"]),
    ("s4", ["blocking", "forwarding"])
])
def test_stp(switch, expected_lines):
    try:
        net = IPNet(topo=SimpleSpanningTree())
        net.start()
        partial_cmd = "brctl showstp"
        possible_states = "listening|learning|forwarding|blocking"
        ignore_state = "listening", "learning"  # state to be ignored
        cmd = ("%s %s" % (partial_cmd, switch))
        out = net[switch].cmd(cmd)
        states = re.findall(possible_states, out)
        # wait for the ports to be bounded
        count = 0
        while any(item in states for item in ignore_state):
            if count == 60:  # system waited too long for the stp, a problem may have occurred
                pytest.fail("[STP] system waited 60 seconds and the spanning tree wasn't fully computed")
            time.sleep(1)
            count += 1
            out = net[switch].cmd(cmd)
            states = re.findall(possible_states, out)
        for i in range(len(states)):
            assert states[i] == expected_lines[i], "[STP] state of port %d of switch %s wasn't correct" % (i, switch)
        net.stop()
    finally:
        cleanup()
