Configuring daemons
===================

We can add daemons to the routers or hosts and pass options to them.
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

            super().build(*args, **kwargs)

This page presents how to configure each daemon.


BGP
---

When adding BGP to a router with ``router.addDaemon(BGP, **kargs)``, we change the following default parameters:

.. automethod:: ipmininet.router.config.bgp.BGP.set_defaults
    :noindex:

We can declare a set of routers in the same AS by using the overlay AS:

The overlay iBGPFullMesh extends the AS class and allows us to establish iBGP sessions in full mesh between BGP routers.

There are also some helper functions:

.. automethod:: ipmininet.router.config.bgp.BGPConfig.set_local_pref
    :noindex:
.. automethod:: ipmininet.router.config.bgp.BGPConfig.set_med
    :noindex:
.. automethod:: ipmininet.router.config.bgp.BGPConfig.set_community
    :noindex:
.. automethod:: ipmininet.router.config.bgp.BGPConfig.deny
    :noindex:
.. automethod:: ipmininet.router.config.bgp.BGPConfig.permit
    :noindex:
.. automethod:: ipmininet.router.config.bgp.bgp_fullmesh
    :noindex:
.. automethod:: ipmininet.router.config.bgp.bgp_peering
    :noindex:
.. automethod:: ipmininet.router.config.bgp.ebgp_session
    :noindex:
.. automethod:: ipmininet.router.config.bgp.set_rr
    :noindex:

The following code shows how to use all these abstractions:

.. testcode:: bgp

    from ipmininet.iptopo import IPTopo
    from ipmininet.router.config import BGP, bgp_fullmesh, bgp_peering, \
        ebgp_session, RouterConfig, AccessList, CommunityList

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            # AS1 routers
            as1r1, as1r2, as1r3 = self.addRouters("as1r1", "as1r2", "as1r3",
                                                  config=RouterConfig)
            as1r1.addDaemon(BGP)
            as1r2.addDaemon(BGP)
            as1r3.addDaemon(BGP)

            self.addLinks((as1r1, as1r2), (as1r1, as1r3), (as1r2, as1r3))

            # AS2 routers
            as2r1, as2r2, as2r3 = self.addRouters("as2r1", "as2r2", "as2r3",
                                                  config=RouterConfig)
            as2r1.addDaemon(BGP)
            as2r2.addDaemon(BGP)
            as2r3.addDaemon(BGP)

            self.addLinks((as2r1, as2r2), (as2r1, as2r3), (as2r2, as2r3))

            # AS3 routers
            as3r1, as3r2, as3r3 = self.addRouters("as3r1", "as3r2", "as3r3",
                                                  config=RouterConfig)
            as3r1.addDaemon(BGP)
            as3r2.addDaemon(BGP)
            as3r3.addDaemon(BGP)

            self.addLinks((as3r1, as3r2), (as3r1, as3r3), (as3r2, as3r3))

            # Inter-AS links
            self.addLinks((as1r1, as2r1), (as2r3, as3r1))

            # Add an access list to 'any'
            # This can be an IP prefix or address instead
            all_al = AccessList('all', ('any',))

            # Add a community list to as2r1
            loc_pref = CommunityList('loc-pref', '2:80')

            # as2r1 set the local pref of all the route coming from as1r1 and matching the community list community to 80
            as2r1.get_config(BGP).set_local_pref(80, from_peer=as1r1, matching=(loc_pref,))

            # as1r1 set the community of all the route sent to as2r1 and matching the access list all_al to 2:80
            as1r1.get_config(BGP).set_community('2:80', to_peer=as2r1, matching=(all_al,))

            #  as3r1 set the med of all the route coming from as2r3 and matching the access list all_al to 50
            as3r1.get_config(BGP).set_med(50, to_peer=as2r3, matching=(all_al,))

            # AS1 is composed of 3 routers that have a full-mesh set of iBGP peering between them
            self.addiBGPFullMesh(1, routers=[as1r1, as1r2, as1r3])

            # AS2 only has one iBGP session between its routers
            self.addAS(2, routers=[as2r1, as2r2, as2r3])
            bgp_peering(self, as2r1, as2r3)

            # AS3 is also composed of 3 routers that have a full-mesh set of iBGP peering between them
            self.addAS(3, routers=[as3r1, as3r2, as3r3])
            bgp_fullmesh(self, [as3r1, as3r2, as3r3])

            # Establish eBGP sessions between ASes
            ebgp_session(self, as1r1, as2r1)
            ebgp_session(self, as2r3, as3r1)

            super().build(*args, **kwargs)


IPTables
--------

This is currently mainly a proxy class to generate a list of static rules to pass to iptables.

