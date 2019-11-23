"""This modules contains various utilies to streamline config generation"""
from builtins import str
from ipmininet import basestring

from ipaddress import ip_interface


class ConfigDict(dict):
    """A dictionary whose attributes are its keys.
    Be careful if subclassing, as attributes defined by doing
    assignments such as self.xx = yy in __init__ will be shadowed!"""

    def __init__(self, **kwargs):
        super(ConfigDict, self).__init__()
        for key, val in kwargs.items():
            self[key] = val

    def __getattr__(self, item):
        # so that self.item == self[item]
        try:
            # But preserve i.e. methods
            return super(ConfigDict, self).__getattr__(item)
        except Exception:
            try:
                return self[item]
            except KeyError:
                return None

    def __setattr__(self, key, value):
        # so that self.key = value <==> self[key] = key
        self[key] = value


def ip_statement(ip):
    """Return the zebra ip statement for a given ip prefix

    :type ip: ip_interface, ip_network, ip_address, int, str"""
    if not isinstance(ip, int):
        ip = (ip_interface(ip) if not isinstance(ip, basestring) else
              ip_interface(str(ip))).version
    return 'ipv6' if ip == 6 else 'ip'
