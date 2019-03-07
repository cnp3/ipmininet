"""This modules provides a config object for a router,
that is able to provide configurations for a set of routing daemons.
It also defines the base class for a routing daemon, as well as a minimalistic
configuration for a router."""
import os
import abc
from contextlib import closing
from operator import attrgetter
from ipaddress import ip_address

from .utils import ConfigDict, template_lookup, ip_statement
from ipmininet.utils import require_cmd, realIntfList
from ipmininet.link import address_comparator

import mako

from mininet.log import lg as log


last_routerid = ip_address(u'0.0.0.1')


class RouterConfig(object):
    """This class manages a set of daemons, and generates the global
    configuration for a router"""

    def __init__(self, node, daemons=(), sysctl=None,
                 *args, **kwargs):
        """Initialize our config builder

        :param node: The node for which this object will build configurations
        :param daemons: an iterable of active routing daemons for this node
        :param sysctl: A dictionnary of sysctl to set for this node.
                       By default, it enables IPv4/IPv6 forwarding on all
                       interfaces."""
        self._node = node  # The node for which we will build the configuration
        self._daemons = {}  # Active daemons
        map(self.register_daemon, daemons)
        self._cfg = ConfigDict()  # Our root config object
        self._sysctl = {'net.ipv4.ip_forward': 1,
                        'net.ipv6.conf.all.forwarding': 1}
        self.routerid = None
        if sysctl:
            self._sysctl.update(sysctl)
        super(RouterConfig, self).__init__(*args, **kwargs)

    def build(self):
        """Build the configuration for each daemon, then write the
        configuration files"""
        self._cfg.clear()
        self._cfg.password = self._node.password
        self._cfg.name = self._node.name
        # Check that all daemons have their dependencies satisfied
        map(self.register_daemon,
            (c for cls in self._daemons.values()
             for c in cls.DEPENDS if c.NAME not in self._daemons))
        # Set the router id
        self.routerid = self.compute_routerid()
        # Build their config
        for name, d in self._daemons.iteritems():
            self._cfg[name] = d.build()
        # Write their config, using the global ConfigDict to handle
        # dependencies
        for d in self._daemons.itervalues():
            cfg = d.render(self._cfg)
            d.write(cfg)

    def cleanup(self):
        """Cleanup all temporary files for the daemons"""
        for d in self._daemons.itervalues():
            d.cleanup()

    def register_daemon(self, cls, **daemon_opts):
        """Add a new daemon to this configuration

        :param cls: Daemon class or object, or a 2-tuple (Daemon, dict)
        :param daemon_opts: Options to set on the daemons"""
        try:
            cls, kw = cls
            daemon_opts.update(kw)
        except TypeError:
            pass
        if cls.NAME in self._daemons:
            return
        if not isinstance(cls, Daemon):
            if issubclass(cls, Daemon):
                cls = cls(self._node, **daemon_opts)
            else:
                raise TypeError('Expected an object or a subclass of '
                                'Daemon, got %s instead' % cls)
        else:
            cls.options.update(daemon_opts)
        self._daemons[cls.NAME] = cls
        require_cmd(cls.NAME, 'Could not find an executable for a daemon!')

    @property
    def sysctl(self):
        """Return an iterator over all sysctl to set on this node"""
        return self._sysctl.iteritems()

    @sysctl.setter
    def sysctl(self, *values):
        """Sets sysctl to particular value.
        :param values: sysctl strings, as `key=val`
        Example:  RouterConfig().sysctl = 'net.ipv4.ip_forward=1',
                                          'net.ipv6.conf.all.forwarding=1'"""
        for value in values:
            try:
                key, val = value.split('=')
                self._sysctl[key] = val
            except ValueError:
                raise ValueError('sysctl must be specified using `key=val` '
                                 'format. Ignoring %s' % value)

    @property
    def daemons(self):
        return sorted(self._daemons.itervalues(), key=attrgetter('PRIO'))

    def daemon(self, key):
        """Return the Daemon object in this config for the given key
        :param key: the daemon name or a daemon class or instance
        :return the Daemon object
        :raise KeyError: if not found"""
        if not isinstance(key, basestring):
            key = key.NAME
        return self._daemons[key]

    @staticmethod
    def incr_last_routerid():
        global last_routerid
        last_routerid += 1

    def _equal_routerid(self, n):

        # Router id of 'n' already set
        if n.config.routerid:
            return str(n.config.routerid) != str(last_routerid)

        # Check that a router id explicitly set
        # in any other daemon is not in conflict
        # with the current router id
        for d in n.config.daemons:
            if d != self \
                    and d.options.routerid \
                    and str(d.options.routerid) == str(last_routerid):
                return True

        # Check that the most-visible IPv4 address is not in conflict
        # with the current router id
        ip_list = sorted((ip for itf in realIntfList(n)
                          for ip in itf.ips()),
                         cmp=address_comparator)
        if len(ip_list) != 0 \
                and str(ip_list.pop().ip) == str(last_routerid):
            return True

        return False

    def compute_routerid(self):
        """Computes the default router id for all daemons.
        If a router ids were explicitly set for some of its daemons,
        the router id set to the daemon with the highest priority is chosen as the global router id.
        Otherwise if it has IPv4 addresses, it returns the most-visible one among its router interfaces.
        If both conditions are wrong, it generates a unique router id."""

        for d in self.daemons:
            if d.options.routerid:
                return d.options.routerid

        ip_list = sorted((ip for itf in realIntfList(self._node)
                          for ip in itf.ips()),
                         cmp=address_comparator)
        if len(ip_list) == 0:

            to_visit = realIntfList(self._node)
            # Explore all routers to check that none has the same router id
            while to_visit:
                self.incr_last_routerid()
                visited = set()
                while to_visit:
                    i = to_visit.pop()
                    if i in visited:
                        continue
                    visited.add(i)
                    for n in i.broadcast_domain.routers:
                        if self._equal_routerid(n.node):
                            break  # We need to change the router id
                        to_visit.extend(realIntfList(n.node))
                to_visit = realIntfList(self._node) if to_visit else []
            return last_routerid.compressed
        else:
            id = ip_list.pop().ip.compressed
            return id


