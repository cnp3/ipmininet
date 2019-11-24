"""An enhanced CLI providing IP-related commands"""
import sys
from cmd import Cmd
from select import poll

from mininet.cli import CLI
from mininet.log import lg

from ipmininet.utils import address_pair


class IPCLI(CLI):

    # XXX When PR https://github.com/mininet/mininet/pull/897
    # is accepted, we can remove this constructor
    def __init__(self, mininet, stdin=sys.stdin, script=None):
        """Start and run interactive or batch mode CLI
           mininet: Mininet network object
           stdin: standard input for CLI
           script: script to run in batch mode"""
        self.mn = mininet
        # Local variable bindings for py command
        self.locals = {'net': mininet}
        # Attempt to handle input
        self.stdin = stdin
        self.inPoller = poll()
        self.inPoller.register(stdin)
        self.inputFile = script
        Cmd.__init__(self, stdin=self.stdin)
        lg.info('*** Starting CLI:\n')

        if self.inputFile:
            self.do_source(self.inputFile)
            return

        self.initReadline()
        self.run()

    def do_route(self, line=""):
        """route destination: Print all the routes towards that destination
        for every router in the network"""
        for r in self.mn.routers:
            lg.output("[%s] " % r.name)
            self.default('%s ip route get %s' % (r.name, line))

    def do_ip(self, line):
        """ip IP1 IP2 ...: return the node associated to the given IP"""
        for ip in line.split(' '):
            try:
                n = self.mn.node_for_ip(ip)
            except KeyError:
                n = 'unknown IP'
            finally:
                lg.output(ip, '|', n, "\n")

    def do_ips(self, line):
        """ips n1 n2 ...: return the ips associated to the given node name"""
        for n in line.split(' '):
            try:
                ips = [ip.ip.compressed for itf in self.mn[n].intfList()
                       for ip in list(itf.ips())
                       + list(itf.ip6s(exclude_lls=True))]
            except KeyError:
                ips = 'unknown node'
            finally:
                lg.output(n, '|', ips, "\n")

    def do_ping4all(self, line):
        """Ping (IPv4-only) between all hosts."""
        self.mn.ping4All(line)

    def do_ping4pair(self, _line):
        """Ping (IPv4-only) between first two hosts, useful for testing."""
        self.mn.ping4Pair()

    def do_ping6all(self, line):
        """Ping (IPv4-only) between all hosts."""
        self.mn.ping6All(line)

    def do_ping6pair(self, _line):
        """Ping (IPv6-only) between first two hosts, useful for testing."""
        self.mn.ping6Pair()

    def default(self, line):
        """Called on an input line when the command prefix is not recognized.
        Overridden to run shell commands when a node is the first CLI argument.
        Past the first CLI argument, node names are automatically replaced with
        corresponding addresses if possible.
        We select only one IP version for these automatic replacements.
        The chosen IP version chosen is first restricted by the addresses
        available on the first node.
        Then, we choose the IP version that enables every replacement.
        We use IPv4 as a tie-break."""

        first, args, line = self.parseline(line)

        if first in self.mn:
            if not args:
                lg.error("*** Enter a command for node: %s <cmd>" % first)
                return
            node = self.mn[first]
            rest = args.split(' ')

            hops = [h for h in rest if h in self.mn]
            v4_support, v6_support = address_pair(self.mn[first])
            v4_map = {}
            v6_map = {}
            for hop in hops:
                ip, ip6 = address_pair(self.mn[hop],
                                       v4_support is not None,
                                       v6_support is not None)
                if ip is not None:
                    v4_map[hop] = ip
                if ip6 is not None:
                    v6_map[hop] = ip6
            ip_map = v4_map if len(v4_map) >= len(v6_map) else v6_map

            node.sendCmd(' '.join([ip_map.get(r, r) for r in rest]))
            self.waitForNode(node)
        else:
            lg.error('*** Unknown command: %s\n' % line)
