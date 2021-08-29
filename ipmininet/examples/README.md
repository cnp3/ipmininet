# Example topologies

This directory contains example topologies, you can start them using
```bash
python -m ipmininet.examples --topo=[topo_name] [--args key=val,key=val]
```
Where topo_name is the name of the topology, and args are optional arguments
for it.

The following sections will detail the topologies.

   - [SimpleOSPFNetwork](#simpleospfnetwork)
   - [SimpleBGPNetwork](#simplebgpnetwork)
   - [BGPDecisionProcess](#bgpdecisionprocess)
   - [BGPLocalPref](#bgplocalpref)
   - [BGPMED](#bgpmed)
   - [BGPRR](#bgprr)
   - [BGPFullConfig](#bgpfullconfig)
   - [BGPPolicies](#bgppolicies)
   - [BGPPoliciesAdjust](#bgppoliciesadjust)
   - [IPTables](#iptables)
   - [LinkFailure](#linkfailure)
   - [GRETopo](#gretopo)
   - [SSHd](#sshd)
   - [RouterAdvNetwork](#routeradvnetwork)
   - [SimpleOpenRNetwork](#simpleopenrnetwork)
   - [StaticAddressNetwork](#staticaddressnetwork)
   - [PartialStaticAddressNet](#partialstaticaddressnetwork)
   - [StaticRoutingNet](#staticroutingnet)
   - [StaticRoutingNetBasic](#staticroutingnetbasic)
   - [StaticRoutingNetComplex](#staticroutingnetcomplex)
   - [StaticRoutingNetFailure](#staticroutingnetfailure)
   - [SpanningTreeNet](#spanningtreenet)
   - [SpanningTreeHub](#spanningtreehub)
   - [SpanningTreeBus](#spanningtreebus)
   - [SpanningTreeIntermediate](#spanningtreeintermediate)
   - [SpanningTreeFullMesh](#spanningtreefullmesh)
   - [SpanningTreeAdjust](#spanningtreeadjust)
   - [SpanningTreeCost](#spanningtreecost)
   - [DNSNetwork](#dnsnetwork)
   - [DNSAdvancedNetwork](#dnsadvancednetwork)
   - [IPv6SegmentRouting](#ipv6segmentrouting)
   - [TCNetwork](#tcnetwork)
   - [TCAdvancedNetwork](#tcadvancednetwork)
   - [ExaBGPPrefixInjector](#exabgpprefixinjector)
   - [NetworkCapture](#networkcapture)


## SimpleOSPFNetwork

_topo name_ : simple_ospf_network
_args_ : n/a

This network spawn a single AS topology, using OSPF, with multiple areas and
variable link metrics.
From the mininet CLI, access the routers vtysh using
```bash
[noecho rx] telnet localhost [ospfd/zebra]
```
Where the noecho rx is required if you don't use a separate xterm window for
the node (via `xterm rx`), and ospfd/zebra is the name of the daemon you wish to
connect to.

## SimpleOSPFv3Network

_topo name_ : simple_ospfv3_network
_args_ : n/a

This network spawn a single AS topology, using OSPFv3, with variable link metrics.
From the mininet CLI, access the routers vtysh using
```bash
[noecho rx] telnet localhost [ospf6d/zebra]
```
Where the noecho rx is required if you don't use a separate xterm window for
the node (via `xterm rx`), and ospf6d/zebra is the name of the daemon you wish to
connect to.

## SimpleBGPNetwork

_topo name_ : simple_bgp_network
_args_ : n/a

This networks spawn ASes, exchanging reachability information.

   - AS1 has one eBGP peering with AS2
   - AS2 has 2 routers, using iBGP between them, and has two eBGP peering, one with AS1 and one with AS3
   - AS3 has one eBGP peering with AS2


## BGPDecisionProcess

_topo name_ : bgp_decision_process
_args_ : other_cost (defaults to 5)

This network is similar to SimpleBGPNetwork. However, AS2 has more routers, and
not all of them run BGP. It attempts to show cases the effect of the IGP cost
in the BGP decision process in FRRouting.

Both AS1 and AS3 advertize a router towards 1.2.3.0/24 to AS2 eBGP routers as2r1
and as2r2. These routers participate in an OSPF topology inside their AS, which
looks as follow:
as2r1 -[10]- x -[1]- as2r3 -[1]- y -[other_cost]- as2r2.
as2r1, as2r3 and as2r2 also participate in an iBGP fullmesh.

Depending on the value of [other_cost] (if it is greater or lower than 10),
as2r3 will either choose to use as2r1 or as2r2 as nexthop for 1.2.3.0/24, as
both routes are equal up to step #8 in the decision process, which is the IGP 
cost (in a loosely defined way, as it includes any route towards the BGP
nexthop). If other_cost is 10, we then arrive at step #10 to choose the best
routes, and compare the router ids of as2r1 and as2r2 to select the path
(1.1.1.1 (as2r1) vs 1.1.1.2 (as2r2), so we select the route from as2r1).

You can observe this selection by issuing one of the following command sequence
once BGP has converged:

   - net > as2r3 ip route show 1.2.3.0/24
   - [noecho as2r3] telnet localhost bgpd > password is zebra > enable > show ip bgp 1.2.3.0/24

## BGPLocalPref

_topo name_ : bgp_local_pref
_args_ : n/a

This topology is composed of two ASes connected in dual homing
with a higher local pref on one of the BGP peerings.
Thus, all the traffic coming from AS1 will go through the upper link.

## BGPMED

_topo name_ : bgp_med
_args_ : n/a

This topology is composed of two ASes connected in dual homing
with a higher MED for routes from the upper peering than the lower one.
Thus, all the traffic coming from AS1 will go through the lower link.

## BGPRR

_topo name_ : bgp_rr
_args_ : n/a

This topology is composed of five AS.
AS1 uses two router reflectors.

## BGPFullConfig

_topo name_ : bgp_full_config
_args_ : n/a

This topology is composed of two AS connected in dual homing with different local pref,
MED and communities. AS1 has one route reflector as well.

## BGPPolicies

The following topologies are built from the exercise sessions
of [CNP3 syllabus](https://www.computer-networking.info/exercises/html/).

_topo name_ : bgp_policies_1
_args_ : n/a

_topo name_ : bgp_policies_2
_args_ : n/a

_topo name_ : bgp_policies_3
_args_ : n/a

_topo name_ : bgp_policies_4
_args_ : n/a

_topo name_ : bgp_policies_5
_args_ : n/a

All of these topologies have routes exchanging BGP reachability.
They use two predefined BGP policies: shared-cost and client/provider peerings.

ASes always favor routes received from clients, then routes from shared-cost peering,
and finally, routes received from providers.
Moreover, ASes filter out routes depending on the peering type:
 - Routes learned from shared-cost are not forwarded to providers and other shared-cost peers.
 - Routes learned from providers are not forwarded to shared-cost peers and other providers.

## BGPPoliciesAdjust

The following topology is built from the exercise sessions
of [CNP3 syllabus](https://www.computer-networking.info/exercises/html/).

_topo name_ : bgp_policies_adjust
_args_ : as_start (defaults to None), as_end (defaults to None), bgp_policy (defaults to 'Share')

This network contains a topology with 5 shared-cost and 2 client-provider peerings.
Some ASes cannot reach all other ASes.
The user can add a peering to ensure connectivity.
To do so, use the topology arguments.
For instance, the following command will add a link between AS1 and AS3
and start a shared-cost BGP peering.

```bash
python -m ipmininet.examples --topo=bgp_policies_adjust --args as_start=as1r,as_end=as3r,bgp_policy=Share
```

## IPTables

_topo name_ : iptables
_args_ : n/a

This network spawns two routers, which have custom ACLs set such that their
inbound traffic (the INPUT chains in ip(6)tables):

  - Can only be ICMP traffic over IPv4 as well as non-privileged TCP ports
  - Can only be (properly established) TCP over IPv6

You can test this by trying to ping(6) both routers, use nc to (try to)
exchange data over TCP, or [tracebox](http://www.tracebox.org) to send a crafted TCP
packet not part of an already established session.

## LinkFailure

_topo name_ : failure
_args_ : n/a

This network spawns 4 routers: r1, r2 and r3 are in a full mesh and r4 is
connected to r3. Once the network is ready and launched, the script will:

1. Down links between routers given in the list of the failure plan.
2. Down two random links of the entire network
3. Randomly down one link of r1. Either the link r1 - r2 or r1 - r3

For each of these 3 scenario, the network will be rebuilt on its initial
configuration. At the end of the failure simulation, the network should be
restored back to its initial configuration.

## GRETopo

_topo name_ : gre
_args_ : n/a

This network spawns routers in a line, with two hosts attached on the ends.
A GRE Tunnel for prefix 10.0.1.0/24 is established with the two hosts (h1
having 10.0.1.1 assigned and h2 10.0.1.2).

Example tests:
* Verify connectivity, normally: h1 ping h2, over the tunnel: h1 ping 10.0.1.2
* h1 traceroute h2, h1 traceroute 10.0.1.2, should show two different routes,
  with the second one hiding the intermediate routers.

## SSHd

_topo name_ : ssh
_args_ : n/a

This network spawns two routers with an ssh daemon, an a key that is renewed at
each run.

You can try to connect by reusing the per-router ssh config, e.g.:

```bash
r1 ssh -o IdentityFile=/tmp/__ipmininet_temp_key r2
```

## RIPngNetwork

_topo name_ : ripng_network
_args_ : n/a

This network uses the RIPng daemon to ensure connectivity between hosts.
Like all FRRouting daemons, you can access the routers vtysh using, from the mininet CLI:
```bash
[noecho rx] telnet localhost 2603
```

## RIPngNetworkAdjust

_topo name_ : ripng_network_adjust
_args_ : lr1r2_cost, lr1r3_cost, lr1r5_cost, lr2r3_cost, lr2r4_cost, lr2r5_cost, lr4r5_cost

This network also uses the RIPng daemon to ensure connectivity between hosts.
Moreover, the IGP metric on each link can be customized.
For instance, the following command changes IGP cost of both the link between r1 and r2
and the link between r1 and r3 to 2:
```bash
python -m ipmininet.examples --topo=ripng_network_adjust --args lr1r2_cost=2,lr1r3_cost=2
```

## RouterAdvNetwork

_topo name_ : router_adv_network
_args_ : n/a

This network spawn a small topology with two hosts and a router.
One of these hosts uses Router Advertisements to get its IPv6 addresses
The other one's IP addresses are announced in the Router Advertisements
as the DNS server's addresses.


## SimpleOpenRNetwork

_topo name_ : simple_openr_network
_args_ : n/a

This network represents a small OpenR network connecting three routers in a Bus
topology. Each router has hosts attached. OpenR routers use private `/tmp`
folders to isolate the ZMQ sockets used by the daemon. The OpenR logs are by
default available in the host machine at `/var/tmp/log/<NODE_NAME>`.

Use
[breeze](https://github.com/facebook/openr/blob/master/openr/docs/Breeze.md) to
investigate the routing state of OpenR.

## StaticAddressNetwork

_topo name_ : static_address_network
_args_ : n/a

This network has statically assigned addresses
instead of using the IPMininet auto-allocator.

## PartialStaticAddressNetwork

_topo name_ : partial_static_address_network
_args_ : n/a

This network has some statically assigned addresses
and the others are dynamically allocated.

## StaticRoutingNet

_topo name_ : static_routing_network
_args_ : n/a

This network uses static routes with zebra and static
daemons.

## StaticRoutingNetBasic

_topo name_ : static_routing_network_basic
_args_ : n/a

This nework uses static routes with zebra and static daemons.
This topology uses only 4 routers.

## StaticRoutingNetComplex

_topo name_ : static_routing_network_complex
_args_ : n/a

This network uses static routes with zebra and static daemons.
This topology uses 6 routers. The routes are not the same
as if they were chosen by OSPF6. The path from X to Y
and its reverse path are not the same.

## StaticRoutingNetFailure

_topo name_ : static_routing_network_failure
_args_ : n/a

This network uses static routes with zebra and static
daemons. These static routes are incorrect.
They do not enable some routers to communicate with each other.

## SpanningTreeNet

_topo name_ : spanning_tree_network
_args_ : n/a

This network contains a single LAN with a loop.
It enables the spanning tree protocol to prevent packet looping in the LAN.

## SpanningTreeHub

_topo name_ : spanning_tree_hub
_args_ : n/a

This network contains a more complex LAN with many loops,
using hubs to simulate one-to-many links between switches.
It enables the spanning tree protocol to prevent packet looping in the LAN.

## SpanningTreeBus

_topo name_ : spanning_tree_bus
_args_ : n/a

This network contains a single LAN without any loop,
but using a hub to simulate a bus behavior.
It enables the spanning tree protocol to prevent packet looping in the LAN,
even if there is no loop here.

## SpanningTreeIntermediate

_topo name_ : spanning_tree_intermediate
_args_ : n/a

This network contains a single LAN with 2 loops inside.
It shows the spanning tree protocol to avoid the packets looping in the network.

## SpanningTreeFullMesh

_topo name_ : spanning_tree_full_mesh
_args_ : n/a

This network contains a single LAN with many loops inside.
It enables the spanning tree protocol to prevent packet looping in the LAN.

## SpanningTreeAdjust

_topo name_ : spannnig_tree_adjust

_args_ :
 - l1_start: Endpoint interface of the 1st link on which we want to change the cost
 - l1_end: Endpoint interface of the 1st link on which we want to change the cost
 - l1_cost: Cost to set on the first link
 - l2_start: Endpoint interface of the 2nd link on which we want to change the cost
 - l2_end: Endpoint interface of the 2nd link on which we want to change the cost
 - l2_cost: Cost to set on the second link

This network contains a single LAN with many loops inside.
It enables the spanning tree protocol to prevent packets
from looping in the network.
The arguments of this topology allows users to change the STP cost on two links.

For instance, the following command changes STP cost of the link between s6.1 and s3.4 to 2:

```bash
python -m ipmininet.examples --topo=spannnig_tree_adjust --args l1_start=s6-eth1,l1_end=s3-eth4,l1_cost=2
```

## SpanningTreeCost

_topo name_: spannnig_tree_cost
_args_ : n/a

This network contains a single LAN with one loop inside.
It enables the spanning tree protocol to prevent packet looping in the LAN.
It also changes the STP cost one link.

## DNSNetwork

_topo name_ : dns_network
_args_ : n/a

This network contains two DNS server, a master and a slave.
The domain name is 'mydomain.org' and it contains the address mapping
of all the hosts of the network.
You can query the DNS servers with, for instance, one of the following commands:

```bash
master dig @locahost -t NS mydomain.org
master dig @locahost -t AAAA server.mydomain.org
slave dig @locahost -t NS mydomain.org
slave dig @locahost -t AAAA server.mydomain.org
```

## DNSAdvancedNetwork

_topo name_ : dns_advanced_network
_args_ : n/a

This network has a full DNS architecture with root servers and zone delegation.
You can query the full tree with dig as on the
[DNSNetwork](#dnsnetwork) topology.

## IPv6SegmentRouting

_topo name_ : ipv6_segment_routing
_args_ : n/a

This networks uses [IPv6 Segment Routing](https://segment-routing.org)
to reroute traffic from h1 to h4.
You can observe that a ping and some tcpdumps or tshark that traffic
will go through r1, r6, r5, r2, r3 and r4 instead of going
through r1, r2, r5 and r4 which is the shortest path.

Note that if you cannot use tcpdump to poke behind the Segment Routing
extension headers. Hence, if you use the capture filter 'icmp6', if the
ICMPv6 header is after the SRH, you won't see capture the packet.
tshark does not have this problem.

## TCNetwork

_topo name_ : tc_network
_args_ : n/a

This network emulates delay and bandwidth constraints on the links.

Pinging between two hosts will give a latency of around 32ms.
If you use iperf3, you will notice that the bandwidth between both hosts is
throttled to 100Mbps.

## TCAdvancedNetwork

_topo name_ : tc_advanced_network
_args_ : n/a

This network emulates delay and bandwidth constraints on the links.
But it does so without falling into either tc or mininet pitfalls.
Look at IPMininet documentation for more details.

## ExaBGPPrefixInjector

_topo name_ : exabgp_prefix_injector
_args_ : n/a

This network contains two routers, as1 and as2. as1 runs ExaBGP daemon
while as2 runs FRRouting BGP daemon. as1 is responsible for injecting
custom BGP routes for both IPv4 and IPv6 unicast families to as2.

When the operation is done, as2 BGP RIB is filled with 3 IPv4 and 3
IPv6 prefixes with random BGP attributes.

## NetworkCapture

_topo name_ : network_capture
_args_ : n/a

This topology captures traffic from the network booting.
This capture the initial messages of the OSPF/OSPFv3 daemons and save the capture
on /tmp next to the logs.
