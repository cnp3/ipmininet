hostname ${node.name}
password ${node.password}

% if node.ripngd.logfile:
log file ${node.ripngd.logfile}
% endif

% for section in node.ripngd.debug:
debug ripng ${section}
% endfor

debug ripng event
debug ripng packet

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
  timers basic ${node.ripngd.timers}
  % for intf in node.ripngd.interfaces:
  network ${intf.name}
  offset-list ${intf.name} out ${intf.cost} ${intf.name}
  offset-list ${intf.name} in ${intf.cost} ${intf.name}
  % endfor
  <%block name="router"/>
!
ipv6 access-list ac-all permit any
!
=======
% for intf in node.ripngd.interfaces:
ipv6 access-list ${intf.name} permit ::/0
ipv6 access-list ${intf.name} deny any
% endfor
>>>>>>> 95b975b... Update ripngd.mako
