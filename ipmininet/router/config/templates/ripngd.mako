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

router ripng
  redistribute kernel
  redistribute static
  redistribute connected
  % for net in node.ripngd.interfaces:
  network ${net.name}
  % endfor

  <%block name="router"/>
!
