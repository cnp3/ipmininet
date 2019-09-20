from builtins import str

from ipaddress import ip_network

from ipmininet.router.config.zebra import QuaggaDaemon, Zebra


class STATIC(QuaggaDaemon):
    NAME = 'staticd'
    DEPENDS = (Zebra,)
    KILL_PATTERNS = (NAME,)

    def build(self):
        cfg = super(STATIC, self).build()
        # Update with preset defaults
        cfg.static_routes = self.options.static_routes
        return cfg

    def set_defaults(self, defaults):
        """:param debug: the set of debug events that should be logged
        :param static_routes: The set of StaticRoute to create"""
        defaults.static_routes = []
        super(STATIC, self).set_defaults(defaults)


class StaticRoute(object):
    """A class representing a static route"""

    def __init__(self, prefix, nexthop, distance=1):
        """:param prefix: The prefix for this static route
        :param nexthop: The nexthop for this prefix, one of: <IP address,
                        interface name, null0, blackhole, reject>
        :param distance: The distance metric of the route"""
        self.prefix = ip_network(str(prefix))
        self.nexthop = nexthop
        self.distance = distance
