hostname ${node.name}
password ${node.password}

% if node.ospf6d.logfile:
log file ${node.ospf6d.logfile}
% endif

% for section in node.ospf6d.debug:
debug ospf6 ${section}
% endfor

% for intf in node.ospf6d.interfaces:
interface ${intf.name}
# ${intf.description}
  # Highiest priority routers will be DR
  ipv6 ospf6 priority ${intf.priority}
  ipv6 ospf6 cost ${intf.cost}
  % if not intf.passive and intf.active:
  ipv6 ospf6 dead-interval ${intf.dead_int}
  ipv6 ospf6 hello-interval ${intf.hello_int}
  % else:
  ipv6 ospf6 passive
  % endif
  ipv6 ospf6 instance-id ${intf.instance_id}
  <%block name="interface"/>
!
% endfor

router ospf6
  router-id ${node.ospf6d.routerid}
  % for r in node.ospf6d.redistribute:
  redistribute ${r.subtype}
  % endfor
  % for itf in node.ospf6d.interfaces:
  interface ${itf.name} area ${itf.area}
  % endfor

  <%block name="router"/>
!
