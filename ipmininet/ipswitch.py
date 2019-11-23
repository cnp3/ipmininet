"""This modules defines the IPSwitch class allowing to better support STP
   and to create hubs"""

from mininet.nodelib import LinuxBridge


class IPSwitch(LinuxBridge):
    "Linux Bridge (with optional spanning tree) extended to include the hubs"

    def __init__(self, name, stp=True, hub=False, prio=None, **kwargs):
        """:param name: the name of the node
           :param stp: whether to use spanning tree protocol
           :param hub: whether this switch behaves as a hub (this disable stp)
           :param prio: optional explicit bridge priority for STP"""
        self.hub = hub
        stp = stp and not hub
        LinuxBridge.__init__(self, name, stp=stp, prio=prio, **kwargs)

    def start(self, _controllers):
        "Start Linux bridge"
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
        self.cmd('ifconfig', self, 'up')
