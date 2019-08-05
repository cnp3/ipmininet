hostname ${node.name}
password ${node.password}

% if node.staticd.logfile:
log file ${node.staticd.logfile}
% endif

% for section in node.staticd.debug:
debug ${section}
% endfor

% for route in node.staticd.static_routes:
${ip_statement(route.prefix)} route ${route.prefix} ${route.nexthop} ${route.distance}
% endfor
