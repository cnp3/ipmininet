"""Classes for interfaces and links that are IP-agnostic. This basically
enhance the TCIntf class from Mininet, and then define sane defaults for the link
classes."""
from copy import deepcopy
from itertools import chain
import subprocess
from ipaddress import ip_interface, IPv4Interface, IPv6Interface
import functools
from typing import Union, Tuple, Optional, Generator, Sequence, List, Type

from . import OSPF_DEFAULT_AREA, MIN_IGP_METRIC
from .utils import otherIntf, is_container

import mininet.link as _m
from mininet.log import lg as log
from mininet.node import Node


class IPIntf(_m.TCIntf):
    """This class represents a node interface. It is IP-agnostic, as in
    its `addresses` attribute is a dictionary keyed by IP version,
    containing the list of all addresses for a given version"""
    def __init__(self, *args, **kwargs):
        # Only one IP broadcast domain per interface, VLANs are supported
        # by aliasing interfaces.
        self.broadcast_domain = None
        self.addresses = {4: [], 6: []}
        self.ra_prefixes = kwargs.pop('ra', [])
        self.rdnss_list = kwargs.pop('rdnss', [])
        super().__init__(*args, **kwargs)
        self.isUp(setUp=True)
        self._refresh_addresses()
        self.backup_addresses = {4: [], 6: []}
        self.restore_cmds = []

        # Start the captures on this interface
        for capture in self.get("captures", []):
            capture.start(intf=self)

    @property
    def igp_area(self) -> str:
        """Return the igp area associated to this interface"""
        return self.get('igp_area', OSPF_DEFAULT_AREA)

    @property
    def igp_metric(self) -> int:
        """Return the igp metric associated to this interface"""
        return self.get('igp_metric', MIN_IGP_METRIC)

    @property
    def describe(self) -> str:
        """Return a string describing the interface facing this one"""
        other = otherIntf(self)
        return '-> %s' % (other.name if other else 'n/a')

    @property
    def interface_width(self) -> Tuple[int, int]:
        """Return the number of addresses that should be allocated to this
        interface, per address family"""
        return self.get('v4_width', 1), self.get('v6_width', 1)

    def get(self, key, val):
        """Check for a given key in the interface parameters"""
        return self.params.get(key, val)

    def __default(self, version: int) -> Union[IPv4Interface, IPv6Interface]:
        """Return the default addresses for a given IP version
        :raise IndexError:"""
        return self.addresses[version][0]

    def _ip(self, version: int) -> Optional[str]:
        """Return the main IP of the given version for this interface"""
        try:
            return self.__default(version).ip.compressed
        except IndexError:
            return None

    def _prefixLen(self, version: int) -> Optional[int]:
        """Return the prefixLen of the main IP for the given version"""
        try:
            return self.__default(version).network.prefixlen
        except IndexError:
            return None

    # We want to stay API-compatible with Intf, so we override ip/prefixLen
    @property
    def ip(self) -> Optional[str]:
        return self._ip(4)

    @ip.setter
    def ip(self,
           ip: Union[str, IPv4Interface, Sequence[Union[str, IPv4Interface]]]):
        self.setIP(ip, prefixLen=self.prefixLen)

    def ips(self, exclude_lbs=True) -> Generator[IPv4Interface, None, None]:
        """Return a generator over all IPv4 assigned to this interface

        :param exclude_lbs: Whether Loopback addresses should be included or not
        """
        for i in self.addresses[4]:
            if not exclude_lbs or not i.is_loopback:
                yield i

    @property
    def prefixLen(self) -> Optional[int]:
        return self._prefixLen(4)

    @prefixLen.setter
    def prefixLen(self, prefixLen: int):
        if self.ip is not None:
            self.setIP(self.ip, prefixLen=prefixLen)

    @property
    def ip6(self) -> Optional[str]:
        """Return the default IPv6 for this interface"""
        return self._ip(6)

    @ip6.setter
    def ip6(self,
            ip: Union[str, IPv6Interface, Sequence[Union[str, IPv6Interface]]]):
        self.setIP6(ip, prefixLen=self.prefixLen6)

    def ip6s(self, exclude_lls=False, exclude_lbs=True) \
            -> Generator[IPv6Interface, None, None]:
        """Return a generator over all IPv6 assigned to this interface

        :param exclude_lls: Whether Link-locals should be included or not
        :param exclude_lbs: Whether Loopback addresses should be included or not
        """
        for i in self.addresses[6]:
            if (not exclude_lls or not i.is_link_local) \
                    and (not exclude_lbs or not i.is_loopback):
                yield i

    @property
    def prefixLen6(self) -> Optional[int]:
        """Return the prefix length for the default IPv6 for this interface"""
        return self._prefixLen(6)

    @prefixLen6.setter
    def prefixLen6(self, prefixLen: int):
        if self.ip6 is not None:
            self.setIP6(self.ip6, prefixLen=prefixLen)

    def _set_ip(self, ip: Union[str, IPv4Interface, IPv6Interface,
                                Sequence[Union[str, IPv4Interface,
                                               IPv6Interface]]],
                prefixLen: Optional[int] = None) -> Union[None, List[str], str]:
        """Set one or more IP addresses, possibly from different families.
        This will remove previously set addresses of the affected families.

        :param ip: either an IP string (mininet-like behavior),
                    or an ip_interface like, or a sequence of both
        :param prefixLen: the prefix length to use for all cases where
                          the addresses is given as a string without a given
                          prefix."""
        if not ip:
            return None
        setv4 = setv6 = False
        lb_v4_update = lb_v6_update = False
        # Make sure we have an up-to-date view of our addresses
        self._refresh_addresses()
        cmds = []
        # We want to iterate over the new ip sets
        if not is_container(ip):
            ip = (ip,)
        for addr in ip:
            # Make sure we have ip_interface-like objects
            if isinstance(addr, str):
                if '/' not in addr and prefixLen is not None:
                    # And use the default prefix if absent
                    addr = ip_interface('%s/%s' % (addr, prefixLen))
                else:
                    # no prefixLen defaults to full /128 or /32
                    addr = ip_interface(str(addr))

            # Prepare assignment commands
            cmds.append('ip address add dev %s %s'
                        % (self.name, addr.with_prefixlen))
            # Record assignment family
            if addr.version == 4:
                setv4 = True
                lb_v4_update = addr.is_loopback or lb_v4_update
            elif addr.version == 6:
                setv6 = True
                lb_v6_update = addr.is_loopback or lb_v6_update
        # Clean-up old addresses
        cleanup = []   # type: List
        if setv4:
            cleanup.append(self.ips(exclude_lbs=not lb_v4_update))
        if setv6:
            cleanup.append(self.ip6s(exclude_lls=True,
                                     exclude_lbs=not lb_v6_update))
        for old_ip in chain.from_iterable(cleanup):
            self._del_ip(old_ip)
        # Assign IP
        rval = [self.cmd(cmd) for cmd in cmds]
        self._refresh_addresses()
        return rval.pop() if rval and len(rval) == 1 else rval

    def _del_ip(self, ip: Union[IPv4Interface, IPv6Interface]):
        """Remove an assigned IP fom this interface.
        Does not update self.addresses!

        :param ip: ip_interface-like"""
        self.cmd('ip', 'address', 'del', 'dev', self.name, ip.with_prefixlen)

    setIP = setIP6 = _set_ip

    def _refresh_addresses(self):
        """Request and parse the addresses of this interface"""
        self.mac, self.addresses[4], self.addresses[6] = \
            _addresses_of(self.name, self.node)

    def updateIP(self) -> Optional[str]:
        self._refresh_addresses()
        return self.ip

    def updateIP6(self) -> Optional[str]:
        self._refresh_addresses()
        return self.ip6

    def updateMAC(self) -> Optional[str]:
        self._refresh_addresses()
        return self.mac

    def updateAddr(self) -> Tuple[Optional[str], Optional[str]]:
        self._refresh_addresses()
        return self.ip, self.mac

    def down(self, backup=True):
        """Down the interface and, if 'backup' is true,
           save the current allocated IPs"""
        if backup:
            self.backup_addresses = deepcopy(self.addresses)

        self.node.cmd("ip link set dev " + self.name + " down")

    def up(self, restore=True):
        """Up the interface and, if 'restore' is true,
           restore the saved addresses"""
        self.isUp(setUp=True)
        if restore:
            self.setIP(self.backup_addresses[4] + self.backup_addresses[6])
            for cmd in self.restore_cmds:
                self.node.cmd(cmd)


