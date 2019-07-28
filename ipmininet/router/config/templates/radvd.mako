# See `man radvd.conf` for more details
% for itf in node.radvd.interfaces:
    interface ${itf.name}
    {
        IgnoreIfMissing on;
        AdvSendAdvert on;
        MaxRtrAdvInterval 15;
        % for adv_prefixes in itf.ra_prefixes:
            % for prefix in adv_prefixes.prefixes:
        prefix ${prefix}
        {
            AdvOnLink on;
            AdvAutonomous on;
            AdvValidLifetime ${adv_prefixes.valid_lifetime};
            AdvPreferredLifetime ${adv_prefixes.preferred_lifetime};
        };
            %endfor
        % endfor
        % for rdnss in itf.rdnss_list:
            % for ip in rdnss.ips:
        RDNSS ${ip} {
            AdvRDNSSLifetime ${rdnss.max_lifetime}; # in seconds (0 means invalid)
        };
        DNSSL local {
            # list of dnssl specific options
        };
            % endfor
        % endfor
    };
% endfor
