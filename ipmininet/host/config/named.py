"""Base classes to configure a Named daemon"""
import copy
import os
import re
from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import List, Union, Sequence, Optional

from mininet.log import lg

from ipmininet.overlay import Overlay
from ipmininet.router.config.utils import ConfigDict
from ipmininet.utils import realIntfList, find_node, has_cmd
from .base import HostDaemon

DNS_REFRESH = 86400
DNS_RETRY = 7200
DNS_EXPIRE = 3600000
DNS_MIN_TTL = 172800
DNS_ROOT = "."


def dns_base_name(full_name: str) -> str:
    return full_name.split(".")[0]


def dns_join_name(base_name: str, dns_zone: str) -> str:
    return base_name + ("." + dns_zone if dns_zone != DNS_ROOT
                        else DNS_ROOT)


def is_reverse_zone(zone_name: str) -> bool:
    return re.search(r"\.arpa\.$", zone_name) is not None


class Named(HostDaemon):
    NAME = 'named'
    KILL_PATTERNS = (NAME,)

    def __init__(self, node, **kwargs):
        # Check if apparmor is enabled in the distribution
        self.apparmor = has_cmd("aa-exec")
        self.additional_zone_filenames = []
        super().__init__(node, **kwargs)

    @property
    def startup_line(self):
        # This runs the daemon outside of AppArmor's restrictions
        return '{apparmor}{name} -c {cfg} -f -u root -t / -p {port}' \
            .format(apparmor="aa-exec -p unconfined " if self.apparmor else "",
                    name=self.NAME,
                    cfg=self.cfg_filename,
                    port=self.options.dns_server_port)

    @property
    def dry_run(self):
        return '{name} {cfg}' \
            .format(name='named-checkconf', cfg=self.cfg_filename)

    def build(self):
        cfg = super().build()
        cfg.log_severity = self.options.log_severity
        cfg.abs_logfile = os.path.abspath(cfg.logfile)

        cfg.zones = ConfigDict()
        root_zone_found = False
        for zone in self._node.get('dns_zones', []):
            root_zone_found = root_zone_found or zone.name == DNS_ROOT
            cfg.zones[self.zone_filename(zone.name)] = self.build_zone(zone)

        self.build_reverse_zone(cfg.zones)

        root = self._node.get('root_zone', None)
        if self.options.hint_root_zone and not root_zone_found \
                and root is not None:
            root_filename = self.zone_filename(root.name)
            cfg.zones[root_filename] = self.build_zone(root)
            self.additional_zone_filenames.append(root_filename)

        return cfg

    def build_zone(self, zone: 'DNSZone') -> ConfigDict:
        master_ips = []
        for s_name in zone.servers + [zone.dns_master] + zone.dns_slaves + \
                      zone.delegation_servers:
            server_itf = find_node(self._node, dns_base_name(s_name))
            if server_itf is None:
                lg.error("Cannot find the server node {name} of DNS zone"
                         " {zone}. Are you sure that they are connected to "
                         "the current node {current}?"
                         .format(name=s_name, zone=zone.name,
                                 current=self._node.name))
                continue
            server = server_itf.node
            for itf in realIntfList(server):
                for ip in itf.ips():
                    if not is_reverse_zone(zone.name):
                        zone.add_record(ARecord(s_name, ip.ip.compressed))
                    if s_name == zone.dns_master:
                        master_ips.append(ip.ip.compressed)

                for ip6 in itf.ip6s(exclude_lls=True):
                    if not is_reverse_zone(zone.name):
                        zone.add_record(AAAARecord(s_name, ip6.ip.compressed))
                    if s_name == zone.dns_master:
                        master_ips.append(ip6.ip.compressed)

        return ConfigDict(name=zone.name,
                          soa_record=zone.soa_record,
                          records=zone.records,
                          master=self._node.name == zone.dns_master,
                          master_ips=master_ips,
                          delegation_servers=zone.delegation_servers)

    def build_reverse_zone(self, cfg_zones: ConfigDict):
        """
        Build non-existing PTR records. Then, adds them to an existing reverse
        zone if any. The remaining ones are inserted in a new reverse zone
        that is added to cfg_zones dictionary.
        """
        # Build PTR records
        ptr_records = set()
        for zone in cfg_zones.values():
            for record in zone.records:
                if not isinstance(record, ARecord) \
                        or (record.domain_name in zone.delegation_servers):
                    continue

                if record.full_domain_name:
                    domain_name = record.domain_name
                else:
                    domain_name = dns_join_name(record.domain_name, zone.name)
                ptr_records.add(PTRRecord(record.address, domain_name,
                                          ttl=record.ttl))

        existing_records = [record for zone in cfg_zones.values()
                            for record in zone.records
                            if isinstance(record, PTRRecord)]

        ptr_v6_records = []
        ptr_v4_records = []
        for record in ptr_records:
            # Filter out existing PTR records
            if record in existing_records:
                continue
            # Try to place the rest in existing reverse DNS zones
            found = False
            for zone in cfg_zones.values():
                if zone.name in record.domain_name \
                        and is_reverse_zone(zone.name):
                    zone.records.append(record)
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

    def build_largest_reverse_zone(self, cfg_zones: ConfigDict,
                                   records: List[Union['PTRRecord',
                                                       'NSRecord']]):
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
            if is_reverse_zone(zone.name):
                continue
            for record in zone.records:
                if isinstance(record, NSRecord) \
                        and self._node.name in record.name_server:
                    ns_record = NSRecord("@", record.name_server)
        if ns_record is None:
            lg.warning("Cannot forge a DNS reverse zone because there is no"
                       " NS Record for this node in regular zones.\n")
            return
        records.append(ns_record)

        # Build the reverse zone
        soa_record = SOARecord(domain_name=domain_name)

        reverse_zone = ConfigDict(name=domain_name,
                                  soa_record=soa_record,
                                  records=records,
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
        :param dns_server_port: The port number of the dns server
        :param hint_root_zone: Add hints to root dns servers if this is not
                               the root server"""
        defaults.log_severity = "warning"
        defaults.dns_server_port = 53
        defaults.hint_root_zone = True
        super().set_defaults(defaults)

    def zone_filename(self, domain_name: str) -> str:
        return self._file(suffix='%szone.cfg' % domain_name)

    @property
    def cfg_filenames(self):
        return super().cfg_filenames + \
               [self.zone_filename(z.name)
                for z in self._node.get('dns_zones', [])] + \
               self.additional_zone_filenames

    @property
    def template_filenames(self):
        return super().template_filenames + \
               ["%s-zone.mako" % self.NAME
                for _ in self._node.get('dns_zones', []) +
                self.additional_zone_filenames]


class DNSRecord:

    def __init__(self, rtype: str, domain_name: str, ttl=60):
        self.rtype = rtype
        self.domain_name = domain_name
        self.ttl = ttl

        if not self.full_domain_name and "." in self.domain_name:
            # Full DNS names should be ended by a dot in the config
            self.domain_name = self.domain_name + "."

    @property
    def rdata(self) -> str:
        return ""

    @property
    def full_domain_name(self) -> bool:
        return self.domain_name[-1:] == "."

    def __eq__(self, other):
        return self.rtype == other.rtype \
               and self.domain_name == other.domain_name \
               and self.rdata == other.rdata

    def __hash__(self):
        return hash(self.rtype) + hash(self.domain_name) + hash(self.rdata)


class ARecord(DNSRecord):

    def __init__(self, domain_name,
                 address: Union[str, IPv4Address, IPv6Address], ttl=60):
        self.address = ip_address(str(address))
        rtype = "A" if self.address.version == 4 else "AAAA"
        super().__init__(rtype=rtype, domain_name=domain_name, ttl=ttl)

    @property
    def rdata(self):
        return self.address.compressed


class AAAARecord(ARecord):
    pass  # ARecord already handles IPv6 addresses


class PTRRecord(DNSRecord):

    def __init__(self, address: Union[str, IPv4Address, IPv6Address],
                 domain_name: str, ttl=60):
        self.address = ip_address(str(address))
        self.mapped_domain_name = domain_name
        if self.mapped_domain_name[-1] != "." \
                and "." in self.mapped_domain_name:
            # Full DNS names should be ended by a dot in the config
            self.mapped_domain_name = self.mapped_domain_name + "."
        super().__init__("PTR", self.address.reverse_pointer, ttl=ttl)

    @property
    def v6(self):
        return self.address.version == 6

    @property
    def rdata(self):
        return self.mapped_domain_name


class NSRecord(DNSRecord):

    def __init__(self, domain_name, name_server: str, ttl=60):
        super().__init__(rtype="NS", domain_name=domain_name, ttl=ttl)
        self.name_server = name_server

        if self.name_server[-1] != ".":
            # Full DNS names should be ended by a dot in the config
            self.name_server = dns_join_name(self.name_server, self.domain_name)

    @property
    def rdata(self):
        return self.name_server


class SOARecord(DNSRecord):

    def __init__(self, domain_name, refresh_time=DNS_REFRESH,
                 retry_time=DNS_RETRY, expire_time=DNS_EXPIRE,
                 min_ttl=DNS_MIN_TTL):
        super().__init__(rtype="SOA", domain_name=domain_name, ttl=min_ttl)
        self.refresh_time = refresh_time
        self.retry_time = retry_time
        self.expire_time = expire_time

    @property
    def rdata(self):
        return "{domain_name} {admin} (\n1 ; serial\n{refresh}" \
               " ; refresh timer\n{retry} ; retry timer\n{expire}" \
               " ; retry timer\n{min_ttl} ; minimum ttl\n)"\
            .format(domain_name=self.domain_name,
                    admin=dns_join_name("sysadmin", self.domain_name),
                    refresh=self.refresh_time,
                    retry=self.retry_time, expire=self.expire_time,
                    min_ttl=self.ttl)


class DNSZone(Overlay):

    def __init__(self, name: str, dns_master: str,
                 dns_slaves: Sequence[str] = (),
                 records: Sequence[DNSRecord] = (), nodes: Sequence[str] = (),
                 refresh_time=DNS_REFRESH, retry_time=DNS_RETRY,
                 expire_time=DNS_EXPIRE, min_ttl=DNS_MIN_TTL,
                 ns_domain_name: Optional[str] = None,
                 subdomain_delegation=True,
                 delegated_zones: Sequence['DNSZone'] = ()):
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
        :param subdomain_delegation:
            If set, additional records for subdomain name servers are added
            to guarantee correct delegation
        :param delegated_zones: Additional delegated zones
        """
        self.name = name + "." if name[-1:] != "." else name
        self.dns_master = dns_master
        self.dns_slaves = list(dns_slaves)
        self._records = list(records)
        self.servers = list(nodes)
        self.soa_record = SOARecord(self.name, refresh_time=refresh_time,
                                    retry_time=retry_time,
                                    expire_time=expire_time, min_ttl=min_ttl)
        super().__init__(nodes=[dns_master] + list(dns_slaves))

        self.consistent = True
        for node_name in [dns_master] + self.dns_slaves + self.servers:
            if "." in node_name:
                lg.error("Cannot create zone {name} because the node name"
                         " {node_name} contains a '.'"
                         .format(name=self.name, node_name=node_name))
                self.consistent = False

        self.ns_domain_name = ns_domain_name if ns_domain_name is not None \
            else self.name
        if self.ns_domain_name[-1:] != ".":
            self.ns_domain_name = self.ns_domain_name + "."

        # Add NS Records (if not already present)
        for n in self.nodes:
            server_name = dns_join_name(n, self.ns_domain_name)
            self.add_record(NSRecord(self.name, server_name))
        self.subdomain_delegation = subdomain_delegation
        self.delegated_zones = list(delegated_zones)
        self.delegation_servers = []

    def check_consistency(self, topo):
        return super().check_consistency(topo) and self.consistent

    @property
    def records(self):
        return self._records

    @property
    def ns_records(self):
        return [r for r in self._records if isinstance(r, NSRecord)]

    def add_record(self, record: DNSRecord):
        if record not in self._records:
            self._records.append(record)

    def apply(self, topo):
        super().apply(topo)
        if not self.consistent:
            return

        zones = []
        for overlay in topo.overlays:
            if not isinstance(overlay, type(self)) \
                    or not overlay.consistent or self == overlay:
                continue

            # Find zones that want to hint root dns name servers
            if self.name == DNS_ROOT:
                zones.append(overlay)

            # Add direct subdomains as delegated zones
            if self.subdomain_delegation:
                domain = "." + self.name if self.name != DNS_ROOT else DNS_ROOT
                match = re.match(r"^\w+" + re.escape(domain) + r"$",
                                 overlay.name)
                if match is None:
                    continue

                self.delegated_zones.append(overlay)

        # If this is root zone, add a hint zone for the NS servers
        if self.name == DNS_ROOT:
            for zone in zones:
                for n in zone.nodes:
                    if "root_zone" not in topo.nodeInfo(n):
                        hint_root_zone = copy.deepcopy(self)
                        hint_root_zone.soa_record = None
                        hint_root_zone._records = hint_root_zone.ns_records
                        topo.nodeInfo(n)["root_zone"] = hint_root_zone

        for zone in self.delegated_zones:
            # Create NSRecords for the delegated subdomains
            for ns in [zone.dns_master] + zone.dns_slaves:
                record = NSRecord(zone.name,
                                  dns_join_name(ns, zone.ns_domain_name))
                self.add_record(record)
                self.delegation_servers.append(record.name_server)

        for n in self.nodes:
            topo.nodeInfo(n).setdefault("dns_zones", []).append(self)
