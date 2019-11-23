"""Base classes to configure a Named daemon"""
from builtins import str

import os

import ipaddress
from mininet.log import lg

from ipmininet.overlay import Overlay
from ipmininet.utils import realIntfList, find_node, has_cmd
from ipmininet.router.config.utils import ConfigDict
from .base import HostDaemon

DNS_REFRESH = 86400
DNS_RETRY = 7200
DNS_EXPIRE = 3600000
DNS_MIN_TTL = 172800


class Named(HostDaemon):
    NAME = 'named'
    KILL_PATTERNS = (NAME,)

    def __init__(self, node, **kwargs):
        # Check if apparmor is enabled in the distribution
        self.apparmor = has_cmd("aa-exec")
        super(Named, self).__init__(node, **kwargs)

    @property
    def startup_line(self):
        # This runs the daemon outside of AppArmor's restrictions
        return '{apparmor}{name} -c {cfg} -f -u root -p {port}' \
            .format(apparmor="aa-exec -p unconfined " if self.apparmor else "",
                    name=self.NAME,
                    cfg=self.cfg_filename,
                    port=self.options.dns_server_port)

    @property
    def dry_run(self):
        return '{name} {cfg}' \
            .format(name='named-checkconf', cfg=self.cfg_filename)

    def build(self):
        cfg = super(Named, self).build()
        cfg.log_severity = self.options.log_severity
        cfg.abs_logfile = os.path.abspath(cfg.logfile)

        cfg.zones = ConfigDict()
        for zone in self._node.get('dns_zones', []):
            cfg.zones[self.zone_filename(zone.name)] = self.build_zone(zone)

        self.build_reverse_zone(cfg.zones)
        return cfg

    def build_zone(self, zone):
        master_ips = []
        for s_name in zone.servers + [zone.dns_master] + zone.dns_slaves:
            server = find_node(self._node, s_name).node
            for itf in realIntfList(server):
                for ip in itf.ips():
                    if ".arpa" not in zone.name:  # Not a Reverse zone
                        zone.soa_record.add_record(ARecord(s_name,
                                                           ip.ip.compressed))
                    if s_name == zone.dns_master:
                        master_ips.append(ip.ip.compressed)

                for ip in itf.ip6s(exclude_lls=True):
                    if ".arpa" not in zone.name:  # Not a Reverse zone
                        zone.soa_record.add_record(AAAARecord(s_name,
                                                              ip.ip.compressed))
                    if s_name == zone.dns_master:
                        master_ips.append(ip.ip.compressed)

        return ConfigDict(name=zone.soa_record.domain_name,
                          soa_record=zone.soa_record,
                          records=zone.soa_record.records,
                          master=self._node.name == zone.dns_master,
                          master_ips=master_ips)

    def build_reverse_zone(self, cfg_zones):
        """
        Build non-existing PTR records. Then, adds them to an existing reverse
        zone if any. The remaining ones are inserted in a new reverse zone
        that is added to cfg_zones dictionary.
        """
        # Build PTR records
        ptr_records = []
        for zone in cfg_zones.values():
            for record in zone.soa_record.records:
                if record.rtype != "A" and record.rtype != "AAAA":
                    continue

                domain_name = record.domain_name if record.full_domain_name \
                    else record.domain_name + "." + zone.name
                ptr_records.append(PTRRecord(record.address, domain_name,
                                             ttl=record.ttl))

        existing_records = [record for zone in cfg_zones.values()
                            for record in zone.soa_record.records
                            if record.rtype == "PTR"]

        ptr_v6_records = []
        ptr_v4_records = []
        for record in ptr_records:
            # Filter out existing PTR records
            if record in existing_records:
                continue
            # Try to place the rest in existing reverse DNS zones
            found = False
            for zone in cfg_zones.values():
                if zone.name in record.domain_name:
                    zone.soa_record.records.append(record)
                    found = True
                    break
            # The rest needs a new DNS zone
            if not found:
                if record.v6:
                    ptr_v6_records.append(record)
                else:
                    ptr_v4_records.append(record)

        # Create new reverse DNS zones for remaining PTR records
        if len(ptr_v6_records) > 0:
            self.build_largest_reverse_zone(cfg_zones, ptr_v6_records)
        if len(ptr_v4_records) > 0:
            self.build_largest_reverse_zone(cfg_zones, ptr_v4_records)

    def build_largest_reverse_zone(self, cfg_zones, records):
        """
        Create the ConfigDict object representing a new reverse zone whose
        prefix is the largest one that includes all the PTR records.
        Then it adds it to the cfg_zones dict.

        :param cfg_zones: The dict of ConfigDict representing existing zones
        :param records: The list of PTR records to place a new reverse zone
        """
        if len(records) == 0:
            return

        # Find common prefix between all records
        common = records[0].domain_name.split(".")
        for i in range(1, len(records)):
            prefix = records[i].domain_name.split(".")
            for j in range(1, len(common)):
                if prefix[len(prefix)-j] != common[len(common)-j]:
                    common = common[len(prefix)+1-j:]
                    break
        domain_name = ".".join(common)

        # Retrieve the NS Record for the new zone
        ns_record = None
        for zone in cfg_zones.values():
            if "arpa" in zone.name:
                continue
            for record in zone.soa_record.records:
                if record.rtype == "NS" \
                        and self._node.name in record.name_server:
                    ns_record = NSRecord(record.domain_name, self._node.name)
                    ns_record.domain_name = domain_name
        if ns_record is None:
            lg.warning("Cannot forge a DNS reverse zone because there is no"
                       " NS Record for this node in regular zones.\n")
            return
        records.append(ns_record)

        # Build the reverse zone
        soa_record = SOARecord(domain_name=domain_name, records=records)

        reverse_zone = ConfigDict(name=soa_record.domain_name,
                                  soa_record=soa_record,
                                  records=soa_record.records,
                                  master=True,
                                  master_ips=[])
        self._node.params.setdefault('dns_zones', []).append(reverse_zone)
        cfg_zones[self.zone_filename(reverse_zone.name)] = reverse_zone

    def set_defaults(self, defaults):
        """:param log_severity: It controls the logging levels and may take the
               values defined. Logging will occur for any message equal to or
               higher than the level specified (=>) lower levels will not be
               logged. These levels are 'critical', 'error', 'warning',
               'notice', 'info', 'debug' and 'dynamic'.
        :param dns_server_port: The port number of the dns server"""
        defaults.log_severity = "warning"
        defaults.dns_server_port = 53
        super(Named, self).set_defaults(defaults)

    def zone_filename(self, domain_name):
        return self._file(suffix='%s.cfg' % domain_name)

    @property
    def cfg_filenames(self):
        return super(Named, self).cfg_filenames + \
               [self.zone_filename(z.name)
                for z in self._node.get('dns_zones', [])]

    @property
    def template_filenames(self):
        return super(Named, self).template_filenames + \
               ["%s-zone.mako" % self.NAME
                for _ in self._node.get('dns_zones', [])]


