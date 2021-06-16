"""This module tests the OSPF daemon"""

import pytest

from ipmininet.clean import cleanup
from ipmininet.examples.simple_ospf_network import SimpleOSPFNet
from ipmininet.ipnet import IPNet
from ipmininet.iptopo import IPTopo
from ipmininet.router.config import OSPF
from ipmininet.router.config.base import RouterConfig
from ipmininet.router.config.ospf import OSPFRedistributedRoute
from ipmininet.tests.utils import assert_connectivity, assert_path
from . import require_root


class MinimalOSPFNet(IPTopo):
    """

    h1 ---- r1 ---- r2 ---- h2
            |        |
            +-- r3 --+
                 |
                h3
    """
    def __init__(self, node_params_r1, ospf_params_r1, link_params, *args, **kwargs):
        """:param node_params_r1: Parameters to set on the r1 router
        :param ospf_params_r1: Parameters to set on the OSPF daemon of r1
        :param link_params: Parameters to set on the link between r1 and r2"""
        self.node_params_r1 = node_params_r1
        self.ospf_params_r1 = ospf_params_r1
        self.link_params = link_params
        self.link_params.setdefault("params1", {})\
            .setdefault("ip", "10.0.0.1/24")
        self.link_params.setdefault("params2", {})\
            .setdefault("ip", "10.0.0.2/24")
        super().__init__(*args, **kwargs)

    def build(self, *args, **kwargs):
        r1 = self.addRouter("r1", config=RouterConfig, **self.node_params_r1)
        r2, r3 = self.addRouters("r2", "r3", config=RouterConfig)
        r1.addDaemon(OSPF, **self.ospf_params_r1)
        r2.addDaemon(OSPF)
        r3.addDaemon(OSPF)

        h1 = self.addHost("h1")
        h2 = self.addHost("h2")
        h3 = self.addHost("h3")

        self.addLinks((r1, r2, self.link_params),
                      (r1, r3, {"params1": {"ip": "10.0.4.1/24"},
                                "params2": {"ip": "10.0.4.2/24"}}),
                      (r2, r3, {"params1": {"ip": "10.0.5.1/24"},
                                "params2": {"ip": "10.0.5.2/24"}}),
                      (r1, h1, {"params1": {"ip": "10.0.1.1/24"},
                                "params2": {"ip": "10.0.1.2/24"}}),
                      (r2, h2, {"params1": {"ip": "10.0.2.1/24"},
                                "params2": {"ip": "10.0.2.2/24"}}),
                      (r3, h3, {"params1": {"ip": "10.0.3.1/24"},
                                "params2": {"ip": "10.0.3.2/24"}}))
        super().build(*args, **kwargs)


@require_root
def test_ospf_example():
    try:
        net = IPNet(topo=SimpleOSPFNet())
        net.start()
        assert_connectivity(net)
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

detour_paths = [
    ["h1", "r1", "r3", "r2", "h2"],
    ["h2", "r2", "r3", "r1", "h1"],
    ["h1", "r1", "r3", "h3"],
    ["h3", "r3", "r1", "h1"],
    ["h2", "r2", "r3", "h3"],
    ["h3", "r3", "r2", "h2"],
]


@require_root
@pytest.mark.parametrize("node_params,ospf_params,link_params,exp_cfg,exp_paths", [
    ({},
     {},
     {},
     ["  network 10.0.0.1/24 area 0.0.0.0",
      "interface r1-eth0"],
     unit_igp_cost_paths),
    ({},
     {"debug": ["lsa"]},
     {},
     ["debug ospf lsa"],
     unit_igp_cost_paths),
    ({},
     {},
     {"igp_metric": 5},
     ["  ip ospf cost 5"],
     detour_paths),
    ({},
     {},
     {"igp_area": "1.1.1.1"},
     ["  network 10.0.0.1/24 area 1.1.1.1", "  network 127.0.0.1/8 area 0.0.0.0"],
     detour_paths),
    ({"igp_area": "1.1.1.1"},
     {},
     {},
     ["  network 127.0.0.1/8 area 1.1.1.1", "  network 10.0.0.1/24 area 0.0.0.0"],
     unit_igp_cost_paths),
    ({},
     {},
     {"params1": {"ospf_priority": 1}},
     ["  ip ospf priority 1"],
     unit_igp_cost_paths),
    ({},
     {},
     {"params1": {"ospf_dead_int": "minimal hello-multiplier 2"}},
     ["  ip ospf dead-interval minimal hello-multiplier 2"],
     unit_igp_cost_paths),
    ({},
     {"redistribute": [OSPFRedistributedRoute("connected", 1, 15),
                       OSPFRedistributedRoute("static", 2, 50)]},
     {},
     ["  redistribute connected metric-type 1 metric 15",
      "  redistribute static metric-type 2 metric 50"],
     unit_igp_cost_paths),
])
def test_ospf_daemon_params(node_params, ospf_params, link_params, exp_cfg, exp_paths):
    try:
        net = IPNet(topo=MinimalOSPFNet(node_params, ospf_params, link_params),
                    allocate_IPs=False)
        net.start()

        # Check generated configuration
        with open("/tmp/ospfd_r1.cfg") as fileobj:
            cfg = fileobj.readlines()
            for line in exp_cfg:
                assert line + "\n" in cfg,\
                    "Cannot find the line '%s' in the generated " \
                    "configuration:\n%s" % (line, "".join(cfg))

        # Check reachability and paths
        assert_connectivity(net)
        for path in exp_paths:
            assert_path(net, path)

        net.stop()
    finally:
        cleanup()
