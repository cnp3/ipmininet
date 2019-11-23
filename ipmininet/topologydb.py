"""This module defines a data-store to help dealing with all (possibly)
auto-allocated properties of a topology: ip addresses, router ids, ..."""
from builtins import str

import json
import itertools
from ipaddress import ip_interface

from .utils import otherIntf, realIntfList

from mininet.log import lg


class TopologyDB(object):
    """A convenience store for auto-allocated mininet properties.
    This is *NOT* to be used as IGP graph as it does not reflect the actual
    availability of a node in the network (as-in it is a static view of
    the network)."""
    def __init__(self, db=None, net=None, *args, **kwargs):
        """Either extract properties from a network or load a save file

        :param db: a path towards a saved version of this class which will
                        be loaded
        :param net: an IPNet instance which will be parsed in order to extract
                    useful properties
        """
        super(TopologyDB, self).__init__(*args, **kwargs)
        # dict keyed by node name ->
        #     dict keyed by - properties -> val
        #                   - neighbor   -> interface properties"""
        self._network = {}
        if db:
            self.load(db)
        if net:
            self.parse_net(net)
        if not db and not net:
            lg.warning('TopologyDB instantiated without any data')

    def load(self, fpath):
        """Load a topology database

        :param fpath: path towards the file to load"""
        with open(fpath, 'r') as f:
            self._network = json.load(f)

    def save(self, fpath):
        """Save the topology database

        :param fpath: the save file name"""
        with open(fpath, 'w') as f:
            json.dump(self._network, f)

    def _node(self, x):
        try:
            return self._network[x]
        except KeyError:
            raise ValueError('No node named %s in the network' % x)
    __getitem__ = node = _node

    def _interface(self, x, y):
        try:
            return self._node(x)[y]
        except KeyError:
            raise ValueError('The link %s-%s does not exist' % (x, y))

    def interface(self, x, y):
        """Return the ip address of the interface of x facing y

        :param x: the node from which we want an IP address
        :param y: the node on the other side of the link
        :return: ip_interface-like object"""
        return ip_interface(str(self._interface(x, y)['ip']))

    def interfaces(self, x):
        """Return the list of interface names of node x"""
        return self._node(x)['interfaces']

    def interface_bandwidth(self, x, y):
        """Return the bandwidth capacity of the interface on node x
        facing node y.

        :param x: node name
        :param y: node name
        :return: The bandwidth of link x-y, -1 if unlimited"""
        try:
            return self._interface(x, y)['bw']
        except KeyError:
            return -1

    def subnet(self, x, y):
        """Return the subnet linking node x and y

        :param x: node name
        :param y: node name
        :return: ip_network-like object"""
        return self.interface(x, y).network

    def routerid(self, x):
        """Return the router id of a node

        :param x: router name
        :return: the routerid"""
        n = self._node(x)
        if n['type'] != 'router':
            raise TypeError('%s is not a router' % x)
        return n['routerid']

    def parse_net(self, net):
        """Stores the content of the given network

        :param net: IPNet instance"""
        for h in net.hosts:
            self.add_host(h)
        for s in net.switches:
            self.add_switch(s)
        for r in net.routers:
            self.add_router(r)

    def _add_node(self, n, props):
        itfs = realIntfList(n)
        props['interfaces'] = [itf.name for itf in itfs]
        for itf in itfs:
            nh = otherIntf(itf)
            itf_props = {
                'ip': '%s/%s' % (itf.ip, itf.prefixLen),
                'ips': [ip.with_prefixlen
                        for ip in itertools.chain(itf.ips(), itf.ip6s())],
                'name': itf.name,
                'bw': itf.params.get('bw', -1)
            }
            if nh:
                props[nh.node.name] = itf_props
            props[itf.name] = itf_props
        self._network[n.name] = props

    def add_host(self, n):
        """Register an host

        :param n: Host instance"""
        self._add_node(n, {'type': 'host'})

    def add_switch(self, n):
        """Register an switch

        :param n: Switch instance"""
        self._add_node(n, {'type': 'switch'})

    def add_router(self, n):
        """Register an router

        :param n: Router instance"""
        self._add_node(n, {'type': 'router', })
        # FIXME make routerid global accross all daemons
        #                  'routerid': n.id})