class DNSRecord(object):

    def __init__(self, rtype, domain_name, ttl=60):
        self.rtype = rtype
        self.domain_name = domain_name
        self.ttl = ttl

        if self.domain_name[-1] != "." and "." in self.domain_name:
            # Full DNS names should be ended by a dot in the config
            self.domain_name = self.domain_name + "."

    @property
    def rdata(self):
        return ""

    @property
    def full_domain_name(self):
        return "." in self.domain_name

    def __eq__(self, other):
        return self.rtype == other.rtype \
               and self.domain_name == other.domain_name \
               and self.rdata == other.rdata


class ARecord(DNSRecord):

    def __init__(self, domain_name, address, ttl=60):
        self.address = ipaddress.ip_address(str(address))
        rtype = "A" if self.address.version == 4 else "AAAA"
        super(ARecord, self).__init__(rtype=rtype, domain_name=domain_name,
                                      ttl=ttl)

    @property
    def rdata(self):
        return self.address.compressed


class AAAARecord(ARecord):
    pass  # ARecord already handles IPv6 addresses


class PTRRecord(DNSRecord):

    def __init__(self, address, domain_name, ttl=60):
        self.address = ipaddress.ip_address(str(address))
        self.mapped_domain_name = domain_name
        if self.mapped_domain_name[-1] != "." \
                and "." in self.mapped_domain_name:
            # Full DNS names should be ended by a dot in the config
            self.mapped_domain_name = self.mapped_domain_name + "."
        super(PTRRecord, self).__init__("PTR", self.address.reverse_pointer,
                                        ttl=ttl)

    @property
    def v6(self):
        return self.address.version == 6

    @property
    def rdata(self):
        return self.mapped_domain_name


