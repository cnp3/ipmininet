import re
import time

import pytest

from ipmininet.iptopo import IPTopo
from ipmininet.clean import cleanup
from ipmininet.ipnet import IPNet
from ipmininet.tests import require_root

class SimpleHubSpanningTree(IPTopo):

    def build(self, *args, **kwargs):
        """
            +-----+s2.2   s3.2+-----+s3.2
            | s2  +-----------+ s3  +---------------+
            +--+--+           +--+--+               |
           s2.1|                 |s3.1              |
               |                 |                  |
            ==========================[Hub S99]     |
               |                                    |
           s1.1|                                    |
            +--+--+1.2                              |
            | s1  +---------------------------------+
            +-----+
        """
        # adding switches
        s1 = self.addSwitch("s1", stp=True, prio=1)
        s2 = self.addSwitch("s2", stp=True, prio=2)
        s3 = self.addSwitch("s3", stp=True, prio=3)
        # adding hub
        s99 = self.addHub("s99")

        # adding links
        l = []
        l.append(self.addLink(s1, s99))
        l.append(self.addLink(s2, s99))
        l.append(self.addLink(s3, s99))
        self.addLink(s2, s3)
        self.addLink(s1, s3)

        super(SimpleHubSpanningTree, self).build(*args, **kwargs)

@require_root
@pytest.mark.parametrize("switch,expected_lines", [
    ("s1", ["forwarding", "forwarding"]),
    ("s2", ["forwarding", "forwarding"]),
    ("s3", ["forwarding", "blocking", "blocking"]),
    ("s99", ["forwarding", "forwarding", "forwarding"])
])

def test_hub(switch, expected_lines):
    try:
        net = IPNet(topo=SimpleHubSpanningTree())
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