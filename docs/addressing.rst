Configuring IPv4 and IPv6 networks
==================================

In Mininet, we can only use IPv4 in the emulated network.
IPMininet enables the emulation of either IPv6-only or dual-stacked networks.

Dual-stacked networks
---------------------

By default, your network is dual-stacked.
It has both IPv4 and IPv6 addresses dynamically assigned by the library.
Moreover, both OSPF and OSPF6 daemons are running on each router to ensure basic routing.

.. testcode:: dual stack dynamic

    from ipmininet.iptopo import IPTopo
    from ipmininet.ipnet import IPNet
    from ipmininet.cli import IPCLI

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            r1 = self.addRouter("r1")
            r2 = self.addRouter("r2")
            h1 = self.addHost("h1")
            h2 = self.addHost("h2")

            self.addLink(h1, r1)
            self.addLink(r1, r2)
            self.addLink(r2, h2)

            super().build(*args, **kwargs)

    net = IPNet(topo=MyTopology())
    try:
        net.start()
        IPCLI(net)
    finally:
        net.stop()

If you wait for the network to converge and execute `pingall`
in the IPMininet CLI, you will see that hosts can ping
each other in both IPv4 and IPv6.
You can also check the routes on the nodes
with `<nodename> ip [-6|-4] route`.

Single-stacked networks
-----------------------

You can choose to make a whole network only in IPv4 or in IPv6
by using one parameter in the IPNet constructor.
The two following examples show respectively an IPv4-only
and IPv6-only network.
In single stacked networks, only one of the routing daemons
(either OSPF or OSPF6) is launched.

.. testcode:: ipv4 network

    from ipmininet.iptopo import IPTopo
    from ipmininet.ipnet import IPNet
    from ipmininet.cli import IPCLI

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            r1 = self.addRouter("r1")
            r2 = self.addRouter("r2")
            h1 = self.addHost("h1")
            h2 = self.addHost("h2")

            self.addLink(h1, r1)
            self.addLink(r1, r2)
            self.addLink(r2, h2)

            super().build(*args, **kwargs)

    net = IPNet(topo=MyTopology(), use_v6=False)  # This disables IPv6
    try:
        net.start()
        IPCLI(net)
    finally:
        net.stop()

.. testcode:: ipv6 network

    from ipmininet.iptopo import IPTopo
    from ipmininet.ipnet import IPNet
    from ipmininet.cli import IPCLI

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            r1 = self.addRouter("r1")
            r2 = self.addRouter("r2")
            h1 = self.addHost("h1")
            h2 = self.addHost("h2")

            self.addLink(h1, r1)
            self.addLink(r1, r2)
            self.addLink(r2, h2)

            super().build(*args, **kwargs)

    net = IPNet(topo=MyTopology(), use_v4=False)  # This disables IPv4
    try:
        net.start()
        IPCLI(net)
    finally:
        net.stop()

Hybrids networks
----------------

In some cases, it is interesting to have only some parts of the network
with IPv6 and/or IPv4. The hosts will have IPv4 (resp. IPv6) routes
only if its access router has IPv4 (resp. IPv6) addresses.
IPv4-only (resp. IPv6-only) routers won't have
an OSPF (resp. OSPF6) daemon.

.. testcode:: hybrid network

    from ipmininet.iptopo import IPTopo
    from ipmininet.ipnet import IPNet
    from ipmininet.cli import IPCLI

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            r1 = self.addRouter("r1")
            r2 = self.addRouter("r2", use_v4=False)  # This disables IPv4 on the router
            r3 = self.addRouter("r3", use_v6=False)  # This disables IPv6 on the router
            h1 = self.addHost("h1")
            h2 = self.addHost("h2")
            h3 = self.addHost("h3")

            self.addLink(r1, r2)
            self.addLink(r1, r3)
            self.addLink(r2, r3)

            self.addLink(r1, h1)
            self.addLink(r2, h2)
            self.addLink(r3, h3)

            super().build(*args, **kwargs)

    net = IPNet(topo=MyTopology())
    try:
        net.start()
        IPCLI(net)
    finally:
        net.stop()

