"""This module defines IP(6)Table configuration. Due to the current (sad)
state of affairs of IPv6, one is required to explicitely make two different
daemon instances, one to manage iptables, one to manage ip6tables ..."""
from itertools import groupby
from operator import attrgetter


from .base import Daemon


class IPTables(Daemon):
    """iptables: the default Linux firewall/ACL engine for IPv4.
    This is currently mainly a proxy class to generate a list of static rules
    to pass to iptables.

    As such, see `man iptables` and `man iptables-extensions` to see the
    various table names, commands, pre-existing chains, ..."""

    NAME = 'iptables'

    @property
    def startup_line(self):
        return '{name}-restore {fname}'.format(name=self.NAME,
                                               fname=self.cfg_filename)

    @property
    def dry_run(self):
        return '{name}-restore -vt {fname}'.format(name=self.NAME,
                                                   fname=self.cfg_filename)

    def set_defaults(self, defaults):
        """
        :param rules: The (ordered) list of iptables rules that should be
                      executed. If a rule is an iterable of strings,
                      these will be joined using a space."""
        defaults.rules = []
        super(IPTables, self).set_defaults(defaults)

    def build(self):
        cfg = super(IPTables, self).build()
        table_name = attrgetter('table')
        cfg.rules = {k: [str(x) for x in v]
                     for k, v in groupby(sorted(self.options.rules,
                                                key=table_name),
                                         table_name)}
        return cfg


class IP6Tables(IPTables):
    """The IPv6 counterpart to iptables ..."""

    NAME = 'ip6tables'
    # Everything else is already handled through iptables (and ip6tables.mako)


class Rule(object):
    """A wrapper to represent an IPTable rule"""
    def __init__(self, *args, **kw):
        """:param args: the rule members, which will joined by a whitespace
        :param table: Specify the table in which the rule should be installed.
                      Defaults to filter."""
        self.args = list(args)
        self.table = kw.get('table', 'filter')
        super(Rule, self).__init__()

    def __str__(self):
        return ' '.join(self.args)
    __repr__ = __str__
