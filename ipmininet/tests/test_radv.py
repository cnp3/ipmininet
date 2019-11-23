"""This module tests the RADVD daemon"""
import pytest

from ipmininet.clean import cleanup
from ipmininet.examples.router_adv_network import RouterAdvNet
from ipmininet.ipnet import IPNet
from ipmininet.iptopo import IPTopo
from ipmininet.router.config import RADVD, AdvPrefix, AdvRDNSS
from ipmininet.tests.utils import assert_connectivity
from . import require_root


class CustomRouterAdvNet(IPTopo):
    def __init__(self, link_params, *args, **kwargs):
        """:param link_params: Parameters to set on the link between h and r"""
        self.link_params = link_params
        self.link_params.setdefault("params1", {})\
            .setdefault("ip", "2001:1341::1/64")
        super(CustomRouterAdvNet, self).__init__(*args, **kwargs)

    def build(self, *args, **kwargs):
        """
                            +---+       +---+       +------------+
                            | H +-------+ R +-------+ DNS server |
                            +---+       +---+       +------------+
        """
        r = self.addRouter('r', use_v4=False, use_v6=True)
        r.addDaemon(RADVD)
        h = self.addHost('h')
        dns = self.addHost('dns')
        self.addLink(r, h, **self.link_params)
        self.addLink(r, dns, params1={"ip": "2001:89ab::1/64"},
                     params2={"ip": "2001:89ab::d/64"})
        super(CustomRouterAdvNet, self).build(*args, **kwargs)


@require_root
def test_radvd_example():
    try:
        net = IPNet(topo=RouterAdvNet(), use_v4=False, use_v6=True,
                    allocate_IPs=False)
        net.start()
        assert_connectivity(net, v6=True)
        net.stop()
    finally:
        cleanup()


@require_root
@pytest.mark.parametrize("link_params,expected_cfg", [
    ({"params1": {"ra": [AdvPrefix("2001:1341::/64", valid_lifetime=2000,
                                   preferred_lifetime=1000)]}},
     ["        prefix 2001:1341::/64",
      "            AdvValidLifetime 2000;",
      "            AdvPreferredLifetime 1000;"]),
    ({"params1": {"ra": [AdvPrefix("2001:1341::/64")],
                  "rdnss": [AdvRDNSS("2001:89ab::d", max_lifetime=1000)]}},
     ["        RDNSS 2001:89ab::d {",
      "            AdvRDNSSLifetime 1000; # in seconds (0 means invalid)"])
])
def test_radvd_daemon_params(link_params, expected_cfg):
    try:
        net = IPNet(topo=CustomRouterAdvNet(link_params), use_v4=False,
                    use_v6=True, allocate_IPs=False)
        net.start()

        # Check generated configuration
        with open("/tmp/radvd_r.cfg") as fileobj:
            cfg = fileobj.readlines()
            for line in expected_cfg:
                assert line + "\n" in cfg,\
                    "Cannot find the line '%s' in the generated" \
                    " configuration:\n%s" % (line, "".join(cfg))

        # Check reachability
        assert_connectivity(net, v6=True)

        net.stop()
    finally:
        cleanup()


@require_root
def test_radvd_cleanup():
    try:
        net = IPNet(topo=RouterAdvNet(), use_v4=False, use_v6=True,
                    allocate_IPs=False)
        net.start()
        net["r"].nconfig.daemon(RADVD).cleanup()
        try:
            net["r"].nconfig.daemon(RADVD).cleanup()
        except Exception as e:
            assert False, "An exception '%s' was raised" \
                          " while cleaning twice RADVD daemon" % e
        net.stop()
    finally:
        cleanup()
