"""This module tests the SSH daemon"""
import os
import time

from ipmininet.clean import cleanup
from ipmininet.examples.sshd import SSHTopo
from ipmininet.ipnet import IPNet
from . import require_root


@require_root
def test_sshd_example():
    try:
        net = IPNet(topo=SSHTopo())
        net.start()

        ssh_key = None
        with open("/tmp/sshd_r2.cfg") as fileobj:
            for line in fileobj:
                if "AuthorizedKeysFile" in line:
                    ssh_key = line.split(" ")[1].split(".")[0]
        assert ssh_key is not None,\
            "No authorized SSH key found in the configuration"
        assert os.path.isfile(ssh_key), "Cannot find key file at %s" % ssh_key

        ip = net["r2"].intf("r2-eth0").ip
        cmd = "ssh -oStrictHostKeyChecking=no -oConnectTimeout=1" \
              " -oPasswordAuthentication=no -i %s %s ls" % (ssh_key, ip)
        t = 0
        while t < 60 and net["r1"].popen(cmd.split(" ")).wait() != 0:
            time.sleep(0.5)
            t += 1
        p = net["r1"].popen(cmd.split(" "))
        assert p.wait() == 0, "Cannot connect with SSH to the router"

        net.stop()
    finally:
        cleanup()
