# HOW TO: document to help students (BGP)

The goal of this document is to help students using the examples about BGP. Through it, the student will learn the important commands to be able to work with the given networks to understand further these concepts of the course. The following examples/exercises are taken from the exercise sessions of the course.

## Border Gateway Protocol

BGP is used to make autonomous systems (AS) communicate. Each AS is a group of routers, and is therefore a higher level of hierarchy. Of course, each AS does not have the same strength and some are more powerfull than others. That's why, most of the time, AS use BGP to establish communication.

__Important point:__ in real life, AS can be a groupe of hundreds of even thousands of routers. Here, in the following examples/exercices, we will an AS-as-router simplification: each AS is represented by only one router. This simplification is explained by the fact that we want to focus on BGP bewteen different AS and not inside a single AS.

### Usefull commands

* `noecho <node> telnet localhost <protocol>`. This command allows you to connect to the node `<node>`, throught the protocol `<protocol>`. In our case, we use the protocol BGP, and here the nodes are simplified by AS. the __password__ to connect to the node is always the same: `zebra`. Once you are connected to the router/AS, you can use the following commands (use CTRL+D to exit the inside-the-node view):
    * `show bgp`. This command will show the BGP table of the node. This tool is very usefull, because you can see all the routes learned by the node, but what is more, you can see the prefered route by this node.

* `<node1> traceroute -6 -n <node2>`. This command will make the traceroute from `<node1>`to `<node2>`. It will be usefull to see the chosen routes by BGP for each AS, and to check if you understand correctly the protocol. The arguments `-6` is used to indicate to use IPv6 instead of IPv4 (even if, it should be automatic because IPv4 is most of the time disabled). `-n` is an argument to indicate not to try to use an inversed DNS call to get the name of the node instead of its IP address (on some laptops, not using this argument could cause to a very very long traceroute time).

* `<node> ip link set dev <interface> down|up`, where you have to choose between `up` and `down`. This command will disable (if `down`) or enable (if `up`) the interface `interface`.

### Exercices

1. The first exercice is `bgp_network_centralized`. To launch it from the terminal (once you are in the `ipmininet` directory) is

```
    sudo python3 -m ipmininet.examples --topo=bgp_network_centralized
```

This very first exercise shows a simple topology using 4 AS's, and using customer-provider and shared-cost links between them. Use the above commands to see the BGP tables, and make traceroutes to see if the paths are as you think !

2. ??????

3. ??????

4. The exercise `bgp_network_failure` shows the consequences of a link failure in the network. When you start it, all the links are working, and the BGP will converge to a stable solution. Then, try to disable a link (using the above command with interfaces) and see what happens for BGP. You can also, before disabling a link, launch an `xterm` window and see which packets are sent and received when a link happens to fail. You can also see the logs of the routers/AS, using the command `sh cat /tmp/bgpd_<node>.log` where `<node>` is the node where you want to see the log. It will show the messages sent and received, thanks to the debug option.

5. ??????