import functools
from typing import Union, Type, Dict, Optional

from ipmininet.router.config.base import Daemon, NodeConfig, RouterConfig
from ipmininet.router.config import BasicRouterConfig, OpenrDaemon, Openr, \
    OpenrRouterConfig
from ipmininet.host.config import HostConfig


class NodeDescription(str):
    def __new__(cls, value, *args, **kwargs):
        return super().__new__(cls, value)

    def __init__(self, o, topo: Optional['IPTopo'] = None):
        self.topo = topo
        self.node = o
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
        super().addDaemon(daemon,
                          default_cfg_class=default_cfg_class,
                          **kwargs)


class OpenrRouterDescription(RouterDescription):
    def addOpenrDaemon(
            self,
            daemon: Union[OpenrDaemon, Type[OpenrDaemon]] = Openr,
            default_cfg_class: Type[OpenrRouterConfig] = OpenrRouterConfig,
            **kwargs
    ):
        self.addDaemon(daemon,
                       default_cfg_class=default_cfg_class,
                       **kwargs)


class HostDescription(NodeDescription):
    def addDaemon(self, daemon: Union[Daemon, Type[Daemon]],
                  default_cfg_class: Type[HostConfig] = HostConfig, **kwargs):
        super().addDaemon(daemon,
                          default_cfg_class=default_cfg_class,
                          **kwargs)


@functools.total_ordering
class LinkDescription:
    def __init__(self,
                 topo: 'IPTopo',
                 src: str,
                 dst: str,
                 key,
                 link_attrs: Dict):
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
    def __init__(self, o: str, topo: 'IPTopo', link: LinkDescription,
                 intf_attrs: Dict):
        self.link = link
        self.intf_attrs = intf_attrs
        super().__init__(o, topo)

    def addParams(self, **kwargs):
        self.intf_attrs.update(kwargs)

    def __hash__(self):
        return self.node.__hash__()

    def __eq__(self, other):
        return self.node.__eq__(other)
