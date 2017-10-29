"""An enhanced CLI providing IP-related commands"""
from mininet.cli import CLI
from mininet.log import lg


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
        An IPv4 address will be chosen by default if any and if the network allows IPv4.
        An IPv6 address will be chosen if any and if the network allows IPv6.
        In all the other cases, the name is not replaced."""

        first, args, line = self.parseline(line)

        if first in self.mn:
            if not args:
                print("*** Enter a command for node: %s <cmd>" % first)
                return
            node = self.mn[first]
            rest = args.split(' ')
            # Substitute IP addresses for node names in command
            # If updateIP() returns None, then use node name
            if self.mn.use_v4:
                rest = [self.mn[arg].defaultIntf().updateIP() or arg
                        if arg in self.mn else arg
                        for arg in rest]
            if self.mn.use_v6:
                rest = [self.mn[arg].defaultIntf().updateIP6() or arg
                        if arg in self.mn else arg
                        for arg in rest]
            rest = ' '.join(rest)
            # Run cmd on node:
            node.sendCmd(rest)
            self.waitForNode(node)
        else:
            lg.error('*** Unknown command: %s\n' % line)
