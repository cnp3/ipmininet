from .base import Daemon
from .utils import ConfigDict
from ipmininet.utils import realIntfList

RA_DEFAULT_VALID = 86400
RA_DEFAULT_PREF = 14400
DEFAULT_ADV_RDNSS_LIFETIME = 25


class AdvPrefix(ConfigDict):
    """The class representing an advertised prefix in a Router Advertisement"""

    def __init__(self, prefix, valid_lifetime=RA_DEFAULT_VALID,
                 preferred_lifetime=RA_DEFAULT_PREF):
        """:param prefix: the IPv6 prefix to advertise
           :param valid_lifetime: corresponds to the AdvValidLifetime
                                  in radvd.conf(5) for this prefix
           :param preferred_lifetime: corresponds to the AdvPreferredLifetime
                                      in radvd.conf(5) for this prefix"""
        super(AdvPrefix, self).__init__()
        self["prefix"] = prefix
        self["valid_lifetime"] = valid_lifetime
        self["preferred_lifetime"] = preferred_lifetime


class AdvRDNSS(ConfigDict):
    """The class representing an advertised DNS server in a
    Router Advertisement"""

    def __init__(self, ip, max_lifetime=DEFAULT_ADV_RDNSS_LIFETIME):
        """:param ip: the IPv6 address of the DNS server
           :param max_lifetime: corresponds to the AdvValidLifetime
                                in radvd.conf(5) for this dns server address"""
        super(AdvRDNSS, self).__init__()
        self["ip"] = ip
        self["max_lifetime"] = max_lifetime


class RADVD(Daemon):
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
        return cfg

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

