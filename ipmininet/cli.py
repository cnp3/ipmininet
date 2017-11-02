"""An enhanced CLI providing IP-related commands"""
from mininet.cli import CLI
from mininet.log import lg

from ipmininet.utils import realIntfList


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
        Then, we choose the IP version that enables as many replacements as possible.
        We use IPv4 as a tie-break."""

        first, args, line = self.parseline(line)

        if first in self.mn:
            if not args:
                print("*** Enter a command for node: %s <cmd>" % first)
                return
            node = self.mn[first]
            rest = args.split(' ')

            # Identify which IP protocols can be used by the node on which the command is issued
            first_v4 = False
            first_v6 = False
            for itf in realIntfList(node):
                if itf.updateIP() is not None:
                    first_v4 = True
                itf.updateIP6()
                for _ in itf.ip6s(exclude_lls=True):
                    first_v6 = True
                    break

            # Identify the possible substitutions
            ipv4_map = {}
            ipv6_map = {}
            for r in rest:
                if r in self.mn:
                    other_node = self.mn[r]
                    for itf in realIntfList(other_node):
                        if first_v4 and itf.updateIP() is not None:
                            ipv4_map[r] = itf.ip
                        if first_v6:
                            itf.updateIP6()
                            for ip6 in itf.ip6s(exclude_lls=True):
                                ipv6_map[r] = str(ip6.ip)
                                break

            ip_map = ipv4_map if len(ipv4_map) >= len(ipv6_map) else ipv6_map

            # Substitute IP addresses for node names in command
            rest = [ip_map[arg] if arg in ip_map else arg for arg in rest]
            rest = ' '.join(rest)

            # Run cmd on node
            node.sendCmd(rest)
            self.waitForNode(node)
        else:
            lg.error('*** Unknown command: %s\n' % line)
