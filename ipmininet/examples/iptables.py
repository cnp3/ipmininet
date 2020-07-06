"""This module shows a simple network topology where routers have set
custom ip(6)table rules, aka ACLs, to control traffic destined to them
(hence why only INPUT rules are specified).

Only ICMP traffic will be allowed between the routers over
IPv4 as well as non-privileged TCP ports, whereas IPv6 traffic can only be
made of TCP traffic (regularly established, hence the use of CONNTRACK) or
ICMP6 ND/NA."""
from ipmininet.iptopo import IPTopo
from ipmininet.router.config import IPTables, IP6Tables, RouterConfig, Rule, \
    InputFilter, NOT, Deny, Allow


class IPTablesTopo(IPTopo):
    """This is a simple 2-hosts topology with custom IPTable rules."""
    def build(self, *args, **kw):
        ip_rules = [InputFilter(default="DROP", rules=[
                        Deny(proto='tcp', port='80:1024'),
                        Allow(proto='tcp', port=NOT(1480)),
                        Allow(proto='icmp'),
                    ])]
        ip6_rules = [
            Rule('-A INPUT -p icmpv6 -m icmpv6',
                 '--icmpv6-type neighbour-solicitation -j ACCEPT'),
            Rule('-A INPUT -p icmpv6 -m icmpv6 --icmpv6-type',
                 'neighbour-advertisement -j ACCEPT'),
            Rule('-A INPUT -m conntrack --ctstate RELATED,ESTABLISHED',
                 '-j ACCEPT'),
            Rule('-A INPUT -m conntrack --ctstate INVALID -j DROP'),
            Rule('-A INPUT -p tcp -m tcp --tcp-flags FIN,SYN,RST,ACK SYN',
                 '-m conntrack --ctstate NEW -j ACCEPT'),
            Rule('-A INPUT -j DROP')]
        r1 = self.addRouter('r1', config=RouterConfig)
        r2 = self.addRouter('r2', config=RouterConfig)
        self.addLink(r1, r2)
        r1.addDaemon(IPTables, rules=ip_rules)
        r1.addDaemon(IP6Tables, rules=ip6_rules)
        r2.addDaemon(IPTables, rules=ip_rules)
        r2.addDaemon(IP6Tables, rules=ip6_rules)
        super().build(*args, **kw)
