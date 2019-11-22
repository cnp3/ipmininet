import shlex
import signal
import time
import traceback
from typing import Dict, List, Tuple

import pytest

from ipmininet.clean import cleanup
from ipmininet.examples.srv6 import SRv6Topo
from ipmininet.ipnet import IPNet
from ipmininet.srv6 import LocalSIDTable, SRv6EndFunction, SRv6EndXFunction, \
    SRv6EndTFunction, SRv6EndDX6Function, SRv6Encap, SRv6EndDT6Function, \
    SRv6EndB6EncapsFunction
from ipmininet.tests import require_root
from ipmininet.tests.utils import assert_connectivity, assert_path
from ipmininet.utils import require_cmd

MAIN_TABLE = 254


class SRv6TestTopo(SRv6Topo):

    def __init__(self, new_routes: Dict[str, Tuple], *args, **kwargs):
        """
        :param new_routes: A dictionary mapping the host name to the router name
                           to a list of tuples (SRv6Route class, params).
                           The params have to contain all the constructor
                           parameter except the node and the network.
        """
        self.new_routes = new_routes
        super(SRv6TestTopo, self).__init__(*args, **kwargs)

    def post_build(self, net):
        super(SRv6TestTopo, self).post_build(net)

        for r in self.new_routes.keys():
            route_class, route_params = self.new_routes[r]

            if issubclass(route_class, SRv6EndFunction):
                if r not in self.tables:
                    r_segment_space = next(net[r].intf("lo").ip6s()).network
                    self.tables[r] = LocalSIDTable(net[r],
                                                   matching=[r_segment_space])
                # We use the local SID table
                route_params["table"] = self.tables[r]
            try:
                route_params["to"] = net[route_params["to"]].intf().ip6
            except KeyError:  # This is already an IP address
                pass
            try:
                route_class(net=net, node=net[r], **route_params)
            except Exception as e:
                traceback.print_exc()
                raise e


def sr_path(net: IPNet, src: str, dst_ip: str, timeout=1, through=()) \
        -> List[str]:
    require_cmd("tshark", help_str="tshark is required to run tests")
    require_cmd("nmap", help_str="nmap is required to run tests")

    # Check connectivity
    ping_cmd = "ping -6 -c 1 -W %d %s" % (int(timeout), dst_ip)
    out = net[src].cmd(shlex.split(ping_cmd))
    if ", 0% packet loss" not in out:
        return []

    # Start captures of SYN packets to port 80
    tsharks = []
    try:
        for n in net.routers + net.hosts:
            p = n.popen(shlex.split("tshark -n -i any -f 'ip6'"
                                    " -w /tmp/{}.pcap".format(n.name)))
            tsharks.append(p)
        time.sleep(15)  # Wait for tshark to start

        # Launch ping
        out = net[src].cmd(shlex.split(ping_cmd))
        assert "100% packet loss" not in out, \
            "Connectivity from %s to %s is not ensured," \
            " so we cannot infer the path." % (src, dst_ip)
        time.sleep(1)  # Wait for tshark to register the info

        for p in tsharks:
            assert p.poll() is None, "tshark stopped unexpectedly:" \
                                     "stderr '{}'".format(p.stderr.read())
    finally:
        # Stop captures
        for p in tsharks:
            p.send_signal(signal.SIGINT)
            p.wait()

    # Retrieve packet captures
    captures = {}  # type: Dict[str, List[Tuple[float, str]]]
    for n in net.routers + net.hosts:
        out = n.cmd(shlex.split("tshark -n -r /tmp/{}.pcap -T fields "
                                "-E separator=, "
                                "-e icmpv6.type -e ipv6.dst -e frame.time_epoch"
                                .format(n.name)))
        data = out.split("\n")[1:-1]
        for line in data:
            values = line.strip().split(",")
            if len(values) < 3:
                continue
            icmp_type = values[0]
            data_dst = values[1]
            data_time = values[-1]
            if icmp_type == "128":
                captures.setdefault(n.name, []) \
                    .append((float(data_time), data_dst))

    # Analyze results

    packet_received = {}  # type: Dict[str, List[Tuple[float, str]]]
    for n, packets in captures.items():
        for data_time, destination in packets:
            packet_received.setdefault(destination, []).append((data_time, n))

    sub_paths = {}  # type: Dict[str, List[str]]
    for dest in packet_received:
        ordered_reception = sorted(packet_received[dest])

        sub_paths[dest] = []
        for _, n in ordered_reception:
            if len(sub_paths[dest]) == 0 or sub_paths[dest][-1] != n:
                sub_paths[dest].append(n)

    # Order sub paths with the trough list
    path = []  # type: List[str]
    for intermediate in through:
        found = False

        try:
            intermediate_ips = [ip.ip.compressed
                                for itf in net[intermediate].intfList()
                                for ip in itf.ip6s(exclude_lls=True)]
        except KeyError:
            intermediate_ips = [intermediate]

        for ip in intermediate_ips:
            if ip in sub_paths:
                found = True
                path.extend(sub_paths[ip])
                break
        if not found:
            return path
    path.extend(sub_paths[dst_ip])

    # Remove duplicates
    compressed_path = []  # type: List[str]
    for n in path:
        if len(compressed_path) == 0 or n != compressed_path[-1]:
            compressed_path.append(n)

    # Remove source to get a similar output to traceroute
    path = [net[n].intf().ip6 for n in compressed_path][1:]
    return path


