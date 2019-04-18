import abc
import os
import shlex
import subprocess
import sys


def sh(*cmds, **kwargs):
    if not 'stdout' in kwargs:
        kwargs['stdout'] = subprocess.PIPE
    if not 'stderr' in kwargs:
        kwargs['stderr'] = subprocess.STDOUT
    may_fail = kwargs.pop("may_fail", False)
    env = kwargs.pop("env", os.environ)
    env["LC_ALL"] = "C"

    for cmd in cmds:
        print("\n*** " + cmd)
        p = subprocess.Popen(shlex.split(cmd),
                             env=env,
                             **kwargs)

        if kwargs.get('stdout') == subprocess.PIPE:
            while p.poll() is None:
                out = p.stdout.readline()
                if out != '':
                    sys.stdout.write(out)

            out = p.stdout.read()
            if out != '':
                sys.stdout.write(out)

            if p.poll() != 0:
                if not may_fail:
                    sys.exit(1)
                return p
    return p


class Distribution(object):
    __metaclass__ = abc.ABCMeta

    NAME = None
    INSTALL_CMD = None
    UPDATE_CMD = None

    def install(self, *packages):
        sh(self.INSTALL_CMD + " " + " ".join(packages))

    def update(self):
        sh(self.UPDATE_CMD)


class Ubuntu(Distribution):
    NAME = "Ubuntu"
    INSTALL_CMD = "apt-get -y -q install"
    UPDATE_CMD = "apt-get update"


class Debian(Distribution):
    NAME = "Debian"
    INSTALL_CMD = "apt-get -y -q install"
    UPDATE_CMD = "apt-get update"


class Fedora(Distribution):
    NAME = "Fedora"
    INSTALL_CMD = "yum -y install"
    UPDATE_CMD = "true"


def supported_distributions():
    return Distribution.__subclasses__()


def identify_distribution():
    try:
        subprocess.check_call(shlex.split("grep Ubuntu /etc/lsb-release"))
        return Ubuntu()
    except subprocess.CalledProcessError:
        pass

    if os.path.exists("/etc/debian_version"):
        return Debian()

    if os.path.exists("/etc/fedora-release"):
        return Fedora()

    return None
