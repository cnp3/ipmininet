"""This module defines topology class that supports adding L3 routers"""
import functools
import itertools
from typing import Union, Type, Dict, List, Optional, Tuple, Any

from mininet.topo import Topo
from mininet.log import lg

from ipmininet.overlay import Overlay, Subnet
from ipmininet.utils import get_set, is_container
from ipmininet.router.config import BasicRouterConfig, OSPFArea, AS,\
    iBGPFullMesh, OpenrDomain
from ipmininet.router.config.base import Daemon, RouterConfig, NodeConfig
from ipmininet.host.config import HostConfig, DNSZone
from ipmininet.ipnet import IPNet


class IPTopo(Topo):
    """A topology that supports L3 routers"""

    OVERLAYS = {cls.__name__: cls
                for cls in (AS, iBGPFullMesh, OpenrDomain, OSPFArea,
                            Subnet, DNSZone)}

    def __init__(self, *args, **kwargs):
        self.overlays = []
        self.phys_interface_capture = {}
        super().__init__(*args, **kwargs)

    def build(self, *args, **kwargs):
        for o in self.overlays:
            o.apply(self)
        for o in self.overlays:
            if not o.check_consistency(self):
                lg.error('Consistency checks for', str(o),
                         'overlay have failed!\n')
        super().build(*args, **kwargs)

    def post_build(self, net: IPNet):
        """A method that will be invoked once the topology has been fully built
        and before it is started.

        :param net: The freshly built (Mininet) network"""

    def isNodeType(self, n: str, x) -> bool:
        """Return whether node n has a key x set to True

        :param n: node name
        :param x: the key to check"""
        try:
            return self.g.node[n].get(x, False)
        except KeyError:  # node not found
            return False

    def addHost(self, name: str, **kwargs) -> 'HostDescription':
        """Add a host to the topology

           :param name: the name of the node"""
        return HostDescription(super().addHost(str(name), **kwargs), self)

    def addRouter(self, name: str, **kwargs) -> 'RouterDescription':
        """Add a router to the topology

        :param name: the name of the node"""
        return RouterDescription(self.addNode(str(name), isRouter=True,
                                              **kwargs), self)

    def addRouters(self, *routers: Union[str, Tuple[str, Dict[str, Any]]],
                   **common_opts) -> List['RouterDescription']:
        """Add several routers in one go.

        :param routers: router names or tuples (each containing the router name
            and options only applying to this router)
        :param common_opts: common router options (optional)"""
        new_routers = []
        for router_info in routers:
            # Accept either router names or tuple containing both a router name
            # and the specific options of the router
            n, opt = router_info if is_container(router_info) \
                else (router_info, {})
            # Merge router options by giving precedence to specific ones
            router_opts = {k: v
                           for k, v in itertools.chain(common_opts.items(),
                                                       opt.items())}
            try:
                new_routers.append(self.addRouter(n, **router_opts))
            except Exception as e:
                lg.error("Cannot create router '{}' with options '{}'"
                         .format(n, router_opts))
                raise e

        return new_routers

    def addLink(self, node1: str, node2: str, port1=None, port2=None,
                key=None, **opts) -> 'LinkDescription':
        """:param node1: first node to link
           :param node2: second node to link
           :param port1: port of the first node (optional)
           :param port2: port of the second node (optional)
           :param key: a key to identify the link (optional)
           :param opts: link options (optional)
           :return: link info key"""

        # XXX When PR https://github.com/mininet/mininet/pull/895
        # is accepted, we can replace this code by a call to the
        # super() method
        if not opts and self.lopts:
            opts = self.lopts
        port1, port2 = self.addPort(node1, node2, port1, port2)
        opts = dict(opts)
        opts.update(node1=node1, node2=node2, port1=port1, port2=port2)
        key = self.g.add_edge(node1, node2, key, opts)

        # Create an abstraction to allow additional calls
        link_description = LinkDescription(self, node1, node2, key,
                                           self.linkInfo(node1, node2, key))
        return link_description

    def addLinks(self, *links: Union[Tuple[str, str],
                                     Tuple[str, str, Dict[str, Any]]],
                 **common_opts) -> List['LinkDescription']:
        """Add several links in one go.

        :param links: link description tuples, either only both node names
            or nodes names with link-specific options
        :param common_opts: common link options (optional)"""

        new_links = []
        for u, v, *opt in links:
            # Merge link options by giving precedence to specific ones
            opt = opt[0] if opt else {}
            link_opts = {k: v for k, v in itertools.chain(common_opts.items(),
                                                          opt.items())}
            try:
                new_links.append(self.addLink(u, v, **link_opts))
            except Exception as e:
                lg.error("Cannot create link between '{}' and '{}'"
                         " with options '{}'".format(u, v, link_opts))
                raise e

        return new_links

    def addDaemon(self, node: str, daemon: Union[Daemon, Type[Daemon]],
                  default_cfg_class: Type[NodeConfig] = BasicRouterConfig,
                  cfg_daemon_list="daemons", **daemon_params):
        """Add the daemon to the list of daemons to start on the router.

        :param node: node name
        :param daemon: daemon class
        :param default_cfg_class: config class to use
            if there is no configuration class defined for the router yet.
        :param cfg_daemon_list: name of the parameter containing
            the list of daemons in your config class constructor.
            For instance, RouterConfig uses 'daemons'
            but BasicRouterConfig uses 'additional_daemons'.
        :param daemon_params: all the parameters to give
            when instantiating the daemon class."""

        config = self.nodeInfo(node).setdefault("config", default_cfg_class)
        try:
            config_params = config[1]
        except (IndexError, TypeError):
            config_params = {cfg_daemon_list: []}
            self.nodeInfo(node)["config"] = (config, config_params)

        daemon_list = config_params.setdefault(cfg_daemon_list, [])
        daemon_list.append((daemon, daemon_params))

    def addHub(self, name: str, **opts) -> str:
        """Convenience method: Add hub to graph.
           name: hub name
           opts: hub options
           returns: hub name"""
        if not opts and self.sopts:
            opts = self.sopts
        result = self.addSwitch(name, stp=False, hub=True, **opts)
        return result

    def isRouter(self, n: str) -> bool:
        """Check whether the given node is a router

        :param n: node name"""
        return self.isNodeType(n, 'isRouter')

    def isHub(self, n: str) -> bool:
        """Check whether the given node is a router

        :param n: node name"""
        return self.isNodeType(n, 'hub')

    def hosts(self, sort=True) -> List['HostDescription']:
        # The list is already sorted, simply filter out the routers
        return [h for h in super().hosts(sort)
                if not self.isRouter(h)]

    def routers(self, sort=True) -> List['RouterDescription']:
        """Return a list of router node names"""
        return [RouterDescription(n, self)
                for n in self.nodes(sort) if self.isRouter(n)]

    def hubs(self, sort=True) -> List[str]:
        """Return a list of hub node names"""
        return [n for n in self.nodes(sort) if self.isHub(n)]

    def addOverlay(self, overlay: Union[Overlay, Type[Overlay]]):
        """Add a new overlay on this topology"""
        if not isinstance(overlay, Overlay) and issubclass(overlay, Overlay):
            overlay = overlay()
        self.overlays.append(overlay)

    def __getattr__(self, item):
        if item.startswith('add'):
            try:
                return OverlayWrapper(self, self.OVERLAYS[item[3:]])
            except KeyError:
                pass
        raise AttributeError('%s is neither a method of IPTopo'
                             ' nor refers to any known overlay' % item)

    def getNodeInfo(self, n: str, key, default: Type):
        """Attempt to retrieve the information for the given node/key
        combination. If not found, set to an instance of default and return
        it"""
        return get_set(self.nodeInfo(n), key, default)

    def getLinkInfo(self, link: 'LinkDescription', key, default: Type):
        """Attempt to retrieve the information for the given link/key
        combination. If not found, set to an instance of default and return
        it"""
        return get_set(self.linkInfo(link[0], link[1]), key, default)

    def capture_physical_interface(self, intfname: str, node: str):
        """Adds a pre-existing physical interface to the given node."""
        self.phys_interface_capture[intfname] = node