It takes one parameter:

.. automethod:: ipmininet.router.config.iptables.IPTables.set_defaults
    :noindex:

These rules can be Rule objects with raw iptables command
As such, see `man iptables` and `man iptables-extensions`
to see the various table names, commands, pre-existing chains, ...

.. autoclass:: ipmininet.router.config.iptables.Rule
    :noindex:

In this example, only ICMP traffic will be allowed between the routers over
IPv4 as well as non-privileged TCP ports:

.. testcode:: iptables

    from ipmininet.iptopo import IPTopo
    from ipmininet.router.config import IPTables, Rule

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):
            r1 = self.addRouter('r1')
            r2 = self.addRouter('r2')
            self.addLink(r1, r2)

            ip_rules = [Rule("-P INPUT DROP"),
                        Rule("-A INPUT -p tcp -m multiport --ports 80:1024 -j "
                             "DROP"),
                        Rule("-A INPUT -p tcp -m multiport ! --ports 1480 -j "
                             "ACCEPT"),
                        Rule("-A INPUT -p icmp -j ACCEPT")]
            r1.addDaemon(IPTables, rules=ip_rules)
            r2.addDaemon(IPTables, rules=ip_rules)

            super().build(*args, **kwargs)

You can use other classes for better abstraction.
You can use the Chain class or one of its subclasses:

.. autoclass:: ipmininet.router.config.iptables.Chain
    :noindex:

.. autoclass:: ipmininet.router.config.iptables.Filter
    :noindex:

.. autoclass:: ipmininet.router.config.iptables.InputFilter
    :noindex:

.. autoclass:: ipmininet.router.config.iptables.OutputFilter
    :noindex:

.. autoclass:: ipmininet.router.config.iptables.TransitFilter
    :noindex:

Each rule in the Chain instance is a ChainRule that you can use directly or
use one of its subclasses:

.. autoclass:: ipmininet.router.config.iptables.ChainRule
    :noindex:

.. autoclass:: ipmininet.router.config.iptables.Allow
    :noindex:

.. autoclass:: ipmininet.router.config.iptables.Deny
    :noindex:

Each input value used for matching in ChainRule constructor can be negated
with the NOT class:

.. autoclass:: ipmininet.router.config.iptables.NOT
    :noindex:

This example implements the same properties as the previous one with the API.

.. testcode:: iptables2

    from ipmininet.iptopo import IPTopo
    from ipmininet.router.config import IPTables, InputFilter, NOT, \
        Deny, Allow

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):
            r1 = self.addRouter('r1')
            r2 = self.addRouter('r2')
            self.addLink(r1, r2)

            ip_rules = [InputFilter(default="DROP", rules=[
                            Deny(proto='tcp', port='80:1024'),
                            Allow(proto='tcp', port=NOT(1480)),
                            Allow(proto='icmp'),
                        ])]
            r1.addDaemon(IPTables, rules=ip_rules)
            r2.addDaemon(IPTables, rules=ip_rules)

            super().build(*args, **kwargs)

IP6Tables
---------

This class is the IPv6 equivalent to IPTables.

It also takes the same parameter (see previous section for details):

.. automethod:: ipmininet.router.config.iptables.IP6Tables.set_defaults
    :noindex:


OpenR
-----

The OpenR daemon can be tuned by adding keyword arguments to
``router.addDaemon(Openr, **kargs)``.  Here is a list of the parameters:

.. automethod:: ipmininet.router.config.openrd.OpenrDaemon._defaults
    :noindex:

At the moment IPMininet supports OpenR release `rc-20190419-11514
<https://github.com/facebook/openr/releases/tag/rc-20190419-11514>`_. This
release can be build from the script
``install/build_openr-rc-20190419-11514.sh``.

As of ``rc-20190419-11514`` the OpenR daemon creates `ZeroMQ
<https://zeromq.org>`_ sockets in ``/tmp``. Therefore, it is advisable for
networks with several OpenR daemons to isolate the ``/tmp`` folder within Linux
namespaces. ``OpenrRouter`` utilizes Mininet's ``privateDirs`` option to
provide this isolation. We can pass the ``cls`` option to ``addRouter`` to
select custom router classes:

