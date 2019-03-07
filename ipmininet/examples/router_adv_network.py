"""This file contains a topology using Router Advertisements to setup IPv6
addresses and to advertise DNS server's addresses"""

from ipmininet.iptopo import IPTopo
from ipmininet.router.config import RouterConfig, RADVD, AdvPrefix, AdvRDNSS


class RouterAdvNet(IPTopo):

    def build(self, *args, **kwargs):
        """
                            +---+       +---+       +------------+
                            | H +-------+ R +-------+ DNS server |
                            +---+       +---+       +------------+

        Host H is attached to router R and gets its IPv6 addresses via Router
        Advertisements. The DNS server address is also advertised. Therefore,
        issuing dig(1) in Host H should trigger DNS requests towards this DNS
        server.  Note that the DNS service is not actually started and thus the
        host won't get a DNS reply.
        """
        r = self.addRouter_v6('r')
        r.addDaemon(RADVD)
        h = self.addHost('h')
        dns = self.addHost('dns')
        self.addLink(r, h, params1={
            "ip": ("2001:1341::1/64", "2001:2141::1/64"),
            "ra": [AdvPrefix("2001:1341::/64"), AdvPrefix("2001:2141::/64")],
            "rdnss": [AdvRDNSS("2001:89ab::d"), AdvRDNSS("2001:cdef::d")]})
        self.addLink(r, dns,
                     params1={"ip": ("2001:89ab::1/64", "2001:cdef::1/64")},
                     params2={"ip": ("2001:89ab::d/64", "2001:cdef::d/64")})

        super(RouterAdvNet, self).build(*args, **kwargs)

    def addRouter_v6(self, name, **kwargs):
        return self.addRouter(name, config=RouterConfig, use_v4=False, use_v6=True, **kwargs)

