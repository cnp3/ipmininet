from .zebra import QuaggaDaemon, Zebra
from .utils import ConfigDict
from ipmininet.utils import realIntfList


class PIMD(QuaggaDaemon):
    """This class configures a PIM daemon to responds to IGMP queries in order
    to setup multicast routing in the network."""

    NAME = 'pimd'
    DEPENDS = (Zebra,)
    KILL_PATTERNS = (NAME,)

    def __init__(self, node, *args, **kwargs):
        super(PIMD, self).__init__(node=node, *args, **kwargs)

    def build(self):
        cfg = super(PIMD, self).build()
        cfg.update(self.options)
        cfg.interfaces = [
            ConfigDict(name=itf.name,
                       ssm=itf.get('multicast_ssm', self.options.multicast_ssm),
                       igmp=itf.get('multicast_igmp',
                                    self.options.multicast_igmp))
            for itf in realIntfList(self._node) if itf.enable_multicast]
        return cfg

    def set_defaults(self, defaults):
        """:param debug: the set of debug events that should be logged
        :param multicast_ssm: Enable pim ssm mode by default or not
        :param multicast_igmp: Enable igmp by default or not"""
        defaults.multicast_ssm = True
        defaults.multicast_igmp = True
        super(PIMD, self).set_defaults(defaults)