.. testcode:: OpenR

    from ipmininet.iptopo import IPTopo
    from ipmininet.router import OpenrRouter
    from ipmininet.node_description import OpenrRouterDescription


    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):
            r1 = self.addRouter('r1',
                                cls=OpenrRouter,
                                routerDescription=OpenrRouterDescription)
            r1.addOpenrDaemon()

            r2 = self.addRouter('r2',
                                cls=OpenrRouter,
                                routerDescription=OpenrRouterDescription)
            r2.addOpenrDaemon()
            self.addLink(r1, r2)

            super().build(*args, **kwargs)


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
            router1, router2 = self.addRouters("router1", "router2")

            # Add link
            l = self.addLink(router1, router2,
                             igp_cost=5, igp_area="0.0.0.1")  # Link parameters
            l[router1].addParams(ospf_dead_int=1)             # Router1 interface parameters
            l[router2].addParams(ospf_priority=1)             # Router2 interface parameters

            super().build(*args, **kwargs)


OSPF can use an overlay to declare with routers or links are completely in a given OSPF area.
The following code adds all the interfaces of router r1 to '0.0.0.1'
while the link between r2 and r3 is in area '0.0.0.5':

.. testcode:: ospf overlay

    from ipmininet.iptopo import IPTopo

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            # Add routers (OSPF daemon is added by default with the default config)
            r1, r2, r3 = self.addRouters("r1", "r2", "r3")

            # Add links
            self.addLinks((r1, r2), (r1, r3), (r2, r3))

            # Define OSPF areas
            self.addOSPFArea('0.0.0.1', routers=[r1], links=[])
            self.addOSPFArea('0.0.0.5', routers=[], links=[(r2, r3)])

            super().build(*args, **kwargs)


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
            router1, router2 = self.addRouters("router1", "router2")

            # Add link
            l = self.addLink(router1, router2,
                             igp_cost=5)            # Link parameters
            l[router1].addParams(ospf6_dead_int=1)  # Router1 interface parameters
            l[router2].addParams(ospf6_priority=1)  # Router2 interface parameters

            super().build(*args, **kwargs)


PIMD
----

When adding PIMD to a router with ``router.addDaemon(PIMD, **kargs)``, we can give the following parameters:

.. automethod:: ipmininet.router.config.pimd.PIMD.set_defaults
    :noindex:


Named
-----

When adding Named to a host with ``host.addDaemon(Named, **kargs)``, we can give the following parameters:

.. automethod:: ipmininet.host.config.named.Named.set_defaults
    :noindex:

Named uses an overlay to declare DNS zones:

.. automethod:: ipmininet.host.config.named.DNSZone.__init__
    :noindex:

The following code will create a DNS server in dns_master and dns_slave
with one DNS zone: 'mydomain.org'. This will also create one reverse DNS zones
for both IPv4 and IPv6.

.. testcode:: named

    from ipmininet.iptopo import IPTopo
    from ipmininet.host.config import Named

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            # Add router
            r = self.addRouter("r")

            # Add hosts
            h1 = self.addHost("h1")
            h2 = self.addHost("h2")
            h3 = self.addHost("h3")
            dns_master = self.addHost("dns_master")
            dns_master.addDaemon(Named)
            dns_slave = self.addHost("dns_slave")
            dns_slave.addDaemon(Named)

            # Add links
            for h in self.hosts():
                self.addLink(r, h)

            # Define a DNS Zone
            self.addDNSZone(name="mydomain.org",
                            dns_master=dns_master,
                            dns_slaves=[dns_slave],
                            nodes=self.hosts())

            super().build(*args, **kwargs)

By default, the DNSZone will create all the NS, A and AAAA records.
If you need to change the TTL of one of these record, you can define it explicitly.

.. testcode:: named explicit record

    from ipmininet.iptopo import IPTopo
    from ipmininet.host.config import Named, NSRecord

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            # Add router
            r = self.addRouter("r")

            # Add hosts
            h1 = self.addHost("h1")
            h2 = self.addHost("h2")
            h3 = self.addHost("h3")
            dns_master = self.addHost("dns_master")
            dns_master.addDaemon(Named)
            dns_slave = self.addHost("dns_slave")
            dns_slave.addDaemon(Named)

            # Add links
            for h in self.hosts():
                self.addLink(r, h)

            # Define a DNS Zone
            records = [NSRecord("mydomain.org", dns_master, ttl=120), NSRecord("mydomain.org", dns_slave, ttl=120)]
            self.addDNSZone(name="mydomain.org",
                            dns_master=dns_master,
                            dns_slaves=[dns_slave],
                            records=records,
                            nodes=self.hosts())

            super().build(*args, **kwargs)

By default, one `reverse DNS zone <https://en.wikipedia.org/wiki/Reverse_DNS_lookup>`_
are created for all A records and another for all AAAA records. However, you may want to split
the PTR records more than two different zones. You may also want to change the default values of the zones
or their PTR records. To change this, you can declare the reverse DNS zone yourself. No need to add the
PTR records that you don't want to modify, they will be created for you and placed in the zone that you declared
if they fit in its domain name. Otherwise, another zone will be created.

