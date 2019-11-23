"""This module tests the switches, hubs and STP"""

import pytest

from ipmininet.clean import cleanup
from ipmininet.examples.spanning_tree import SpanningTreeNet
from ipmininet.examples.spanning_tree_adjust import SpanningTreeAdjust
from ipmininet.examples.spanning_tree_bus import SpanningTreeBus
from ipmininet.examples.spanning_tree_full_mesh import SpanningTreeFullMesh
from ipmininet.examples.spanning_tree_hub import SpanningTreeHub
from ipmininet.examples.spanning_tree_intermediate import \
    SpanningTreeIntermediate
from ipmininet.examples.spanning_tree_cost import SpanningTreeCost
from ipmininet.ipnet import IPNet
from ipmininet.iptopo import IPTopo
from ipmininet.tests import require_root
from ipmininet.tests.utils import assert_stp_state, assert_connectivity


class SimpleSpanningTree(IPTopo):

    def build(self, *args, **kwargs):
        """
            +-----+s2.2   s3.2+-----+
            | s2  +-----1-----+ s3  |
            +--+--+           +--+--+
           s2.1|         s3.1/   |s3.3
               |            /    |
               |           /     |
               |          /      |
               |         /       |
               4        1        1
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
        s1 = self.addSwitch("s1", prio=1)
        s2 = self.addSwitch("s2", prio=2)
        s3 = self.addSwitch("s3", prio=3)
        s4 = self.addSwitch("s4", prio=4)

        # adding links (with stp costs)
        self.addLink(s1, s2, stp_cost=4)
        self.addLink(s1, s3)
        self.addLink(s1, s4, stp_cost=5)
        self.addLink(s2, s3)
        self.addLink(s3, s4)

        for s in self.switches():
            self.addLink(s, self.addHost('h%s' % s))

        super(SimpleSpanningTree, self).build(*args, **kwargs)


expected_states = {
    SimpleSpanningTree.__name__: {
        "s1": {"s1-eth1": "forwarding", "s1-eth2": "forwarding",
               "s1-eth3": "forwarding"},
        "s2": {"s2-eth1": "blocking", "s2-eth2": "forwarding"},
        "s3": {"s3-eth1": "forwarding", "s3-eth2": "forwarding",
               "s3-eth3": "forwarding"},
        "s4": {"s4-eth1": "blocking", "s4-eth2": "forwarding"}
    },
    SpanningTreeNet.__name__: {
        "s1": {"s1-eth1": "blocking", "s1-eth2": "forwarding"},
        "s2": {"s2-eth1": "forwarding", "s2-eth2": "forwarding"},
        "s3": {"s3-eth1": "forwarding", "s3-eth2": "forwarding"}
    },
    SpanningTreeAdjust.__name__: {
        "s1": {"s1-eth1": "forwarding", "s1-eth2": "forwarding",
               "s1-eth3": "forwarding", "s1-eth4": "forwarding"},
        "s2": {"s2-eth1": "forwarding", "s2-eth2": "blocking"},
        "s3": {"s3-eth1": "forwarding", "s3-eth2": "forwarding",
               "s3-eth3": "forwarding", "s3-eth4": "forwarding"},
        "s4": {"s4-eth1": "forwarding", "s4-eth2": "blocking"},
        "s5": {"s5-eth1": "forwarding", "s5-eth2": "blocking",
               "s5-eth3": "forwarding", "s5-eth4": "forwarding"},
        "s6": {"s6-eth1": "forwarding", "s6-eth2": "blocking"}
    },
    "SpanningTreeAdjust-mod": {
        "s1": {"s1-eth1": "forwarding", "s1-eth2": "forwarding",
               "s1-eth3": "forwarding", "s1-eth4": "forwarding"},
        "s2": {"s2-eth1": "blocking", "s2-eth2": "forwarding"},
        "s3": {"s3-eth1": "blocking", "s3-eth2": "forwarding",
               "s3-eth3": "forwarding", "s3-eth4": "forwarding"},
        "s4": {"s4-eth1": "blocking", "s4-eth2": "forwarding"},
        "s5": {"s5-eth1": "forwarding", "s5-eth2": "forwarding",
               "s5-eth3": "forwarding", "s5-eth4": "forwarding"},
        "s6": {"s6-eth1": "blocking", "s6-eth2": "forwarding"}
    },
    SpanningTreeBus.__name__: {
        "s1": {"s1-eth1": "forwarding"},
        "s2": {"s2-eth1": "forwarding"},
        "s3": {"s3-eth1": "forwarding"}
    },
    SpanningTreeFullMesh.__name__: {
        "s1": {"s1-eth1": "forwarding", "s1-eth2": "forwarding",
               "s1-eth3": "forwarding",
               "s1-eth4": "forwarding", "s1-eth5": "forwarding"},
        "s2": {"s2-eth1": "forwarding", "s2-eth2": "forwarding",
               "s2-eth3": "forwarding",
               "s2-eth4": "forwarding", "s2-eth5": "forwarding"},
        "s3": {"s3-eth1": "forwarding", "s3-eth2": "blocking",
               "s3-eth3": "forwarding",
               "s3-eth4": "forwarding", "s3-eth5": "forwarding"},
        "s4": {"s4-eth1": "forwarding", "s4-eth2": "blocking",
               "s4-eth3": "blocking",
               "s4-eth4": "forwarding", "s4-eth5": "forwarding"},
        "s10": {"s10-eth1": "forwarding", "s10-eth2": "blocking"},
        "s11": {"s11-eth1": "forwarding", "s11-eth2": "blocking"},
        "s12": {"s12-eth1": "forwarding", "s12-eth2": "blocking"},
        "s17": {"s17-eth1": "forwarding", "s17-eth2": "blocking"}
    },
    SpanningTreeHub.__name__: {
        "s3": {"s3-eth1": "forwarding", "s3-eth2": "forwarding",
               "s3-eth3": "forwarding"},
        "s6": {"s6-eth1": "forwarding", "s6-eth2": "forwarding",
               "s6-eth3": "forwarding"},
        "s10": {"s10-eth1": "forwarding", "s10-eth2": "forwarding"},
        "s11": {"s11-eth1": "blocking", "s11-eth2": "forwarding",
                "s11-eth3": "blocking"},
        "s12": {"s12-eth1": "forwarding", "s12-eth2": "blocking"},
        "s17": {"s17-eth1": "forwarding", "s17-eth2": "forwarding"}
    },
    SpanningTreeIntermediate.__name__: {
        "s2": {"s2-eth1": "forwarding", "s2-eth2": "forwarding"},
        "s4": {"s4-eth1": "forwarding", "s4-eth2": "forwarding"},
        "s5": {"s5-eth1": "forwarding", "s5-eth2": "blocking",
               "s5-eth3": "blocking"},
        "s10": {"s10-eth1": "forwarding", "s10-eth2": "forwarding",
                "s10-eth3": "forwarding"}
    },
    SpanningTreeCost.__name__: {
        "s1": {"s1-eth1": "forwarding", "s1-eth2": "forwarding"},
        "s2": {"s2-eth1": "forwarding", "s2-eth2": "forwarding"},
        "s3": {"s3-eth1": "forwarding", "s3-eth2": "blocking"}
    }
}


@require_root
@pytest.mark.parametrize("topo", [
    SimpleSpanningTree,
    SpanningTreeNet,
    SpanningTreeAdjust,
    SpanningTreeBus,
    SpanningTreeFullMesh,
    SpanningTreeHub,
    SpanningTreeIntermediate,
    SpanningTreeCost
])
def test_stp(topo):
    try:
        net = IPNet(topo=topo())
        net.start()

        assert_connectivity(net, v6=False)
        assert_connectivity(net, v6=True)

        for switch, states in expected_states[topo.__name__].items():
            assert_stp_state(net[switch], states)
        net.stop()
    finally:
        cleanup()


def test_stp_adjust():
    try:
        net = IPNet(topo=SpanningTreeAdjust(l1_start="s2-eth1",
                                            l1_end="s1-eth1", l1_cost=2,
                                            l2_start="s1-eth3",
                                            l2_end="s3-eth1", l2_cost=3))
        net.start()

        assert_connectivity(net, v6=False)
        assert_connectivity(net, v6=True)

        for switch, states in expected_states["SpanningTreeAdjust-mod"].items():
            assert_stp_state(net[switch], states)
        net.stop()
    finally:
        cleanup()
