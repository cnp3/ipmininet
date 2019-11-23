"""This module tests the Named daemon"""
import pytest
import time

from ipmininet.clean import cleanup
from ipmininet.examples.dns_network import DNSNetwork
from ipmininet.ipnet import IPNet
from ipmininet.host.config import Named, ARecord, AAAARecord, NSRecord,\
    PTRRecord
from ipmininet.tests.utils import assert_connectivity, assert_dns_record
from . import require_root


class CustomDNSNetwork(DNSNetwork):
    def __init__(self, named_cfg, zone_args, *args, **kwargs):
        """:param named_cfg: Parameters to set on the master dns daemon
           :param zone_args: Parameters to set on the DNS Zone"""
        self.named_cfg = named_cfg
        self.zone_args = zone_args
        super(CustomDNSNetwork, self).__init__(*args, **kwargs)

    def build(self, *args, **kwargs):

        # Update master DNS parameters
        master2 = self.addHost('master2')
        master2.addDaemon(Named, **self.named_cfg)

        # Add new parametrized DNS zone
        self.addDNSZone(name="test.org", dns_master="master2", **self.zone_args)

        super(CustomDNSNetwork, self).build(*args, **kwargs)
        self.addLink("r2", master2)


@require_root
@pytest.mark.parametrize("named_cfg,zone_args,exp_named_cfg,exp_zone_cfg", [
    ({}, {}, [], []),
    ({"log_severity": "info"},
     {},
     ["        severity info;"],
     []),
    ({"dns_server_port": 2000},
     {},
     [],
     []),
    ({},
     {"refresh_time": 20, "retry_time": 30, "expire_time": 40, "min_ttl": 50},
     [],
     ["20 ; refresh timer", "30 ; retry timer", "40 ; retry timer",
      "50 ; minimum ttl"]),
    ({},
     {"records": [AAAARecord("new", "fc00::2", ttl=100),
                  ARecord("new", "192.0.0.1", ttl=300),
                  NSRecord("test.org", "new", ttl=10)]},
     [],
     ["new   100\tIN\tAAAA\tfc00::2",
      "new   300\tIN\tA\t192.0.0.1",
      "test.org.   10\tIN\tNS\tnew.test.org."]),
])
def test_dns_network(named_cfg, zone_args, exp_named_cfg, exp_zone_cfg):
    try:
        net = IPNet(topo=CustomDNSNetwork(named_cfg, zone_args))
        net.start()

        # Check generated configurations
        with open("/tmp/named_master2.cfg") as fileobj:
            cfg = fileobj.readlines()
            for line in exp_named_cfg:
                assert line + "\n" in cfg,\
                    "Cannot find the line '%s' in the generated " \
                    "main configuration:\n%s" % (line, "".join(cfg))
        with open("/tmp/named_master2.test.org.cfg") as fileobj:
            cfg = fileobj.readlines()
            for line in exp_zone_cfg:
                assert line + "\n" in cfg,\
                    "Cannot find the line '%s' in the generated zone " \
                    "configuration:\n%s" % (line, "".join(cfg))

        # Check port number configuration
        dns_server_port = named_cfg.get("dns_server_port", 53)
        assert_dns_record(net["master2"], "localhost",
                          ARecord("master2.test.org",
                                  net["master2"].defaultIntf().ip6),
                          port=dns_server_port)

        # Check connectivity
        assert_connectivity(net, v6=False)
        assert_connectivity(net, v6=True)

        # Check generated DNS record
        records = [
            NSRecord("mydomain.org", "master"),
            NSRecord("mydomain.org", "slave"),
            ARecord("master.mydomain.org", net["master"].defaultIntf().ip),
            AAAARecord("master.mydomain.org", net["master"].defaultIntf().ip6),
            ARecord("slave.mydomain.org", net["slave"].defaultIntf().ip),
            AAAARecord("slave.mydomain.org", net["slave"].defaultIntf().ip6),
            ARecord("server.mydomain.org", net["server"].defaultIntf().ip),
            AAAARecord("server.mydomain.org", net["server"].defaultIntf().ip6,
                       ttl=120),
            PTRRecord(net["master"].defaultIntf().ip, "master.mydomain.org"),
            PTRRecord(net["master"].defaultIntf().ip6, "master.mydomain.org"),
            PTRRecord(net["slave"].defaultIntf().ip, "slave.mydomain.org"),
            PTRRecord(net["slave"].defaultIntf().ip6, "slave.mydomain.org"),
            PTRRecord(net["server"].defaultIntf().ip, "server.mydomain.org"),
            PTRRecord(net["server"].defaultIntf().ip6, "server.mydomain.org",
                      ttl=120)
        ]
        for node in [net["master"], net["slave"]]:
            for record in records:
                assert_dns_record(node, "localhost", record)
            time.sleep(10)

        net.stop()
    finally:
        cleanup()
