hostname ${node.name}
password ${node.password}

router rip
    % for net in node.rip.networks:
    network ${net.domain.with_prefixlen}
    % endfor
