"""This module tests GRE tunnels"""
import time

from ipmininet.clean import cleanup
from ipmininet.examples.gre import GRETopo
from ipmininet.ipnet import IPNet
from . import require_root


@require_root
def test_gre_example():
    try:
        net = IPNet(topo=GRETopo())
        net.start()

        t = 0
        cmd = "ping -W 1 -c 1 -I 10.0.1.1 10.0.1.2".split(" ")
        while t < 60 and net["h1"].popen(cmd).wait() != 0:
            t += 1
            time.sleep(.5)
        p = net["h1"].popen(cmd)
        code = p.wait()
        out, err = p.communicate()
        assert code == 0, "Cannot use GRE tunnel.\nThe command '%s' printed:" \
                          " [stdout]\n%s\n[stderr]\n%s" % (cmd, out, err)

        net.stop()
    finally:
        cleanup()
