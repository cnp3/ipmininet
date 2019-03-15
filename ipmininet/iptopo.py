"""This module defines topology class that supports adding L3 routers"""
from mininet.topo import Topo
from mininet.log import lg

from ipmininet.overlay import Overlay
from ipmininet.utils import get_set
from ipmininet.router.config import BasicRouterConfig


class IPTopo(Topo):
    """A topology that supports L3 routers"""

    def __init__(self, *args, **kwargs):
        self.overlays = []
        self.phys_interface_capture = {}
        super(IPTopo, self).__init__(*args, **kwargs)

    def build(self, *args, **kwargs):
        for o in self.overlays:
            o.apply(self)
        for o in self.overlays:
            if not o.check_consistency(self):
                lg.error('Consistency checks for', str(o),
                         'overlay have failed!\n')
        super(IPTopo, self).build(*args, **kwargs)

    def post_build(self, net):
        """A method that will be invoced once the topology has been fully built
        and before it is started.

        :param net: The freshly built (Mininet) network"""

    def isNodeType(self, n, x):
        """Return wether node n has a key x set to True

        :param n: node name
        :param x: the key to check"""
        try:
            return self.g.node[n].get(x, False)
        except KeyError:  # node not found
            return False

    def addRouter(self, name, **kwargs):
        """Add a router to the topology

        :param name: the name of the node"""
        return RouterDescription(self.addNode(name, isRouter=True, **kwargs), self)

    def addDaemon(self, router, daemon, default_cfg_class=BasicRouterConfig,
                  cfg_daemon_list="daemons", **daemon_params):
        """Add the daemon to the list of daemons to start on the router.

        :param router: router name
        :param daemon: daemon class
        :param default_cfg_class: config class to use
        if there is no configuration class defined for the router yet.
        :param cfg_daemon_list: name of the parameter containing
        the list of daemons in your config class constructor.
        For instance, RouterConfig uses 'daemons'
        but BasicRouterConfig uses 'additional_daemons'.
        :param daemon_params: all the parameters to give
        when instantiating the daemon class."""

        config = self.nodeInfo(router).setdefault("config", default_cfg_class)
        try:
            config_params = config[1]
        except (IndexError, TypeError):
            config_params = {cfg_daemon_list: []}
            self.nodeInfo(router)["config"] = (config, config_params)

        daemon_list = config_params.setdefault(cfg_daemon_list, [])
        daemon_list.append((daemon, daemon_params))

    def isRouter(self, n):
        """Check whether the given node is a router

        :param n: node name"""
        return self.isNodeType(n, 'isRouter')

    def hosts(self, sort=True):
        # The list is already sorted, simply filter out the routers
        return [h for h in super(IPTopo, self).hosts(sort)
                if not self.isRouter(h)]

    def routers(self, sort=True):
        """Return a list of router node names"""
        return filter(self.isRouter, self.nodes(sort))

    def addOverlay(self, overlay):
        """Add a new overlay on this topology"""
        if not isinstance(overlay, Overlay) and issubclass(overlay, Overlay):
            overlay = overlay()
        self.overlays.append(overlay)

    def getNodeInfo(self, n, key, default):
        """Attempt to retrieve the information for the given node/key
        combination. If not found, set to an instance of default and return
        it"""
        return get_set(self.nodeInfo(n), key, default)

    def getLinkInfo(self, l, key, default):
        """Attempt to retrieve the information for the given link/key
        combination. If not found, set to an instance of default and return
        it"""
        return get_set(self.linkInfo(l[0], l[1]), key, default)

    def capture_physical_interface(self, intfname, node):
        """Adds a pre-existing physical interface to the given node."""
        self.phys_interface_capture[intfname] = node


class RouterDescription(str):

    def __new__(cls, value, *args, **kwargs):
        return super(RouterDescription, cls).__new__(cls, value)

    def __init__(self, o, topo):
        self.topo = topo
        super(RouterDescription, self).__init__(o)

    def addDaemon(self, daemon, default_cfg_class=BasicRouterConfig,
                  cfg_daemon_list="daemons", **daemon_params):
        """Add the daemon to the list of daemons to start on the router.

        :param daemon: daemon class
        :param default_cfg_class: config class to use
        if there is no configuration class defined for the router yet.
        :param cfg_daemon_list: name of the parameter containing
        the list of daemons in your config class constructor.
        For instance, RouterConfig uses 'daemons'
        but BasicRouterConfig uses 'additional_daemons'.
        :param daemon_params: all the parameters to give
        when instantiating the daemon class."""

        self.topo.addDaemon(self, daemon, default_cfg_class=default_cfg_class,
                            cfg_daemon_list=cfg_daemon_list, **daemon_params)
