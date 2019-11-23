"""This modules defines a L3 router class,
   with a modulable config system."""
from builtins import str

import sys
import time

from ipmininet import DEBUG_FLAG
from ipmininet.utils import L3Router
from ipmininet.link import IPIntf
from .config import BasicRouterConfig, NodeConfig

import mininet.clean
from mininet.node import Node
from mininet.log import lg
import shlex


class ProcessHelper(object):
    """This class holds processes that are part of a given family, e.g. routing
    daemons. This also provides the abstraction to execute a new process,
    currently in a mininet namespace, but could be extended to execute in
    a different environment."""

    def __init__(self, node, *args, **kwargs):
        """:param node: The object to use to create subprocesses."""
        self.node = node
        self._pid_gen = 0
        self._processes = {}
        super(ProcessHelper, self).__init__(*args, **kwargs)

    def call(self, *args, **kwargs):
        """Call a command, wait for it to end and return its ouput.

        :param args: the command + arguments
        :param kwargs: key-val arguments, as used in subprocess.Popen"""
        return self.node.cmd(*args, **kwargs)

    def popen(self, *args, **kwargs):
        """Call a command and return a Popen handle to it.

        :param args: the command + arguments
        :param kwargs: key-val arguments, as used in subprocess.Popen
        :return: a process index in this family"""
        self._pid_gen += 1
        self._processes[self._pid_gen] = self.node.popen(*args, **kwargs)
        return self._pid_gen

    def pexec(self, *args, **kw):
        """Call a command, wait for it to terminate and save stdout, stderr and
        its return code"""
        return self.node.pexec(*args, **kw)

    def get_process(self, pid):
        """Return a given process handle in this family

        :param pid: a process index, as return by popen"""
        return self._processes[pid]

    def terminate(self):
        """Terminate all processes in this family"""
        for p in self._processes.values():
            try:
                p.terminate()
            except OSError:
                pass  # Process is already dead


class IPNode(Node):
    """A Node which manages a set of daemons"""

    def __init__(self, name,
                 config=NodeConfig,
                 cwd='/tmp',
                 process_manager=ProcessHelper,
                 use_v4=True,
                 use_v6=True,
                 *args, **kwargs):
        """Most of the heavy lifting for this node should happen in the
        associated config object.

        :param config: The configuration generator for this node. Either a
                        class or a tuple (class, kwargs)
        :param cwd: The base directory for temporary files such as configs
        :param process_manager: The class that will manage all the associated
                                processes for this node
        :param use_v4: Whether this node has IPv4
        :param use_v6: Whether this node has IPv6"""
        super(IPNode, self).__init__(name, *args, **kwargs)
        self.use_v4 = use_v4
        self.use_v6 = use_v6
        self.cwd = cwd
        self._old_sysctl = {}
        try:
            self.nconfig = config[0](self, **config[1])
        except (TypeError, IndexError):
            self.nconfig = config(self)
        self._processes = process_manager(self)

    def start(self):
        """Start the node: Configure the daemons, set the relevant sysctls,
        and fire up all needed processes"""
        # Build the config
        self.nconfig.build()
        # Check them
        err_code = False
        for d in self.nconfig.daemons:
            out, err, code = self._processes.pexec(shlex.split(d.dry_run))
            err_code = err_code or code
            if code:
                lg.error(d.NAME, 'configuration check failed ['
                         'rcode:', str(code), ']\n'
                         'stdout:', str(out), '\n'
                         'stderr:', str(err))
        if err_code:
            lg.error('Config checks failed, aborting!')
            mininet.clean.cleanup()
            sys.exit(1)
        # Set relevant sysctls
        for opt, val in self.nconfig.sysctl:
            self._old_sysctl[opt] = self._set_sysctl(opt, val)
        # Fire up all daemons
        for d in self.nconfig.daemons:
            self._processes.popen(shlex.split(d.startup_line))
            # Busy-wait if the daemon needs some time before being started
            while not d.has_started():
                time.sleep(.001)

    def terminate(self):
        """Stops this node and sets back all sysctls to their old values"""
        self._processes.terminate()
        if not DEBUG_FLAG:
            self.nconfig.cleanup()
        for opt, val in self._old_sysctl.items():
            self._set_sysctl(opt, val)
        super(IPNode, self).terminate()

    def _set_sysctl(self, key, val):
        """Change a sysctl value, and return the previous set value"""
        val = str(val)
        try:
            v = self._processes.call('sysctl', key)\
                    .split('=')[1]\
                    .strip(' \n\t\r')
        except IndexError:
            v = None
        if v != val:
            self._processes.call('sysctl', '-w', '%s=%s' % (key, val))
        return v

    def get(self, key, val=None):
        """Check for a given key in the node parameters"""
        return self.params.get(key, val)


class Router(IPNode, L3Router):
    """The actual router, which manages a set of daemons"""

    def __init__(self, name,
                 config=BasicRouterConfig,
                 password='zebra',
                 lo_addresses=(),
                 *args, **kwargs):
        """:param password: The password for the routing daemons vtysh access
           :param lo_addresses: The list of addresses to set on the loopback
                                interface"""
        super(Router, self).__init__(name, config=config, *args, **kwargs)
        self.password = password

        # This interface already exists in the node,
        # so no need to move it
        lo = IPIntf('lo', node=self, port=-1, moveIntfFn=lambda x, y: None)
        lo.ip = lo_addresses

    @property
    def asn(self):
        return self.get('asn')
