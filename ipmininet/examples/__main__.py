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
from .simple_openr_network import SimpleOpenrNet
from .static_address_network import StaticAddressNet
from .partial_static_address_network import PartialStaticAddressNet
from .static_routing import StaticRoutingNet
from .static_routing_failure import StaticRoutingNetFailure
from .spanning_tree import SpanningTreeNet
from .spanning_tree_3 import SpanningTree3
from .spanning_tree_4 import SpanningTree4
from .spanning_tree_bus import SpanningTreeBus
from .spanning_tree_1 import SpanningTree1

from mininet.log import lg, LEVELS

TOPOS = {'simple_ospf_network': SimpleOSPFNet,
         'simple_ospfv3_network': SimpleOSPFv3Net,
         'simple_bgp_network': SimpleBGPTopo,
         'bgp_decision_process': BGPDecisionProcess,
         'iptables': IPTablesTopo,
         'gre': GRETopo,
         'ssh': SSHTopo,
         'router_adv_network': RouterAdvNet,
         'simple_openr_network': SimpleOpenrNet,
         'static_address_network': StaticAddressNet,
         'partial_static_address_network': PartialStaticAddressNet,
         'static_routing_network': StaticRoutingNet,
         'static_routing_network_failure': StaticRoutingNetFailure,
         'spanning_tree_network': SpanningTreeNet,
         'spanning_tree_3': SpanningTree3,
         'spanning_tree_4': SpanningTree4,
         'spanning_tree_bus': SpanningTreeBus,
         'spanning_tree_1': SpanningTree1}

NET_ARGS = {'router_adv_network': {'use_v4': False,
                                   'use_v6': True,
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
