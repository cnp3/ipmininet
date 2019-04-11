import re
import time

import signal
from ipaddress import ip_address


def traceroute(net, src, dst_ip, timeout=300):
    t = 0
    old_path_ips = []
    same_path_count = 0
    white_space = re.compile(r" +")
    while t != timeout / 5.:
        out = net[src].cmd(["traceroute", "-w", "0.05", "-q", "1", "-n", "-I",
                            "-m", len(net.routers) + len(net.hosts), dst_ip]).split("\n")[1:-1]
        path_ips = [unicode(white_space.split(line)[2])
                    for line in out if "*" not in line and "!" not in line]
        if len(path_ips) > 0 and path_ips[-1] == unicode(dst_ip) and old_path_ips == path_ips:
            same_path_count += 1
            if same_path_count > 2:
                # Network has converged
                return path_ips
        else:
            same_path_count = 0

        old_path_ips = path_ips
        time.sleep(5)
        t += 1

    assert False, "The network did not converged"


def assert_path(net, expected_path, v6=False, timeout=300):
    src = expected_path[0]
    dst = expected_path[-1]
    dst_ip = net[dst].defaultIntf().ip6 if v6 else net[dst].defaultIntf().ip

    path_ips = traceroute(net, src, dst_ip, timeout=timeout)

    path = [src]
    for path_ip in path_ips:
        found = False
        for n in net.routers + net.hosts:
            for itf in n.intfList():
                itf_ips = itf.ip6s() if v6 else itf.ips()
                for ip in itf_ips:
                    if ip.ip == ip_address(path_ip):
                        found = True
                        break
                if found:
                    break
            if found:
                path.append(n.name)
                break
        assert found, "Traceroute returned the address '%s' " \
                      "that cannot be linked to a node" % path_ip

    assert path == expected_path, "We expected the path from %s to %s to go " \
                                  "through %s but it went through %s" \
                                  % (src, dst, expected_path[1:-1], path[1:-1])


def host_connected(net, v6=False, timeout=0.5):
    for src in net.hosts:
        for dst in net.hosts:
            if src != dst:
                dst.defaultIntf().updateIP()
                dst.defaultIntf().updateIP6()
                dst_ip = dst.defaultIntf().ip6 if v6 else dst.defaultIntf().ip
                cmd = "nmap%s -sn -n --max-retries 0 --max-rtt-timeout %dms %s"\
                      % (" -6" if v6 else "", int(timeout * 1000), dst_ip)
                out = src.cmd(cmd.split(" "))
                if u"0 hosts up" in out:
                    return False
    return True


def assert_connectivity(net, v6=False, timeout=300):
    t = 0
    while t != timeout / 5. and not host_connected(net, v6=v6):
        t += 1
        time.sleep(5)
    assert host_connected(net, v6=v6), "Cannot ping all hosts over %s" % ("IPv4" if not v6 else "IPv6")


def check_tcp_connectivity(client, server, v6=False, server_port=80, timeout=300):
    server_ip = server.defaultIntf().ip6 if v6 else server.defaultIntf().ip
    server_cmd = "nc %s -l %d" % ("-6" if v6 else "-4", server_port)
    server_p = server.popen(server_cmd.split(" "))

    t = 0
    client_cmd = "nc -z -w 1 -v %s %d" % (server_ip, server_port)

    client_p = client.popen(client_cmd.split(" "))
    while t != timeout * 2 and client_p.wait() != 0:
        t += 1
        if server_p.poll() is not None:
            out, err = server_p.communicate()
            assert False, \
                "The netcat server used to check TCP connectivity failed with the output:" \
                "\n[stdout]\n%s\n[stderr]\n%s" % (out, err)
        time.sleep(.5)
        client_p = client.popen(client_cmd.split(" "))
    out, err = client_p.communicate()
    code = client_p.poll()
    server_p.send_signal(signal.SIGINT)
    server_p.wait()
    return code, out, err
