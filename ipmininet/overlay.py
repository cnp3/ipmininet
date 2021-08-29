import os
import shlex
import signal
import subprocess
from collections import defaultdict
from builtins import str
from subprocess import Popen
from typing import List, Sequence, Tuple, Optional, Dict, TYPE_CHECKING, Any, \
    Mapping

from ipaddress import ip_network
from mininet.log import lg

if TYPE_CHECKING:
    from ipmininet.iptopo import IPTopo
    from ipmininet.link import IPIntf
    from ipmininet.node_description import IntfDescription, NodeDescription
    from ipmininet.router import IPNode


class Overlay:
    """This overlay simply defines groups of nodes and links, and properties
    that are common to all of them. It then registers these properties to the
    element when apply() is called.

    Elements are referenced in the same way than for the IPTopo:
    node -> node name
    link -> (node1 name, node2 name)."""

    def __init__(self, nodes: Sequence[str] = (),
                 links: Sequence[str] = (), nprops: Optional[Dict] = None,
                 lprops: Optional[Dict] = None):
        """:param nodes: The nodes in this overlay
        :param links: the links in this overlay
        :param nprops: the properties shared by all nodes in this overlay
        :param lprops: the properties shared by all links in this overlay"""
        self.nodes = list(nodes)
        self.links = list(links)
        self.nodes_properties = {} if not nprops else nprops
        self.links_properties = {} if not lprops else lprops
        self.per_link_properties = defaultdict(dict)  # type: Mapping
        self.per_node_properties = defaultdict(dict)  # type: Mapping

    def apply(self, topo: 'IPTopo'):
        """Apply the Overlay properties to the given topology"""
        # First set the common properties, then the element-specific ones
        for n in self.nodes:
            topo.nodeInfo(n).update(self.node_property(n))
        for l in self.links:
            topo.linkInfo(l[0], l[1]).update(self.link_property(l))

    def check_consistency(self, topo: 'IPTopo') -> bool:
        """Check that this overlay is consistent"""
        return True

    def add_node(self, *node: str):
        """Add one or more nodes to this overlay"""
        self.nodes.extend(node)

    def add_link(self, *link: str):
        """Add one or more link to this overlay"""
        self.links.extend(link)

    def node_property(self, n: str) -> Dict:
        """Return the properties for the given node"""
        p = self.nodes_properties.copy()
        p.update(self.per_node_properties[n])
        return p

    def set_node_property(self, n: str, key, val):
        """Set the property of a given node"""
        self.per_node_properties[n][key] = val

    def link_property(self, link: str) -> Dict:
        """Return the properties for the given link"""
        p = self.links_properties.copy()
        p.update(self.per_link_properties[link])
        return p

    def set_link_property(self, link: str, key, val):
        """Set the property of a given link"""
        self.per_link_properties[link][key] = val


