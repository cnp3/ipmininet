import pytest
import ipaddress
import ipmininet.utils as utils
import subprocess
from ipmininet.link import _parse_addresses


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
    out = subprocess.check_output(['ip', 'address', 'show', 'dev', 'lo']).decode("utf-8")
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