class NSRecord(DNSRecord):

    def __init__(self, domain_name, name_server, ttl=60):
        super(NSRecord, self).__init__(rtype="NS", domain_name=domain_name,
                                       ttl=ttl)
        self.name_server = name_server
        if "." not in self.name_server:
            self.name_server = self.name_server + "." + self.domain_name

        if self.name_server[-1] != ".":
            # Full DNS names should be ended by a dot in the config
            self.name_server = self.name_server + "."

    @property
    def rdata(self):
        return self.name_server


class SOARecord(DNSRecord):

    def __init__(self, domain_name, refresh_time=DNS_REFRESH,
                 retry_time=DNS_RETRY, expire_time=DNS_EXPIRE,
                 min_ttl=DNS_MIN_TTL, records=()):
        super(SOARecord, self).__init__(rtype="SOA", domain_name=domain_name,
                                        ttl=min_ttl)
        self.refresh_time = refresh_time
        self.retry_time = retry_time
        self.expire_time = expire_time
        self._records = list(records)

    @property
    def rdata(self):
        return "{domain_name} sysadmin.{domain_name} (\n1 ; serial\n{refresh}" \
               " ; refresh timer\n{retry} ; retry timer\n{expire}" \
               " ; retry timer\n{min_ttl} ; minimum ttl\n)"\
            .format(domain_name=self.domain_name, refresh=self.refresh_time,
                    retry=self.retry_time, expire=self.expire_time,
                    min_ttl=self.ttl)

    @property
    def records(self):
        return self._records

    def add_record(self, record):
        if record not in self._records:
            self._records.append(record)


class DNSZone(Overlay):

    def __init__(self, name, dns_master, dns_slaves=(), records=(), nodes=(),
                 refresh_time=DNS_REFRESH, retry_time=DNS_RETRY,
                 expire_time=DNS_EXPIRE, min_ttl=DNS_MIN_TTL,
                 ns_domain_name=None):
        """
        :param name: The domain name of the zone
        :param dns_master: The name of the master DNS server
        :param dns_slaves: The list of names of DNS slaves
        :param records: The list of DNS Records to be included in the zone
        :param nodes: The list of nodes for which one A/AAAA record has to be
                      created for each of their IPv4/IPv6 addresses
        :param refresh_time: The number of seconds before the zone should be
                             refreshed
        :param retry_time: The number of seconds before a failed refresh should
                           be retried
        :param expire_time: The upper limit in seconds before a zone is
                            considered no longer authoritative
        :param min_ttl: The negative result TTL
        :param ns_domain_name: If it is defined, it is the suffix of the domain
                               of the name servers, otherwise, parameter 'name'
                               is used.
        """
        self.name = name
        self.dns_master = dns_master
        self.dns_slaves = list(dns_slaves)
        self.records = records
        self.servers = list(nodes)
        self.soa_record = SOARecord(name, refresh_time=refresh_time,
                                    retry_time=retry_time,
                                    expire_time=expire_time, min_ttl=min_ttl,
                                    records=records)
        super(DNSZone, self).__init__(nodes=[dns_master] + list(dns_slaves))

        self.consistent = True
        for node_name in [dns_master] + self.dns_slaves + self.servers:
            if "." in node_name:
                lg.error("Cannot create zone {name} because the node name"
                         " {node_name} contains a '.'"
                         .format(name=name, node_name=node_name))
                self.consistent = False

        self.ns_domain_name = ns_domain_name if ns_domain_name is not None \
            else self.name

    def check_consistency(self, topo):
        return super(DNSZone, self).check_consistency(topo) and self.consistent

    def apply(self, topo):
        super(DNSZone, self).apply(topo)
        if not self.consistent:
            return

        # Add NS Records (if not already present)
        for n in self.nodes:
            self.soa_record.add_record(NSRecord(self.name,
                                                n + "." + self.ns_domain_name))

        for n in self.nodes:
            topo.nodeInfo(n).setdefault("dns_zones", []).append(self)
