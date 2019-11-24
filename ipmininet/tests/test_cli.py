import os
import re
import tempfile

import pytest

from ipmininet.clean import cleanup
from ipmininet.cli import IPCLI
from ipmininet.examples.static_address_network import StaticAddressNet
from ipmininet.ipnet import IPNet
from ipmininet.tests import require_root
from ipmininet.tests.utils import CLICapture, assert_connectivity, assert_path


@pytest.fixture(scope="module")
def net(request):
    cleanup()
    net = IPNet(topo=StaticAddressNet())
    net.start()

    assert_connectivity(net, v6=False)
    assert_connectivity(net, v6=True)

    paths = [
        ["h1", "r1", "r2", "h3"],
        ["h3", "r2", "r1", "h1"],
        ["h3", "r2", "r1", "h2"],
        ["h3", "r2", "r1", "h4"],
    ]
    for p in paths:
        assert_path(net, p, v6=False)
        assert_path(net, p, v6=True)

    request.addfinalizer(cleanup)
    return net


@pytest.fixture(scope="function")
def tmp(request):
    name = tempfile.mktemp()
    request.addfinalizer(lambda: os.unlink(name))
    return name


def perm(*args):
    s = "(?:("
    for i, arg in enumerate(args):
        s = s + "(" + arg + ")"
        if i != len(args) - 1:
            s += "|"
    s = s + r")(?!.*\1)){%d}" % len(args)
    print(s)
    return s


@require_root
@pytest.mark.parametrize("input_line,expected_lines", [
    ("route 2001:1a::2",
     [re.compile(r"\[r1\] 2001:1a::2.*dev +r1-eth0.*"),
      re.compile(r"\[r2\] 2001:1a::2.*dev +r2-eth0.*")]),
    ("ip 2001:1a::1/64 2001:1a::1 10.2.0.3 10.2.0.3/24 2001::3/64 invalid",
     ["2001:1a::1/64 | r1 ", "2001:1a::1 | r1 ",
      "10.2.0.3/24 | h4 ", "10.2.0.3 | h4 ",
      "2001::3/64 | unknown IP ", "invalid | unknown IP "]),
    ("ips h1 h4 invalid",
     [re.compile(r"h1 \| \[u?'10\.0\.0\.2', u?'2001:1a::2'\] "),
      re.compile(r"h4 \| \[u?'10\.2\.0\.3', u?'2001:12b::3'\] "),
      "invalid | unknown node "]),
    ("pingall", [re.compile(r"h1 --IPv4--> %s" % perm("h2 ", "h3 ", "h4 ")),
                 re.compile(r"h1 --IPv6--> %s" % perm("h2 ", "h3 ", "h4 ")),
                 re.compile(r"h2 --IPv4--> %s" % perm("h1 ", "h3 ", "h4 ")),
                 re.compile(r"h2 --IPv6--> %s" % perm("h1 ", "h3 ", "h4 ")),
                 re.compile(r"h3 --IPv4--> %s" % perm("h1 ", "h2 ", "h4 ")),
                 re.compile(r"h3 --IPv6--> %s" % perm("h1 ", "h2 ", "h4 ")),
                 re.compile(r"h4 --IPv4--> %s" % perm("h1 ", "h2 ", "h3 ")),
                 re.compile(r"h4 --IPv6--> %s" % perm("h1 ", "h2 ", "h3 "))]),
    ("pingpair h1 h2", ["h1 --IPv4--> h2 ",
                        "h1 --IPv6--> h2 ",
                        "h2 --IPv4--> h1 ",
                        r"h2 --IPv6--> h1 "]),
    ("ping4all", [re.compile(r"h1 --IPv4--> %s" % perm("h2 ", "h3 ", "h4 ")),
                  re.compile(r"h2 --IPv4--> %s" % perm("h1 ", "h3 ", "h4 ")),
                  re.compile(r"h3 --IPv4--> %s" % perm("h1 ", "h2 ", "h4 ")),
                  re.compile(r"h4 --IPv4--> %s" % perm("h1 ", "h2 ", "h3 "))]),
    ("ping4pair h1 h2", ["h1 --IPv4--> h2 ",
                         "h2 --IPv4--> h1 "]),
    ("ping6all", [re.compile(r"h1 --IPv6--> %s" % perm("h2 ", "h3 ", "h4 ")),
                  re.compile(r"h2 --IPv6--> %s" % perm("h1 ", "h3 ", "h4 ")),
                  re.compile(r"h3 --IPv6--> %s" % perm("h1 ", "h2 ", "h4 ")),
                  re.compile(r"h4 --IPv6--> %s" % perm("h1 ", "h2 ", "h3 "))]),
    ("ping6pair", ["h1 --IPv6--> h2 ",
                   "h2 --IPv6--> h1 "]),
    ("h1 echo h4", ["10.2.0.3"]),
    ("s2 echo h4", ["h4"]),
    ("h1", ["*** Enter a command for node: h1 <cmd>"]),
    ("invalid_command", ["*** Unknown command: invalid_command"])
])
def test_cli(tmp, net, input_line, expected_lines):

    with open(tmp, "w") as fileobj:
        fileobj.write(input_line + "\n")

    with CLICapture("info") as capture:
        f = open(tmp, "r")
        try:
            IPCLI(net, stdin=f, script=tmp)
        finally:
            f.close()

    pattern = re.compile("")
    for l in expected_lines:
        if isinstance(l, type(pattern)):
            assert len([x for x in capture.out
                        if l.match(x) is not None]) > 0, \
                "Regex '%s' does not match the output of '%s':\n%s" \
                % (l, input_line, "\n".join(capture.out))
        else:
            assert l in capture.out, \
                "Line '%s' cannot be found in the output of '%s':\n%s" \
                % (l, input_line, "\n".join(capture.out))
