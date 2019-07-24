hostname ${node.name}
password ${node.password}

% if node.bgpd.logfile:
log file ${node.bgpd.logfile}
% endif

% for section in node.bgpd.debug:
debug bgp ${section}
% endfor

router bgp ${node.bgpd.asn}
    bgp router-id ${node.bgpd.routerid}
    bgp bestpath compare-routerid
    no bgp default ipv4-unicast
% for n in node.bgpd.neighbors:
    no auto-summary
    neighbor ${n.peer} remote-as ${n.asn}
    neighbor ${n.peer} port ${n.port}
    neighbor ${n.peer} description ${n.description}
    % if n.ebgp_multihop:
    neighbor ${n.peer} ebgp-multihop
    % endif
    <%block name="neighbor"/>
% endfor
% for af in node.bgpd.address_families:
    address-family ${af.name}
    % for net in af.networks:
    network ${net.with_prefixlen}
    % endfor
    % for r in af.redistribute:
    redistribute ${r}
    % endfor
    % for n in af.neighbors:
        % if n.family == af.name:
    neighbor ${n.peer} activate
            % if n.nh_self:
    neighbor ${n.peer} ${n.nh_self}
            % endif
        % endif
    % endfor

% endfor
<%block name="router"/>
!
