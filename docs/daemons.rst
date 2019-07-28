Configuring daemons
===================

We can add daemons to the routers and pass options to them.
In the following code snippet, we add BGP daemon to r1.

.. testcode:: addDaemons

    from ipmininet.iptopo import IPTopo
    from ipmininet.router.config import OSPF, OSPF6, RouterConfig

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            r1 = self.addRouter("r1", config=RouterConfig)
            r1.addDaemon(OSPF, hello_int=1)
            r1.addDaemon(OSPF6, hello_int=1)

            # [...]

            super(MyTopology, self).build(*args, **kwargs)

This page presents how to configure each daemon.


BGP
---

When adding BGP to a router with ``router.addDaemon(BGP, **kargs)``, we change the following default parameters:

.. automethod:: ipmininet.router.config.bgp.BGP.set_defaults
    :noindex:

We can declare a set of routers in the same AS by using the overlay AS:

The overlay iBGPFullMesh extends the AS class and allows us to establish iBGP sessions in full mesh between BGP routers.

There are also three helper functions:

- bgp_fullmesh(topo, routers): Establish a full-mesh set of BGP peerings between routers
- bgp_peering(topo, r1, r2): Register a BGP peering between two routers
- ebgp_session(topo, r1, r2): Register an eBGP peering between two routers, and disable IGP adjacencies between them

The following code shows how to use all these abstractions:

.. testcode:: bgp

    from ipmininet.iptopo import IPTopo
    from ipmininet.router.config import BGP, AS, iBGPFullMesh, bgp_fullmesh, bgp_peering, ebgp_session, RouterConfig

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            # AS1 routers
            as1r1 = self.addRouter("as1r1", config=RouterConfig)
            as1r1.addDaemon(BGP)
            as1r2 = self.addRouter("as1r2", config=RouterConfig)
            as1r2.addDaemon(BGP)
            as1r3 = self.addRouter("as1r3", config=RouterConfig)
            as1r3.addDaemon(BGP)

            self.addLink(as1r1, as1r2)
            self.addLink(as1r1, as1r3)
            self.addLink(as1r2, as1r3)

            # AS2 routers
            as2r1 = self.addRouter("as2r1", config=RouterConfig)
            as2r1.addDaemon(BGP)
            as2r2 = self.addRouter("as2r2", config=RouterConfig)
            as2r2.addDaemon(BGP)
            as2r3 = self.addRouter("as2r3", config=RouterConfig)
            as2r3.addDaemon(BGP)

            self.addLink(as2r1, as2r2)
            self.addLink(as2r1, as2r3)
            self.addLink(as2r2, as2r3)

            # AS3 routers
            as3r1 = self.addRouter("as3r1", config=RouterConfig)
            as3r1.addDaemon(BGP)
            as3r2 = self.addRouter("as3r2", config=RouterConfig)
            as3r2.addDaemon(BGP)
            as3r3 = self.addRouter("as3r3", config=RouterConfig)
            as3r3.addDaemon(BGP)

            self.addLink(as3r1, as3r2)
            self.addLink(as3r1, as3r3)
            self.addLink(as3r2, as3r3)

            # Inter-AS links
            self.addLink(as1r1, as2r1)
            self.addLink(as2r3, as3r1)

            # AS1 is composed of 3 routers that have a full-mesh set of iBGP peering between them
            self.addOverlay(iBGPFullMesh(1, routers=[as1r1, as1r2, as1r3]))

            # AS2 only has one iBGP session between its routers
            self.addOverlay(AS(2, routers=[as2r1, as2r2, as2r3]))
            bgp_peering(self, as2r1, as2r3)

            # AS3 is also composed of 3 routers that have a full-mesh set of iBGP peering between them
            self.addOverlay(AS(3, routers=[as3r1, as3r2, as3r3]))
            bgp_fullmesh(self, [as3r1, as3r2, as3r3])

            # Establish eBGP sessions between ASes
            ebgp_session(self, as1r1, as2r1)
            ebgp_session(self, as2r3, as3r1)

            super(MyTopology, self).build(*args, **kwargs)


IPTables
--------