@require_root
@pytest.mark.parametrize("routes,paths,through", [
    ({},
     [["h6", "r6", "r5", "r4", "h4"],
      ["h1", "r1", "r6", "r5", "r2", "r3", "r4", "h4"]],
     [[],
      ["r6", "r5", "2042:3:3::34", "r4"]]),  # Intermediate destinations
    (
        {
            "h6": (SRv6Encap, {"to": "h4", "through": ["2042:6:6::600"],
                               "mode": SRv6Encap.INLINE}),
            "r6": (SRv6EndFunction, {"to": "2042:6:6::600"})
        },
        [["h6", "r6", "r5", "r4", "h4"],
         ["h1", "r1", "r6", "r5", "r2", "r3", "r4", "h4"]],
        [["2042:6:6::600"],
         ["r6", "r5", "2042:3:3::34", "r4"]]
    ),
    (
        {
            "h6": (SRv6Encap, {"to": "h4", "through": ["2042:5:5::500"],
                               "mode": SRv6Encap.INLINE}),
            "r5": (SRv6EndXFunction, {"to": "2042:5:5::500",
                                      "nexthop": "2042:2:2::1"})
        },
        [["h6", "r6", "r5", "r2", "r5", "r4", "h4"],
         ["h1", "r1", "r6", "r5", "r2", "r3", "r4", "h4"]],
        [["2042:5:5::500"],
         ["r6", "r5", "2042:3:3::34", "r4"]]
    ),
    (
        {
            "h6": (SRv6Encap, {"to": "h4",
                               "through": ["2042:5:5::501", "2042:2:2::1"],
                               "mode": SRv6Encap.INLINE}),
            "r5": (SRv6EndTFunction, {"to": "2042:5:5::501",
                                      "lookup_table": MAIN_TABLE})
        },
        [["h6", "r6", "r5", "r2", "r5", "r4", "h4"],
         ["h1", "r1", "r6", "r5", "r2", "r3", "r4", "h4"]],
        [["2042:5:5::501", "2042:2:2::1"],
         ["r6", "r5", "2042:3:3::34", "r4"]]
    ),
    (
        {
            "h6": (SRv6Encap, {"to": "h4", "through": ["2042:5:5::500"],
                               "mode": SRv6Encap.ENCAP}),
            "r5": (SRv6EndDX6Function, {"to": "2042:5:5::500",
                                        "nexthop": "2042:2:2::1"})
        },
        [["h6", "r6", "r5", "r2", "r5", "r4", "h4"],
         ["h1", "r1", "r6", "r5", "r2", "r3", "r4", "h4"]],
        [["2042:5:5::500"],
         ["r6", "r5", "2042:3:3::34", "r4"]]
    ),
    (
        {
            "h6": (SRv6Encap, {"to": "h4", "through": ["2042:5:5::501",
                                                       "2042:4:4::1"],
                               "mode": SRv6Encap.INLINE}),
            "r5": (SRv6EndB6EncapsFunction, {"to": "2042:5:5::501",
                                             "segments": ["2042:2:2::1"]})
        },
        [["h6", "r6", "r5", "r2", "r5", "r4", "h4"],
         ["h1", "r1", "r6", "r5", "r2", "r3", "r4", "h4"]],
        [["2042:5:5::501", "2042:2:2::1", "2042:4:4::1"],
         ["r6", "r5", "2042:3:3::34", "r4"]]
    ),
    (
        {
            "h6": (SRv6Encap, {"to": "h4",
                               "through": ["2042:5:5::501", "2042:4:4::1"],
                               "mode": SRv6Encap.INLINE}),
            "r5": (SRv6EndB6EncapsFunction, {"to": "2042:5:5::501",
                                             "segments": ["2042:2:2::200"]}),
            "r2": (SRv6EndDT6Function, {"to": "2042:2:2::200",
                                        "lookup_table": MAIN_TABLE})
        },
        [["h6", "r6", "r5", "r2", "r5", "r4", "h4"],
         ["h1", "r1", "r6", "r5", "r2", "r3", "r4", "h4"]],
        [["2042:5:5::501", "2042:2:2::200", "2042:4:4::1"],
         ["r6", "r5", "2042:3:3::34", "r4"]]
    )
])
def test_static_examples(routes, paths, through):
    try:
        topo = SRv6TestTopo(new_routes=routes)
        net = IPNet(topo=topo)
        net.start()

        assert_connectivity(net, v6=False)
        for i, p in enumerate(paths):
            assert_path(net, p, v6=True, traceroute_fun=sr_path,
                        through=through[i], timeout=1, retry=30)

        topo.clean()
        net.stop()
    finally:
        cleanup()
