import time
from subprocess import check_output, CalledProcessError

import mininet.clean as mnclean
from mininet.log import lg as log

import ipmininet.router.config as router_daemons
import ipmininet.host.config as host_daemons
from .utils import is_container


def cleanup(level='info'):
    """Cleanup all possible junk that we may have started."""
    log.setLogLevel(level)
    # Standard mininet cleanup
    mnclean.cleanup()
    # Cleanup any leftover daemon
    patterns = []
    for package in [router_daemons, host_daemons]:
        for d in package.__all__:
            obj = getattr(package, d, None)
            killp = getattr(obj, 'KILL_PATTERNS', None)
            if not killp:
                continue
            if not is_container(killp):
                killp = [killp]
            patterns.extend(killp)
    log.info('*** Cleaning up daemons:\n')
    killprocs(['"^%s"' % p for p in patterns])
    log.info('\n')


def killprocs(patterns, timeout=10):
    """Reliably terminate processes matching a pattern (including args)"""

    # Try clean kill
    for p in patterns:
        mnclean.sh('pkill -SIGINT -f %s' % p)

    # Make sure they are gone
    t = 0
    to_be_killed = {p: True for p in patterns}
    while any(to_be_killed.values()) or t >= timeout:
        for p in patterns:
            try:
                pids = check_output(['pgrep', '-f', p])
            except CalledProcessError:
                pids = ''
            if not pids:
                log.info(p)
                to_be_killed[p] = False

        time.sleep(.5)
        t += .5

    # Last resort
    for p in patterns:
        if to_be_killed[p]:
            log.info(p)
            mnclean.killprocs(p)


if __name__ == '__main__':
    cleanup()
