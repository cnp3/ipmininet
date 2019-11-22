"""This modules show how to add IPv6 Segment Routes on top of an existing
   network. For instance, it introduces rerouting on h1 the routing of the
   traffic to h4 through r1, r6, r5, r2, r3 and r4 instead of taking the
   shortest IGP path."""
from ipmininet.iptopo import IPTopo
from ipmininet.srv6 import SRv6Encap, SRv6EndXFunction, LocalSIDTable


class SRv6Topo(IPTopo):

    def __init__(self, *args, **kwargs):
        self.tables = {}
        super(SRv6Topo, self).__init__(*args, **kwargs)

    def build(self, *args, **kwargs):
        """
            +-----+     +-----+     +-----+     +-----+     +-----+
            | h1  +-----+ r1  +-----+ r2  +-----+ r3  +-----+ h3  |
            +-----+     +--+--+     +--+--+     +--+--+     +-----+
                         4 |         3 |         9 |
            +-----+     +--+--+     +--+--+     +--+--+     +-----+
            | h6  +-----+ r6  +-----+ r5  +-----+ r4  +-----+ h4  |
            +-----+     +-----+     +-----+     +-----+     +-----+

        """
        # Routers need to have a separate prefix for segments
        # and those representing interfaces to use SRv6 functions
        r1 = self.addRouter('r1',
                            lo_addresses=["2042:1:1::1/64", "192.168.1.1/24"])
        r2 = self.addRouter('r2',
                            lo_addresses=["2042:2:2::1/64", "192.168.2.1/24"])
        r3 = self.addRouter('r3',
                            lo_addresses=["2042:3:3::1/64", "192.168.3.1/24"])
        r4 = self.addRouter('r4',
                            lo_addresses=["2042:4:4::1/64", "192.168.4.1/24"])
        r5 = self.addRouter('r5',
                            lo_addresses=["2042:5:5::1/64", "192.168.5.1/24"])
        r6 = self.addRouter('r6',
                            lo_addresses=["2042:6:6::1/64", "192.168.6.1/24"])

        h1 = self.addHost('h1')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')
        h6 = self.addHost('h6')

        # Links to hosts
        self.addLink(h1, r1)
        self.addLink(h3, r3)
        self.addLink(h4, r4)
        self.addLink(h6, r6)

        # Links between routers
        self.addLink(r1, r2)
        self.addLink(r1, r6, igp_metric=4)
        self.addLink(r2, r5, igp_metric=3)
        self.addLink(r2, r3)
        self.addLink(r3, r4, igp_metric=9)
        self.addLink(r4, r5)
        self.addLink(r5, r6)

        super().build(*args, **kwargs)

    def post_build(self, net):
        # Adds an inline SRH on packets to h4
        SRv6Encap(net=net, node=net["h1"], to=net["h4"],
                  # You can specify the intermediate point with any of the host,
                  # interface or the address itself
                  through=[net["r6"], net["r5"].intf("lo"), "2042:3:3::34",
                           net["r4"]], mode=SRv6Encap.INLINE)

        # Every packet on r3 destined to 2042:3:3::/64 except for 2042:3:3::1
        # will trigger a lookup to the LocalSIDTable
        r3_segment_space = next(net["r3"].intf("lo").ip6s()).network
        self.tables["r3"] = LocalSIDTable(net["r3"],
                                          matching=[r3_segment_space])

        # Packets with "2042:3:3::34" as active segment on r3 will be sent
        # to r3-r4 link
        # This rule is added to the LocalSIDTable created above
        SRv6EndXFunction(net=net, node=net["r3"], to="2042:3:3::34",
                         nexthop=net["r4"].intf("r4-eth1").ip6,
                         table=self.tables["r3"])
        super().post_build(net)

    def clean(self):
        for table in self.tables.values():
            table.clean()
