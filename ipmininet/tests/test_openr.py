import pytest
import os
import tempfile
import uuid

from ipmininet.clean import cleanup
from ipmininet.ipnet import IPNet
from ipmininet.iptopo import IPTopo
from ipmininet.router import OpenrRouter
from ipmininet.node_description import OpenrRouterDescription
from ipmininet.router import OpenrRouter
from ipmininet.router.config import OpenrRouterConfig
from ipmininet.tests.utils import assert_connectivity

from . import require_root


class SimpleOpenrTopo(IPTopo):
    def __init__(self, *args, **kwargs):
        self.r4_log_dir = '/var/tmp/custom/log_dir/location'
        super().__init__(*args, **kwargs)

    def build(self, *args, **kwargs):
        r1, r2, r3 = \
            self.addRouters('r1', 'r2', 'r3',
                            cls=OpenrRouter,
                            routerDescription=OpenrRouterDescription,
                            config=OpenrRouterConfig)
        r4 = self.addRouter('r4',
                            cls=OpenrRouter,
                            routerDescription=OpenrRouterDescription)
        r4.addOpenrDaemon(log_dir=self.r4_log_dir)
        self.addLinks((r1, r2), (r1, r3), (r3, r4))
        super().build(*args, **kwargs)


@require_root
def test_openr_connectivity():
    try:
        net = IPNet(topo=SimpleOpenrTopo())
        net.start()
        assert_connectivity(net, v6=True)
        net.stop()
    finally:
        cleanup()


@require_root
def test_logdir_creation():
    try:
        topo = SimpleOpenrTopo()
        net = IPNet(topo=topo)
        net.start()

        default_log_dir = '/var/tmp/log'

        for i in range(1, 4):
            assert os.path.isdir(f'{default_log_dir}/r{i}')
        assert not os.path.isdir(f'{default_log_dir}/r4')
        assert os.path.isdir(topo.r4_log_dir)

        net.stop()
    finally:
        cleanup()


@require_root
def test_tmp_isolation():
    try:
        net = IPNet(topo=SimpleOpenrTopo())
        net.start()

        tmp_dir = '/tmp'
        with tempfile.NamedTemporaryFile(dir=tmp_dir) as f:
            host_file_name = f.name
            host_file_base_name = os.path.basename(host_file_name)
            host_tmp_dir_content = os.listdir(tmp_dir)

            assert os.path.isfile(host_file_name)
            assert host_file_base_name in host_tmp_dir_content
            for i in range(1, 5):
                node_tmp_dir_content = net[f'r{i}'].cmd(f'ls {tmp_dir}') \
                                                   .split()
                assert not host_file_base_name in node_tmp_dir_content

        node_file_base_name = str(uuid.uuid1())
        node_file_name = f'{tmp_dir}/{node_file_base_name}'
        net['r1'].cmd(f'touch {node_file_name}')
        node_tmp_dir_content = net['r1'].cmd(f'ls {tmp_dir}').split()
        host_tmp_dir_content = os.listdir(tmp_dir)

        assert node_file_base_name in node_tmp_dir_content
        assert not os.path.isfile(node_file_name)
        assert not node_file_base_name in host_tmp_dir_content

        net.stop()
    finally:
        cleanup()
