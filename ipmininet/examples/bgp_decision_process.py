"""This lab showcases step 8 in the BGP decision process in Quagga,
the IGP metric comparaison. Keep in mind that 'igp metric' is loosely defined
and as a result is simply the metric of the FIB route for the BGP nexthop.

The key factor here is that the nexthop advertized over BGP must NOT be in a
subnet directly connected to the router whose decision process we want to
analyze, as this would result in a metric of 0 since the connected routes
types as an administrative distance and a metric of 0.:"""
from ipmininet.iptopo import IPTopo
from ipmininet.router.config import BGP, ebgp_session, OSPF, RouterConfig
import ipmininet.router.config.bgp as _bgp


class BGPDecisionProcess(IPTopo):
    """This topology builds a 3-AS network exchanging BGP reachability
    information towards the same route. The final decision is thus dependent
    on the IGP cost."""
    def __init__(self, other_cost=5, *args, **kwargs):
        """:param other_cost: The cost of the link as2r3--as2r2.
                              If it is lower than 10, it will cause as 2r3
                              to use as2r2 as egress for 1.2.3.0/24 as it will
                              be cheaper than as2r1, although its router-id
                              is greater."""
        self.other_cost = int(other_cost)
        super(BGPDecisionProcess, self).__init__(*args, **kwargs)

    def build(self, *args, **kwargs):
        """
           +----------+                                   +--------+
                      |                                   |
         AS1          |                  AS2              |        AS3
                      |                                   |
                      |                  iBGP             |
    +-------+   eBGP  |  +-------+             +-------+  |  eBGP   +-------+
    | as1r1 +------------+ as2r1 +--X-as2r3-Y--+ as2r2 +------------+ as3r1 |
    +-------+         |  +-------+      OSPF   +-------+  |         +-------+
    1.2.3.0/24        |                                   |         1.2.3.0/24
                      |                                   |
                      |                                   |
         +------------+                                   +--------+
        """
        # Add all routers
        as1r1 = self.addRouter('as1r1')
        as1r1.addDaemon(BGP, address_families=(
            _bgp.AF_INET(networks=('1.2.3.0/24',)),))

        as2r1 = self.addRouter('as2r1')
        as2r1.addDaemon(BGP, routerid='1.1.1.1')
        as2r1.addDaemon(OSPF)

        as2r2 = self.addRouter('as2r2')
        as2r2.addDaemon(BGP, routerid='1.1.1.2')
        as2r2.addDaemon(OSPF)

        as2r3 = self.addRouter('as2r3')
        as2r3.addDaemon(BGP)
        as2r3.addDaemon(OSPF)

        x = self.addRouter('x')
        x.addDaemon(OSPF)

        y = self.addRouter('y')
        y.addDaemon(OSPF)

        as3r1 = self.addRouter('as3r1')
        as3r1.addDaemon(BGP, address_families=(
            _bgp.AF_INET(networks=('1.2.3.0/24',)),))

        self.addLink(as1r1, as2r1)
        self.addLink(as2r1, x, igp_metric=1)
        self.addLink(x, as2r3, igp_metric=10)
        # as2r1 has preferred routerid but higher IGP cost
        self.addLink(as2r3, y, igp_metric=1)
        self.addLink(y, as2r2, igp_metric=self.other_cost)
        self.addLink(as3r1, as2r2)
        # Set AS-ownerships
        self.addAS(1, (as1r1,))
        self.addiBGPFullMesh(2, (as2r1, as2r2, as2r3))
        self.addAS(3, (as3r1,))
        # Add eBGP peering
        ebgp_session(self, as1r1, as2r1)
        ebgp_session(self, as3r1, as2r2)
        super(BGPDecisionProcess, self).build(*args, **kwargs)

    def addRouter(self, name, **kwargs):
        return super(BGPDecisionProcess, self).addRouter(name,
                                                         config=RouterConfig,
                                                         **kwargs)
