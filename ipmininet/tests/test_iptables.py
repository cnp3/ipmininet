"""This module tests iptables"""

from ipmininet.clean import cleanup
from ipmininet.examples.iptables import IPTablesTopo
from ipmininet.ipnet import IPNet
from ipmininet.tests.utils import check_tcp_connectivity
from . import require_root


@require_root
def test_iptables_example():
    try:
        net = IPNet(topo=IPTablesTopo())
        net.start()

        ip = net["r2"].intf("r2-eth0").ip
        cmd = "ping -W 1 -c 1 %s" % ip
        p = net["r1"].popen(cmd.split(" "))
        out, err = p.communicate()
        ret = p.poll()
        assert ret == 0, "Pings over IPv4 should not be blocked.\n" \
                         "[stdout]\n%s\n[stderr]\n%s" % (out, err)

        ip6 = net["r2"].intf("r2-eth0").ip6
        cmd = "ping6 -W 1 -c 1 %s" % ip6
        p = net["r1"].popen(cmd.split(" "))
        assert p.wait() != 0, "Pings over IPv6 should be blocked"

        ret, _, _ = check_tcp_connectivity(net["r1"], net["r2"],
                                           server_port=80,
                                           server_itf=net["r2"].intf("r2-eth0"),
                                           timeout=.5)
        assert ret != 0, "TCP over port 80 should be blocked over IPv4"

        ret, _, _ = check_tcp_connectivity(net["r1"], net["r2"],
                                           server_port=1480,
                                           server_itf=net["r2"].intf("r2-eth0"),
                                           timeout=.5)
        assert ret != 0, "TCP over port 1480 should be blocked over IPv4"

        ret, _, _ = check_tcp_connectivity(net["r1"], net["r2"],
                                           server_port=2000,
                                           server_itf=net["r2"].intf("r2-eth0"),
                                           timeout=.5)
        assert ret == 0, "TCP over port 2000 should not be blocked over IPv4"

        ret, out, err = \
            check_tcp_connectivity(net["r1"], net["r2"], v6=True,
                                   server_port=80,
                                   server_itf=net["r2"].intf("r2-eth0"))
        assert ret == 0, "TCP over port 80 should not be blocked over IPv6.\n" \
                         "[stdout]\n%s\n[stderr]\n%s" % (out, err)

        net.stop()
    finally:
        cleanup()