class OverlayWrapper:

    def __init__(self, topo: IPTopo, overlay: Type[Overlay]):
        self.topo = topo
        self.overlay = overlay

    def __call__(self, *args, **kwargs):
        return self.topo.addOverlay(self.overlay(*args, **kwargs))


class NodeDescription(str):

    def __new__(cls, value, *args, **kwargs):
        return super().__new__(cls, value)

    def __init__(self, o, topo: Optional[IPTopo] = None):
        self.topo = topo
        super().__init__()

    def addDaemon(self, daemon: Union[Daemon, Type[Daemon]],
                  default_cfg_class: Type[NodeConfig] = BasicRouterConfig,
                  cfg_daemon_list="daemons", **daemon_params):
        """Add the daemon to the list of daemons to start on the node.

        :param daemon: daemon class
        :param default_cfg_class: config class to use
            if there is no configuration class defined for the router yet.
        :param cfg_daemon_list: name of the parameter containing
            the list of daemons in your config class constructor.
            For instance, RouterConfig uses 'daemons'
            but BasicRouterConfig uses 'additional_daemons'.
        :param daemon_params: all the parameters to give
            when instantiating the daemon class."""
        if self.topo is None:
            return
        self.topo.addDaemon(self, daemon, default_cfg_class=default_cfg_class,
                            cfg_daemon_list=cfg_daemon_list, **daemon_params)

    def get_config(self, daemon: Union[Daemon, Type[Daemon]], **kwargs):
        if self.topo is None:
            return
        return daemon.get_config(topo=self.topo, node=self, **kwargs)