class Subnet(Overlay):
    """This overlay simply defines groups of routers and hosts that share
    a common set of subnets. These routers and hosts have to be on the same LAN.
    """

    def __init__(self, nodes=(), links=(), subnets=()):
        """
        :param nodes: The routers and hosts that needs an address on their
                      common LAN.
        :param links: The links that has to be in the LAN. This parameter
                      is useful to identify LANs if there is more than one
                      common LAN between the nodes. Routers and Hosts of the
                      links will have an address assigned.
        :param subnets: For each subnet, an address will be added to the
                        interface of the nodes in their common LAN.
        """
        self.subnets = subnets
        self.node_links = {}
        self.consistent = True

        super().__init__(nodes=nodes, links=links)

    def check_consistency(self, topo):
        return super().check_consistency(topo) and self.consistent

    def apply(self, topo):
        super().apply(topo)

        self.nodes = list(self.nodes)
        for x, y in self.links:
            if not topo.isSwitch(x):
                self.nodes.append(x)
            if not topo.isSwitch(y):
                self.nodes.append(y)

        if not self._check_subnets() \
                or not self._find_nodes_in_lan(topo, self.nodes):
            self.consistent = False
            return

        for subnet_str in self.subnets:
            subnet = ip_network(str(subnet_str))
            for i, node in enumerate(self.nodes):
                for value in self.node_links[node]:
                    attrs = value

                    addr = '%s/%d' % (subnet[i+1], subnet.prefixlen)
                    addrs = tuple(attrs.get("ip", tuple()))
                    attrs["ip"] = addrs + (addr,)

    def _check_subnets(self) -> bool:
        """
        :return: True if there is enough addresses in each subnet
         for each node in the overlay and that each subnet is valid
        """
        try:
            for subnet in self.subnets:
                if ip_network(str(subnet)).num_addresses - 1 < len(self.nodes):
                    lg.error("The subnet %s does not contain enough addresses."
                             " We need %s addresses\n"
                             % (subnet, len(self.nodes)))
                    return False
        except ValueError as e:
            lg.error("One of the subnet is invalid: %s\n" % e)
            return False
        return True

    @staticmethod
    def _build_adjacency_list(topo: 'IPTopo') \
            -> Dict[str, List[Tuple[str, str, Any, Dict]]]:
        adjacencies = {}  # type: Dict[str, List[Tuple[str, str, Any, Dict]]]
        for src, dst, k, attrs in topo.iterLinks(withInfo=True, withKeys=True):
            adjacencies.setdefault(src, [])\
                .append((src, dst, k, attrs.setdefault("params2", {})))
            adjacencies.setdefault(dst, [])\
                .append((dst, src, k, attrs.setdefault("params1", {})))
        return adjacencies

    def _find_nodes_in_lan(self, topo: 'IPTopo', nodes: List[str]) -> bool:
        """Checks that all nodes are in one same LAN.
        It also fills a map for each node name, the link on which an address
        should be set

        :return: True if all nodes are in the same LAN"""

        if len(nodes) == 0:
            return True

        # Build adjacency list for each node
        adjacencies = self._build_adjacency_list(topo)

        # Try to identify a LAN that includes every node among the LANs
        # attached to nodes[0]

        node_links = {}
        count_nodes = 0
        count_links = 0
        for previous, n_start, k_start, n_start_value in adjacencies[nodes[0]]:
            nodes_0_value = [x for x in adjacencies[n_start]
                             if x[1] == nodes[0] and x[2] == k_start][0][3]
            node_links = {nodes[0]: [nodes_0_value]}
            count_nodes = 1

            # to_visit is a list of tuples giving, in order, the previously
            # visited node, the current node that we explore, the key of the
            # link from which we are coming and the attributes of the interface.
            # The first three values identify an interface in the topology.
            to_visit = [(previous, n_start, k_start, n_start_value)]

            # Contains a tuple identifying an interface of the graph
            visited = {(n_start, previous, k_start)}

            # Includes one of the requested links
            if (n_start, previous) in self.links:
                count_links += 1

            # Go through the LAN
            while to_visit:
                prev, curr, curr_k, curr_value = to_visit.pop()
                curr_itf = (prev, curr, curr_k)
                if curr_itf in visited:
                    continue
                visited.add(curr_itf)

                # Includes one of the requested links
                if (prev, curr) in self.links:
                    count_links += 1

                if topo.isSwitch(curr):
                    # Look at neighbors
                    to_visit.extend(adjacencies[curr])
                elif curr in self.nodes:
                    # Add to node_links
                    if node_links.get(curr, None) is None:
                        count_nodes += 1
                    node_links.setdefault(curr, []).append(curr_value)

            if count_nodes == len(nodes):
                break  # Found the LAN that includes all the nodes

        if count_nodes != len(nodes):
            lg.error("The nodes of %s are not in the same LAN\n" % self)
            return False

        self.node_links = node_links
        return True

    def __str__(self):
        return "<SubnetOverlay nodes=%s subnets=%s>" % (self.nodes,
                                                        self.subnets)


class NetworkCapture(Overlay):
    """This overlays capture traffic on multiple interfaces before starting the daemons and stores the result"""

    def __init__(self, nodes: List['NodeDescription'] = (), interfaces: List['IntfDescription'] = (),
                 base_filename: str = "capture", extra_arguments: str = ""):
        """
        :param nodes: The routers and hosts that needs to capture traffic on every of their interfaces
        :param interfaces: The interfaces on which traffic should be captured
        :param base_filename: The base name of the network capture. One file by router or interface will be created
            of the form "{base_filename}_{router/interface}.pcapng" in the working directory of the node on which
            each capture is made.
        :param extra_arguments: The string encoding any additional argument for the tcpdump call
        """

        self.base_filename = base_filename
        self.interfaces = list(set(interfaces))
        self.extra_arguments = extra_arguments
        self.ongoing_captures = {}
        super().__init__(nodes=list(set(nodes)))

    def apply(self, topo: 'IPTopo'):
        for n in self.nodes:
            topo.nodeInfo(n).setdefault("captures", []).append(self)
        for itf in self.interfaces:
            itf.intf_attrs.setdefault("captures", []).append(self)

    def check_consistency(self, topo: 'IPTopo') -> bool:
        return len(self.nodes) != 0 or len(self.interfaces) != 0

    def start(self, node: Optional['IPNode'] = None, intf: Optional['IPIntf'] = None) -> Popen:
        if node is not None:
            # We need to specify the interfaces explicitly because switches that are loaded on the root namespace
            # and therefore using '-i any' would listen on all the switches
            interfaces = [itf.name for itf in node.intfList()]
            file_path = os.path.join(node.cwd, self.base_filename + '_' + node.name + '.pcapng')
            cmd = f"tcpdump -Z root -i {' -i '.join(interfaces)} -w {file_path} {self.extra_arguments}"
            process = node.popen(shlex.split(cmd))
            self.ongoing_captures[node.name] = process
            return process
        elif intf is not None:
            file_path = os.path.join(intf.node.cwd, self.base_filename + '_' + intf.name + '.pcapng')
            cmd = f"tcpdump -Z root -i {intf.name} -w {file_path} {self.extra_arguments}"
            process = intf.node.popen(shlex.split(cmd))
            self.ongoing_captures[intf.name] = process
            return process
        else:
            raise ValueError("The Network capture need a router or an interface to run")

    def stop(self, node: Optional['IPNode'] = None, intf: Optional['IPIntf'] = None):
        for anchor in [node, intf]:
            if anchor is not None:
                process: subprocess.Popen = self.ongoing_captures.get(anchor.name)
                process.send_signal(signal.SIGINT)
                process.wait()
