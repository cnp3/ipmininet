Getting started
===============

To start your network, you need to do two things:

1. Creating a topology
2. Running the network

Topology creation
-----------------

To create a new topology, we need to declare a class
that extends ``IPTopo``.

.. code-block:: python

    from ipmininet.iptopo import IPTopo

    class MyTopology(IPTopo):
        pass

Then we extend in its build method to add switches, hosts,
routers and links between the nodes.

.. testcode:: topo creation

    from ipmininet.iptopo import IPTopo

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            r1 = self.addRouter("r1")
            r2 = self.addRouter("r2")
            # Helper to create several routers in one function call
            r3, r4, r5 = self.addRouters("r3", "r4", "r5")

            s1 = self.addSwitch("s1")
            s2 = self.addSwitch("s2")

            h1 = self.addHost("h1")
            h2 = self.addHost("h2")

            self.addLink(r1, r2)
            # Helper to create several links in one function call
            self.addLinks((s1, r1), (h1, s1), (s2, r2), (h2, s2), (r2, r3),
                          (r3, r4), (r4, r5))

            super().build(*args, **kwargs)

We can add daemons to the routers and hosts as well.

.. testcode:: topo creation addDaemon

    from ipmininet.iptopo import IPTopo
    from ipmininet.router.config import SSHd
    from ipmininet.host.config import Named

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            r1 = self.addRouter("r1")
            r1.addDaemon(SSHd)

            h1 = self.addHost("h1")
            h1.addDaemon(Named)

            # [...]

            super().build(*args, **kwargs)

By default, OSPF and OSPF6 are launched on each router.
This means that your network has basic routing working by default.
To change that, we have to modify the router configuration class.

.. testcode:: topo creation config param

    from ipmininet.iptopo import IPTopo
    from ipmininet.router.config import SSHd, RouterConfig

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            r1 = self.addRouter("r1", config=RouterConfig)
            r1.addDaemon(SSHd)

            # [...]

            super().build(*args, **kwargs)

We can customize the daemons configuration by passing options to them.
In the following code snippet, we change the hello interval of the OSPF daemon.
You can find the configuration options in :ref:`Configuring daemons`

.. testcode:: topo creation addDeamon params

    from ipmininet.iptopo import IPTopo
    from ipmininet.router.config import OSPF, RouterConfig

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            r1 = self.addRouter("r1", config=RouterConfig)
            r1.addDaemon(OSPF, hello_int=1)

            # [...]

            super().build(*args, **kwargs)


Network run
-----------

We run the topology by using the following code.
The IPCLI object creates a extended Mininet CLI.
More details can be found in :ref:`Command-Line interface`
As for Mininet, IPMininet networks need root access to be executed.

.. testcode:: network run
    :hide:

    from ipmininet.iptopo import IPTopo

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            r1 = self.addRouter("r1")
            r2 = self.addRouter("r2")

            s1 = self.addSwitch("s1")
            s2 = self.addSwitch("s2")

            h1 = self.addHost("h1")
            h2 = self.addHost("h2")

            self.addLink(r1, r2)
            self.addLink(s1, r1)
            self.addLink(h1, s1)
            self.addLink(s2, r2)
            self.addLink(h2, s2)

            super().build(*args, **kwargs)

.. testcode:: network run

    from ipmininet.ipnet import IPNet
    from ipmininet.cli import IPCLI

    net = IPNet(topo=MyTopology())
    try:
        net.start()
        IPCLI(net)
    finally:
        net.stop()

.. testoutput:: network run
    :hide:
    :options: +ELLIPSIS

    mininet> ...

.. _`Mininet CLI`: http://mininet.org/walkthrough/#part-3-mininet-command-line-interface-cli-commands

.. _getting_started_cleaning:

IPMininet network cleaning
--------------------------

If you forget to clean your network with ``net.stop()`` in your script,
your machine can will have ghost daemon process and uncleaned network namespaces.
This can also happen if IPMininet crashes.
In both cases, you have to clean it up with the following command:

.. code-block:: bash

    sudo python -m ipmininet.clean

Mininet compatibility
---------------------

IPMininet is an upper layer above Mininet.
Therefore, everything that works in Mininet, also works in IPMininet.
Feel free to consult the `Mininet documentation`_ as well.

.. _`Mininet documentation`: https://github.com/mininet/mininet/wiki/Introduction-to-Mininet


Additional helpers functions
----------------------------

You can pass parameters to ``addLinks`` and ``addRouters`` helpers.
These parameters can be common to all links and routers but they can also be
specific:

.. testcode:: topo creation addLinks addRouters

    from ipmininet.iptopo import IPTopo
    from ipmininet.router.config import RouterConfig

    class MyTopology(IPTopo):

        def build(self, *args, **kwargs):

            # The config parameter is set to RouterConfig for every router
            r1, r2 = self.addRouters("r1", "r2", config=RouterConfig)
            # The config parameter is set only for "r3"
            r3, r4, r5 = self.addRouters(("r3", {"config": RouterConfig}),
                                         "r4", "r5")

            s1 = self.addSwitch("s1")
            s2 = self.addSwitch("s2")

            h1 = self.addHost("h1")
            h2 = self.addHost("h2")

            # 'igp_metric' parameter is set to 5 for all the links while
            # the 'ip' parameter is set only for the link between 'r1' and 'r2'
            self.addLinks((r1, r2, {'ip': ("2042:12::1/64", "10.12.0.1/24")}),
                          (s1, r1), (h1, s1), (s2, r2), (h2, s2),
                          (r2, r3), (r3, r4), (r4, r5), igp_metric=5)

            super().build(*args, **kwargs)


.. doctest related functions


.. testsetup:: *

    from ipmininet.clean import cleanup
    cleanup(level='warning')

.. testcode:: topo creation,topo creation addDaemon,topo creation config param,topo creation addDeamon params,topo creation addLinks addRouters
    :hide:

    try:
        MyTopology
    except NameError:
        MyTopology = None

    if MyTopology is not None:
        from ipmininet.ipnet import IPNet
        net = IPNet(topo=MyTopology())
        net.start()

.. testcleanup:: topo creation,topo creation addDaemon,topo creation config param,topo creation addDeamon params,topo creation addLinks addRouters

    try:
        net
    except NameError:
        net = None

    if net is not None:
        net.stop()