.. testcode:: named explicit reverse dns

    from ipmininet.iptopo import IPTopo
    from ipmininet.host.config import Named, PTRRecord
    from ipaddress import ip_address

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            # Add router
            r = self.addRouter("r")

            # Add hosts
            h1 = self.addHost("h1")
            h2 = self.addHost("h2")
            h3 = self.addHost("h3")
            dns_master = self.addHost("dns_master")
            dns_master.addDaemon(Named)
            dns_slave = self.addHost("dns_slave")
            dns_slave.addDaemon(Named)

            # Add links
            for h in [h1, h2, dns_master, dns_slave]:
                self.addLink(r, h)
            lrh3 = self.addLink(r, h3)
            self.addSubnet(links=[lrh3], subnets=["192.168.0.0/24", "fc00::/64"])

            # Define a DNS Zone
            self.addDNSZone(name="mydomain.org",
                            dns_master=dns_master,
                            dns_slaves=[dns_slave],
                            nodes=self.hosts())

            # Change the TTL of one PTR record and the retry_time of its zone
            ptr_record = PTRRecord("fc00::2", h3 + ".mydomain.org", ttl=120)
            reverse_domain_name = ip_address("fc00::").reverse_pointer[-10:]  # keeps "f.ip6.arpa"
            self.addDNSZone(name=reverse_domain_name, dns_master=dns_master, dns_slaves=[dns_slave],
                            records=[ptr_record], ns_domain_name="mydomain.org", retry_time=8200)

            super().build(*args, **kwargs)

By default, subdomains authority is delegated to the direct child zone name
servers by copying the NS records of the child zone to the parent zone. You can
remove this behavior, by zone, by setting the parameter ``subdomain_delegation``
to ``False``. You can also delegate more zones by using the ``delegated_zones``
parameter.

By default, all DNS servers that are not root DNS servers have hints to the
root DNS servers (if the root zone is added to the topology). This behavior
can be disabled by setting the parameter ``hint_root_zone`` of ``Named`` to
``False``.

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

            lrh = self.addLink(r, h)
            lrh[r].addParams(ip=("2001:1341::1/64", "2001:2141::1/64"),
                             ra=[AdvPrefix("2001:1341::/64", valid_lifetime=86400, preferred_lifetime=14400),
                                 AdvPrefix("2001:2141::/64")],
                             rdnss=[AdvRDNSS("2001:89ab::d", max_lifetime=25),
                                    AdvRDNSS("2001:cdef::d", max_lifetime=25)])
            lrdns = self.addLink(r, dns)
            lrdns[r].addParams(ip=("2001:89ab::1/64", "2001:cdef::1/64"))    # Static IP addresses
            lrdns[dns].addParams(ip=("2001:89ab::d/64", "2001:cdef::d/64"))  # Static IP addresses

            super().build(*args, **kwargs)

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

            lrh = self.addLink(r, h)
            lrh[r].addParams(ip=("2001:1341::1/64", "2001:2141::1/64"),
                             ra=[AdvConnectedPrefix(valid_lifetime=86400, preferred_lifetime=14400)],
                             rdnss=[AdvRDNSS(dns, max_lifetime=25)])
            lrdns = self.addLink(r, dns)
            lrdns[r].addParams(ip=("2001:89ab::1/64", "2001:cdef::1/64"))    # Static IP addresses
            lrdns[dns].addParams(ip=("2001:89ab::d/64", "2001:cdef::d/64"))  # Static IP addresses

            super().build(*args, **kwargs)


RIPng
-----

When adding RIPng to a router with ``router.addDaemon(RIPng, **kargs)``, we can give the following parameters:

.. automethod:: ipmininet.router.config.ripng.RIPng.set_defaults
    :noindex:

RIPng uses one link parameter:

- igp_metric: the metric of the link (default value: 1)

We can pass parameters to links when calling addLink():

.. testcode:: ripng

    from ipmininet.iptopo import IPTopo
    from ipmininet.router.config import RIPng, RouterConfig

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):
            # We use RouterConfig to prevent OSPF6 to be run
            r1, r2 = self.addRouters("r1", "r2", config=RouterConfig)
            h1 = self.addHost("h1")
            h2 = self.addHost("h2")

            self.addLink(r1, r2, igp_metric=10)  # The IGP metric is set to 10
            self.addLinks((r1, h1), (r2, h2))

            r1.addDaemon(RIPng)
            r2.addDaemon(RIPng)

            super().build(*args, **kwargs)

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
    cleanup(level='warning')

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
