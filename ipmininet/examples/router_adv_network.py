"""This file contains a topology using Router Advertisements to setup IPv6
addresses and to advertise DNS server's addresses"""

from ipmininet.iptopo import IPTopo
from ipmininet.router.config import RouterConfig, RADVD, AdvConnectedPrefix,\
    AdvRDNSS


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
        r = self.addRouter('r', config=RouterConfig, use_v4=False,
                           use_v6=True)
        r.addDaemon(RADVD)
        h = self.addHost('h')
        dns = self.addHost('dns')
        lrh = self.addLink(r, h)
        lrh[r].addParams(ip=("2001:1341::1/64", "2001:2141::1/64"),
                         ra=[AdvConnectedPrefix()],
                         rdnss=[AdvRDNSS(dns)])
        lrdns = self.addLink(r, dns)
        lrdns[r].addParams(ip=("2001:89ab::1/64", "2001:cdef::1/64"))
        lrdns[dns].addParams(ip=("2001:89ab::d/64", "2001:cdef::d/64"))

        super().build(*args, **kwargs)
