import os
import socket

from .base import RouterDaemon
from .utils import ConfigDict

#  Route Map actions
DENY = 'deny'
PERMIT = 'permit'


class QuaggaDaemon(RouterDaemon):
    """The base class for all Quagga-derived daemons"""

    # Additional parameters to pass when starting the daemon
    STARTUP_LINE_EXTRA = ''

    @property
    def startup_line(self):
        return '{name} -f {cfg} -i {pid} -z {api} -u root {extra}'\
                .format(name=self.NAME,
                        cfg=self.cfg_filename,
                        pid=self._file('pid'),
                        api=self.zebra_socket,
                        extra=self.STARTUP_LINE_EXTRA)

    @property
    def zebra_socket(self):
        """Return the path towards the zebra API socket for the given node"""
        return os.path.join(self._node.cwd,
                            '%s_%s.api' % ('quagga', self._node.name))

    def build(self):
        cfg = super(QuaggaDaemon, self).build()
        cfg.debug = self.options.debug
        return cfg

    def set_defaults(self, defaults):
        """:param debug: the set of debug events that should be logged"""
        defaults.debug = ()
        super(QuaggaDaemon, self).set_defaults(defaults)

    @property
    def dry_run(self):
        return '{name} -Cf {cfg} -u root'\
               .format(name=self.NAME,
                       cfg=self.cfg_filename)


class Zebra(QuaggaDaemon):
    NAME = 'zebra'
    PRIO = 0
    # We want zebra to preserve existing routes in the kernel RT (e.g. those
    # set via ip route)
    STARTUP_LINE_EXTRA = '-k'
    KILL_PATTERNS = (NAME,)

    def __init__(self, *args, **kwargs):
        super(Zebra, self).__init__(*args, **kwargs)
        self.files.append(self.zebra_socket)

    def build(self):
        cfg = super(Zebra, self).build()
        # Update with preset defaults
        cfg.update(self.options)
        # Track interfaces
        cfg.interfaces = (ConfigDict(name=itf.name,
                                     description=itf.describe)
                          for itf in self._node.intfList())
        return cfg

    def set_defaults(self, defaults):
        """:param debug: the set of debug events that should be logged
        :param access_lists: The set of AccessList to create, independently
                             from the ones already included by route_maps
        :param route_maps: The set of RouteMap to create"""
        defaults.access_lists = []
        defaults.route_maps = []
        super(Zebra, self).set_defaults(defaults)

    def has_started(self):
        # We override this such that we wait until we have the API socket
        # and until wa can connect to it
        return os.path.exists(self.zebra_socket) and self.listening()

    def listening(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(self.zebra_socket)
            sock.close()
            return True
        except socket.error:
            return False


class CommunityList(object):
    """A zebra community-list entry"""
    # Number of CmL
    count = 0

    def __init__(self, name=None, action=PERMIT, community=0):
        """

        :param name:
        :param action:
        :param community:
        """
        CommunityList.count += 1
        self.name = name if name else 'cml%d' % CommunityList.count
        self.action = action
        self.community = community

    def __eq__(self, other):
        return self.name == other.name and self.action == other.action


class AccessListEntry(object):
    """A zebra access-list entry"""

    def __init__(self, prefix, action=PERMIT):
        """:param prefix: The ip_interface prefix for that ACL entry
        :param action: Wether that prefix belongs to the ACL (PERMIT)
                        or not (DENY)"""
        self.prefix = prefix
        self.action = action


class AccessList(object):
    """A zebra access-list class. It contains a set of AccessListEntry,
    which describes all prefix belonging or not to this ACL"""

    # Number of ACL
    count = 0

    def __init__(self, name=None, entries=()):
        """Setup a new access-list

        :param name: The name of the acl, which will default to acl## where ##
                     is the instance number
        :param entries: A sequence of AccessListEntry instance,
                        or of ip_interface which describes which prefixes
                        are composing the ACL"""
        AccessList.count += 1
        self.name = name if name else 'acl%d' % AccessList.count
        self.entries = [e if isinstance(e, AccessListEntry)
                        else AccessListEntry(prefix=e)
                        for e in entries]

    def __eq__(self, other):
        return self.name == other.name


class RouteMapMatchCond(object):
    """
    A class representing a RouteMap matching condition
    """

    def __init__(self, cond_type, condition):
        """
        :param condition: Can be an ip address, the id of an access
                          or prefix list
        :param cond_type: The type of condition access list, prefix list,
                          peer ...
        """
        self.condition = condition
        self.cond_type = cond_type

    def __eq__(self, other):
        return self.condition == other.condition \
               and self.cond_type == other.cond_type


class RouteMapSetAction(object):
    """
    A class representing a RouteMap set action
    """

    def __init__(self, action_type, value):
        """
        :param action_type: Type of value to me modified
        :param value: Value to be modified
        """
        self.action_type = action_type
        self.value = value

    def __eq__(self, other):
        return self.action_type == other.action_type \
               and self.value == other.value


class RouteMap(object):
    """A class representing a set of route maps applied to a given protocol"""

    # Number of route maps
    count = 0

    def __init__(self, name=None, match_policy=PERMIT, match_cond=(),
                 set_actions=(), call_action=None, exit_policy=None,
                 order=10, proto=(), neighbor=(), direction='in'):
        """
        :param name: The name of the route-map, defaulting to rm##
        :param match_policy: Deny or permit the actions if the route match
                             the condition
        :param match_cond: Specify one or more conditions which must be matched
                           if the entry is to be considered further
        :param set_actions: Specify one or more actions to do
                            if there is a match
        :param call_action: call to an other route map
        :param exit_policy: An entry may, optionally specify an alternative exit
                            policy if the entry matched or of (action, [acl,
                            acl, ...]) tuples that will compose the route map
        :param order: Priority of the route map compare to others
        :param proto: The set of protocols to which this route-map applies
        :param neighbor: List of peers this route map is applied to
        :param direction: Direction of the routemap(in, out, both)
        """
        RouteMap.count += 1
        self.name = name if name else 'rm%d' % RouteMap.count
        self.match_policy = match_policy
        self.match_cond = [e if isinstance(e, RouteMapMatchCond)
                           else RouteMapMatchCond(cond_type=e[0],
                                                  condition=e[1])
                           for e in match_cond]
        self.set_actions = [e if isinstance(e, RouteMapSetAction)
                            else RouteMapSetAction(action_type=e[0], value=e[1])
                            for e in set_actions]
        self.call_action = call_action
        self.exit_policy = exit_policy
        self.neighbor = neighbor
        self.direction = direction
        self.order = order
        self.proto = proto

    def __eq__(self, other):
        return self.neighbor == other.neighbor \
               and self.direction == other.direction \
               and self.exit_policy == other.exit_policy \
               and self.order == other.order

    def append_match_cond(self, match_conditions):
        """

        :return:
        """
        for match_condition in match_conditions:
            if match_condition not in self.match_cond:
                self.match_cond.append(match_condition)

    def append_set_action(self, set_actions):
        """

        :param set_actions:
        :return:
        """
        for set_action in set_actions:
            if set_action not in self.set_actions:
                self.set_actions.append(set_action)

    @staticmethod
    @property
    def describe():
        """Return the zebra description of this route map and apply it to the
        relevant protocols"""
        return 'route-map'
