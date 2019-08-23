#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 19 15:03:29 2019

@author: Louis
"""

from ipmininet.iptopo import IPTopo
from ipmininet.switch_hub import SwitchHub

class SpanningTreeBus(IPTopo):
    
    def build(self, *args, **kwargs):
        """
                  +-----+
                  | s1  |
                  +--+--+
                     |
                     |
                  +--+--+
            +-----+ BUS +-----+
            |     +-----+     |
            |                 |
         +--+--+           +--+--+
         | s2  |           | s3  |
         +-----+           +-----+
        """
        s1  =  self.addSwitch("s1", stp=True)
        s2  =  self.addSwitch("s2", stp=True)
        s3  =  self.addSwitch("s3", stp=True)
        s99 =  self.addHub("s99", stp=False) # Hub
        
        self.addLink(s1,s99)
        self.addLink(s2,s99)
        self.addLink(s3,s99)

        self.addLink(s1,s2)
        self.addLink(s2,s3)
        self.addLink(s1,s3)
        
        for s in (s1,s2,s3):
            self.addLink(s, self.addHost('h%s' % s))
            
        super(SpanningTreeBus, self).build(*args, **kwargs)