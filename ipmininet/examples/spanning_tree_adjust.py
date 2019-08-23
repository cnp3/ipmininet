#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 23 09:48:24 2019

@author: augustin
"""
from ipmininet.iptopo import IPTopo

class SpanningTreeAdjust(IPTopo):
    
    def build(self, *args, **kwargs):
        """
        === Full topology ===      
        
           +------------------------+
           |s6.2                    |
        +--+--+          +-----+    |
        | s6  +          | s2  |    |
        +--+--+          ++---++    |
           |s6.1      s2.1|   |s2.2 |
           |              |   |     |
           |s3.4      s1.1|   |s4.2 |
        +--+--+s3.1  s1.3++---++    |
        | s3  +----------+ s1  |    |
        +--+--+          +--+--+    |
       s3.2|   \s3.3        |s1.4   |
           |    \           |       |
           |     \          |       |
           |      \         |       |
           |       \        |       |
           |        \       |       |
           |         \      |       |
           |          \     |       |
           |           \    |       |
           |s4.1    s5.2\   |s5.1   |
        +--+--+          +--+--+    |
        | s4  +----------+ s5  +----+
        +-----+s4.2  s5.3+-----+ s5.4
        
        === Spanning tree ===
        
        +--+--+          +-----+    
        | s6  +          | s2  |    
        +--+--+          ++---++    
           |s6.1      s2.1|    
           |              | 
           |s3.4      s1.1|    
        +--+--+s3.1  s1.3++---++    
        | s3  +----------+ s1  |    
        +--+--+          +--+--+    
       s3.2|                |s1.4   
           |                |       
           |                |       
           |                |       
           |                |       
           |                |       
           |                |
           |                |       
           |                |       
           |s4.1            |s5.1   
        +--+--+          +--+--+    
        | s4  +          + s5  +
        +-----+          +-----+ 
        
        === Adjust 2 weights to get ===
            
           +------------------------+
           |s6.2                    |
        +--+--+          +-----+    |
        | s6  +          | s2  |    |
        +--+--+          ++---++    |
                              |s2.2 |
                              |     |
                              |s4.2 |
        +--+--+          ++---++    |
        | s3  +          + s1  |    |
        +--+--+          +--+--+    |
               \s3.3        |s1.4   |
                \           |       |
                 \          |       |
                  \         |       |
                   \        |       |
                    \       |       |
                     \      |       |
                      \     |       |
                       \    |       |
                    s5.2\   |s5.1   |
        +--+--+          +--+--+    |
        | s4  +----------+ s5  +----+
        +-----+s4.2  s5.3+-----+ s5.4
        """
        #adding switches
        s1 =  self.addSwitch("s1", stp=True, prio=1)
        s2 =  self.addSwitch("s2", stp=True, prio=2)
        s3 =  self.addSwitch("s3", stp=True, prio=3)
        s4 =  self.addSwitch("s4", stp=True, prio=4)
        s5 =  self.addSwitch("s5", stp=True, prio=5)
        s6 =  self.addSwitch("s6", stp=True, prio=6)
        
        #adding links
        self.addLink(s1,s2)
        self.addLink(s1,s2)
        self.addLink(s1,s3)
        self.addLink(s1,s5)
        self.addLink(s3,s4)
        self.addLink(s3,s5)
        self.addLink(s3,s6)
        self.addLink(s4,s5)
        self.addLink(s5,s6)
        
        super(SpanningTreeAdjust, self).build(*args, **kwargs)