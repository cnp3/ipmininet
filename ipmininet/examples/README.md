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
   - [IPTables](#iptables)
   - [GRETopo](#gretopo)
   - [SSHd](#sshd)
   - [RouterAdvNetwork](#routeradvnetwork)
   - [SimpleOpenRNetwork](#simpleopenrnetwork)
   - [StaticAddressNetwork](#staticaddressnetwork)
   - [PartialStaticAddressNet](#partialstaticaddressnetwork)
   - [StaticRoutingNet](#staticroutingnet)
   - [StaticRoutingNetBasic](#staticroutingnetbasic)
   - [StaticRoutingNetIntermediate](#staticroutingnetintermediate)
   - [StaticRoutingNetComplex](#staticroutingnetcomplex)
   - [StaticRoutingNetFailure](#staticroutingnetfailure)
   - [SpanningTreeNet](#spanningtreenet)
   - [SpanningTreeHub](#spanningtreehub)
   - [SpanningTreeBus](#spanningtreebus)
   - [SpanningTreeIntermediate](#spanningtreeintermediate)
   - [SpanningTreeFullMesh](#spanningtreefullmesh)
   - [SpanningTreeAdjust](#spanningtreeadjust)


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
   - AS3 has one eBGP peerin with AS2


## BGPDecisionProcess

_topo name_ : bgp_decision_process
_args_ : other_cost (defaults to 5)

This network is similar to SimpleBGPNetwork. However, AS2 has more routers, and
not all of them run BGP. It attempts to show cases the effect of the IGP cost
in the BGP decision process in Quagga.

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
routes, and compare the routerids of as2r1 and as2r2 to select the path
(1.1.1.1 (as2r1) vs 1.1.1.2 (as2r2), so we select the route from as2r1).

You can observe this selection by issuing one of the following command sequence
once BGP has converged:

   - net > as2r3 ip route show 1.2.3.0/24
   - [noecho as2r3] telnet localhost bgpd > password is zebra > enable > show ip bgp 1.2.3.0/24


## IPTables

_topo name_ : iptables
_args_ : n/a

This network spawns two routers, which have custom ACLs set such that their
inbound traffic (the INPUT chains in ip(6)tables):

  - Can only be ICMP traffic over IPv4
  - Can only be (properly established) TCP over IPv6

You can test this by trying to ping(6) both routers, use nc to (try to)
exchange data over TCP, or [tracebox](http://www.tracebox.org) to send a crafted TCP
packet not part of an already established session.


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
topology. Each router has hosts attached. The `/tmp` folders are private to
isolate the unix sockets used by OpenR. The private `/var/log` directories
isolate logs.

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

## StaticRoutingNetIntermediate

_topo name_ : static_routing_network_intermediate
_args_ : n/a

This network uses static routes with zebra and static daemons.
This topology uses 6 routers. The routes are not the same as
if they were chosen by OSPF6, but a path from X to Y is the
exact opposite to the path from Y to X.

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
_args_ : n/a

This network contains a single LAN with many loops inside.
It enables the spanning tree protocol to prevent packets
from looping in the network.
