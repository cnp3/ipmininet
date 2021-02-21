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
    ! To prevent BGP4 of sending only IPv4 routes
    no bgp default ipv4-unicast
    ! (see https://docs.frrouting.org/en/latest/bgp.html#require-policy-on-ebgp)
    no bgp ebgp-requires-policy
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
    address-family ${af.name} unicast
    % for rm in node.bgpd.route_maps:
        % if rm.family == af.name:
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
            % if node.bgpd.rr and n.asn == node.bgpd.asn:
        neighbor ${n.peer} route-reflector-client
            % endif
        % endif
    % endfor
    % if node.bgpd.rr:
    bgp cluster-id ${node.bgpd.routerid}
    % endif
    exit-address-family
    !
% endfor
!
% for al in node.bgpd.access_lists:
    % for e in al.entries:
${al.zebra_family}access-list ${al.name} ${e.action} ${e.prefix}
    % endfor
% endfor

% for cl in node.bgpd.community_lists:
bgp community-list standard ${cl.name} ${cl.action} ${cl.community}
% endfor

% for pl in node.bgpd.prefix_lists:
    %for e in pl.entries:
${pl.zebra_family} prefix-list ${pl.name} ${e.action} ${e.prefix} ${ 'le %s' % e.le if e.le else ''} ${ 'ge %s' % e.ge if e.ge else ''}
    %endfor
% endfor


% for rm in node.bgpd.route_maps:
    %for order in sorted(rm.entries.keys()):
route-map ${rm.name} ${rm.entries[order].match_policy} ${order}
        %for match in rm.entries[order].match_cond:
            %if match.cond_type == "access-list" and match.family == rm.family:
    match ${match.zebra_family} address ${match.condition}
            %elif match.cond_type == "prefix-list" and match.family == rm.family:
    match ${match.zebra_family} address ${match.cond_type} ${match.condition}
            %elif match.cond_type =='next-hop':
    match ${match.zebra_family} address ${match.cond_type} ${match.condition}
            %elif match.cond_type == 'community':
    match ${match.cond_type} ${match.condition}
            %elif match.family == rm.family:
    match ${match.cond_type} ${match.condition}
            %endif
        %endfor
        %for action in rm.entries[order].set_actions:
            %if action.action_type == 'community' and isinstance(action.value, int):
    set ${action.action_type} ${node.bgpd.asn}:${action.value}
            %else:
    set ${action.action_type} ${action.value}
            %endif
        %endfor
        %if rm.entries[order].call_action:
    call ${rm.call_action}
        %endif
        %if rm.entries[order].exit_policy:
    on-match ${rm.exit_policy}
        %endif
!
    %endfor
!
% endfor
<%block name="router"/>
!
