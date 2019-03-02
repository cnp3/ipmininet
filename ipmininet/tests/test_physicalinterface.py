"""This module tests that we can move physical interface correctly across
network namespaces, and that their IP addresses are preserved."""
from ipmininet.iptopo import IPTopo
from ipmininet.link import _addresses_of
from ipmininet.ipnet import IPNet

import pytest
from subprocess import check_output, CalledProcessError
from ipaddress import ip_interface

from . import require_root

import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

itf = 'dummy0'


class LinkTopo(IPTopo):
    def build(self, *args, **kw):
        r1 = self.addRouter('r1')
        r2 = self.addRouter('r2')
        # Default config is OSPF, add another router so we have at least
        # one (auto-allocated) IPv4 address---don't break config generation
        self.addLink(r1, r2)
        self.capture_physical_interface(itf, r1)
        super(LinkTopo, self).build(*args, **kw)


@pytest.fixture(scope='module',
                params=[[ip_interface(u'192.168.1.2/24')],
                        [ip_interface(u'2001:db8:ff::d/48')],
                        [ip_interface(u'192.168.1.2/24'),
                         ip_interface(u'2001:db8:ff::d/48')],
                        ])
def dummy_interface(request):
    if itf in ip('link'):
        ip('link', 'delete', 'dev', itf)
    ip('link', 'add', 'dev', itf, 'type', 'dummy')
    ip('link', 'set', 'dev', itf, 'up')
    for addr in request.param:
        ip('address', 'add', 'dev', itf, addr.compressed)

    # Turns out deleting a net ns also deletes dummy interfaces so no need
    # for a finalizer/teardown
    # def fin():
    #     ip('link', 'delete', 'dev', itf)
    # request.addfinalizer(fin)

    return list(request.param)


@require_root
def test_capture_dummy_interface(dummy_interface):
    check_addresses(dummy_interface, node=None)
    net = IPNet(topo=LinkTopo())
    net.start()
    check_addresses(dummy_interface, node=net['r1'])
    net.stop()


def check_addresses(addr_list, node):
    _, v4, v6 = _addresses_of(itf, node=node)
    v4.extend(ip for ip in v6 if not ip.is_link_local)
    assert set(v4) == set(addr_list)


def ip(*args):
    cmd = ['ip']
    cmd.extend(args)
    try:
        log.info('Calling: %s', cmd)
        return check_output(cmd).decode("utf-8")
    except (OSError, CalledProcessError):
        log.error('Command failed!')
