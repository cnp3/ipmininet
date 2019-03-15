from collections import defaultdict


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
