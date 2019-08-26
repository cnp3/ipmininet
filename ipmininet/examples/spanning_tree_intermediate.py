#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 19 15:03:29 2019

@author: augustin
"""

from ipmininet.iptopo import IPTopo

class SpanningTreeIntermediate(IPTopo):
    
    def build(self, *args, **kwargs):
        """
                      +-----+
           +----------+ s2  +----------+
           |          +-----+          |
           |                           |
           |                           |
        +--+--+       +-----+       +--+--+
        | s9  +-------+ s5  +-------+ s10 |
        +-----+       +--+--+       +--+--+
                         |             |
                         |             |
                      +--+--+          |
                      | s4  +----------+
                      +-----+
        """
        s2 =  self.addSwitch("s2", stp=True, prio=2)
        s4 =  self.addSwitch("s4", stp=True, prio=4)
        s5 =  self.addSwitch("s5", stp=True, prio=5)
        s9 =  self.addSwitch("s9", stp=True, prio=9)
        s10 =  self.addSwitch("s10", stp=True, prio=10)
        
        self.addLink(s2,s9)
        self.addLink(s9,s5)
        self.addLink(s5,s4)
        self.addLink(s2,s10)
        self.addLink(s4,s10)
        self.addLink(s5,s10)
        
        for s in (s2,s4,s5,s9,s10):
            self.addLink(s, self.addHost('h%s' % s))
            
        super(SpanningTreeIntermediate, self).build(*args, **kwargs)