Static addressing
-----------------

Addresses are allocated dynamically by default
but you can set your own addresses if you disable auto-allocation
when creating the IPNet object. You can do so for both for router loopbacks
and for real interfaces of all the nodes.

.. testcode:: static addressing

    from ipmininet.iptopo import IPTopo
    from ipmininet.ipnet import IPNet
    from ipmininet.cli import IPCLI

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            r1 = self.addRouter("r1", lo_addresses=["2042:1::1/64", "10.1.0.1/24"])
            r2 = self.addRouter("r2", lo_addresses=["2042:2::1/64", "10.2.0.1/24"])
            h1 = self.addHost("h1")
            h2 = self.addHost("h2")

            lr1r2 = self.addLink(r1, r2)
            lr1r2[r1].addParams(ip=("2042:12::1/64", "10.12.0.1/24"))
            lr1r2[r2].addParams(ip=("2042:12::2/64", "10.12.0.2/24"))

            lr1h1 = self.addLink(r1, h1)
            lr1h1[r1].addParams(ip=("2042:1a::1/64", "10.51.0.1/24"))
            lr1h1[h1].addParams(ip=("2042:1a::a/64", "10.51.0.5/24"))

            lr2h2 = self.addLink(r2, h2)
            lr2h2[r2].addParams(ip=("2042:2b::2/64", "10.62.0.2/24"))
            lr2h2[h2].addParams(ip=("2042:2b::b/64", "10.62.0.6/24"))

            super().build(*args, **kwargs)

    net = IPNet(topo=MyTopology(), allocate_IPs=False)  # Disable IP auto-allocation
    try:
        net.start()
        IPCLI(net)
    finally:
        net.stop()

You can also declare your subnets by declaring a Subnet overlay.

.. testcode:: static addressing 2

    from ipmininet.iptopo import IPTopo
    from ipmininet.ipnet import IPNet
    from ipmininet.cli import IPCLI

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            r1 = self.addRouter("r1", lo_addresses=["2042:1::1/64", "10.1.0.1/24"])
            r2 = self.addRouter("r2", lo_addresses=["2042:2::1/64", "10.2.0.1/24"])
            h1 = self.addHost("h1")
            h2 = self.addHost("h2")

            lr1r2 = self.addLink(r1, r2)
            self.addLink(r1, h1)
            self.addLink(r2, h2)

            # The interfaces of the nodes and links on their common LAN
            # will get an address for each subnet.
            self.addSubnet(nodes=[r1, r2], subnets=["2042:12::/64", "10.12.0.0/24"])
            self.addSubnet(nodes=[r1, h1], subnets=["2042:1a::/64", "10.51.0.0/24"])
            self.addSubnet(links=[lr1r2],  subnets=["2042:2b::/64", "10.62.0.0/24"])

            super().build(*args, **kwargs)

    net = IPNet(topo=MyTopology(), allocate_IPs=False)  # Disable IP auto-allocation
    try:
        net.start()
        IPCLI(net)
    finally:
        net.stop()

Static routing
--------------

By default, OSPF and OSPF6 are launched on each router.
If you want to prevent that, you have to change the router configuration class.
You can change it when adding a new router to your topology.

