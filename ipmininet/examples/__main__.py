"""This files lets you start all examples"""
import argparse

import ipmininet
from ipmininet.examples.network_capture import NetworkCaptureTopo
from ipmininet.ipnet import IPNet
from ipmininet.cli import IPCLI

from .simple_ospf_network import SimpleOSPFNet
from .simple_ospfv3_network import SimpleOSPFv3Net
from .simple_bgp_network import SimpleBGPTopo
from .bgp_decision_process import BGPDecisionProcess
from .iptables import IPTablesTopo
from .gre import GRETopo
from .sshd import SSHTopo
from .router_adv_network import RouterAdvNet
from .ripng_network import RIPngNetwork
from .ripng_network_adjust import RIPngNetworkAdjust
from .simple_openr_network import SimpleOpenrNet
from .static_address_network import StaticAddressNet
from .static_routing_network_complex import StaticRoutingNetComplex
from .partial_static_address_network import PartialStaticAddressNet
from .static_routing import StaticRoutingNet
from .static_routing_network_basic import StaticRoutingNetBasic
from .static_routing_failure import StaticRoutingNetFailure
from .spanning_tree import SpanningTreeNet
from .spanning_tree_intermediate import SpanningTreeIntermediate
from .spanning_tree_full_mesh import SpanningTreeFullMesh
from .spanning_tree_bus import SpanningTreeBus
from .spanning_tree_hub import SpanningTreeHub
from .spanning_tree_cost import SpanningTreeCost
from .spanning_tree_adjust import SpanningTreeAdjust
from .bgp_full_config import BGPTopoFull
from .bgp_local_pref import BGPTopoLocalPref
from .bgp_med import BGPTopoMed
from .bgp_rr import BGPTopoRR
from .bgp_policies_1 import BGPPoliciesTopo1
from .bgp_policies_2 import BGPPoliciesTopo2
from .bgp_policies_4 import BGPPoliciesTopo4
from .bgp_policies_3 import BGPPoliciesTopo3
from .bgp_policies_adjust import BGPPoliciesAdjustTopo
from .bgp_policies_5 import BGPPoliciesTopo5
from .dns_network import DNSNetwork
from .dns_advanced_network import DNSAdvancedNetwork
from .srv6 import SRv6Topo
from .tc_network import TCNet
from .tc_advanced_network import TCAdvancedNet
from .exabgp_prefix_injector import ExaBGPTopoInjectPrefixes
from .link_failure import FailureTopo

from mininet.log import lg, LEVELS

TOPOS = {'simple_ospf_network': SimpleOSPFNet,
         'simple_ospfv3_network': SimpleOSPFv3Net,
         'simple_bgp_network': SimpleBGPTopo,
         'bgp_decision_process': BGPDecisionProcess,
         'iptables': IPTablesTopo,
         'gre': GRETopo,
         'ssh': SSHTopo,
         'router_adv_network': RouterAdvNet,
         'ripng_network': RIPngNetwork,
         'ripng_network_adjust': RIPngNetworkAdjust,
         'simple_openr_network': SimpleOpenrNet,
         'static_address_network': StaticAddressNet,
         'static_routing_network_complex': StaticRoutingNetComplex,
         'partial_static_address_network': PartialStaticAddressNet,
         'static_routing_network': StaticRoutingNet,
         'static_routing_network_basic': StaticRoutingNetBasic,
         'static_routing_network_failure': StaticRoutingNetFailure,
         'spanning_tree_network': SpanningTreeNet,
         'spanning_tree_intermediate': SpanningTreeIntermediate,
         'spanning_tree_full_mesh': SpanningTreeFullMesh,
         'spanning_tree_bus': SpanningTreeBus,
         'spanning_tree_hub': SpanningTreeHub,
         'spanning_tree_cost': SpanningTreeCost,
         'spanning_tree_adjust': SpanningTreeAdjust,
         'bgp_full_config': BGPTopoFull,
         'bgp_local_pref': BGPTopoLocalPref,
         'bgp_med': BGPTopoMed,
         'bgp_rr': BGPTopoRR,
         'bgp_policies_1': BGPPoliciesTopo1,
         'bgp_policies_2': BGPPoliciesTopo2,
         'bgp_policies_3': BGPPoliciesTopo3,
         'bgp_policies_4': BGPPoliciesTopo4,
         'bgp_policies_adjust': BGPPoliciesAdjustTopo,
         'bgp_policies_5': BGPPoliciesTopo5,
         'dns_network': DNSNetwork,
         'dns_advanced_network': DNSAdvancedNetwork,
         'ipv6_segment_routing': SRv6Topo,
         'tc_network': TCNet,
         'tc_advanced_network': TCAdvancedNet,
         'exabgp_prefix_injector': ExaBGPTopoInjectPrefixes,
         'failure': FailureTopo,
         'network_capture': NetworkCaptureTopo}

NET_ARGS = {'router_adv_network':  {'use_v4': False,
                                    'use_v6': True,
                                    'allocate_IPs': False},
            'bgp_full_config':     {'use_v4': False,
                                    'use_v6': True},
            'bgp_local_pref':      {'use_v4': False,
                                    'use_v6': True},
            'bgp_med':             {'use_v4': False,
                                    'use_v6': True},
            'bgp_rr':              {'use_v4': False,
                                    'use_v6': True}}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--topo', choices=TOPOS.keys(),
                        default='simple_ospf_network',
                        help='The topology that you want to start.')
    parser.add_argument('--log', choices=LEVELS.keys(), default='info',
                        help='The level of details in the logs.')
    parser.add_argument('--args', help='Additional arguments to give'
                        'to the topology constructor (key=val, key=val, ...)',
                        default='')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    lg.setLogLevel(args.log)
    if args.log == 'debug':
        ipmininet.DEBUG_FLAG = True
    kwargs = {}
    for arg in args.args.strip(' \r\t\n').split(','):
        arg = arg.strip(' \r\t\n')
        if not arg:
            continue
        try:
            k, v = arg.split('=')
            kwargs[k] = v
        except ValueError:
            lg.error('Ignoring args:', arg)
    net = IPNet(topo=TOPOS[args.topo](**kwargs), **NET_ARGS.get(args.topo, {}))
    net.start()
    IPCLI(net)
    net.stop()
