% for table, rules in node.iptables.rules.items():
*${table}
  % for rule in rules:
${rule}
  % endfor
COMMIT
% endfor
