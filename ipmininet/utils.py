"""utils: utility functions to manipulate host, interfaces, ..."""
from builtins import str
from ipmininet import basestring

import collections
import os

from mininet.log import lg as log

from ipaddress import ip_address


def has_cmd(cmd):
    """Return whether the given executable is available on the system or not"""
    # Check if cmd is a valid absolute path
    if os.path.isfile(cmd) and os.access(cmd, os.X_OK):
        return True
    # Try to find the cmd in each directory in $PATH
    for path in os.environ["PATH"].split(os.path.pathsep):
        path = path.strip('"')
        exe = os.path.join(path, cmd)
        if os.path.isfile(exe) and os.access(exe, os.X_OK):
            return True
    return False


def require_cmd(cmd, help_str=None):
    """
    Ensures that a command is available in $PATH

    :param cmd: the command to test
    :param help_str: an optional help string to display if cmd is not found
    """
    if has_cmd(cmd):
        return

    if help_str:
        log.error(help_str)
    raise RuntimeError('[%s] is not available in $PATH' % cmd)


def otherIntf(intf):
    """"Get the interface on the other side of a link"""
    link = intf.link
    return (link.intf1 if link.intf2 == intf else link.intf2) if link else None


def realIntfList(n):
    """Return the list of interfaces of node n excluding loopback"""
    return [i for i in n.intfList() if i.name != 'lo']


def address_pair(n, use_v4=True, use_v6=True):
    """Returns a tuple (ip, ip6) with ip/ip6 being one of the IPv4/IPv6
       addresses of the node n"""
    from .link import IPIntf  # Prevent circular imports
    v4 = v6 = None
    for itf in n.intfList():
        # Mininet switches have a loopback interface
        # declared as an Intf.
        # This object does not have ips() or ip6s() methods.
        if not isinstance(itf, IPIntf):
            continue

        if use_v4 and v4 is None:
            itf.updateIP()
            v4 = next(itf.ips(), None)
            v4 = v4.ip.compressed if v4 is not None else v4
        if use_v6 and v6 is None:
            itf.updateIP6()
            v6 = next(itf.ip6s(exclude_lls=True), None)
            v6 = v6.ip.compressed if v6 is not None else v6
        if (not use_v4 or v4 is not None) and (not use_v6 or v6 is not None):
            break
    return v4, v6


def is_container(x):
    """Return whether x is a container (=iterable but not a string)"""
    return (isinstance(x, collections.Sequence) and
            not isinstance(x, basestring))


def prefix_for_netmask(mask):
    """Return the prefix length associated to a given netmask.
    Will return garbage if the netmask is unproperly formatted!"""
    ip = ip_address(str(mask))
    v = ~int(ip) & ~(1 - (1 << ip.max_prefixlen))
    length = 0
    while v > 0:
        v >>= 1
        length += 1
    return ip.max_prefixlen - length


class L3Router(object):
    """Placeholder class to identify L3 routing devices (primarely routers,
    but this could also be used for a device needing to participate to some
    routing protocol e.g. for TE purposes)"""
    @staticmethod
    def is_l3router_intf(itf):
        """Returns whether an interface belongs to an L3Router
        (in the Mininet meaning: an intf with an associated node)"""
        try:
            return itf is not None and isinstance(itf.node, L3Router)
        except AttributeError:
            return False


def get_set(d, key, default):
    """Attempt to return the value for the given key,
    otherwise intialize it

    :param d: dict
    :param default: constructor"""
    try:
        return d[key]
    except KeyError:
        x = d[key] = default()
        return x


def find_node(start, node_name):
    """
    :param start: The starting node of the search
    :param node_name: The name of the node to find
    :return: The interface of the node connected to start with node_name as name
    """

    if start.name == node_name:
        return start.intf()

    visited = set()
    to_visit = realIntfList(start)
    # Explore all interfaces recursively, until we find one
    # connected to the node
    while to_visit:
        i = to_visit.pop()
        if i in visited:
            continue
        visited.add(i)
        for n in i.broadcast_domain.interfaces:
            if n.node.name == node_name:
                return n
            if L3Router.is_l3router_intf(n):
                to_visit.extend(realIntfList(n.node))
    return None
