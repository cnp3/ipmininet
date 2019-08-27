"This files lets you start all examples"
import argparse

import ipmininet
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
from .static_routing_network_intermediate import StaticRoutingNetIntermediate
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
from .spanning_tree_simple import SpanningTreeSimple
from .spanning_tree_adjust import SpanningTreeAdjust
from .simple_rip6_crash_test import MinimalRIPngNetTest
from .test import MinimalRIPngNet

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
         'static_routing_network_intermediate': StaticRoutingNetIntermediate,
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
         'spanning_tree_simple': SpanningTreeSimple,
         'spanning_tree_adjust':SpanningTreeAdjust,
         'simple_ripng_network': MinimalRIPngNetTest,
         'test': MinimalRIPngNet}

NET_ARGS = {'router_adv_network': {'use_v4': False,
                                   'use_v,6': True,
                                   'allocate_IPs': False}}


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
