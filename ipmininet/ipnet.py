"""IPNet: The Mininet that plays nice with IP networks.
This modules will auto-generate all needed configuration properties if
unspecified by the user"""
from builtins import str

import math
from operator import attrgetter, methodcaller

from ipaddress import ip_network, ip_interface

from . import MIN_IGP_METRIC, OSPF_DEFAULT_AREA
from .utils import otherIntf, realIntfList, L3Router, address_pair, has_cmd
from .host import IPHost
from .router import Router
from .router.config import BasicRouterConfig
from .link import IPIntf, IPLink, PhysicalInterface
from .ipswitch import IPSwitch

from mininet.net import Mininet
from mininet.node import Host
from mininet.log import lg as log

# ping6 is not provided by default on newer systems
PING6_CMD = 'ping6' if has_cmd('ping6') else 'ping -6'


class IPNet(Mininet):
    """IPNet: An IP-aware Mininet"""
    def __init__(self,
                 router=Router,
                 config=BasicRouterConfig,
                 use_v4=True,
                 ipBase=u'192.168.0.0/16',
                 max_v4_prefixlen=24,
                 use_v6=True,
                 ip6Base=u'fc00::/7',
                 allocate_IPs=True,
                 max_v6_prefixlen=48,
                 igp_metric=MIN_IGP_METRIC,
                 igp_area=OSPF_DEFAULT_AREA,
                 host=IPHost,
                 link=IPLink,
                 intf=IPIntf,
                 switch=IPSwitch,
                 controller=None,
                 *args, **kwargs):
        """Extends Mininet by adding IP-related ivars/functions and
        configuration knobs.


        :param router: The class to use to build routers
        :param config: The default configuration for the routers
        :param use_v4: Enable IPv4
        :param max_v4_prefixlen: The maximal IPv4 prefix for the auto-allocated
                                    broadcast domains
        :param use_v6: Enable IPv6
        :param ip6Base: Base prefix to use for IPv6 allocations
        :param max_v6_prefixlen: Maximal IPv6 prefixlen to auto-allocate
        :param allocate_IPs: wether to auto-allocate subnets in the network
        :param igp_metric: The default IGP metric for the links
        :param igp_area: The default IGP area for the links"""
        self.router = router
        self.config = config
        self.routers = []  # the list of router in the network
        self._ip_allocs = {}  # We need this to be able to do inverse-lookups
        self.max_v4_prefixlen = max_v4_prefixlen
        self._unallocated_ipbase = [ip_network(ipBase)]
        self.use_v4 = use_v4
        self.use_v6 = use_v6
        self.ip6Base = ip6Base
        self.max_v6_prefixlen = max_v6_prefixlen
        self._unallocated_ip6base = [ip_network(ip6Base)]
        self.broadcast_domains = None
        self.igp_metric = igp_metric
        self.igp_area = igp_area
        self.allocate_IPs = allocate_IPs
        self.physical_interface = {}  # itf: node
        super(IPNet, self).__init__(ipBase=ipBase, host=host, switch=switch,
                                    link=link, intf=intf, controller=controller,
                                    *args, **kwargs)

    def addRouter(self, name, cls=None, **params):
        """Add a router to the network

        :param name: the node name
        :param cls: the class to use to instantiate it"""
        defaults = {'use_v4': self.use_v4, 'use_v6': self.use_v6,
                    'config': self.config}
        defaults.update(params)
        if not cls:
            cls = self.router
        r = cls(name, **defaults)
        self.routers.append(r)
        self.nameToNode[name] = r
        return r

    def __iter__(self):
        for r in self.routers:
            yield r.name
        for n in super(IPNet, self).__iter__():
            yield n

    def __len__(self):
        return len(self.routers) + super(IPNet, self).__len__()

    def buildFromTopo(self, topo):
        log.info('\n*** Adding Routers:\n')
        for routerName in topo.routers():
            self.addRouter(routerName, **topo.nodeInfo(routerName))
            log.info(routerName + ' ')
        log.info('\n')
        self.physical_interface.update(topo.phys_interface_capture)
        super(IPNet, self).buildFromTopo(topo)

    def addLink(self, node1, node2,
                igp_metric=None, igp_area=None, igp_passive=False,
                v4_width=1, v6_width=1,
                *args, **params):
        """Register a link with additional properties

        :param igp_metric: the associated igp metric for this link
        :param igp_area: the associated igp area for this link
        :param igp_passive: whether IGP should create adjacencies over this
                            link or not
        :param v4_width: the number of IPv4 addresses to allocate on the
                         interfaces
        :param v6_width: the number of IPv6 addresses to allocate on the
                         interfaces
        :param ra: list of AdvPrefix objects, each one representing an
                   advertised prefix
        :param rdnss: list of AdvRDNSS objects, each one representing
                   an advertised DNS server
        """
        # Handles defaults
        if not igp_metric:
            igp_metric = self.igp_metric
        if not igp_area:
            igp_area = self.igp_area
        # Register all link properties
        props = {'igp_metric': igp_metric,
                 'igp_area': igp_area,
                 'igp_passive': igp_passive,
                 'v4_width': v4_width,
                 'v6_width': v6_width}
        # Update interface properties with link properties
        for pstr in ('params1', 'params2'):
            try:
                p = params[pstr]
            except KeyError:
                p = params[pstr] = {}
            for k, v in props.items():
                # Only iff not already specified
                if k not in p:
                    p[k] = v
        return super(IPNet, self).addLink(node1=node1, node2=node2,
                                          *args, **params)

    def addHost(self, name, **params):
        """Prevent Mininet from forcing the allocation of IPv4 addresses
           on hosts. We delegate it to the address auto-allocation of
           IPNet."""
        if 'ip' not in params:
            params['ip'] = None
        return super(IPNet, self).addHost(name, **params)

    def node_for_ip(self, ip):
        """Return the node owning a given IP address

        :param ip: an IP address
        :return: a node name"""
        return self._ip_allocs[str(ip)]

    def start(self):
        super(IPNet, self).start()
        log.info('*** Starting, ', len(self.routers), 'routers\n')
        for router in self.routers:
            log.info(router.name + ' ')
            router.start()
        log.info('*** Starting, ', len(self.hosts), 'hosts\n')
        for host in self.hosts:
            log.info(host.name + ' ')
            host.start()
        log.info('\n')
        log.info('*** Setting default host routes\n')
        for h in self.hosts:
            if 'defaultRoute' in h.params:
                continue  # Skipping hosts with explicit default route
            default = False
            # The first router we find will become the default gateway
            for itf in realIntfList(h):
                for r in itf.broadcast_domain.routers:
                    log.info('%s via %s, ' % (h.name, r.name))
                    if self.use_v4 and h.use_v4 and len(r.addresses[4]) > 0:
                        h.setDefaultRoute('via %s' % r.ip)
                        default = True
                    if (self.use_v6 and h.use_v6 and len(r.addresses[6]) > 0 and
                            len(r.ra_prefixes)) == 0:
                        # We define a default route only if router xi
                        # advertisement are not activated. If we call the same
                        # function, the route created above might be deleted
                        h.cmd('ip route add default dev %s via %s' % (
                            h.defaultIntf(), r.ip6))
                        default = True
                    break
                if default:
                    break
            if not default:
                log.info('skipping %s , ' % h.name)
        log.info('\n')

    def stop(self):
        log.info('*** Stopping', len(self.routers), 'routers\n')
        for router in self.routers:
            log.info(router.name + ' ')
            router.terminate()
        log.info('\n')
        super(IPNet, self).stop()

    def build(self):
        super(IPNet, self).build()
        self.broadcast_domains = self._broadcast_domains()
        log.info("*** Found", len(self.broadcast_domains),
                 "broadcast domains\n")
        if self.allocate_IPs:
            self._allocate_IPs()
        # Physical interfaces are their own broadcast domain
        for itf_name, n in self.physical_interface.items():
            try:
                itf = PhysicalInterface(itf_name, node=self[n])
                log.info('\n*** Adding Physical interface',
                         itf_name, 'to', n, '\n')
                self.broadcast_domains.append(BroadcastDomain(itf))
            except KeyError:
                log.error('!!! Node', n, 'not found!\n')
        try:
            self.topo.post_build(self)
        except AttributeError as e:
            log.error('*** Skipping post_build():', str(e), '\n')

    def _allocated_ipv4_subnets(self):
        subnets = []
        for d in self.broadcast_domains:
            subnets.extend(d.fixed_net4s)
        return subnets

    def _allocated_ipv6_subnets(self):
        subnets = []
        for d in self.broadcast_domains:
            subnets.extend(d.fixed_net6s)
        return subnets

    def _allocate_IPs(self):
        """Allocate IP addresses on every interface in every broadcast
        domain"""
        if self.use_v4:
            self._allocate_ipv4()
        if self.use_v6:
            self._allocate_ipv6()

    def _allocate_ipv4(self):
        log.info("*** Allocating IPv4 addresses\n")
        self._allocate_subnets(self._unallocated_ipbase,
                               self.broadcast_domains,
                               domainlen='len_v4',
                               net_key='net',
                               size_key='max_v4prefixlen',
                               max_prefixlen=self.max_v4_prefixlen,
                               allocated_subnets=self._allocated_ipv4_subnets())
        for domain in self.broadcast_domains:
            if not domain.use_ip_version(4):
                continue
            for intf in domain:
                if len(list(intf.ips())) == 0:
                    ips = tuple(domain.next_ipv4()
                                for _ in range(intf.interface_width[0]))
                    intf.setIP(ips)
                for ip in intf.ips():
                    self._ip_allocs[ip.with_prefixlen] = intf.node
                    self._ip_allocs[ip.ip.compressed] = intf.node

    def _allocate_ipv6(self):
        log.info("*** Allocating IPv6 addresses\n")
        self._allocate_subnets(self._unallocated_ip6base,
                               self.broadcast_domains,
                               domainlen='len_v6',
                               net_key='net6',
                               size_key='max_v6prefixlen',
                               max_prefixlen=self.max_v6_prefixlen,
                               allocated_subnets=self._allocated_ipv6_subnets())
        for domain in self.broadcast_domains:
            if not domain.use_ip_version(6):
                continue
            for intf in domain:
                if len(list(intf.ip6s(exclude_lls=True))) == 0:
                    ips = tuple(domain.next_ipv6()
                                for _ in range(intf.interface_width[1]))
                    intf.setIP6(ips)
                for ip in intf.ip6s(exclude_lls=True):
                    self._ip_allocs[ip.with_prefixlen] = intf.node
                    self._ip_allocs[ip.ip.compressed] = intf.node

    @staticmethod
    def _allocate_subnets(subnets, domains, domainlen='len_v4',
                          net_key='net', size_key='max_v4prefixlen',
                          max_prefixlen=24, allocated_subnets=()):
        """Allocate subnets to broadcast domains.

        We keep the subnets sorted as x < y wrt the available number of
        addresses in the subnet so that the bigger domains
        take the smallest subnets before subdividing them.
        As the domains range from the biggest to the smallest, and the subnets
        from the smallest to the biggest, the biggest domains will take the
        first subnet that is able to contain it, and split it in several
        subnets until it is restricted to its prefix.
        The next domain then is necessarily of the same size (reuses on of the
        split subnets) or smaller (uses a previsouly split subnet or splits a
        bigger one). This avoids wasting of addresses (wrt. the specified
        max_prefixlen) at the cost of a quadratic (?) behavior.

        :param subnets: a list of ip_network of available subnets. This list
                        will be modified to account for the new allocations.
        :param domains: a list of BroadcastDomain
        :param domainlen: The name of the method used to retrieve the length
                          of the broadcast domain (address count)
        :param net_key: the key to use to set the allocated subnet in the
                        broadcast domain.
        :param size_key: the key to use to retrieve the maximal prefix length
                         suitable for a broadcast domain
        :param max_prefixlen: The maximal prefixlen that can be allocated,
                                e.g. to not allocate /126 for IPv6 P2P links
        :param allocated_subnets: The subnets that are already allocated and
                                  cannot be allocated to another domain
        :return: iterator of (domain, subnet)"""
        _domainlen = methodcaller(domainlen)
        domains.sort(key=_domainlen, reverse=True)
        _prefixlen = attrgetter('prefixlen')
        subnets.sort(key=_prefixlen, reverse=True)
        ip_version = 4 if net_key == 'net' else 6
        for d in domains:
            if not d.use_ip_version(ip_version):
                continue
            if not subnets:
                raise ValueError('No subnet left in the prefix space for all'
                                 'broadcast domains.')
            plen = min(max_prefixlen, getattr(d, size_key))
            if plen < subnets[-1].prefixlen:
                raise ValueError('Could not find a subnet big enough for a '
                                 'broadcast domain.')
            log.debug('Allocating prefix', plen, 'for interfaces',
                      d.interfaces)
            # Try to find a suitable subnet in the list
            for i, net in enumerate(subnets):
                nets = []
                # if the subnet is too big for the prefix, perform a left
                # expansion (only expand one at a time to keep subnets as
                # aggregated as possible).
                while plen > net.prefixlen:
                    # Get list of subnets and append to list of previous
                    # expanded subnets as it is bigger wrt. prefixlen
                    net, next_net = tuple(net.subnets(prefixlen_diff=1))
                    # If not a subnet of an allocated subnet
                    if len(list(filter(lambda y: next_net in y,
                                       allocated_subnets))) == 0:
                        nets.append(next_net)
                # Check if we have an appropriately-sized subnet
                if plen == net.prefixlen:
                    # If the network overlaps with an allocated subnet,
                    # we pass it
                    if len(list(filter(lambda y: net in y or y in net,
                                       allocated_subnets))) == 0:
                        # Register the allocation
                        setattr(d, net_key, net)
                    # Delete the expanded/used subnet
                    del subnets[i]
                    # Insert the created subnets if any
                    subnets.extend(nets)
                    # Sort the array again
                    subnets.sort(key=_prefixlen, reverse=True)
                    # Proceed to the next broadcast domain
                    break
                # Otherwise try the next network for the current domain

    def _broadcast_domains(self):
        """Build the broadcast domains for this topology"""
        domains = []
        interfaces = {intf: False
                      for n in self.values()
                      if BroadcastDomain.is_domain_boundary(n)
                      for intf in realIntfList(n)}
        interfaces.update({r.intf('lo'): False for r in self.routers})
        for intf in interfaces.keys():
            # the interface already belongs to a broadcast domain
            if interfaces[intf]:
                continue
            # create a new domain and explore the interface
            bd = BroadcastDomain(intf)
            # Mark all explored interfaces belonging to that domain
            for i in bd:
                interfaces[i] = True
                i.broadcast_domain = bd
            domains.append(bd)
        return domains

    def _ping_set(self, src, dst_dict, timeout, v4=True):
        """Do the actual ping to the dict of {dst: dst_ip} from src

           :param src: origin of the ping
           :param dst_dict: destinations {dst: dst_ip} of the ping
           :param timeout: the time to wait for a response, as string
           :param v4: whether IPv4 or IPv6 is used
           :param return: a tuple (lost packets, sent packets)"""
        if len(dst_dict) == 0:
            return 0, 0
        lost = 0
        packets = 0
        opts = ''
        if timeout:
            opts = '-W %s' % timeout

        log.output("%s --%s--> " % (src.name, "IPv4" if v4 else "IPv6"))
        for dst, dst_ip in dst_dict.items():
            result = src.cmd('%s -c1 %s %s' % ("ping" if v4 else PING6_CMD,
                                               opts, dst_ip))
            sent, received = self._parsePing(result)
            lost += sent - received
            packets += sent
            log.output("%s " % dst.name if received else "X ")
        log.output('\n')

        return lost, packets

    def ping(self, hosts=None, timeout=None, use_v4=True, use_v6=True):
        """Ping between all specified hosts.
           If use_v4 is true, pings over IPv4 are used between any pair of
           hosts having at least one IPv4 address on one of their interfaces
           (loopback excluded).
           If use_v6 is true, pings over IPv6 are used between any pair of
           hosts having at least one non-link-local IPv6 address on one of
           their interfaces (loopback excluded).

           :param hosts: list of hosts or None if all must be pinged
           :param timeout: time to wait for a response, as string
           :param use_v4: whether IPv4 addresses can be used
           :param use_v6: whether IPv6 addresses can be used
           :return: the packet loss percentage of IPv4 connectivity if
                    self.use_v4 is set the loss percentage of IPv6 connectivity
                    otherwise"""
        packets = lost = 0
        if not hosts:
            hosts = self.hosts
        incompatible_hosts = {}
        if not use_v4 and not use_v6:
            log.output("*** Warning: Parameters forbid both IPv4 and IPv6 for "
                       "pings\n")
            return 0

        log.output("*** Ping: testing reachability over %s%s%s\n"
                   % ("IPv4" if use_v4 else "",
                      " and " if use_v4 and use_v6 else "",
                      "IPv6" if use_v6 else ""))
        for src in hosts:
            src_ip, src_ip6 = address_pair(src, use_v4, use_v6)
            ping_dict = {}
            ping6_dict = {}
            for dst in hosts:
                if src != dst:
                    dst_ip, dst_ip6 = address_pair(dst, src_ip is not None,
                                                   src_ip6 is not None)
                    if dst_ip is not None:
                        ping_dict[dst] = dst_ip
                    if dst_ip6 is not None:
                        ping6_dict[dst] = dst_ip6
                    if (use_v4 and dst_ip is None and
                            use_v6 and dst_ip6 is None):
                        node1 = src if src.name <= dst.name else dst
                        node2 = src if node1 != src else dst
                        if node2.name not in incompatible_hosts.setdefault(
                                node1.name, set()):
                            incompatible_hosts[node1.name].add(node2.name)

            result = self._ping_set(src, ping_dict, timeout, True)
            lost += result[0]
            packets += result[1]
            result = self._ping_set(src, ping6_dict, timeout, False)
            lost += result[0]
            packets += result[1]

        for node1, incompatibilities in incompatible_hosts.items():
            for node2 in incompatibilities:
                log.output("*** Warning: %s and %s have no global address "
                           "in the same IP version\n" % (node1, node2))

        if packets > 0:
            ploss = 100.0 * lost / packets
            received = packets - lost
            log.output("*** Results: %i%% dropped (%d/%d received)\n" %
                       (ploss, received, packets))
        else:
            ploss = 0
            log.output("*** Warning: No packets sent\n")

        return ploss

    def pingAll(self, timeout=None, use_v4=True, use_v6=True):
        """Ping between all hosts.
           return: ploss packet loss percentage"""
        return self.ping(timeout=timeout, use_v4=use_v4, use_v6=use_v6)

    def pingPair(self, use_v4=True, use_v6=True):
        """Ping between first two hosts, useful for testing.
           return: ploss packet loss percentage"""
        hosts = [self.hosts[0], self.hosts[1]]
        return self.ping(hosts=hosts, use_v4=use_v4, use_v6=use_v6)

    def ping4All(self, timeout=None):
        """Ping (IPv4-only) between all hosts.
           return: ploss packet loss percentage"""
        return self.pingAll(timeout=timeout, use_v6=False)

    def ping4Pair(self):
        """Ping (IPv4-only) between first two hosts, useful for testing.
           return: ploss packet loss percentage"""
        return self.pingPair(use_v6=False)

    def ping6All(self, timeout=None):
        """Ping (IPv6-only) between all hosts.
           return: ploss packet loss percentage"""
        return self.pingAll(timeout=timeout, use_v4=False)

    def ping6Pair(self):
        """Ping (IPv6-only) between first two hosts, useful for testing.
           return: ploss packet loss percentage"""
        return self.pingPair(use_v4=False)


