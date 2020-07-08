"""This file contains a simple switch topology using the Named daemon"""
from ipaddress import ip_address

from ipmininet.iptopo import IPTopo
from ipmininet.host.config import Named, ARecord, PTRRecord


class DNSNetwork(IPTopo):
    """This simple network runs a named daemon on both master and slave hosts.
       The zone 'mydomain.org' is configured on both named daemons."""

    def build(self, *args, **kwargs):
        """
                             +--------+
                             | server |
                             +---+----+
                                 |
                              +--+-+
                        +-----+ r1 +-----+
                        |     +----+     |
        +-------+     +-+--+          +--+-+     +--------+
        | slave +-----+ r2 +----------+ r3 +-----+ master |
        +-------+     +----+          +----+     +--------+
        """
        # Add routers

        r1, r2, r3 = self.addRouters('r1', 'r2', 'r3')
        self.addLinks((r1, r2), (r1, r3), (r3, r2))

        # Add hosts

        server = self.addHost('server')
        lr1server = self.addLink(r1, server)
        self.addSubnet(links=[lr1server],
                       subnets=["192.168.0.0/24", "fc00::/64"])

        master = self.addHost('master')
        master.addDaemon(Named)
        self.addLink(r3, master)

        slave = self.addHost('slave')
        slave.addDaemon(Named)
        self.addLink(r2, slave)

        # Declare a new DNS Zone

        # By default all the NS, A and AAAA records are generated
        # but you can add them explicitly to change their TTL
        records = [ARecord(server, "fc00::2", ttl=120)]
        self.addDNSZone(name="mydomain.org", dns_master=master,
                        dns_slaves=[slave], nodes=[server], records=records)

        # By default IPMininet creates the reverse DNS zones for the addresses
        # of the other zones but if you want to change the default values of
        # the zone or of the PTR records, you can declare them explicitly.
        # The missing PTR records will be placed in this zone if their prefix
        # match or another reverse zone will be created.
        ptr_record = PTRRecord("fc00::2", server + ".mydomain.org", ttl=120)
        # reverse_domain_name is "f.ip6.arpa"
        reverse_domain_name = ip_address("fc00::").reverse_pointer[-10:]
        self.addDNSZone(name=reverse_domain_name, dns_master=master,
                        dns_slaves=[slave], records=[ptr_record],
                        ns_domain_name="mydomain.org", retry_time=8200)

        super().build(*args, **kwargs)
