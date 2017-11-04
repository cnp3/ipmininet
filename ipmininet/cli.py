"""An enhanced CLI providing IP-related commands"""
from mininet.cli import CLI
from mininet.log import lg

from ipmininet.utils import address_pair


class IPCLI(CLI):
    def do_route(self, line=""):
        """route destination: Print all the routes towards that destination
        for every router in the network"""
        for r in self.mn.routers:
            self.default('[%s] ip route get %s' % (r.name, line))

    def do_ip(self, line):
        """ip IP1 IP2 ...: return the node associated to the given IP"""
        for ip in line.split(' '):
            try:
                n = self.mn.node_for_ip(ip)
            except KeyError:
                n = 'unknown IP'
            finally:
                lg.info(ip, '|', n)
        lg.info('\n')

    def do_ips(self, line):
        """ips n1 n2 ...: return the ips associated to the given node name"""
        for n in line.split(' '):
            try:
                l = [itf.ip for itf in self.mn[n].intfList()]
            except KeyError:
                l = 'unknown node'
            finally:
                lg.info(n, '|', l)
        lg.info('\n')

    def default(self, line):
        """Called on an input line when the command prefix is not recognized.
        Overridden to run shell commands when a node is the first CLI argument.
        Past the first CLI argument, node names are automatically replaced with
        corresponding addresses if possible.
        We select only one IP version for these automatic replacements. The IP version
        chosen is first restricted by the addresses available on the first node.
        Then, we choose the IP version that enables every replacement.
        We use IPv4 as a tie-break."""

        first, args, line = self.parseline(line)

        if first in self.mn:
            if not args:
                print("*** Enter a command for node: %s <cmd>" % first)
                return
            node = self.mn[first]
            rest = args.split(' ')

            hops = [h for h in rest if h in self.mn]
            v4_support, v6_support = address_pair(self.mn[first])
            v4_map = {}
            v6_map = {}
            for hop in hops:
                ip, ip6 = address_pair(self.mn[hop], v4_support is not None, v6_support is not None)
                if ip is not None:
                    v4_map[hop] = ip
                if ip6 is not None:
                    v6_map[hop] = ip6
            ip_map = v4_map if len(v4_map) >= len(v6_map) else v6_map

            if len(ip_map) < len(hops):
                missing = filter(lambda h: h not in ip_map, hops)
                version = 'IPv4' if v4_support else 'IPv6'
                lg.error('*** Nodes', missing, 'have no', version, 'address! Cannot execute the command.\n')
                return

            node.sendCmd(' '.join([ip_map.get(r, r) for r in rest]))
            self.waitForNode(node)
        else:
            lg.error('*** Unknown command: %s\n' % line)