class BroadcastDomain(object):
    """An IP broadcast domain in the network. This class stores the set of
    interfaces belonging to the same broadcast domain, as well as the
    associated IP prefix if any"""

    # The set of object that will define L3 domain boundaries
    # FIXME Where do we put middleboxes in this model ?
    BOUNDARIES = (Host, IPHost, Router)

    def __init__(self, interfaces=None, *args, **kwargs):
        """Initialize the broadcast domain and optionally explore a set of
        interfaces

        :param interfaces: one Intf or a list of Intf"""
        super(BroadcastDomain, self).__init__(*args, **kwargs)
        self.interfaces = set()
        self.net = None
        self._allocated_v4 = 1  # We need to skip subnet address
        self.net6 = None
        # self._allocated_v6 = 0  # We can use the full address space
        self._allocated_v6 = 1  # FIXME null-addresses are routed directly
        # to the routers loopback .. Might be a bug in the netns code.
        if interfaces:
            if not isinstance(interfaces, list):
                interfaces = [interfaces]
            self.explore(interfaces)

        # Retrieve pre-fixed subnets
        self.fixed_net4s = []
        self.fixed_net6s = []
        for i in self.interfaces:
            for ip in i.ips():
                net = ip_interface(ip).network
                if net not in self.fixed_net4s:
                    self.fixed_net4s.append(net)
            for ip6 in i.ip6s(exclude_lls=True):
                net6 = ip_interface(ip6).network
                if net6 not in self.fixed_net6s:
                    self.fixed_net6s.append(net6)

    @staticmethod
    def is_domain_boundary(node):
        """Check whether the node is a L3 broadcast domain boundary

        :param node: a Node instance"""
        return isinstance(node, BroadcastDomain.BOUNDARIES)

    def __iter__(self):
        """Iterates over all interfaces in this broadcast domain"""
        return iter(self.interfaces)

    def len_v4(self):
        """The number of IPv4 addresses in this broadcast domain"""
        return sum(map(lambda x: x.interface_width[0]
                       if len(list(x.ips())) > 0 else 0, self.interfaces))

    def len_v6(self):
        """The number of IPv6 addresses in this broadcast domain"""
        return sum(map(lambda x: x.interface_width[1]
                       if len(list(x.ip6s(exclude_lls=True))) > 0 else 0,
                       self.interfaces))

    def explore(self, itfs):
        """Explore a new list of interfaces and add them and their neightbors
        to this broadcast domain

        :param itf: a list of Intf"""
        visited = []
        while itfs:
            # Explore one element
            i = itfs.pop()
            if i in visited:
                continue
            visited.append(i)
            if self.is_domain_boundary(i.node):
                self.interfaces.add(i)
            # check its corresponding interface
            other = otherIntf(i)
            if not other:  # This is an unbound interface
                continue
            # if it is a L3 boundary register it and stop there
            if self.is_domain_boundary(other.node):
                self.interfaces.add(other)
            else:
                # explode the node's interface to explore them
                itfs.extend([x for x in realIntfList(other.node)
                             if x is not other])

    @property
    def max_v4prefixlen(self):
        """Return the maximal IPv4 prefix suitable for this domain"""
        # IPv4 reserves 2 addresses for broadcast/subnet addresses
        return 32 - math.ceil(math.log(2 + self.len_v4(), 2))

    @property
    def max_v6prefixlen(self):
        """Return the maximal IPv6 prefix suitable for this domain"""
        # IPv6 should use whole subnet space for addressing
        # But see FIXME in constructor
        return 128 - math.ceil(math.log(1 + self.len_v6(), 2))

    @property
    def routers(self):
        """List all interfaces in this domain belonging to a L3 router"""
        return [i for i in self.interfaces if L3Router.is_l3router_intf(i)]

    def next_ipv4(self):
        """Allocate and return the next available IPv4 address in this
        domain

        :return ip_interface:"""
        try:
            addr = self.net[self._allocated_v4]
            self._allocated_v4 += 1
            return ip_interface(u'%s/%d' % (addr, self.net.prefixlen))
        except IndexError:
            raise ValueError('No more available IPv4 address')
        except TypeError:
            raise ValueError('No associated IPv4 subnet')

    def next_ipv6(self):
        """Allocate and return the next available IPv6 address in this
        domain

        :return ip_interface:"""
        try:
            addr = self.net6[self._allocated_v6]
            self._allocated_v6 += 1
            return ip_interface(u'%s/%d' % (addr, self.net6.prefixlen))
        except IndexError:
            raise ValueError('No more available IPv6 address')
        except TypeError:
            raise ValueError('No associated IPv6 subnet')

    def use_ip_version(self, ip_version):
        """ Checks whether it makes sense to allocate a subnet
        of an IP version to this domain. If there is no other node
        allowing it, there is no point in allocating an address
        to a single host.

        :param ip_version: either 4 or 6
        :return: True iif there is more than one interface on the domain
                 enabling this IP version
        """
        for i in self.routers:
            if i.node.use_v4 and ip_version == 4 \
                    or i.node.use_v6 and ip_version == 6:
                return True
        return len(self.interfaces) - len(self.routers) > 1