class RouterDescription(NodeDescription):
    def addDaemon(self, daemon: Union[Daemon, Type[Daemon]],
                  default_cfg_class: Type[RouterConfig] = BasicRouterConfig,
                  **kwargs):
        super(RouterDescription, self)\
            .addDaemon(daemon, default_cfg_class=default_cfg_class, **kwargs)


class HostDescription(NodeDescription):

    def addDaemon(self, daemon: Union[Daemon, Type[Daemon]],
                  default_cfg_class: Type[HostConfig] = HostConfig, **kwargs):
        super(HostDescription, self)\
            .addDaemon(daemon, default_cfg_class=default_cfg_class, **kwargs)


@functools.total_ordering
class LinkDescription:

    def __init__(self, topo: IPTopo, src: str, dst: str, key, link_attrs: Dict):
        self.src = src
        self.dst = dst
        self.key = key
        self.link_attrs = link_attrs
        self.src_intf = IntfDescription(self.src, topo, self,
                                        self.link_attrs.setdefault("params1",
                                                                   {}))
        self.dst_intf = IntfDescription(self.dst, topo, self,
                                        self.link_attrs.setdefault("params2",
                                                                   {}))
        super().__init__()

    def __getitem__(self, item):
        if isinstance(item, int):
            if item == 0:
                return self.src_intf
            if item == 1:
                return self.dst_intf
            if item == 3:
                return self.key
            raise IndexError("Links have only two nodes and one key")

        if item == self.src:
            return self.src_intf
        if item == self.dst:
            return self.dst_intf
        raise KeyError("Node '%s' is not on this link" % item)

    # The following methods allow this object to behave like an edge key
    # for mininet.topo.MultiGraph

    def __hash__(self):
        return self.key.__hash__()

    def __eq__(self, other):
        return self.key == other

    def __lt__(self, other):
        return self.key.__lt__(other)


class IntfDescription(NodeDescription):

    def __init__(self, o: str, topo: IPTopo, link: LinkDescription,
                 intf_attrs: Dict):
        self.link = link
        self.node = o
        self.intf_attrs = intf_attrs
        super().__init__(o, topo)

    def addParams(self, **kwargs):
        self.intf_attrs.update(kwargs)

    def __hash__(self):
        return self.node.__hash__()

    def __eq__(self, other):
        return self.node.__eq__(other)
