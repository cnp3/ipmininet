import pytest
from ipaddress import ip_interface

from ipmininet.clean import cleanup
from ipmininet.examples.static_address_network import StaticAddressNet
from ipmininet.ipnet import IPNet
from ipmininet.link import OrderedAddress
from ipmininet.tests import require_root


@pytest.mark.parametrize("unsorted_list,sorted_list", [
    ([u"10.0.0.1/8", u"2001::1/16"],
     [u"2001::1/16", u"10.0.0.1/8"]),  # V4 before V6
    ([u"2001::1/16", u"10.0.0.1/8"],
     [u"2001::1/16", u"10.0.0.1/8"]),  # V4 before V6
    ([u"fe80::/16", u"::1/128"],
     [u"fe80::/16", u"::1/128"]),  # Link-local before loopback
    ([u"::1/128", u"fe80::/16"],
     [u"fe80::/16", u"::1/128"]),  # Link-local before loopback
    ([u"fe80::/16", u"2001::1/16"],
     [u"2001::1/16", u"fe80::/16"]),  # Global before link-local
    ([u"2001::1/16", u"fe80::/16"],
     [u"2001::1/16", u"fe80::/16"]),  # Global before link-local
    ([u"10.0.0.1/8", u"100.64.0.1/32"],
     [u"100.64.0.1/32", u"10.0.0.1/8"]),  # Public before private
    ([u"100.64.0.1/32", u"10.0.0.1/8"],
     [u"100.64.0.1/32", u"10.0.0.1/8"]),  # Public before private
    ([u"2001::1/16", u"2002::1/16"],
     [u"2002::1/16", u"2001::1/16"]),  # Bigger network value first
    ([u"2002::1/16", u"2001::1/16"],
     [u"2002::1/16", u"2001::1/16"]),  # Bigger network value first
    ([u"2001::1/16", u"2001::2/16"],
     [u"2001::2/16", u"2001::1/16"]),  # Bigger IP value first
    ([u"2001::2/16", u"2001::1/16"],
     [u"2001::2/16", u"2001::1/16"]),  # Bigger IP value first
])
def test_ordered_address(unsorted_list, sorted_list):
    unsorted_list = [ip_interface(ip) for ip in unsorted_list]
    new_list = sorted(unsorted_list, key=OrderedAddress, reverse=True)
    new_list = [ip.with_prefixlen for ip in new_list]
    assert sorted_list == new_list, "The IP list was not sorted correctly"


@require_root
def test_addr_intf():
    try:
        net = IPNet(topo=StaticAddressNet())
        net.start()
        itf = net["r1"].intf("r1-eth1")

        # Check IP6 update
        itf.ip6 = "2001:21::1"
        ip6s = list(itf.ip6s(exclude_lls=True))
        assert len(ip6s) == 1 and ip6s[0].with_prefixlen == "2001:21::1/64",\
            "Cannot update an IPv6 address"
        assert itf.prefixLen6 == 64
        itf.prefixLen6 = 48
        assert itf.prefixLen6 == 48,\
            "Cannot update prefix len of an IPv6 address"

        # Check IP update
        itf.ip = "10.1.2.1"
        ips = list(itf.ips())
        assert len(ips) == 1 and ips[0].with_prefixlen == "10.1.2.1/24",\
            "Cannot update an IPv4 address"
        assert itf.prefixLen == 24
        itf.prefixLen = 28
        assert itf.prefixLen == 28,\
            "Cannot update prefix len of an IPv4 address"

        # Check MAC getters
        assert itf.updateMAC() == itf.updateAddr()[1],\
            "MAC address obtained through two methods is not identical"

        net.stop()
    finally:
        cleanup()
