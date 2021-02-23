logging {
    channel output_file {
        file "${node.named.abs_logfile}";
        severity ${node.named.log_severity};
        print-severity yes;
        print-time yes;
    };
    category default { output_file; };
};

% for filename, zone in node.named.zones.items():
zone "${zone.name}" {
    % if zone.soa_record is None:
    type hint;
    % elif zone.master:
    type master;
    % else:
    type slave;
    masters {
        % for m in zone.master_ips:
        ${m};
        % endfor
    };
    % endif
    file "${filename}";
};
% endfor

options {
    dnssec-validation no;
};
