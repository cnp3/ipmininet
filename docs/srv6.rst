Using IPv6 Segment Routing
==========================

IPMininet enables you to use the `Linux implementation of IPv6 Segment Routing`_
(SRv6).

.. _`Linux implementation of IPv6 Segment Routing`: https://segment-routing.org/

Using this part of IPMininet requires a recent version of the linux kernel
(see https://segment-routing.org/index.php/Implementation/Installation) for
more details.

Note that all the abstractions presented here have to be used once the
network is setup. We leverage the following method to do it:

.. automethod:: ipmininet.iptopo.IPTopo.post_build
    :noindex:

Activation
----------

By default, routers and hosts will drop packets with IPv6 Segment Routing
Header. You can enable IPv6 Segment Routing on a per-node basis with the
following function.

.. autofunction:: ipmininet.srv6.enable_srv6
    :noindex:

Here is an example of topology where IPv6 Segment Routing is enabled on all
hosts and routers:

.. testcode:: srv6activate

    from ipmininet.iptopo import IPTopo
    from ipmininet.srv6 import enable_srv6


    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):
            r1 = self.addRouter("r1")
            r2 = self.addRouter("r2")
            h1 = self.addHost("h1")
            h2 = self.addHost("h2")

            self.addLink(r1, r2)
            self.addLink(r1, h1)
            self.addLink(r2, h2)

            super().build(*args, **kwargs)

        def post_build(self, net):
            for n in net.hosts + net.routers:
                enable_srv6(n)
            super().post_build(net)


Using any of the following SRv6 abstractions also enables SRv6 on all hosts and
routers.


Insertion and encapsulation
---------------------------

The following abstraction enables you to insert or
encapsulate SRH in your packets based on the destination.

.. automethod:: ipmininet.srv6.SRv6Encap.__init__
    :noindex:

.. testcode:: srv6encapsulation

    from ipmininet.iptopo import IPTopo
    from ipmininet.srv6 import SRv6Encap


    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):
            r1 = self.addRouter("r1")
            r2 = self.addRouter("r2")
            h1 = self.addHost("h1")
            h2 = self.addHost("h2")

            self.addLink(r1, r2)
            self.addLink(r1, h1)
            self.addLink(r2, h2)

            super().build(*args, **kwargs)

        def post_build(self, net):
            # No need to enable SRv6 because the call to the abstraction
            # triggers it

            # This adds an SRH encapsulation route on h1 for packets to h2
            SRv6Encap(net=net, node=net["h1"], to=net["h2"],
                      # You can specify the intermediate point with any
                      # of the host, interface or the address itself
                      through=[net["r1"], net["r1"].intf("lo"),
                               net["r1"].intf("lo").ip6],
                      # Either insertion (INLINE) or encapsulation (ENCAP)
                      mode=SRv6Encap.INLINE)
            super().post_build(net)


Advanced configuration
----------------------

The advanced processing of SRv6-enabled packets detailed in
https://segment-routing.org/index.php/Implementation/AdvancedConf is also
supported by IPMininet with the following abstractions:

.. automethod:: ipmininet.srv6.SRv6EndFunction.__init__
    :noindex:

.. automethod:: ipmininet.srv6.SRv6EndXFunction.__init__
    :noindex:

.. automethod:: ipmininet.srv6.SRv6EndTFunction.__init__
    :noindex:

.. automethod:: ipmininet.srv6.SRv6EndDX2Function.__init__
    :noindex:

.. automethod:: ipmininet.srv6.SRv6EndDX6Function.__init__
    :noindex:

.. automethod:: ipmininet.srv6.SRv6EndDX4Function.__init__
    :noindex:

.. automethod:: ipmininet.srv6.SRv6EndDT6Function.__init__
    :noindex:

.. automethod:: ipmininet.srv6.SRv6EndB6Function.__init__
    :noindex:

.. automethod:: ipmininet.srv6.SRv6EndB6EncapsFunction.__init__
    :noindex:

They are used in the same way as SRv6Encap in the previous section.
You can instantiate any of these classes to make add the corresponding route
to your network.

However, these special routes are supposed to be in a separate tables, called
a Local SID table so that we can split plain routing and SRH management.
To create this new table in a router, you can instantiate the following class:

.. automethod:: ipmininet.srv6.LocalSIDTable.__init__
    :noindex:

This LocalSIDTable instance can then be used to instantiate the previous
classes to insert the routes in this table instead of the default one.

.. testcode:: srv6functions

    from ipmininet.iptopo import IPTopo
    from ipmininet.srv6 import SRv6Encap, SRv6EndFunction, LocalSIDTable


    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):
            r1 = self.addRouter("r1")
            r2 = self.addRouter("r2", lo_addresses="2042:2:2::1/64")
            h1 = self.addHost("h1")
            h2 = self.addHost("h2")

            self.addLink(r1, r2)
            self.addLink(r1, h1)
            self.addLink(r2, h2)

            super().build(*args, **kwargs)

        def post_build(self, net):
            # No need to enable SRv6 because the call to the abstraction
            # triggers it

            # This adds an SRH encapsulation route on h1 for packets to h2
            SRv6Encap(net=net, node=net["h1"], to=net["h2"],
                      # You can specify the intermediate point with any
                      # of the host, interface or the address itself
                      through=[net["r1"], net["r1"].intf("lo"),
                               net["r1"].intf("lo").ip6, "2042:2:2::200"],
                      # Either insertion (INLINE) or encapsulation (ENCAP)
                      mode=SRv6Encap.INLINE)

            # Creates a LocalSIDTable table handling all traffic for
            # 2042:2:2::/64 (except 2042:2:2::1 which is the loopback address)
            sid_table = LocalSIDTable(net["r2"], matching=["2042:2:2::/64"])

            # Receiving a packet on r2 with "2042:2:2::200" as active segment
            # will trigger the function 'End' which is regular SRH processing
            SRv6EndFunction(net=net, node=net["r2"], to="2042:2:2::200",
                            table=sid_table)

            super().post_build(net)


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
