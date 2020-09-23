from .base import RouterDaemon
from .utils import ConfigDict


class OpenrDaemon(RouterDaemon):
    """The base class for the OpenR daemon"""

    NAME = 'openr'

    @property
    def STARTUP_LINE_EXTRA(self):
        # Add options to the standard startup line
        return ''

    @property
    def startup_line(self):
        return '{name} {cfg} {extra}'\
                .format(name=self.NAME,
                        cfg=self._cfg_options(),
                        extra=self.STARTUP_LINE_EXTRA)

    def build(self):
        cfg = ConfigDict()
        return cfg

    def _defaults(self, **kwargs):
        """
        Default parameters of the OpenR daemon. The template file openr.mako
        sets the default parameters listed here. See:
        https://github.com/facebook/openr/blob/master/openr/docs/Runbook.md.

        :param alloc_prefix_len: Block size of allocated prefix in terms of
            it's prefix length. In this case '/80' prefix will be elected for a
            node. e.g. 'face:b00c:0:0:1234::/80'. Default: 128.
        :param assume_drained: Default: False.
        :param config_store_filepath: Default:
            /tmp/aq_persistent_config_store.bin
        :param decision_debounce_max_ms: Knobs to control how often to run
            Decision. On receipt of first even debounce is created with MIN
            time which grows exponentially up to max if there are more events
            before debounce is executed. This helps us to react to single
            network failures quickly enough (with min duration) while avoid
            high CPU utilization under heavy network churn. Default: 250.
        :param decision_debounce_min_ms: Knobs to control how often to run
            Decision. On receipt of first even debounce is created with MIN time
            which grows exponentially up to max if there are more events before
            debounce is executed.  This helps us to react to single network
            failures quickly enough (with min duration) while avoid high CPU
            utilization under heavy network churn.  Default: 10.
        :param decision_rep_port: Default: 60004.
        :param domain: Name of domain this node is part of. OpenR will 'only'
            form adjacencies to OpenR instances within it's own domain.  This
            option becomes very useful if you want to run OpenR on two nodes
            adjacent to each other but belonging to different domains, e.g.
            Data Center and Wide Area Network.  Usually it should depict the
            Network. Default: openr.
        :param dryrun: OpenR will not try to program routes in it's default
            configuration. You should explicitly set this option to false to
            proceed with route programming. Default: False.
        :param enable_subnet_validation: OpenR supports subnet validation to
            avoid mis-cabling of v4 addresses on different subnets on each end
            of the link. Need to enable v4 and this flag at the same time to
            turn on validation. Default: True.
        :param enable_fib_sync: Default: False.
        :param enable_health_checker: OpenR can measure network health
            internally by pinging other nodes in the network and exports this
            information as counters or via breeze APIs. By default health
            checker is disabled. The expectation is that each node must have at
            least one v6 loopback addressed announced into the network for the
            reachability check. Default: False.
        :param enable_legacy_flooding: Default: True.
        :param enable_lfa: With this option, additional Loop-Free Alternate
            (LFA) routes can be computed, per RFC 5286, for fast failure
            recovery.  Under the failure of all primary nexthops for a prefix,
            because of link failure, next best precomputed LFA will be used
            without need of an SPF run. Default: False.
        :param enable_netlink_fib_handler: Knob to enable/disable default
            implementation of 'FibService' that comes along with OpenR for
            Linux platform. If you want to run your own FIB service then
            disable this option. Default: True.
        :param enable_netlink_system_handler: Knob to enable/disable default
            implementation of 'SystemService' and 'PlatformPublisher' that
            comes along with OpenR for Linux platform. If you want to run your
            own SystemService then disable this option. Default: True.
        :param enable_perf_measurement: Experimental feature to measure
            convergence performance. Performance information can be viewed via
            breeze API 'breeze perf fib'. Default: True.
        :param enable_prefix_alloc: Enable prefix allocator to elect and assign
            a unique prefix for the node. You will need to specify other
            configuration parameters below. Default: False.
        :param enable_rtt_metric: Default mechanism for cost of a link is '1'
            and hence cost of path is hop count. With this option you can ask
            OpenR to compute and use RTT of a link as a metric value.  You
            should only use this for networks where links have significant
            delay, on the order of a couple of milliseconds.  Using this for
            point-to-point links will cause lot of churn in metric updates as
            measured RTT will fluctuate a lot because of packet processing
            overhead. RTT is measured at application level and hence the
            fluctuation for point-to-point links. Default: True.
        :param enable_secure_thrift_server: Flag to enable TLS for our thrift
            server. Disable this for plaintext thrift. Default: False.
        :param enable_segment_routing: Experimental and partially implemented
            segment routing feature. As of now it only elects node/adjacency
            labels. In future we will extend it to compute and program FIB
            routes. Default: False.
        :param enable_spark: Default: True.
        :param enable_v4: OpenR supports v4 as well but it needs to be turned
            on explicitly. It is expected that each interface will have v4
            address configured for link local transport and v4/v6 topologies
            are congruent. Default: False.
        :param enable_watchdog: Default: True.
        :param fib_handler_port: TCP port on which 'FibService' will be
            listening. Default: 60100.
        :param fib_rep_port: Default: 60009.
        :param health_checker_ping_interval_s: Configure ping interval of the
            health checker. The below option configures it to ping all other
            nodes every 3 seconds. Default: 3.
        :param health_checker_rep_port: Default: 60012.
        :param ifname_prefix: Interface prefixes to perform neighbor discovery
            on. All interfaces whose names start with these are used for
            neighbor discovery. Default: ""
        :param iface_regex_exclude: Default:"".
        :param iface_regex_include: Default: "".
        :param ip_tos: Set type of service (TOS) value with which every control
            plane packet from Open/R will be marked with. This marking can be
            used to prioritize control plane traffic (as compared to data
            plane) so that congestion in network doesn't affect operations of
            Open/R. Default: 192
        :param key_prefix_filters: This comma separated string is used to set
            the key prefixes when key prefix filter is enabled (See
            SET_LEAF_NODE).  It is also set when requesting KEY_DUMP from peer
            to request keys that match one of these prefixes. Default: "".
        :param kvstore_flood_msg_per_sec: Default: 0.
        :param kvstore_flood_msg_burst_size: Default: 0.
        :param kvstore_flood_msg_per_sec: Default: 0.
        :param kvstore_ttl_decrement_ms: Default: 1.
        :param kvstore_zmq_hwm: Set buffering size for KvStore socket
            communication. Updates to neighbor node during flooding can be
            buffered upto this number. For larger networks where burst of
            updates can be high having high value makes sense. For smaller
            networks where burst of updates are low, having low value makes
            more sense. Default: 65536.
        :param link_flap_initial_backoff_ms: Default: 1000.
        :param link_flap_max_backoff_ms: Default: 60000.
        :param link_monitor_cmd_port: Default: 60006.
        :param loopback_iface: Indicates loopback address to which auto elected
            prefix will be assigned if enabled. Default: "lo".
        :param memory_limit_mb: Enforce upper limit on amount of memory in
            mega-bytes that open/r process can use. Above this limit watchdog
            thread will trigger crash. Service can be auto-restarted via system
            or some kind of service manager. This is very useful to guarantee
            protocol doesn't cause trouble to other services on device where it
            runs and takes care of slow memory leak kind of issues. Default:
            300.
        :param minloglevel: Log messages at or above this level. Again, the
            numbers of severity levels INFO, WARNING, ERROR, and FATAL are 0,
            1, 2, and 3, respectively. Default: 0.
        :param node_name: Name of the OpenR node. Crucial setting if you run
            multiple nodes. Default: "".
        :param override_loopback_addr: Whenever new address is elected for a
            node, before assigning it to interface all previously allocated
            prefixes or other global prefixes will be overridden with the new
            one. Use it with care! Default: False.
        :param prefix_manager_cmd_port: Default: 60011.
        :param prefixes: Static list of comma separate prefixes to announce
            from the current node. Can't be changed while running. Default: "".
        :param redistribute_ifaces: Comma separated list of interface names
            whose '/32' (for v4) and '/128' (for v6) should be announced. OpenR
            will monitor address add/remove activity on this interface and
            announce it to rest of the network. Default: "lo".
        :param seed_prefix: In order to elect a prefix for the node a super
            prefix to elect from is required. This is only applicable when
            'ENABLE_PREFIX_ALLOC' is set to true. Default: "".
        :param set_leaf_node: Sometimes a node maybe a leaf node and have only
            one path in to network. This node does not require to keep track of
            the entire topology. In this case, it may be useful to optimize
            memory by reducing the amount of key/vals tracked by the node.
            Setting this flag enables key prefix filters defined by
            KEY_PREFIX_FILTERS. A node only tracks keys in kvstore that matches
            one of the prefixes in KEY_PREFIX_FILTERS. Default: False.
        :param set_loopback_address: If set to true along with
            'ENABLE_PREFIX_ALLOC' then second valid IP address of the block
            will be assigned onto 'LOOPBACK_IFACE' interface. e.g. in this case
            'face:b00c:0:0:1234::1/80' will be assigned on 'lo' interface.
            Default: False.
        :param spark_fastinit_keepalive_time_ms: When interface is detected UP,
            OpenR can perform fast initial neighbor discovery as opposed to
            slower keep alive packets. Default value is 100 which means
            neighbor will be discovered within 200ms on a link. Default: 100.
        :param spark_hold_time_s: Hold time indicating time in seconds from
            it's last hello after which neighbor will be declared as down.
            Default: 30.
        :param spark_keepalive_time_s: How often to send spark hello messages
            to neighbors. Default: 3.
        :param static_prefix_alloc: Default: False.
        :param tls_acceptable_peers: A comma separated list of strings. Strings
            are x509 common names to accept SSL connections from. Default: ""
        :param tls_ecc_curve_name: If we are running an SSL thrift server, this
            option specifies the eccCurveName for the associated
            wangle::SSLContextConfig. Default: "prime256v1".
        :param tls_ticket_seed_path: If we are running an SSL thrift server,
            this option specifies the TLS ticket seed file path to use for
            client session resumption. Default: "".
        :param x509_ca_path: If we are running an SSL thrift server, this
            option specifies the certificate authority path for verifying
            peers. Default: "".
        :param x509_cert_path: If we are running an SSL thrift server, this
            option specifies the certificate path for the associated
            wangle::SSLContextConfig. Default: "".
        :param x509_key_path: If we are running an SSL thrift server, this
            option specifies the key path for the associated
            wangle::SSLContextConfig. Default: "".
        :param logbufsecs: Default: 0
        :param log_dir: Directory to store log files at. The folder must exist.
            Default: /var/log.
        :param max_log_size: Default: 1.
        :param v: Show all verbose 'VLOG(m)' messages for m less or equal the
            value of this flag. Use higher value for more verbose logging.
            Default: 1.
        """
        defaults = ConfigDict()
        # Apply daemon-specific defaults
        self.set_defaults(defaults)
        # Use user-supplied defaults if present
        defaults.update(**kwargs)
        return defaults

    def set_defaults(self, defaults):
        super().set_defaults(defaults)

    def _cfg_options(self):
        """The OpenR daemon has currently no option to read config from
        configuration file itself. The run_openr.sh script can be used to read
        options from environment files. However, we want to run the daemon
        directly. The default options from the shell script are implemented in
        the openr.mako template and passed to the daemon as argument."""
        cfg = ConfigDict()
        cfg[self.NAME] = self.options
        return self.template_lookup.get_template(self.template_filenames[0])\
                                   .render(node=cfg)

    @property
    def dry_run(self):
        """The OpenR dryrun runs the daemon and does not shutdown the daemon.
        As a workaround we only show the version of the openr daemon"""
        # TODO: Replace with a config parser or shutdown the daemon after few
        # seconds
        return '{name} --version'\
               .format(name=self.NAME)
