from builtins import str

from ipaddress import ip_address

from ipmininet.utils import find_node
from ipmininet.utils import realIntfList
from .base import RouterDaemon
from .utils import ConfigDict
from ipmininet.utils import is_container

RA_DEFAULT_VALID = 86400
RA_DEFAULT_PREF = 14400
DEFAULT_ADV_RDNSS_LIFETIME = 25


class AdvPrefix(ConfigDict):
    """The class representing advertised prefixes in a Router Advertisement"""

    def __init__(self, prefix=(), valid_lifetime=RA_DEFAULT_VALID,
                 preferred_lifetime=RA_DEFAULT_PREF):
        """:param prefix: the list of IPv6 prefixes to advertise
           :param valid_lifetime: corresponds to the AdvValidLifetime
                                  in radvd.conf(5) for this prefix
           :param preferred_lifetime: corresponds to the AdvPreferredLifetime
                                      in radvd.conf(5) for this prefix"""
        super(AdvPrefix, self).__init__()
        self["prefixes"] = list(prefix) if is_container(prefix) else [prefix]
        self["valid_lifetime"] = valid_lifetime
        self["preferred_lifetime"] = preferred_lifetime


class AdvConnectedPrefix(AdvPrefix):
    """This class forces the advertisement of all prefixes on the interface"""

    def __init__(self, valid_lifetime=RA_DEFAULT_VALID,
                 preferred_lifetime=RA_DEFAULT_PREF):
        """:param valid_lifetime: corresponds to the AdvValidLifetime
                                  in radvd.conf(5) for this prefix
           :param preferred_lifetime: corresponds to the AdvPreferredLifetime
                                      in radvd.conf(5) for this prefix"""
        super(AdvConnectedPrefix, self).\
            __init__(valid_lifetime=valid_lifetime,
                     preferred_lifetime=preferred_lifetime)


class AdvRDNSS(ConfigDict):
    """The class representing an advertised DNS server in a
    Router Advertisement"""

    def __init__(self, node, max_lifetime=DEFAULT_ADV_RDNSS_LIFETIME):
        """:param node: Either the IPv6 address of the DNS server
                        or the node name
           :param max_lifetime: corresponds to the AdvValidLifetime
                                in radvd.conf(5) for this dns server address"""
        super(AdvRDNSS, self).__init__()
        self["node"] = node
        self["max_lifetime"] = max_lifetime
        try:
            ip_address(str(node))
            self["ips"] = [node]
        except ValueError:
            pass


class RADVD(RouterDaemon):
    """The class representing the radvd daemon,
    used for router advertisements"""

    NAME = 'radvd'
    KILL_PATTERNS = (NAME,)

    def build(self):
        cfg = super(RADVD, self).build()
        # Update with preset defaults
        cfg.update(self.options)
        # Track interfaces
        cfg.interfaces = (ConfigDict(name=itf.name, description=itf.describe,
                                     ra_prefixes=itf.ra_prefixes,
                                     rdnss_list=itf.rdnss_list)
                          for itf in realIntfList(self._node)
                          if itf.ra_prefixes)
        # Fill AdvConnectedPrefix prefixes
        self._fill_connected_prefixes()
        # Fill AdvRDNSS IP addresses
        self._fill_rdnss_addresses()
        return cfg

    def _fill_connected_prefixes(self):
        for itf in realIntfList(self._node):
            for ra_prefix in itf.ra_prefixes:
                if isinstance(ra_prefix, AdvConnectedPrefix):
                    for ip in itf.ip6s(exclude_lls=True):
                        ra_prefix.prefixes.append(ip.network.with_prefixlen)

    def _fill_rdnss_addresses(self):
        for itf in realIntfList(self._node):
            for rdnss in itf.rdnss_list:
                if rdnss.ips is None:
                    rdnss.ips = []
                    dns = find_node(self._node, rdnss.node).node
                    for dns_itf in realIntfList(dns):
                        for ip in dns_itf.ip6s(exclude_lls=True):
                            rdnss.ips.append(ip.ip.compressed)

    def set_defaults(self, defaults):
        """
        :param debuglevel: Turn on debugging information. Takes an integer
                           between 0 and 5, where 0 completely turns off
                           debugging, and 5 is extremely verbose.
                           (see radvd(8) for more details)"""
        defaults.debuglevel = 0
        super(RADVD, self).set_defaults(defaults)

    @property
    def startup_line(self):
        return ('radvd -d {debuglevel} -C {cfg} -p {pid} -m logfile -l {log}'
                ' -u root'.format(debuglevel=self.options.debuglevel,
                                  cfg=self.cfg_filename, log=self._file('log'),
                                  pid=self._file('pid')))

    @property
    def dry_run(self):
        return 'radvd -c -C {cfg} -u root'.format(cfg=self.cfg_filename)

    def cleanup(self):
        try:
            with open(self._file('pid'), 'r') as f:
                for line in f:
                    if len(line) > 1:
                        pid = int(line[:-1])
                        self._node._processes.call('kill -9 %d ' % pid)
        except (IOError, OSError):
            pass
        super(RADVD, self).cleanup()
