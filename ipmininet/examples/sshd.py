"""This modules shows a 2-routers topology which run the sshd daemon."""
from ipmininet.iptopo import IPTopo
from ipmininet.router.config import SSHd, RouterConfig


class SSHTopo(IPTopo):
    def build(self, *args, **kw):
        r1 = self.addRouter('r1', config=RouterConfig)
        r2 = self.addRouter('r2', config=RouterConfig)
        self.addLink(r1, r2)
        r1.addDaemon(SSHd)
        r2.addDaemon(SSHd)
        super(SSHTopo, self).build(*args, **kw)
