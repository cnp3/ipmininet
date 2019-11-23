"""Base classes to configure an OSPF6 daemon"""

from .ospf import OSPF, OSPFRedistributedRoute
from .utils import ConfigDict


class OSPF6(OSPF):
    """This class provides a simple configuration for an OSPF6 daemon.
    It advertizes one network per interface (the primary one), and set
    interfaces not facing another L3Router to passive"""
    NAME = 'ospf6d'
    DEAD_INT = 3
    KILL_PATTERNS = (NAME,)

    def _build_interfaces(self, interfaces):
        """Return the list of OSPF6 interface properties from the list of
        active interfaces"""
        conf = [ConfigDict(
            description=i.describe,
            name=i.name,
            # Is the interface between two routers?
            active=self.is_active_interface(i),
            priority=i.get('ospf6_priority',
                           i.get('ospf_priority', self.options.priority)),
            dead_int=i.get('ospf6_dead_int',
                           i.get('ospf_dead_int', self.options.dead_int)),
            hello_int=i.get('ospf6_hello_int',
                            i.get('ospf_hello_int', self.options.hello_int)),
            cost=i.igp_metric,
            # Is the interface forcefully disabled?
            passive=i.get('igp_passive', False),
            instance_id=i.get('instance_id', self.options.instance_id),
            area=i.igp_area) for i in interfaces]
        # 'minimal hello-multiplier x' is not implemented in ospf6d
        for dic in conf:
            try:
                int(dic["dead_int"])
            except ValueError:
                dic["dead_int"] = self.DEAD_INT
        return conf

    def set_defaults(self, defaults):
        """:param debug: the set of debug events that should be logged
        :param dead_int: Dead interval timer
        :param hello_int: Hello interval timer
        :param priority: priority for the interface, used for DR election
        :param redistribute: set of OSPFRedistributedRoute sources
        :param instance_id: the number of the attached OSPF instance"""
        defaults.instance_id = 0
        super(OSPF6, self).set_defaults(defaults)
        # 'minimal hello-multiplier x' is not implemented in ospf6d
        defaults.dead_int = self.DEAD_INT


class OSPF6RedistributedRoute(OSPFRedistributedRoute):
    """A class representing a redistributed route type in OSPF6"""
