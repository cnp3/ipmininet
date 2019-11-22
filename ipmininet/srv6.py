"""This modules defines classes to create IPv6 Segment Routing (SRv6) Routes
   For more information about SRv6, see https://segment-routing.org"""
import abc
import shlex
import subprocess
from ipaddress import IPv6Address, AddressValueError, NetmaskValueError, \
    IPv4Address, IPv6Network
from typing import List, Union, Iterable, Optional

from mininet.log import lg as log

from .ipnet import IPNet
from .link import IPIntf
from .router import IPNode
from .utils import address_pair, realIntfList


def enable_srv6(node: IPNode):
    """
    Enable IPv6 Segment Routing parsing on all interfaces of the node
    """
    node.nconfig.sysctl = "net.ipv6.conf.all.seg6_enabled=1"
    node.nconfig.sysctl = "net.ipv6.conf.default.seg6_enabled=1"
    for intf in realIntfList(node):
        node.nconfig.sysctl = "net.ipv6.conf.%s.seg6_enabled=1" % intf.name


def check_srv6_compatibility() -> bool:
    """
    :return: True if the distribution supports SRv6
    """
    try:
        subprocess.check_output(
            shlex.split("sysctl net.ipv6.conf.all.seg6_enabled"))
        return True
    except subprocess.CalledProcessError:
        return False


def nexthops_to_ips(nexthops: List[Union[str, IPNode, IPIntf, IPv6Address,
                                         IPv4Address]],
                    v6=True) -> List[str]:
    """
    :param nexthops: Each element of the list can either be an IPv6 address,
                     an IPIntf or an IPNode. In both later cases,
                     the default IPv6 address is selected.
    :param v6: Whether we return IPv6 or IPv4 addresses
    :return: a list of addresses
    """
    s = []
    for nh in nexthops:
        try:
            IPv6Address(str(nh)) if v6 else IPv4Address(str(nh))
            # This is an IPv6 or IPv4 address
            s.append(str(nh))
        except (AddressValueError, NetmaskValueError):
            ip = None
            if isinstance(nh, IPNode):
                ip = address_pair(nh, use_v4=not v6)[1 if v6 else 0]
            elif isinstance(nh, IPIntf):
                ip = nh.ip6 if v6 else nh.ip
            if ip is None:
                raise ValueError("Cannot find for the nexthop %s"
                                 " a global IPv%d address\n"
                                 % (nh, 6 if v6 else 4))
            s.append(ip)
    return s


class LocalSIDTable:
    """A class representing a LocalSID routing table"""

    def __init__(self, node: IPNode,
                 matching: Iterable[Union[str, IPv6Network]] = ("::/0",)):
        """
        :param node: The node on which the table is added
        :param matching: The list of prefixes that are
                         whose processing is delegated to the table
        """
        self.node = node
        self.prefixes = [IPv6Network(str(prefix)) for prefix in matching]

        # Find Free table number
        tables = []
        out = self.node.cmd("ip rule list")
        lines = out.split("\n")
        for line in lines:
            if "lookup " in line:
                try:
                    tables.append(int(line.split("lookup ")[-1]))
                except ValueError:
                    pass
        self.num = 1
        while self.num in tables:
            self.num += 1
        if self.num >= 253:
            raise Exception("Cannot find a free table number on the host")

        # Create the table
        self.create()

    def create(self):
        self.clean()
        for prefix in self.prefixes:
            cmd = "ip -6 rule add to {prefix} table {num}"\
                .format(prefix=prefix, num=self.num)
            out, err, exitcode = self.node.pexec(shlex.split(cmd))
            if exitcode != 0:
                log.error("Cannot install rule for new LocalSIDTable:\n"
                          "{cmd}\nstdout:{out}\nstderr:{err}\n"
                          .format(cmd=cmd, out=out, err=err))
        cmd = "ip -6 route add blackhole default table {num}"\
            .format(num=self.num)
        out, err, exitcode = self.node.pexec(cmd)
        if exitcode != 0:
            log.error("Cannot install blackhole rule for new LocalSIDTable:\n"
                      "{cmd}\nstdout:{out}\nstderr:{err}\n"
                      .format(cmd=cmd, out=out, err=err))

    def clean(self):
        self.node.cmd("ip -6 route flush table {num}".format(num=self.num))
        for prefix in self.prefixes:
            self.node.cmd(shlex.split("ip rule del to {prefix} table {num}"
                                      .format(prefix=prefix, num=self.num)))


