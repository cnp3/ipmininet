Configuring a LAN
=================

By default, IPMininet uses :class:`~ipmininet.ipswitch.IPSwitch`
to create regular switches (not Openflow switches) and hubs.
The switches use the Spanning Tree Protocol by default to break the loops.
The hubs are switches that do not maintain a MAC address table and
always broadcast any received frame on all its interfaces.

Here is an example of a LAN with a few switches and one hub.

.. testcode:: lan

    from ipmininet.iptopo import IPTopo

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            # Switches
            s1 = self.addSwitch("s1")
            s2 = self.addSwitch("s2")
            s3 = self.addSwitch("s3")
            s4 = self.addSwitch("s4")

            # Hub
            hub1 = self.addHub("hub1")

            # Links
            self.addLink(s1, s2)
            self.addLink(s1, hub1)
            self.addLink(hub1, s3)
            self.addLink(hub1, s4)

            super(MyTopology, self).build(*args, **kwargs)

The Spanning Tree Protocol can be configured by changing
the ```stp_cost``` on the links (or directly on each interface).
The default cost is 1.

.. testcode:: stp

    from ipmininet.iptopo import IPTopo

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            # Switches
            s1 = self.addSwitch("s1")
            s2 = self.addSwitch("s2")
            s3 = self.addSwitch("s3")
            s4 = self.addSwitch("s4")

            # Hub
            hub1 = self.addHub("hub1")

            # Links
            self.addLink(s1, s2, stp_cost=2)  # Cost changed for both interfaces
            self.addLink(s1, hub1)
            ls3 = self.addLink(hub1, s3)
            ls3[s3].addParams(stp_cost=2)  # Cost changed on a single interface
            self.addLink(hub1, s4)

            super(MyTopology, self).build(*args, **kwargs)

In the Spanning Tree Protocol, each switch has a priority.
The lowest priority switch becomes the root of the spanning tree.
By default, switches declared first have a lower priority number.
You can manually set this value when you create the switch.

.. testcode:: stp

    from ipmininet.iptopo import IPTopo

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            # Switches with manually set STP priority
            s1 = self.addSwitch("s1", prio=1)
            s2 = self.addSwitch("s2", prio=2)
            s3 = self.addSwitch("s3", prio=3)
            s4 = self.addSwitch("s4", prio=4)

            # Hub
            hub1 = self.addHub("hub1")

            # Links
            self.addLink(s1, s2, stp_cost=2)  # Cost changed for both interfaces
            self.addLink(s1, hub1)
            ls3 = self.addLink(hub1, s3)
            ls3[s3].addParams(stp_cost=2)  # Cost changed on a single interface
            self.addLink(hub1, s4)

            super(MyTopology, self).build(*args, **kwargs)

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