This is currently mainly a proxy class to generate a list of static rules to pass to iptables.
As such, see `man iptables` and `man iptables-extensions`
to see the various table names, commands, pre-existing chains, ...

It takes one parameter:

.. automethod:: ipmininet.router.config.iptables.IPTables.set_defaults
    :noindex:


IP6Tables
---------

This class is the IPv6 equivalent to IPTables.

It also takes one parameter:

.. automethod:: ipmininet.router.config.iptables.IP6Tables.set_defaults
    :noindex:


OpenR
-----

The OpenR daemon can be tuned by adding keyword arguments to ``router.addDaemon(OpenR, **kargs)``.
Here is a list of the parameters:

.. automethod:: ipmininet.router.config.openrd.OpenrDaemon._defaults
    :noindex:


OSPF
----

You can add keyword arguments to ``router.addDaemon(OSPF, **kargs)``
to change the following parameters:

.. automethod:: ipmininet.router.config.ospf.OSPF.set_defaults
    :noindex:


This daemon also uses the following interface parameters:

- igp_passive: Whether the interface is passive (default value: False)
- ospf_dead_int: Dead interval timer specific to this interface (default value: ``dead_int`` parameter)
- ospf_hello_int: Hello interval timer specific to this interface (default value: ``hello_int`` parameter)
- ospf_priority: Priority for this specific to this interface (default value: ``priority`` parameter)

OSPF uses two link parameters:

- igp_cost: The IGP cost of the link (default value: 1)
- igp_area: The OSPF area of the link (default value: '0.0.0.0')

We can pass parameters to links and interfaces when calling ``addLink()``:

.. testcode:: ospf

    from ipmininet.iptopo import IPTopo

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            # Add routers (OSPF daemon is added by default with the default config)
            router1 = self.addRouter("router1")
            router2 = self.addRouter("router2")

            # Add link
            self.addLink(router1, router2,
                         igp_cost=5, igp_area="0.0.0.1",  # Link parameters
                         params1={"ospf_dead_int": 1},    # Router1 interface parameters
                         params2={"ospf_priority": 1})    # Router2 interface parameters

            super(MyTopology, self).build(*args, **kwargs)


OSPF can use an overlay to declare with routers or links are completely in a given OSPF area.
The following code adds all the interfaces of router r1 to '0.0.0.1'
while the link between r2 and r3 is in area '0.0.0.5':

.. testcode:: ospf overlay

    from ipmininet.iptopo import IPTopo
    from ipmininet.router.config import OSPFArea

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            # Add routers (OSPF daemon is added by default with the default config)
            r1 = self.addRouter("r1")
            r2 = self.addRouter("r2")
            r3 = self.addRouter("r3")

            # Add links
            self.addLink(r1, r2)
            self.addLink(r1, r3)
            self.addLink(r2, r3)

            # Define OSPF areas
            self.addOverlay(OSPFArea('0.0.0.1', routers=[r1], links=[]))
            self.addOverlay(OSPFArea('0.0.0.5', routers=[], links=[(r2, r3)]))

            super(MyTopology, self).build(*args, **kwargs)


OSPF6
-----

OSPF6 supports the same parameters as OSPF.
It supports the following parameter:

.. automethod:: ipmininet.router.config.ospf6.OSPF6.set_defaults
    :noindex:


OSPF6 uses one link parameter:

- igp_cost: The IGP cost of the link (default value: 1)

It uses the following interface parameters:

- igp_passive: Whether the interface is passive (default value: False)
- instance_id: The number of the attached OSPF6 instance (default value: 0)
- ospf6_dead_int: Dead interval timer specific to this interface (default value: ``ospf_dead_int`` parameter)
- ospf6_hello_int: Hello interval timer specific to this interface (default value: ``ospf_hello_int`` parameter)
- ospf6_priority: Priority for this specific to this interface (default value: ``ospf_priority`` parameter)

.. testcode:: ospf6

    from ipmininet.iptopo import IPTopo

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            # Add routers (OSPF daemon is added by default with the default config)
            router1 = self.addRouter("router1")
            router2 = self.addRouter("router2")

            # Add link
            self.addLink(router1, router2,
                         igp_cost=5,                       # Link parameters
                         params1={"ospf6_dead_int": 1},    # Router1 interface parameters
                         params2={"ospf6_priority": 1})    # Router2 interface parameters

            super(MyTopology, self).build(*args, **kwargs)


