"""This file contains a simple OpenR topology"""

from ipmininet.iptopo import IPTopo
from ipmininet.router import OpenrRouter
from ipmininet.node_description import OpenrRouterDescription
from ipmininet.router.config import OpenrRouterConfig

HOSTS_PER_ROUTER = 2


class SimpleOpenrNet(IPTopo):
    """
        +----+     +----+
        | r1 +-----+ r2 |
        +--+-+     +----+
           |
           |       +----+
           +-------+ r3 |
                   +----+
    """

    def build(self, *args, **kwargs):
        # pylint: disable=unbalanced-tuple-unpacking
        r_1, r_2, r_3 = \
            self.addRouters('r_1', 'r_2', 'r_3',
                            cls=OpenrRouter,
                            routerDescription=OpenrRouterDescription,
                            config=OpenrRouterConfig)
        self.addLinks((r_1, r_2), (r_1, r_3))
        for router in (r_1, r_2, r_3):
            for i in range(HOSTS_PER_ROUTER):
                self.addLink(router, self.addHost('h%s%s' % (i, router)),
                             params2={'v4_width': 5})

        super().build(*args, **kwargs)
