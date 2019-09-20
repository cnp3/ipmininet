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
  <%block name="interface"/>
% endfor
!
% if node.ripngd.split_horizon_with_poison:
ipv6 ripng split-horizon poisoned-reverse
% elif node.ripngd.split_horizon:
ipv6 ripng split-horizon
% endif
!
router ripng
  timers basic ${node.ripngd.update_timer} ${node.ripngd.timeout_timer} ${node.ripngd.garbage_timer}
  % for intf in node.ripngd.interfaces:
  network ${intf.name}
  offset-list ${intf.name} out ${intf.cost} ${intf.name}
  offset-list ${intf.name} in ${intf.cost} ${intf.name}
  % endfor
  % for r in node.ripngd.redistribute:
  redistribute ${r.subtype} metric ${r.metric}
  % endfor
  <%block name="router"/>
!
% for intf in node.ripngd.interfaces:
ipv6 access-list ${intf.name} permit ::/0
ipv6 access-list ${intf.name} deny any
% endfor