class SRv6Route(metaclass=abc.ABCMeta):
    """The SRv6Route abstract class, which enables to create an SRv6 route"""

    def __init__(self, net: IPNet, node: IPNode,
                 to: Union[str, IPv6Network, IPNode, IPIntf] = "::/0", cost=1,
                 table: Optional[LocalSIDTable] = None):
        """
        :param net: The IPNet instance
        :param node: The IPNode object on which the route has to be installed
        :param to: Either directly the prefix, an IPNode or an IPIntf object
                   so that it matches all its addresses.
        :param cost: The cost of using the route: routes with lower cost is
                     preferred if the destination prefix is the same.
        :param table: Install the route into the specified table instead of
                      the main one.
        """
        self.table = table
        self.destination = to
        self.cost = cost
        self.source = node
        itfs = realIntfList(self.source)
        if len(itfs) == 0:
            raise ValueError("Cannot install SRv6Route %s without"
                             " a real interface on node %s\n"
                             % (self, self.source.name))
        self.dev = itfs[0].name

        # Check SRv6 capability
        if not self.is_available():
            raise ValueError("Cannot create %s because"
                             " the distribution does not support it" % self)

        # Activate SRv6 on all routers and hosts
        for n in net.routers + net.hosts:
            enable_srv6(n)

        # Add routes
        self.cmds = self.build_commands()
        self.install()

    def is_available(self) -> bool:
        """Check the compatibility with this encapsulation method"""
        return check_srv6_compatibility()

    def dest_prefixes(self) -> List[str]:
        prefixes = []
        try:
            IPv6Network(str(self.destination))
            # This is an IPv6 address
            prefixes.append(str(self.destination))
        except (AddressValueError, NetmaskValueError):
            if isinstance(self.destination, IPNode):
                for itf in self.destination.intfList():
                    for ip6 in itf.ip6s(exclude_lls=True, exclude_lbs=True):
                        prefixes.append(ip6.network.with_prefixlen)
            elif isinstance(self.destination, IPIntf):
                for ip6 in self.destination.ip6s(exclude_lls=True,
                                                 exclude_lbs=True):
                    prefixes.append(ip6.network.with_prefixlen)

            if len(prefixes) == 0:
                log.error("Cannot install SRv6Route", self,
                          "because the destination", self.destination,
                          "does not have a global IPv6 address\n")
        return prefixes

    @abc.abstractmethod
    def build_commands(self) -> List[str]:
        return []

    def install(self):
        self._run_cmds()

    def cleanup(self):
        self._run_cmds(prefix="ip -6 route add ")

    def _run_cmds(self, prefix: str = "ip -6 route add ") -> int:
        for cmd in self.cmds:
            cmd = prefix + cmd
            if self.table is not None:
                cmd = cmd + " table {num}".format(num=self.table.num)
            out, err, code = self.source.pexec(shlex.split(cmd))
            log.debug("Installing route on router %s: '%s'\n"
                      % (self.source.name, cmd))
            if code:
                log.error('Cannot install SRv6Route', self, '[rcode:',
                          str(code), ']:\n', cmd, '\nstdout:', str(out),
                          '\nstderr:', str(err))
                return code
        return -1

    def __str__(self):
        return "SRv6Route<on=%s, to=%s, cost=%s>" \
               % (self.source.name, self.destination, self.cost)


