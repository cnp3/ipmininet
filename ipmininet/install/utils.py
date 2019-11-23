import os
import shlex
import subprocess
import sys

from distutils.spawn import find_executable


def sh(*cmds, **kwargs):
    if 'stdout' not in kwargs:
        kwargs['stdout'] = subprocess.PIPE
    if 'stderr' not in kwargs:
        kwargs['stderr'] = subprocess.STDOUT
    may_fail = kwargs.pop("may_fail", False)
    output_stdout = kwargs.pop("output_stdout", True)
    env = kwargs.pop("env", os.environ)
    env["LC_ALL"] = "C"

    for cmd in cmds:
        print("\n*** " + cmd)
        p = subprocess.Popen(shlex.split(cmd),
                             env=env,
                             **kwargs)

        if output_stdout:
            while p.poll() is None:
                out = p.stdout.readline()
                if out != '':
                    sys.stdout.write(out.decode("utf-8"))

            out = p.stdout.read()
            if out != '':
                sys.stdout.write(out.decode("utf-8"))

            if p.poll() != 0:
                if not may_fail:
                    sys.exit(1)
                return p
    return p


class Distribution(object):
    NAME = None
    INSTALL_CMD = None
    UPDATE_CMD = None
    PIP3_CMD = None
    PIP2_CMD = None
    SpinPipVersion = "18.1"

    def __init__(self):
        self.pip2_args = self.check_pip_version(self.PIP2_CMD)
        self.pip3_args = self.check_pip_version(self.PIP3_CMD)

    def check_pip_version(self, pip):
        from pkg_resources import parse_version

        if find_executable(pip) is None:
            return ""
        p = sh("%s -V" % pip, output_stdout=False)
        if p.wait() != 0:
            print("Print cannot get the version of %s" % pip)
            return ""
        content, _ = p.communicate()
        try:
            v = content.decode("utf-8").split(u" ")[1]

            if parse_version(v) >= parse_version(self.SpinPipVersion):
                return ""
            return "--process-dependency-links"
        except (ValueError, IndexError):
            print("Cannot retrieve version number of %s" % pip)
            sys.exit(1)

    def install(self, *packages):
        sh(self.INSTALL_CMD + " " + " ".join(packages))

    def update(self):
        sh(self.UPDATE_CMD)

    def pip_install(self, version, *packages, **kwargs):
        if version == 2:
            pip = self.PIP2_CMD
            args = self.pip2_args
        else:
            pip = self.PIP3_CMD
            args = self.pip3_args
        if find_executable(pip) is not None:
            sh(pip + " -q install " + args + " ".join(packages), **kwargs)

    def require_pip(self, version):
        pip = self.PIP2_CMD if version == 2 else self.PIP3_CMD
        if find_executable(pip) is None:
            raise RuntimeError("Cannot find %s" % pip)


class Ubuntu(Distribution):
    NAME = "Ubuntu"
    INSTALL_CMD = "apt-get -y -q install"
    UPDATE_CMD = "apt-get update"
    PIP3_CMD = "pip3"
    PIP2_CMD = "pip2"


class Debian(Distribution):
    NAME = "Debian"
    INSTALL_CMD = "apt-get -y -q install"
    UPDATE_CMD = "apt-get update"
    PIP3_CMD = "pip3"
    PIP2_CMD = "pip2"


class Fedora(Distribution):
    NAME = "Fedora"
    INSTALL_CMD = "yum -y install"
    UPDATE_CMD = "true"
    PIP3_CMD = "pip"
    PIP2_CMD = "pip2"


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