def _addresses_of(devname: str, node: Optional[Node] = None):
    """Return the addresses of a named interface"""
    cmdline = ['ip', 'address', 'show', 'dev', devname]
    try:
        if node is not None:
            addrstr = node.cmd(*cmdline)
        else:
            addrstr = subprocess.check_output(cmdline).decode("utf-8")
    except (OSError, subprocess.CalledProcessError):
        addrstr = None
    if not addrstr:
        log.warning('Failed to run ip address!')
        return None, (), ()
    mac, v4, v6 = _parse_addresses(addrstr)
    return (mac,
            sorted(v4, key=OrderedAddress, reverse=True),
            sorted(v6, key=OrderedAddress, reverse=True))


def _parse_addresses(out: str) -> Tuple[Optional[str], List[IPv4Interface],
                                        List[IPv6Interface]]:
    """Parse the output of an ip address command
    :return: mac, [ipv4], [ipv6]"""
    # 1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state ...
    #    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    #    inet 127.0.0.1/8 scope host lo
    #    valid_lft forever preferred_lft forever
    #    inet6 ::1/128 scope host
    #    valid_lft forever preferred_lft forever
    mac = None
    v4 = []
    v6 = []
    for line in out.strip(' \n\t\r').split('\n'):
        parts = line.strip(' \n\t\r').split(' ')
        try:
            t = parts[0]
            if t == 'inet':
                v4.append(IPv4Interface(parts[1]))
            elif t == 'inet6':
                v6.append(IPv6Interface(parts[1]))
            elif 'link/' in t:
                mac = parts[1]
        except IndexError:
            log.error('Malformed ip-address line:', line)
    return mac, v4, v6