class SRv6Encap(SRv6Route):
    """The SRv6Encap class, which enables to create an IPv6
    Segment Routing encapsulation in a router.

    The instantiation of these tunnels should happen
    *after* the network has been built and its addresses has been allocated.
    You can leverage the IPTopo.post_build method to do it."""
    ENCAP = "encap"
    INLINE = "inline"

    def __init__(self, net: IPNet, node: IPNode,
                 to: Union[str, IPv6Network, IPNode, IPIntf] = "::/0",
                 through: List[Union[str, IPv6Address, IPNode, IPIntf]] = (),
                 mode=ENCAP, cost=1):
        """
        :param net: The IPNet instance
        :param node: The IPNode object on which the route has to be installed
        :param to: Either directly the prefix, an IPNode or an IPIntf object
                   so that it matches all its addresses.
        :param through: A list of nexthops to set in the IPv6 Segment Routing
                        Header. Each element of the list can either be an
                        IPv6 address, an IPIntf or an IPNode. In both later
                        cases, the default IPv6 address is selected.
        :param mode: Either SRv6Encap.ENCAP or SRv6Encap.INLINE whether
                     the route should encapsulate packets in an outer IPv6
                     packet with the SRH or insert the SRH directly inside
                     the packet.
        :param cost: The cost of using the route: routes with lower cost is
                     preferred if the destination prefix is the same.
        """
        if len(through) == 0:
            raise ValueError("It does not make sense to use Segment Routing"
                             " without any redirection.")
        self.nexthops = list(through)
        self.mode = mode
        super().__init__(net, node, to=to, cost=cost)

    def is_available(self) -> bool:
        """Check the compatibility with this encapsulation method"""
        return super().is_available() \
            and subprocess.check_call(shlex.split("ip sr tunsrc set ::")) == 0

    def build_commands(self) -> List[str]:
        cmds = []  # type: List[str]

        # Get destination addresses
        prefixes = self.dest_prefixes()
        if len(prefixes) == 0:
            return cmds

        # Get segments
        nexthops = nexthops_to_ips(self.nexthops)
        if len(nexthops) == 0:
            return cmds

        # Build iproute2 commands
        for prefix in prefixes:
            cmds.append("%s encap seg6 mode %s segs %s metric %s dev %s"
                        % (prefix, self.mode, ",".join(nexthops), self.cost,
                           self.dev))
        return cmds

    def __str__(self):
        return "SRv6Encap<on=%s, to=%s, through=%s, mode=%s, cost=%s>" \
               % (self.source.name, self.destination, self.nexthops,
                  self.mode, self.cost)


class SRv6EndFunction(SRv6Route):
    """This class represents an SRv6 End function"""
    ACTION = "End"

    @property
    def params(self) -> str:
        return ""

    def is_available(self) -> bool:
        """Check the compatibility with this advanced SRv6 routes"""
        cmd = "{seg} encap seg6local action End dev {dev}".format(seg="::2/128",
                                                                  dev=self.dev)
        src = self.source
        return super().is_available() \
            and src.pexec(shlex.split("ip -6 route add " + cmd))[2] == 0 \
            and src.pexec(shlex.split("ip -6 route del " + cmd))[2] == 0

    def build_commands(self) -> List[str]:
        cmds = []  # type: List[str]

        # Get destination addresses
        prefixes = self.dest_prefixes()
        if len(prefixes) == 0:
            return cmds

        # Build iproute2 commands
        for prefix in prefixes:
            cmds.append("{segment} encap seg6local action {action} {params}"
                        " metric {metric} dev {dev}"
                        .format(segment=prefix, action=self.ACTION,
                                params=self.params, metric=self.cost,
                                dev=self.dev))
        return cmds

    def __str__(self):
        return "SRv6Function<action=%s, on=%s, to=%s, cost=%s, params=%s>" \
               % (self.ACTION, self.source.name, self.destination, self.cost,
                  self.params)


class SRv6EndXFunction(SRv6EndFunction):
    """This class represents an SRv6 End.X function"""
    ACTION = "End.X"

    def __init__(self, nexthop: Union[str, IPv6Address, IPIntf, IPNode], *args,
                 **kwargs):
        """
        :param net: The IPNet instance
        :param node: The IPNode object on which the route has to be installed
        :param to: Either directly the prefix, an IPNode or an IPIntf object
                   so that it matches all its addresses.
        :param cost: The cost of using the route: routes with lower cost is
                     preferred if the destination prefix is the same.
        :param table: Install the route into the specified table instead of
                      the main one.
        :param nexthop: The nexthop to consider when forwarding the packet.
                        It can be an IPv6 address, an IPIntf or an IPNode.
                        In both later cases, the default IPv6 address is
                        selected.
        """
        self.nexthop = nexthops_to_ips([nexthop])[0]
        super().__init__(*args, **kwargs)

    @property
    def params(self) -> str:
        return "nh6 " + self.nexthop


