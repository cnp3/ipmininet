#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 19 15:03:29 2019

@author: augustin
"""

from ipmininet.iptopo import IPTopo

class SpanningTreeComplex(IPTopo):
    
    def build(self, *args, **kwargs):
        """
        +-----+     +-----+
        | s10 |     | s11 |
        +--+--+     +--+--+
           |   \   /   |
           |    \ /    |
           |     \     |
           |    / \    |
           |   /   \   |
        +--+--+     +--+--+ 
        | s1  +-----+ s2  |
        +--+--+     +--+--+
           |   \   /   |
           |    \ /    |
           |     \     |
           |    / \    |
           |   /   \   |
        +--+--+     +--+--+
        | S3  +-----+ S4  |
        +--+--+     +--+--+
           |   \   /   |
           |    \ /    |
           |     \     |
           |    / \    |
           |   /   \   |
        +--+--+     +--+--+
        | S12 |     | S17 |
        +-----+     +-----+
        """
        s10 =  self.addSwitch("s10", stp=True, prio=10)
        s11 =  self.addSwitch("s11", stp=True, prio=11)
        s1 =  self.addSwitch("s1", stp=True, prio=1)
        s2 =  self.addSwitch("s2", stp=True, prio=2)
        s3 =  self.addSwitch("s3", stp=True, prio=3)
        s4 =  self.addSwitch("s4", stp=True, prio=4)
        s12 =  self.addSwitch("s12", stp=True, prio=12)
        s17 =  self.addSwitch("s17", stp=True, prio=17)
        
        self.addLink(s10,s1)
        self.addLink(s10,s2)
        self.addLink(s11,s1)
        self.addLink(s11,s2)
        self.addLink(s1,s2)
        self.addLink(s1,s3)
        self.addLink(s1,s4)
        self.addLink(s2,s3)
        self.addLink(s2,s4)
        self.addLink(s3,s4)
        self.addLink(s3,s12)
        self.addLink(s3,s17)
        self.addLink(s4,s12)
        self.addLink(s4,s17)
        
        for s in (s10,s11,s1,s2,s3,s4,s12,s17):
            self.addLink(s, self.addHost('h%s' % s))
            
        super(SpanningTreeComplex, self).build(*args, **kwargs)