"""This modules defines the IPSwitch class allowing to better support STP
   and to create hubs"""
from typing import Optional

from mininet.nodelib import LinuxBridge
from ipmininet.utils import require_cmd


class IPSwitch(LinuxBridge):
    """Linux Bridge (with optional spanning tree) extended to include
       the hubs"""

    def __init__(self, name: str, stp=True, hub=False,
                 prio: Optional[int] = None, cwd='/tmp', **kwargs):
        """:param name: the name of the node
           :param stp: whether to use spanning tree protocol
           :param hub: whether this switch behaves as a hub (this disable stp)
           :param prio: optional explicit bridge priority for STP
           :param cwd: The base directory for temporary files such as configs"""
        self.hub = hub
        self.cwd = cwd
        stp = stp and not hub
        LinuxBridge.__init__(self, name, stp=stp, prio=prio, **kwargs)

    def start(self, _controllers):
        """Start Linux bridge"""
        require_cmd("brctl", help_str="You need brctl to use %s objects"
                                      % self.__class__)

        self.cmd('ifconfig', self, 'down')
        self.cmd('brctl delbr', self)
        self.cmd('brctl addbr', self)
        if self.hub:
            self.cmd('brctl setageing 0', self)
        if self.stp:
            self.cmd('brctl setbridgeprio', self, self.prio)
            self.cmd('brctl stp', self, 'on')
        for i in self.intfList():
            if self.name in i.name:
                self.cmd('brctl addif', self, i)
                self.cmd('brctl setpathcost'
                         ' %s %s %d' % (self.name, i.name,
                                        i.params.get('stp_cost', 1)))
        # Start the captures on this switch
        for capture in self.params.get("captures", []):
            capture.start(node=self)
        for intf in self.intfList():
            for capture in intf.params.get("captures", []):
                capture.start(intf=intf)
        self.cmd('ifconfig', self, 'up')

    def stop(self, deleteIntfs=True):
        # Stop the captures on this switch
        for capture in self.params.get("captures", []):
            capture.stop(node=self)
        for intf in self.intfList():
            for capture in intf.params.get("captures", []):
                capture.stop(intf=intf)
        super().stop(deleteIntfs=deleteIntfs)
