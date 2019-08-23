
from mininet.log import lg as log
import mininet.clean as mnclean

import ipmininet.router.config as daemons

from .utils import is_container


def cleanup(level='info'):
    """Cleanup all possible junk that we may have started."""
    log.setLogLevel(level)
    # Standard mininet cleanup
    mnclean.cleanup()
    # Cleanup any leftover daemon
    patterns = []
    for d in daemons.__all__:
        obj = getattr(daemons, d)
        killp = getattr(obj, 'KILL_PATTERNS', None)
        if not killp:
            continue
        if not is_container(killp):
            killp = [killp]
        patterns.extend(killp)
    log.info('*** Cleaning up daemons:\n')
    for pattern in patterns:
        mnclean.killprocs('"%s"' % pattern)
    log.info('\n')


if __name__ == '__main__':
    cleanup()
