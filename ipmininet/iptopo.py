"""This module defines topology class that supports adding L3 routers"""
from collections import defaultdict
from mininet.topo import Topo
from mininet.log import lg

from ipmininet.utils import get_set


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
        return self.addNode(name, isRouter=True, **kwargs)

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


class Overlay(object):
    """This overlay simply defines groups of nodes and links, and properties
    that are common to all of them. It then registers these properties to the
    element when apply() is called.

    Elements are referenced in the same way than for the IPTopo:
    node -> node name
    link -> (node1 name, node2 name)."""

    def __init__(self, nodes=(), links=(), nprops=None, lprops=None):
        """:param nodes: The nodes in this overlay
        :param links: the links in this overlay
        :param nprops: the properties shared by all nodes in this overlay
        :param lprops: the properties shared by all links in this overlay"""
        self.nodes = list(nodes)
        self.links = list(links)
        self.nodes_properties = {} if not nprops else nprops
        self.links_properties = {} if not lprops else lprops
        self.per_link_properties = defaultdict(dict)
        self.per_node_properties = defaultdict(dict)

    def apply(self, topo):
        """Apply the Overlay properties to the given topology"""
        # First set the common properties, then the element-specific ones
        for n in self.nodes:
            topo.nodeInfo(n).update(self.node_property(n))
        for l in self.links:
            topo.linkInfo(l[0], l[1]).update(self.link_property(l))

    def check_consistency(self, topo):
        """Check that this overlay is consistent"""
        return True

    def add_node(self, *node):
        """Add one or more nodes to this overlay"""
        self.nodes.extend(node)

    def add_link(self, *link):
        """Add one or more link to this overlay"""
        self.links.extend(link)

    def node_property(self, n):
        """Return the properties for the given node"""
        p = self.nodes_properties.copy()
        p.update(self.per_node_properties[n])
        return p

    def set_node_property(self, n, key, val):
        """Set the property of a given node"""
        self.per_node_properties[n][key] = val

    def link_property(self, l):
        """Return the properties for the given link"""
        p = self.links_properties.copy()
        p.update(self.per_link_properties[l])
        return p

    def set_link_property(self, n, key, val):
        """Set the property of a given link"""
        self.per_link_properties[n][key] = val
