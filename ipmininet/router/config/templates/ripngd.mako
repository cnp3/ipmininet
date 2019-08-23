hostname ${node.name}
password ${node.password}

% if node.ripngd.logfile:
log file ${node.ripngd.logfile}
% endif

% for section in node.ripngd.debug:
debug ripng ${section}
% endfor

% for intf in node.ripngd.interfaces:
interface ${intf.name}
# ${intf.description}
  # Highiest priority routers will be DR
  ip ripng priority ${intf.priority}
  ip ripng cost ${intf.cost}
  % if not intf.passive and intf.active:
  ip ripng dead-interval ${intf.dead_int}
  ip ripng hello-interval ${intf.hello_int}
  % endif
  <%block name="interface"/>
!
% endfor

router ripng
  ripng router-id ${node.ripngd.routerid}
  % for r in node.ripngd.redistribute:
  redistribute ${r.subtype} metric-type ${r.metric_type} metric ${r.metric}
  % endfor
  % for net in node.ripngd.networks:
  network ${net.domain.with_prefixlen} area ${net.area}
  % endfor
  % for itf in node.ripngd.interfaces:
      % if itf.passive or not itf.active:
  passive-interface ${itf.name}
    % endif
  % endfor

  <%block name="router"/>
!
