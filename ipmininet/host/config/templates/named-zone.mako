<% zone = node.named.zones[node.current_filename] %>
$TTL ${zone.soa_record.ttl}
@	IN	SOA	${zone.soa_record.rdata}

%for record in zone.records:
${record.domain_name}   ${record.ttl}	IN	${record.rtype}	${record.rdata}
%endfor
