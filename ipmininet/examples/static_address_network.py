"""This file contains a topology with statically assigned addresses"""

from ipmininet.iptopo import IPTopo


class StaticAddressNet(IPTopo):

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
        r1 = self.addRouter('r1', lo_addresses=["2042:1::1/64", "10.1.1.1/24"])
        r2 = self.addRouter('r2', lo_addresses=["2042:2::1/64", "10.2.2.1/24"])

        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')

        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')

        _, lr1r2, _, _, _, lr2s2, ls2h3 = \
            self.addLinks((h1, r1), (r1, r2), (r1, s1), (s1, h2), (s1, h4),
                          (r2, s2), (s2, h3))

        # IP addresses can be set with interface parameters
        lr2s2[r2].addParams(ip=("10.0.3.1/24", "2001:3c::1/64"))
        ls2h3[h3].addParams(ip=("10.0.3.2/24", "2001:3c::2/64"))

        # We can also declare the subnets on each LAN
        # We can use nodes and/or links to specify the host and router
        # interfaces requiring an address for each subnet
        self.addSubnet(nodes=[r1, h1], subnets=["10.0.0.0/24", "2001:1a::/64"])
        self.addSubnet(links=[lr1r2], subnets=["10.1.0.0/24", "2001:12::/64"])
        self.addSubnet(nodes=[r1, h2, h4],
                       subnets=["10.2.0.0/24", "2001:12b::/64"])

        super().build(*args, **kwargs)
