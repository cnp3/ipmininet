"""This file contains a topology with statically assigned addresses on two of
   the LANs. The remaining addresses will be dynamically allocated."""

from ipmininet.iptopo import IPTopo


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
        r1 = self.addRouter('r1', lo_addresses=["2042:1::1/64"])
        r2 = self.addRouter('r2')

        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')

        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')

        _, lr1r2, _, _, _, lr2s2, ls2h3 = self.addLinks((h1, r1), (r1, r2),
                                                        (r1, s1), (s1, h2),
                                                        (s1, h4), (r2, s2),
                                                        (s2, h3))
        lr2s2[r2].addParams(ip=("192.168.1.1/24", "fc00:1::1/64"))
        ls2h3[h3].addParams(ip=("192.168.1.2/24", "fc00:1::2/64"))

        self.addSubnet(links=[lr1r2], subnets=["192.168.0.0/24", "fc00::/64"])

        super().build(*args, **kwargs)