class SRv6EndTFunction(SRv6EndFunction):
    """This class represents an SRv6 End.T function"""
    ACTION = "End.T"

    def __init__(self, lookup_table: str, *args, **kwargs):
        """
        :param net: The IPNet instance
        :param node: The IPNode object on which the route has to be installed
        :param to: Either directly the prefix, an IPNode or an IPIntf object
                   so that it matches all its addresses.
        :param cost: The cost of using the route: routes with lower cost is
                     preferred if the destination prefix is the same.
        :param table: Install the route into the specified table instead of
                      the main one.
        :param lookup_table: The packet is forwarded to the nexthop looked up
                             in this specified routing table
        """
        self.lookup_table = lookup_table
        super().__init__(*args, **kwargs)

    @property
    def params(self) -> str:
        return "table {}".format(self.lookup_table)


class SRv6EndDX2Function(SRv6EndFunction):
    """This class represents an SRv6 End.DX2 function"""
    ACTION = "End.DX2"

    def __init__(self, interface: Union[str, IPIntf], *args, **kwargs):
        """
        :param net: The IPNet instance
        :param node: The IPNode object on which the route has to be installed
        :param to: Either directly the prefix, an IPNode or an IPIntf object
                   so that it matches all its addresses.
        :param cost: The cost of using the route: routes with lower cost is
                     preferred if the destination prefix is the same.
        :param table: Install the route into the specified table instead of
                      the main one.
        :param interface: The packet is forwarded to this specific interface
        """
        self.interface = interface.name if isinstance(interface, IPIntf) \
            else str(interface)
        super().__init__(*args, **kwargs)

    @property
    def params(self) -> str:
        return "oif " + self.interface


class SRv6EndDX6Function(SRv6EndXFunction):
    """This class represents an SRv6 End.DX6 function"""
    ACTION = "End.DX6"


class SRv6EndDX4Function(SRv6EndFunction):
    """This class represents an SRv6 End.DX4 function"""
    ACTION = "End.DX4"

    def __init__(self, nexthop: Union[str, IPv4Address, IPIntf, IPNode],
                 *args, **kwargs):
        """
        :param net: The IPNet instance
        :param node: The IPNode object on which the route has to be installed
        :param to: Either directly the prefix, an IPNode or an IPIntf object
                   so that it matches all its addresses.
        :param cost: The cost of using the route: routes with lower cost is
                     preferred if the destination prefix is the same.
        :param table: Install the route into the specified table instead of
                      the main one.
        :param nexthop: The nexthop to consider when forwarding the packet.
                        It can be an IPv4 address, an IPIntf or an IPNode.
                        In both later cases, the default IPv4 address is
                        selected.
        """
        self.nexthop = nexthops_to_ips([nexthop], v6=False)[0]
        super().__init__(*args, **kwargs)

    @property
    def params(self) -> str:
        return "nh4 " + self.nexthop


class SRv6EndDT6Function(SRv6EndTFunction):
    """This class represents an SRv6 End.DT6 function"""
    ACTION = "End.DT6"


class SRv6EndB6Function(SRv6EndFunction):
    """This class represents an SRv6 End.B6 function"""
    ACTION = "End.B6"

    def __init__(self, segments: List[Union[str, IPv6Address, IPIntf, IPNode]],
                 *args, **kwargs):
        """
        :param net: The IPNet instance
        :param node: The IPNode object on which the route has to be installed
        :param to: Either directly the prefix, an IPNode or an IPIntf object
                   so that it matches all its addresses.
        :param cost: The cost of using the route: routes with lower cost is
                     preferred if the destination prefix is the same.
        :param table: Install the route into the specified table instead of
                      the main one.
        :param segments: A list of segments to set in the IPv6 Segment Routing
                         Header. Each element of the list can either be an
                         IPv6 address, an IPIntf or an IPNode. In both later
                         cases, the default IPv6 address is selected.
        """
        if len(segments) == 0:
            raise ValueError("It does not make sense to use Segment Routing"
                             " without any segment.")
        self.segments = nexthops_to_ips(segments)
        super().__init__(*args, **kwargs)

    @property
    def params(self) -> str:
        return "srh segs " + ",".join(self.segments)


class SRv6EndB6EncapsFunction(SRv6EndB6Function):
    """This class represents an SRv6 End.B6.Encaps function"""
    ACTION = "End.B6.Encaps"
