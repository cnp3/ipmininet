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
    % for rm in node.bgpd.route_maps:
        % if rm.neighbor.family == af.name:
    neighbor ${rm.neighbor.peer} route-map ${rm.name} ${rm.direction}
        % endif
    % endfor
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
    %for rr in node.bgpd.rr:
        %if rr.family == af.name:
    neighbor ${rr.peer} route-reflector-client
        %endif
    %endfor
% endfor

% for al in node.bgpd.access_lists:
    % for e in al.entries:
ip access-list ${al.name} ${e.action} ${e.prefix}
    % endfor
% endfor

% for cl in node.bgpd.community_lists:
ip community-list standard ${cl.name} permit ${cl.community}
% endfor

% for rm in node.bgpd.route_maps:
route-map ${rm.name} ${rm.match_policy} ${rm.order}
    %if rm.neighbor.family == "ipv4":
        %for match in rm.match_cond:
            %if match.type == "access-list":
    match ip address ${match.condition}
            %elif match.type == "prefix-list" or match.type =='next-hop':
    match ip address ${match.type} ${match.condition}
            %else:
    match ${match.type} ${match.condition}
            %endif
        %endfor
        %for action in rm.set_actions:
            %if action.type == 'community':
    set ${action.type} ${action.value} additive
            %else:
    set ${action.type} ${action.value}
            %endif
        %endfor
    %elif rm.neighbor.family == "ipv6":
        %for match in rm.match_cond:
            %if match.type == "access-list":
    match ipv6 address ${match.condition}
            %elif match.type == "prefix-list" or match.type =='next-hop':
    match ipv6 address ${match.type} ${match.condition}
            %else:
    match ${match.type} ${match.condition}
            %endif
        %endfor
        %for action in rm.set_actions:
            %if action.type == 'community':
    set ${action.type} ${action.value} additive
            %else:
    set ${action.type} ${action.value}
            %endif
        %endfor
    %endif
% endfor
<%block name="router"/>
!