PIMD
----

When adding PIMD to a router with ``router.addDaemon(PIMD, **kargs)``, we can give the following parameters:

.. automethod:: ipmininet.router.config.pimd.PIMD.set_defaults
    :noindex:


RADVD
-----

When adding RADVD to a router with ``router.addDaemon(RADVD, **kargs)``, we can give the following parameters:

.. automethod:: ipmininet.router.config.radvd.RADVD.set_defaults
    :noindex:


This daemon also uses the following interface parameters:

- ra: A list of AdvPrefix objects that describes the prefixes to advertise
- rdnss: A list of AdvRDNSS objects that describes the DNS servers to advertise

.. testcode:: radvd

    from ipmininet.iptopo import IPTopo
    from ipmininet.router.config import RADVD, AdvPrefix, AdvRDNSS

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            r = self.addRouter('r')
            r.addDaemon(RADVD, debug=0)

            h = self.addHost('h')
            dns = self.addHost('dns')

            self.addLink(r, h, params1={
                "ip": ("2001:1341::1/64", "2001:2141::1/64"),  # Static IP address
                "ra": [AdvPrefix("2001:1341::/64", valid_lifetime=86400, preferred_lifetime=14400),
                       AdvPrefix("2001:2141::/64")],
                "rdnss": [AdvRDNSS("2001:89ab::d", max_lifetime=25),
                          AdvRDNSS("2001:cdef::d", max_lifetime=25)]})
            self.addLink(r, dns,
                         params1={"ip": ("2001:89ab::1/64", "2001:cdef::1/64")},  # Static IP address
                         params2={"ip": ("2001:89ab::d/64", "2001:cdef::d/64")})  # Static IP address

            super(MyTopology, self).build(*args, **kwargs)

Instead of giving all addresses explicitly, you can use AdvConnectedPrefix() to advertise all the prefixes
of the interface. You can also give the name of the DNS server (instead of an IP address) in the AdvRDNSS constructor.

.. testcode:: radvd2

    from ipmininet.iptopo import IPTopo
    from ipmininet.router.config import RouterConfig, RADVD, AdvConnectedPrefix, AdvRDNSS

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            r = self.addRouter('r')
            r.addDaemon(RADVD, debug=0)

            h = self.addHost('h')
            dns = self.addHost('dns')

            self.addLink(r, h, params1={
                "ip": ("2001:1341::1/64", "2001:2141::1/64"),  # Static IP address
                "ra": [AdvConnectedPrefix(valid_lifetime=86400, preferred_lifetime=14400)],
                "rdnss": [AdvRDNSS(dns, max_lifetime=25)]})
            self.addLink(r, dns,
                         params1={"ip": ("2001:89ab::1/64", "2001:cdef::1/64")},  # Static IP address
                         params2={"ip": ("2001:89ab::d/64", "2001:cdef::d/64")})  # Static IP address

            super(MyTopology, self).build(*args, **kwargs)


SSHd
----

The SSHd daemon does not take any parameter.
The SSH private and public keys are randomly generated but you can retrieve their paths with the following line:

.. testcode:: sshd

    from ipmininet.router.config.sshd import KEYFILE, PUBKEY


Zebra
-----

FRRouting daemons (i.e., OSPF, OSPF6, BGP and PIMD) require this daemon and automatically trigger it.
So we only need to explicitly add it through ``router.addDaemon(Zebra, **kargs)``
if we want to change one of its parameters:

.. automethod:: ipmininet.router.config.zebra.Zebra.set_defaults
    :noindex:


.. doctest related functions


.. testsetup:: *

    from ipmininet.clean import cleanup
    cleanup()

.. testcode:: *
    :hide:

    try:
        MyTopology
    except NameError:
        MyTopology = None

    if MyTopology is not None:
        from ipmininet.ipnet import IPNet
        net = IPNet(topo=MyTopology())
        net.start()

.. testcleanup:: *

    try:
        net
    except NameError:
        net = None

    if net is not None:
        net.stop()
