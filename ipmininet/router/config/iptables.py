"""This module defines IP(6)Table configuration. Due to the current (sad)
state of affairs of IPv6, one is required to explicitly make two different
daemon instances, one to manage iptables, one to manage ip6tables ..."""
from itertools import groupby
from operator import attrgetter

from ipmininet.utils import is_container
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
        :param rules: The (ordered) list of iptables Rules that should be
                      executed or the list of Chain objects each containing
                      rules. If a rule is an iterable of strings, these will
                      be joined using a space."""
        defaults.rules = []
        super().set_defaults(defaults)

    def build(self):
        cfg = super().build()
        table_name = attrgetter('table')
        cfg.rules = {k: [r for x in v
                         for r in self._compile_rule(x)]
                     for k, v in groupby(sorted(self.options.rules,
                                                key=table_name),
                                         table_name)}
        return cfg

    def _compile_rule(self, rule):
        if isinstance(rule, Chain):
            return rule.build()
        return [str(rule)]


class IP6Tables(IPTables):
    """The IPv6 counterpart to iptables ..."""

    NAME = 'ip6tables'
    # Everything else is already handled through iptables (and ip6tables.mako)


class Rule:
    """A Simple wrapper to represent an IPTable rule"""
    def __init__(self, *args, **kw):
        """:param args: the rule members, which will joined by a whitespace
        :param table: Specify the table in which the rule should be installed.
                      Defaults to filter."""
        self.args = list(args)
        self.table = kw.get('table', 'filter')
        super().__init__()

    def __str__(self):
        return ' '.join(self.args)
    __repr__ = __str__


class Chain:
    """Chains are the hooks location for the respective tables.
    Tables support a limited subset of the available chains, see `man iptables`.
    """

    # See the iptables doc for the possible table->chains mappings
    TABLE_CHAINS = {
        'filter': {'INPUT', 'OUTPUT', 'FORWARD'},
        'nat': {'PREROUTING', 'INTPUT', 'OUTPUT', 'POSTROUTING'},
        'mangle': {'PREROUTING', 'INTPUT', 'OUTPUT', 'FORWARD', 'POSTROUTING'},
        'raw': {'PREROUTING', 'OUTPUT'},
        'security': {'SECMARK','CONNSECMARK', 'INPUT', 'OUTPUT', 'FORWARD'}
    }

    def __init__(self, table='filter', name='INPUT', default='DROP', rules=()):
        """Build a chain description. For convenience, most parameters have
        more intuitive aliases than their one-letter CLI params.

        :params table: The table on which the chain applies.
        :params name: The chain name
        :params default: The default verdict if nothing matches
        :params rules: The ordered list of ChainRule to apply
        """
        try:
            _table = str(table).lower()
            allowed_chains = self.TABLE_CHAINS[_table]
        except KeyError:
            raise ValueError('%s does not match to an IPTables table name' % table)

        self.table = _table
        _name = str(name).upper()
        if _name not in allowed_chains:
            raise ValueError('%s is not an allowed Chain for table %s' % (name, table))

        self.name = _name
        _default = str(default).upper()
        if _default != 'DROP' and _default != 'ACCEPT':
            raise ValueError('%s is an invalid default policy' % default)

        self.default = _default
        self.rules = rules

    def build(self):
        yield "-P {chain} {default}".format(chain=self.name, default=self.default)
        for r in self.rules:
            yield "-A {chain} {match_rule}".format(table=self.table,
                                                   chain=self.name,
                                                   match_rule=r.build())


class ChainRule:
    """Describe one set of matching criteria and the corresponding action when
    embedded in a chain."""

    # For convenience, provide more readable aliases of common parameters
    ALIASES = {alias: code for code, aliases in (
        ('o', ('oif', 'out_intf', 'out_interface')),
        ('i', ('iif', 'in_intf', 'in_interface')),
        ('s', ('src', 'source')),
        ('d', ('dst', 'destination')),
        ('p', ('proto', 'protocol')),
        ('m', ('match', 'matching')),
        ('port', ('ports')),
        ('sport', ('source_port', 'sports', 'source_ports')),
        ('dport', ('destination_port', 'dports', 'destination_ports')),
    ) for alias in aliases}
    ALIASES.update({k:k for k in ALIASES.values()})

    def __init__(self, action='DROP', **kwargs):
        """
        :params action: The action to perform on matching packets.
        :params oif: match in the output interface (optional)
        :params iif: match on the input interface (optional)
        :params src: match on the source address/network (optional)
        :params dst: match on the destination address/network (optional)
        :params proto: match on the protocol name/number (optional)
        :params match: additional matching clauses, per `man iptables` (optional)
        :params port: match on the source or destination port number/range (optional)
        :params sport: match on the source port number/range/name (optional)
        :params dport: match on the destination port number/range/name (optional)
        """
        self.action = action

        unknown_args = set(kwargs.keys()).difference(self.ALIASES.keys())
        if unknown_args:
            raise ValueError("Unknown parameters: %s" % unknown_args)

        args = {self.ALIASES[k]: v for k, v in kwargs.items()}
        self.oif = InterfaceClause('o', args)
        self.iif = InterfaceClause('i', args)
        self.src = AddressClause('s', args)
        self.dst = AddressClause('d', args)
        self.proto = MatchClause('p', args)
        self.match = MatchClause('m', args)
        self.port = PortClause('port', args)
        self.sport = PortClause('sport', args)
        self.dport = PortClause('dport', args)

    def build(self):
        sub_rule = []
        for clause in (self.oif, self.iif, self.src, self.dst, self.proto,
                       self.match, self.port, self.sport, self.dport):
            sub_rule.extend([sub_clause for sub_clause in clause.build()
                             if sub_clause is not None])
        return "%s -j %s" % (' '.join(sub_rule), self.action)


class NOT:
    def __init__(self, clause):
        """ Negates the match clause
        :param clause: The value of the match clause to negate
        """
        self.clause = clause


class MatchClause:
    def __init__(self, code, args):
        self.code = code
        self.val = args.get(code, None)
        if isinstance(self.val, NOT):
            self.val = self.val.clause
            self.negate = True
        else:
            self.negate = False
        self.prefix = ""

    def build(self):
        if self.val is None:
            yield None
        else:
            if not is_container(self.val):
                self.val = (str(self.val),)
            for v in self.val:
                for val in self.render(v):
                    yield "{prefix}{neg}-{code} {val}".format(
                        prefix=self.prefix,
                        neg='' if not self.negate else '! ',
                        code=self.code if len(self.code.split()[0]) == 1
                        else "-" + self.code, val=val)

    def render(self, v):
        # useful if we ever want to be able to expand "node objects" to their
        # interfaces/nets/...
        yield str(v)


class PortClause(MatchClause):
    def __init__(self, code, val):
        super().__init__(code, val)
        if self.val is None:
            pass
        elif not is_container(self.val):
            self.val = str(self.val)
        else:
            self.val = ','.join(self.val)
        self.prefix = "-m multiport "
        self.code = "%ss" % self.code


class InterfaceClause(MatchClause):
    pass


class AddressClause(MatchClause):
    pass


class Filter(Chain):
    """The filter table acts as inbound, outbound, and forwarding firewall."""
    def __init__(self, **kwargs):
        super().__init__(table='filter', **kwargs)


class InputFilter(Filter):
    """The inbound firewall."""
    def __init__(self, **kwargs):
        super().__init__(name='INPUT', **kwargs)


class OutputFilter(Filter):
    """The outbound firewall."""
    def __init__(self, **kwargs):
        super().__init__(name='OUTPUT', **kwargs)


class TransitFilter(Filter):
    """The forward firewall."""
    def __init__(self, **kwargs):
        super().__init__(name='FORWARD', **kwargs)


class Allow(ChainRule):
    """Shorthand for ChainRule(action='ACCEPT', ...). Expresses a whitelisting rule."""
    def __init__(self, **kwargs):
        super().__init__(action='ACCEPT', **kwargs)


class Deny(ChainRule):
    """Shorthand for ChainRule(action='DROP', ...). Expresses a blacklisting rule."""
    def __init__(self, **kwargs):
        super().__init__(action='DROP', **kwargs)