class IPLink(_m.Link):
    """A Link class that defaults to IPIntf"""
    def __init__(self, node1: str, node2: str, intf: Type[IPIntf] = IPIntf,
                 *args, **kwargs):
        """We override Link intf default to use IPIntf"""
        super().__init__(node1=node1, node2=node2, intf=intf, *args, **kwargs)


# This aliases is there for a historical reason: IPIntf used to extend
# mininet's Intf and not the mininet's TCIntf
TCIntf = IPIntf


@functools.total_ordering
class OrderedAddress:
    def __init__(self, addr):
        self.addr = addr

    def __eq__(self, other):
        return address_comparator(self.addr, other.addr) == 0

    def __lt__(self, other):
        return address_comparator(self.addr, other.addr) < 0


def address_comparator(a, b):
    """Return -1, 0, 1 if a is less, equally, more visible than b.
    We define visibility according to IP version, address scope, address class,
    and address value"""
    # We prefer IPv6
    if a.version > b.version:
        return 1
    if a.version < b.version:
        return -1
    # We don't prefer loopback addresses
    if a.network.is_loopback and not b.network.is_loopback:
        return -1
    if b.network.is_loopback and not a.network.is_loopback:
        return 1
    # LLs have low visibility
    if a.is_link_local and not b.is_link_local:
        return -1
    if b.is_link_local and not a.is_link_local:
        return 1
    # We prefer global addresses over private ones
    if a.network.is_global and not b.network.is_global:
        return 1
    if b.network.is_global and not a.network.is_global:
        return -1
    # Compare networks
    if b.network.is_global and not a.network.is_global:
        return -1
    # Compare network values
    if a.network < b.network:
        return -1
    if a.network > b.network:
        return 1
    # Otherwise simply rank the IP values
    if a.ip < b.ip:
        return -1
    return 1 if a.ip > b.ip else 0


