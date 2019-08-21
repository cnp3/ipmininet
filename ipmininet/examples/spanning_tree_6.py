#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 21 12:04:47 2019

@author: augustin
"""

from ipmininet.iptopo import IPTopo
from mininet.node import Host

""" source: mininet/examples/vlanhost.py"""
class VLANHost( Host ):
    "Host connected to VLAN interface"

    def config( self, vlan=100, **params ):
        """Configure VLANHost according to (optional) parameters:
           vlan: VLAN ID for default interface"""

        r = super( VLANHost, self ).config( **params )
        intf = self.defaultIntf()
        # remove IP from default, "physical" interface
        self.cmd( 'ifconfig %s inet 0' % intf )
        # create VLAN interface
        self.cmd( 'vconfig add %s %d' % ( intf, vlan ) )
        # assign the host's IP to the VLAN interface
        self.cmd( 'ifconfig %s.%d inet %s' % ( intf, vlan, params['ip'] ) )
        #self.cmd('ip addr add 192.168.1.25/24 dev %s-eth0.100' % self.name)
        print(self.name)
        # update the intf name and host's intf map
        newName = '%s.%d' % ( intf, vlan )
        # update the (Mininet) interface to refer to VLAN interface name
        intf.name = newName
        # add VLAN interface to host's name to intf map
        self.nameToIntf[ newName ] = intf
        print('ok')
        return r

hosts = { 'vlan': VLANHost }

class SpanningTree6(IPTopo):
    
    def build(self, *args, **kwargs):
        """
        +-----+vlan10       +-----+      vlan100+-----+
        | h0  +-------------+ s1  +-------------+ h1  |
        +-----+             +-----+             +-----+
        """
        s1 = self.addSwitch('s1', prio=1 )
        h0 = self.addHost('h0_100', vlan=100)
        h1 = self.addHost('h1_100', vlan=100)
        self.addLink(h0,s1)
        self.addLink(h1,s1)
        
        #other hosts to test
        #h2 = self.addHost('h2')
        #self.addLink(h2,s1)
        #h3 = self.addHost('h3')
        #self.addLink(h3,s1)
        super(SpanningTree6, self).build(*args, **kwargs)
        
