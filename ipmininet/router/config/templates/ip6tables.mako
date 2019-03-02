% for table, rules in node.ip6tables.rules.items():
*${table}
  % for rule in rules:
${rule}
  % endfor
COMMIT
% endfor