class PhysicalInterface(IPIntf):
    """An interface that will wrap around an existing (physical) interface,
    and try to preserve its addresses.
    The interface must be present in the root namespace."""

    def __init__(self, name: str, *args, **kw):
        try:
            node = kw['node']
        except KeyError:
            raise ValueError('PhysicalInterface() requires a node= argument')
        # Save the addresses from the root namespace
        try:
            _, v4, v6 = _addresses_of(name, node=None)
        except (subprocess.CalledProcessError, OSError):
            log.error('Cannot retrieve the addresses of interface', name, '!')
            raise ValueError('Unknown physical interface name')
        if node.inNamespace:
            # cfr man ip-link; some devices cannot change of net ns
            if 'netns-local: on' in subprocess.check_output(
                    ('ethtool', '-k', name)).decode("utf-8"):
                log.error('Cannot move interface', name, 'into another network'
                          ' namespace!')
        super().__init__(name, *args, **kw)
        # Exclude link locals ...
        v4.extend(ip for ip in v6 if not ip.is_link_local)
        # Apply saved addresses
        self.setIP(v4)


class GRETunnel:
    """The GRETunnel class, which enables to create a GRE
    Tunnel in a network linking two existing interfaces.

    Currently, these tunnels only define stretched IP subnets.

    The instantiation of these tunnels should happen
    *after* the network has been built
    and *before* the network has been started.
    You can leverage the IPTopo.post_build method to do it."""
    # TODO add the created tunnel interfaces to the list of interfaces
    # known by the nodes (e.g. so they could be auto-detected-advertized in
    # the routing protocols)

    def __init__(self, if1: IPIntf, if2: IPIntf,
                 if1address: Union[str, IPv4Interface, IPv6Interface],
                 if2address: Union[str, IPv4Interface, IPv6Interface],
                 bidirectional=True):
        """:param if1: The first interface of the tunnel
        :param if2: The second interface of the tunnel
        :param if1address: The ip_interface address for if1
        :param if2address: The ip_interface address for if2
        :param bidirectional: Whether both end of the tunnel should be
                              established or not. GRE is stateless so there is
                              no handshake per-say, however if one end of the
                              tunnel is not established, the kernel will drop
                              by default the encapsulated packets."""
        self.if1, self.if2 = if1, if2
        self.ip1, self.gre1 = (ip_interface(str(if1address)),
                               self._gre_name(if1))
        self.ip2, self.gre2 = (ip_interface(str(if2address)),
                               self._gre_name(if2))
        self.bidirectional = bidirectional
        self.setup_tunnel()

    def setup_tunnel(self):
        self._add_tunnel(self.if1, self.if2, self.gre1,
                         self.ip1.with_prefixlen)
        if self.bidirectional:
            self._add_tunnel(self.if2, self.if1, self.gre2,
                             self.ip2.with_prefixlen)

    @staticmethod
    def _gre_name(x) -> str:
        return 'gre-%s' % x

    @staticmethod
    def _add_tunnel(if_local: IPIntf, if_remote: IPIntf, name: str,
                    address: str, ttl=255):
        log.debug('Creating GRE tunnel named', name, ', for subnet',
                  str(address), 'from', if_local, '[', if_local.ip, '] to',
                  if_remote, '[', if_remote.ip, ']')
        cmd = if_local.node.cmd
        cmd('ip', 'tunnel', 'add', name, 'mode', 'gre', 'remote', if_remote.ip,
            'local', if_local.ip, 'ttl', str(ttl))
        cmd('ip', 'link', 'set', name, 'up')
        cmd('ip', 'address', 'add', 'dev', name, address)

    def cleanup(self):
        self._del_tunnel(self.if1, self.gre1)
        if self.bidirectional:
            self._del_tunnel(self.if1, self.gre1)

    @staticmethod
    def _del_tunnel(if_local: IPIntf, name: str):
        if_local.node.cmd('ip', 'tunnel', 'delete', name)
