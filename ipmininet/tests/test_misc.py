import os
import subprocess

import ipaddress
import pytest

import ipmininet.utils as utils
from ipmininet.clean import cleanup
from ipmininet.examples.static_address_network import StaticAddressNet
from ipmininet.ipnet import IPNet
from ipmininet.link import _parse_addresses
from ipmininet.router.config.utils import ip_statement
from . import require_root


@pytest.mark.parametrize('address', [
    u'::/0', u'0.0.0.0/0', u'1.2.3.0/24', u'2001:db8:1234::/48'
])
def test_nested_ip_networks(address):
    """This test ensures that we can build an IPvXNetwork from another one.
    If this breaks, need to grep through for ip_network calls as I removed the
    checks when instantiating these ...
    Test passing with py2-ipaddress (3.4.1)"""
    _N = ipaddress.ip_network
    n1 = _N(address)  # Build an IPvXNetwork
    n2 = _N(n1)  # Build a new one from the previous one
    assert (n1 == n2 and
            n1.with_prefixlen == address and
            n2.with_prefixlen == address and
            n1.max_prefixlen == n2.max_prefixlen)


@pytest.mark.parametrize("test_input,expected", [
    (u"255.255.0.0", 16),
    (u"f000::", 4),
    (u"ffff::", 16),
    (u"128.0.0.0", 1),
    (u"fe00::", 7)
])
def test_prefix_for_netmask(test_input, expected):
    assert utils.prefix_for_netmask(test_input) == expected


@pytest.mark.parametrize("test_input,expected", [
    (u'0.0.0.1', 1),
    (u'0.0.128.0', 128 << 8),
    (u'0.0.123.3', (123 << 8) + 3),
    (u'::f:1', (0xf << 16) + 1)
])
def test_ipaddress_endianness(test_input, expected):
    """Checks int(ipaddress) endianness"""
    assert int(ipaddress.ip_address(test_input)) == expected


def test_ip_address_format():
    """
    Check that the output of ip address conforms to what we expect in order
    to parse it properly.
    """
    # We force up status so we parse at least one IP of each family
    subprocess.call(['ip', 'link', 'set', 'dev', 'lo', 'up'])
    out = subprocess.check_output(['ip', 'address', 'show', 'dev', 'lo'])\
        .decode("utf-8")
    mac, v4, v6 = _parse_addresses(out)
    assert mac is not None
    assert len(mac.split(':')) == 6
    assert mac in out
    assert len(v4) > 0
    for a in v4:
        assert a.version == 4
        assert a.with_prefixlen in out
    assert len(v6) > 0
    for a in v6:
        assert a.version == 6
        assert a.with_prefixlen in out
    # IF status, MAC, inet, valid, inet, valid, ..., inet6, valid, ...
    assert len(out.strip('\n').split('\n')) == (2 + 2 * len(v4) + 2 * len(v6))


@pytest.mark.parametrize("cmd,present", [
    ("ls", True),
    ("/bin/sh", True),
    ("for", False),  # Never a command because in bash syntax
    (os.path.abspath(__file__), False),
])
def test_require_cmd(cmd, present):
    try:
        utils.require_cmd(cmd)
        assert present, "The command [%s] was found" \
                        " while it is not present" % cmd
    except RuntimeError:
        assert not present, "The command [%s] could not be found" \
                            " while it is present" % cmd


@pytest.mark.parametrize("node,use_v4,use_v6,expected", [
    ("h1", True, True, (u"10.0.0.2", u"2001:1a::2")),
    ("h1", False, True, (None, u"2001:1a::2")),
    ("h1", True, False, (u"10.0.0.2", None)),
    ("h1", False, False, (None, None)),
])
@require_root
def test_address_pair(node, use_v4, use_v6, expected):
    try:
        net = IPNet(topo=StaticAddressNet())
        net.start()
        assert utils.address_pair(net[node], use_v4, use_v6) == expected
        net.stop()
    finally:
        cleanup()


@pytest.mark.parametrize("start,node,present", [
    ("h1", "h1", True),
    ("h1", "r1", True),
    ("h1", "h2", True),
    ("h1", "h3", True),
    ("h1", "s2", False),  # Switches are not searched
    ("h1", "None", False),
])
@require_root
def test_find_node(start, node, present):
    try:
        net = IPNet(topo=StaticAddressNet())
        net.start()
        i = utils.find_node(net[start], node)
        if present:
            assert i is not None,\
                "Node %s not found from node %s" % (node, start)
            assert i.node.name == node,\
                "Node %s was found while we expected %s" % (i.node.name, node)
        else:
            assert i is None,\
                "Node %s should not be found from node %s" % (node, start)
        net.stop()
    finally:
        cleanup()


@pytest.mark.parametrize("test_input,expected", [
    (4, "ip"),
    (6, "ipv6"),
    (u"10.0.0.1", "ip"),
    (u"10.0.0.0/8", "ip"),
    (u"10.0.0.1/8", "ip"),
    (u"2042::1", "ipv6"),
    (u"2042::/16", "ipv6"),
    (u"2042::1/16", "ipv6"),
    (ipaddress.ip_address(u"10.0.0.1"), "ip"),
    (ipaddress.ip_network(u"10.0.0.0/8"), "ip"),
    (ipaddress.ip_interface(u"10.0.0.1/8"), "ip"),
    (ipaddress.ip_address(u"2042::1"), "ipv6"),
    (ipaddress.ip_network(u"2042::/16"), "ipv6"),
    (ipaddress.ip_interface(u"2042::1/16"), "ipv6"),
])
def test_ip_statement(test_input, expected):
    assert ip_statement(test_input) == expected
