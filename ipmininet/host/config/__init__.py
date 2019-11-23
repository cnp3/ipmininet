"""This module holds the configuration generators for daemons
that can be used in a host."""
from .base import HostDaemon, HostConfig
from .named import Named, DNSZone, ARecord, NSRecord, AAAARecord, SOARecord,\
    PTRRecord

__all__ = ['HostConfig', 'HostDaemon', 'Named', 'DNSZone', 'ARecord',
           'NSRecord', 'AAAARecord', 'SOARecord', 'PTRRecord']
