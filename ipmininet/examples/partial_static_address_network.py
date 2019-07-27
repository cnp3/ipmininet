"""This file contains a topology with statically assigned addresses on two of the LANs.
   The remaining addresses will be dynamically allocated."""

from ipmininet.iptopo import IPTopo
from ipmininet.overlay import Subnet


class PartialStaticAddressNet(IPTopo):

    def build(self, *args, **kwargs):
        """
            +----+       +----+       +----+       +----+       +----+
            | h1 +-------+ r1 +-------+ r2 +-------+ s2 +-------+ h3 |
            +----+       +--+-+       +----+       +----+       +----+
                            |
                            |         +----+       +----+
                            +---------+ s1 +-------+ h2 |
                                      +--+-+       +----+
                                         |
                                         |         +----+
                                         +---------+ h4 |
                                                   +----+
        """
        r1 = self.addRouter('r1')
        r2 = self.addRouter('r2')

        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')

        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')

        self.addLink(h1, r1)

        self.addLink(r1, r2)

        self.addLink(r1, s1)
        self.addLink(s1, h2)
        self.addLink(s1, h4)

        self.addLink(r2, s2, params1={"ip": ("192.168.1.1/24", "fc00:1::1/64")})
        self.addLink(s2, h3, params2={"ip": ("192.168.1.2/24", "fc00:1::2/64")})

        self.addOverlay(Subnet(links=[(r1, r2)],
                               subnets=["192.168.0.0/24", "fc00::/64"]))

        super(PartialStaticAddressNet, self).build(*args, **kwargs)