class Daemon(object):
    """This class serves as base for routing daemons"""
    __metaclass__ = abc.ABCMeta
    # The name of this routing daemon
    NAME = None
    # The priority of this daemon, relative to others
    # (e.g. to define startup order)
    PRIO = 10
    # The eventual dependencies of this daemon on other daemons
    DEPENDS = ()
    # The kill patterns to cleanup any processes started by this daemon
    KILL_PATTERNS = ()

    def __init__(self, node, **kwargs):
        """:param node: The node for which we build the config
        :param kwargs: Pre-set options for the daemon, see defaults()"""
        self._node = node
        self._startup_line = None
        self.files = []
        self._options = self._defaults(**kwargs)
        super(Daemon, self).__init__()

    @property
    def options(self):
        """Get the options ConfigDict for this daemon"""
        return self._options

    def build(self):
        """Build the configuration tree for this daemon

        :return: ConfigDict-like object describing this configuration"""
        cfg = ConfigDict()
        cfg.logfile = self._options['logfile']
        cfg.routerid = self._options.routerid if self._options.routerid \
                                              else self._node.config.routerid
        return cfg

    def cleanup(self):
        """Cleanup the files belonging to this daemon"""
        for f in self.files:
            try:
                os.unlink(f)
            except (IOError, OSError):
                pass
        self.files = []

    def render(self, cfg, **kwargs):
        """Render the configuration file for this daemon

        :param cfg: The global config for the node
        :param kwargs: Additional keywords args. will be passed directly
                       to the template"""
        self.files.append(self.cfg_filename)
        log.debug('Generating %s\n' % self.cfg_filename)
        try:
            return template_lookup.get_template(self.template_filename)\
                                  .render(node=cfg,
                                          ip_statement=ip_statement,
                                          **kwargs)
        except:
            # Display template errors in a less cryptic way
            log.error('Couldn''t render a config file(',
                      self.template_filename, ')')
            log.error(mako.exceptions.text_error_template().render())
            raise ValueError('Cannot render a configuration [%s: %s]' % (
                self._node.name, self.NAME))

    def write(self, cfg):
        """Write down the configuration for this daemon

        :param cfg: The configuration string"""
        with closing(open(self.cfg_filename, 'w')) as f:
            f.write(cfg)

    @abc.abstractproperty
    def startup_line(self):
        """Return the corresponding startup_line for this daemon"""

    @abc.abstractproperty
    def dry_run(self):
        """The startup line to use to check that the daemon is
        well-configured"""

    def _filename(self, suffix):
        """Return a filename for this daemon and node,
        with the specified suffix"""
        return '%s_%s.%s' % (self.NAME, self._node.name, suffix)

    def _filepath(self, f):
        """Return a path towards a given file"""
        return os.path.join(self._node.cwd, f)

    def _file(self, suffix):
        """Generates a file name in the daemon's node cwd"""
        return self._filepath(self._filename(suffix=suffix))

    @property
    def cfg_filename(self):
        """Return the filename in which this daemon config should be stored"""
        return self._file(suffix='cfg')

    @property
    def template_filename(self):
        return '%s.mako' % self.NAME

    def _defaults(self, **kwargs):
        """Return the default options for this daemon

        :param logfile: the path to the logfile for the daemon
        :param routerid: the router id for this daemon"""
        defaults = ConfigDict()
        defaults.logfile = self._file('log')
        # Apply daemon-specific defaults
        self.set_defaults(defaults)
        # Use user-supplied defaults if present
        defaults.update(**kwargs)
        return defaults

    @abc.abstractmethod
    def set_defaults(self, defaults):
        """Update defaults to contain the defaults specific to this daemon"""

    def has_started(self):
        """Return whether this daemon has started or not"""
        return True


class BasicRouterConfig(RouterConfig):
    """A basic router that will run an OSPF daemon"""

    def __init__(self, node, daemons=(), additional_daemons=(), *args, **kwargs):
        """A simple router made of at least an OSPF daemon

        :param additional_daemons: Other daemons that should be used"""
        # Importing here to avoid circular import
        from ospf import OSPF
        from ospf6 import OSPF6
        # We don't want any zebra-specific settings, so we rely on the OSPF/OSPF6
        # DEPENDS list for that daemon to run it with default settings
        # We also don't want specific settings beside the defaults, so we don't
        # provide an instance but the class instead
        d = list(daemons)
        if node.use_v4:
            d.append(OSPF)
        if node.use_v6:
            d.append(OSPF6)
        d.extend(additional_daemons)
        super(BasicRouterConfig, self).__init__(node, daemons=d,
                                                *args, **kwargs)