.. testcode:: static routing

    from ipmininet.iptopo import IPTopo
    from ipmininet.router.config import RouterConfig, STATIC, StaticRoute
    from ipmininet.ipnet import IPNet
    from ipmininet.cli import IPCLI

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            # Change the config object for RouterConfig
            # because it does not add by default OSPF or OSPF6
            r1 = self.addRouter("r1", config=RouterConfig, lo_addresses=["2042:1::1/64", "10.1.0.1/24"])
            r2 = self.addRouter("r2", config=RouterConfig, lo_addresses=["2042:2::1/64", "10.2.0.1/24"])
            h1 = self.addHost("h1")
            h2 = self.addHost("h2")

            lr1r2 = self.addLink(r1, r2)
            lr1r2[r1].addParams(ip=("2042:12::1/64", "10.12.0.1/24"))
            lr1r2[r2].addParams(ip=("2042:12::2/64", "10.12.0.2/24"))

            lr1h1 = self.addLink(r1, h1)
            lr1h1[r1].addParams(ip=("2042:1a::1/64", "10.51.0.1/24"))
            lr1h1[h1].addParams(ip=("2042:1a::a/64", "10.51.0.5/24"))

            lr2h2 = self.addLink(r2, h2)
            lr2h2[r2].addParams(ip=("2042:2b::2/64", "10.62.0.2/24"))
            lr2h2[r2].addParams(ip=("2042:2b::b/64", "10.62.0.6/24"))

            # Add static routes
            r1.addDaemon(STATIC, static_routes=[StaticRoute("2042:2b::/64", "2042:12::2"),
                                                StaticRoute("10.62.0.0/24", "10.12.0.2")])
            r2.addDaemon(STATIC, static_routes=[StaticRoute("2042:1a::/64", "2042:12::1"),
                                                StaticRoute("10.51.0.0/24", "10.12.0.1")])

            super().build(*args, **kwargs)

    net = IPNet(topo=MyTopology(), allocate_IPs=False)  # Disable IP auto-allocation
    try:
        net.start()
        IPCLI(net)
    finally:
        net.stop()

You can also add routes manually when the network has started since you can run any command (like in Mininet).

.. testcode:: static routing 2
    :hide:

    from ipmininet.iptopo import IPTopo
    from ipmininet.router.config import RouterConfig, STATIC, StaticRoute
    from ipmininet.ipnet import IPNet
    from ipmininet.cli import IPCLI

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            r1 = self.addRouter("r1", config=RouterConfig, lo_addresses=["2042:1::1/64", "10.1.0.1/24"])
            r2 = self.addRouter("r2", config=RouterConfig, lo_addresses=["2042:2::1/64", "10.2.0.1/24"])
            h1 = self.addHost("h1")
            h2 = self.addHost("h2")

            lr1r2 = self.addLink(r1, r2)
            lr1r2[r1].addParams(ip=("2042:12::1/64", "10.12.0.1/24"))
            lr1r2[r2].addParams(ip=("2042:12::2/64", "10.12.0.2/24"))

            lr1h1 = self.addLink(r1, h1)
            lr1h1[r1].addParams(ip=("2042:1a::1/64", "10.51.0.1/24"))
            lr1h1[h1].addParams(ip=("2042:1a::a/64", "10.51.0.5/24"))

            lr2h2 = self.addLink(r2, h2)
            lr2h2[r2].addParams(ip=("2042:2b::2/64", "10.62.0.2/24"))
            lr2h2[r2].addParams(ip=("2042:2b::b/64", "10.62.0.6/24"))

            # Add static routes
            r1.addDaemon(STATIC, static_routes=[StaticRoute("2042:2b::/64", "2042:12::2"),
                                                StaticRoute("10.62.0.0/24", "10.12.0.2")])
            r2.addDaemon(STATIC, static_routes=[StaticRoute("2042:1a::/64", "2042:12::1"),
                                                StaticRoute("10.51.0.0/24", "10.12.0.1")])

            super().build(*args, **kwargs)

.. testcode:: static routing 2

    net = IPNet(topo=MyTopology(), allocate_IPs=False)  # Disable IP auto-allocation
    try:
        net.start()

        # Static routes
        net["r1"].cmd("ip -6 route add 2042:2b::/64 via 2042:12::2")
        net["r1"].cmd("ip -4 route add 10.62.0.0/24 via 10.12.0.2")
        net["r2"].cmd("ip -6 route add 2042:1a::/64 via 2042:12::1")
        net["r2"].cmd("ip -4 route add 10.51.0.0/24 via 10.12.0.1")

        IPCLI(net)
    finally:
        net.stop()

.. doctest related functions

.. testsetup:: *

    from ipmininet.clean import cleanup
    cleanup(level='warning')

    mocking = MockStdIn()
    mocking.close_on_start_cli()

.. testcleanup:: *

    mocking.clean()

.. testoutput:: *
    :hide:
    :options: +ELLIPSIS

    mininet> ...
