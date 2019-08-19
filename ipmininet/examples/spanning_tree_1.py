#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 21 09:50:11 2019

@author: augustin
"""

from ipmininet.iptopo import IPTopo

class SpanningTree1(IPTopo):
    
    def build(self, *args, **kwargs):
        """
          +-----+s3.2   ||   s17.1+-----+s17.2  ||  s10.1+-----+
          | s3  +-------||--------+ s17 +-------||-------+ s10 |
          +-----+       ||        +-----+       ||       +--+--+
             |s3.1      ||                                  | s10.2
             |          ||                                  |
             |          ||[hub s99]                      =======
             |          ||                                  |
             |          ||                                  |s11.1
             |          ||    s6.2+-----+ s6.3  ||  s11.3+--+--+
          =======       ||--------+ s6  +-------||-------+ s11 |
             |          ||        +--+--+       ||       +--+--+
             |                       |s6.1                  |s11.2
             |                       |                      | 
             |                ===================================[hub s100]
             |s12.1             |
          +--+--+               |
          | s12 +---------------+
          +-----+s12.2
        """
        #adding switches
        s3 =  self.addSwitch("s3", stp=True, prio=3)
        s6 =  self.addSwitch("s6", stp=True, prio=6)
        s10 =  self.addSwitch("s10", stp=True, prio=10)
        s11 =  self.addSwitch("s11", stp=True, prio=11)
        s12 =  self.addSwitch("s12", stp=True, prio=12)
        s17 =  self.addSwitch("s17", stp=True, prio=17)
        #hubs
        s99 =  self.addSwitch("s99", stp=False, hub=True) # Hub
        s100 =  self.addSwitch("s100", stp=False, hub=True) # Hub
        
        #1 to 1 links
        self.addLink(s3,s12,port1=1,port2=1)
        self.addLink(s17,s10,port1=2,port2=1)
        self.addLink(s10,s11,port1=2,port2=1)
        #self.addLink(s6,s11,port1=3, port2=3)
        
        #links with hubs
        self.addLink(s3,s99, cost=0.5)#hub s99
        self.addLink(s17,s99, cost=0.5)
        self.addLink(s6,s99, cost=0.5)
        
        self.addLink(s6,s100, cost=0.5)#hub s100
        self.addLink(s11,s100, cost=0.5)
        self.addLink(s12,s100, cost=0.5)
        
        for s in (s3,s6,s10,s11,s12,s17):
            self.addLink(s, self.addHost('h%s' % s))
            
        super(SpanningTree1, self).build(*args, **kwargs)
