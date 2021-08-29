Capturing traffic since network booting
=======================================

To check the routing configuration of the network, it may be useful
to capture the first messages exchanged by the network's daemon.
To do so, the capture needs to start before the network booting.

IPmininet proposes an overlay to declare a network capture directly inside the topology:

.. autoclass:: ipmininet.overlay.NetworkCapture
    :noindex:

We can add it with ``addNetworkCapture()`` method as shown in this example:

.. testcode:: networkcapture

    from ipmininet.iptopo import IPTopo
    from ipmininet.utils import realIntfList


    class MyTopology(IPTopo):
        """
           +----+                 +----+
           | r1 +-----------------+ r2 |
           +--+-+                 +-+--+
              |   +----+   +----+   |
              +---+ s1 +---+ s2 +---+
                  +----+   +----+
        """

    def build(self, *args, **kw):
        r1, r2 = self.addRouters('r1', 'r2')
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        lr1r2, _, ls1s2, _ = self.addLinks((r1, r2), (r1, s1), (s1, s2), (s2, r2))

        self.addNetworkCapture(# Capture on all the interfaces of r1 and s1
                               nodes=[r1, s1],
                               # Capture on two specific interfaces of r2 and s2
                               interfaces=[lr1r2[r2], ls1s2[s2]],
                               # The prefix of the capture filename
                               base_filename="capture",
                               # Any additional argument to give to tcpdump
                               extra_arguments="-v")
        super().build(*args, **kw)


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
