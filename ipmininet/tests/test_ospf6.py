"""This module tests the OSPF6 daemon"""
import pytest

from ipmininet.clean import cleanup
from ipmininet.examples.simple_ospfv3_network import SimpleOSPFv3Net
from ipmininet.ipnet import IPNet
from ipmininet.iptopo import IPTopo
from ipmininet.router.config import OSPF6
from ipmininet.router.config.base import RouterConfig
from ipmininet.router.config.ospf6 import OSPF6RedistributedRoute
from ipmininet.tests.utils import assert_connectivity, assert_path
from . import require_root


class MinimalOSPFv3Net(IPTopo):
    """

    h1 ---- r1 ---- r2 ---- h2
            |        |
            +-- r3 --+
                 |
                h3
    """
    def __init__(self, node_params_r1, ospf6_params_r1, link_params, *args, **kwargs):
        """:param node_params_r1: Parameters to set on the r1 router
        :param ospf6_params_r1: Parameters to set on the OSPF6 daemon of r1
        :param link_params: Parameters to set on the link between r1 and r2"""
        self.node_params_r1 = node_params_r1
        self.ospf6_params_r1 = ospf6_params_r1
        self.link_params = link_params
        super().__init__(*args, **kwargs)

    def build(self, *args, **kwargs):
        r1 = self.addRouter("r1", config=RouterConfig, **self.node_params_r1)
        r1.addDaemon(OSPF6, **self.ospf6_params_r1)
        r2 = self.addRouter("r2", config=RouterConfig)
        r2.addDaemon(OSPF6)
        r3 = self.addRouter("r3", config=RouterConfig)
        r3.addDaemon(OSPF6)
        self.addLink(r1, r2, **self.link_params)
        self.addLink(r1, r3)
        self.addLink(r2, r3)

        h1 = self.addHost("h1")
        self.addLink(r1, h1)
        h2 = self.addHost("h2")
        self.addLink(r2, h2)
        h3 = self.addHost("h3")
        self.addLink(r3, h3)
        super().build(*args, **kwargs)


@require_root
def test_ospf6_example():
    try:
        net = IPNet(topo=SimpleOSPFv3Net())
        net.start()
        assert_connectivity(net, v6=True)
        net.stop()
    finally:
        cleanup()


unit_igp_cost_paths = [
    ["h1", "r1", "r2", "h2"],
    ["h2", "r2", "r1", "h1"],
    ["h1", "r1", "r3", "h3"],
    ["h3", "r3", "r1", "h1"],
    ["h2", "r2", "r3", "h3"],
    ["h3", "r3", "r2", "h2"],
]

high_igp_cost_paths = [
    ["h1", "r1", "r3", "r2", "h2"],
    ["h2", "r2", "r3", "r1", "h1"],
    ["h1", "r1", "r3", "h3"],
    ["h3", "r3", "r1", "h1"],
    ["h2", "r2", "r3", "h3"],
    ["h3", "r3", "r2", "h2"],
]


@require_root
@pytest.mark.parametrize("node_params,ospf6_params,link_params,exp_cfg,exp_paths", [
    ({},
     {},
     {},
     ["  interface r1-eth0 area 0.0.0.0"],
     unit_igp_cost_paths),
    ({},
     {"debug": ["flooding"]},
     {},
     ["debug ospf6 flooding"],
     unit_igp_cost_paths),
    ({},
     {},
     {"igp_metric": 5},
     ["  ipv6 ospf6 cost 5"],
     high_igp_cost_paths),
    ({},
     {},
     {"igp_area": "1.1.1.1"},
     ["  interface r1-eth0 area 1.1.1.1", "  interface lo area 0.0.0.0"],
     high_igp_cost_paths),
    ({"igp_area": "1.1.1.1"},
     {},
     {},
     ["  interface lo area 1.1.1.1", "  interface r1-eth0 area 0.0.0.0"],
     unit_igp_cost_paths),
    ({},
     {},
     {"params1": {"ospf6_priority": 1}},
     ["  ipv6 ospf6 priority 1"],
     unit_igp_cost_paths),
    ({},
     {},
     {"params1": {"ospf_dead_int": "minimal hello-multiplier 2"}},
     ["  ipv6 ospf6 dead-interval %d" % OSPF6.DEAD_INT],
     unit_igp_cost_paths),
    ({},
     {"redistribute": [OSPF6RedistributedRoute("connected"),
                       OSPF6RedistributedRoute("static")]},
     {},
     ["  redistribute connected",
      "  redistribute static"],
     unit_igp_cost_paths),
])
def test_ospf6_daemon_params(node_params, ospf6_params, link_params, exp_cfg, exp_paths):
    try:
        net = IPNet(topo=MinimalOSPFv3Net(node_params, ospf6_params, link_params))
        net.start()

        # Check generated configuration
        with open("/tmp/ospf6d_r1.cfg") as fileobj:
            cfg = fileobj.readlines()
            for line in exp_cfg:
                assert line + "\n" in cfg,\
                    "Cannot find the line '%s' in the generated" \
                    " configuration:\n%s" % (line, "".join(cfg))

        # Check reachability
        assert_connectivity(net, v6=True)
        for path in exp_paths:
            assert_path(net, path, v6=True)

        net.stop()
    finally:
        cleanup()
