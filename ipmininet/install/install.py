import argparse
import os
import re
import stat
import sys

# For imports to work during setup and afterwards
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import supported_distributions, identify_distribution, sh

MininetVersion = "2.3.0d6"
FRRoutingVersion = "7.1"

os.environ["PATH"] = "%s:/sbin:/usr/sbin/:/usr/local/sbin" % os.environ["PATH"]


def parse_args():
    parser = argparse.ArgumentParser(description="Install IPMininet with"
                                                 " its dependencies")
    parser.add_argument("-o", "--output-dir",
                        help="Path to the directory that will store the"
                             " dependencies", default=os.environ["HOME"])
    parser.add_argument("-i", "--install-ipmininet", help="Install IPMininet",
                        action="store_true")
    parser.add_argument("-m", "--install-mininet",
                        help="Install the last version of mininet"
                             " and its dependencies",
                        action="store_true")
    parser.add_argument("-a", "--all", help="Install all daemons",
                        action="store_true")
    parser.add_argument("-q", "--install-frrouting",
                        help="Install FRRouting (version %s) daemons"
                        % FRRoutingVersion,
                        action="store_true")
    parser.add_argument("-r", "--install-radvd",
                        help="Install the RADVD daemon", action="store_true")
    parser.add_argument("-s", "--install-sshd",
                        help="Install the OpenSSH server", action="store_true")
    parser.add_argument("-n", "--install-named",
                        help="Install the Named daemon", action="store_true")
    parser.add_argument("-6", "--enable-ipv6", help="Enable IPv6",
                        action="store_true")
    parser.add_argument("-f", "--install-openr",
                        help="Install OpenR. OpenR is not installed with '-a'"
                             " option since the build takes quite long. We"
                             " also experienced that the build requires a"
                             " substantial amount of memory (~4GB).",
                        action="store_true")
    return parser.parse_args()


def install_mininet(output_dir: str, pip_install=True):
    dist.install("git")

    if dist.NAME == "Fedora":
        mininet_opts = "-fnp"
        dist.install("openvswitch", "openvswitch-devel", "openvswitch-test")
        sh("systemctl enable openvswitch")
        sh("systemctl start openvswitch")
    else:
        mininet_opts = "-a"

    sh("git clone https://github.com/mininet/mininet.git", cwd=output_dir)
    sh("git checkout %s" % MininetVersion,
       cwd=os.path.join(output_dir, "mininet"))
    sh("mininet/util/install.sh %s -s ." % mininet_opts,
       cwd=output_dir)

    if pip_install:
        dist.pip_install("mininet/", cwd=output_dir)


def install_libyang(output_dir: str):

    packages = []

    if dist.NAME == "Ubuntu" or dist.NAME == "Debian":
        dist.install("libpcre16-3", "libpcre3-dev", "libpcre32-3",
                     "libpcrecpp0v5")
        cmd = "dpkg -i"
        libyang_url = "https://ci1.netdef.org/artifact/LIBYANG-YANGRELEASE" \
                      "/shared/build-10/Debian-AMD64-Packages"
        packages.extend(["libyang0.16_0.16.105-1_amd64.deb",
                         "libyang-dev_0.16.105-1_amd64.deb"])
    elif dist.NAME == "Fedora":
        dist.install("pcre-devel")
        cmd = "rpm -ivh"
        libyang_url = "https://ci1.netdef.org/artifact/LIBYANG-YANGRELEASE" \
                      "/shared/build-10/Fedora-29-x86_64-Packages/"
        packages.extend(["libyang-0.16.111-0.x86_64.rpm",
                         "libyang-devel-0.16.111-0.x86_64.rpm"])
    else:
        return

    for package in packages:
        sh("wget %s/%s" % (libyang_url, package),
           "%s %s" % (cmd, package),
           "rm %s" % package,
           cwd=output_dir)


def install_frrouting(output_dir: str):
    dist.install("autoconf", "automake", "libtool", "make", "gcc", "groff",
                 "patch", "make", "bison", "flex", "gawk", "texinfo",
                 "python3-pytest")

    if dist.NAME == "Ubuntu" or dist.NAME == "Debian":
        dist.install("libreadline-dev", "libc-ares-dev", "libjson-c-dev",
                     "perl", "python3-dev", "libpam0g-dev", "libsystemd-dev",
                     "libsnmp-dev", "pkg-config")
    elif dist.NAME == "Fedora":
        dist.install("readline-devel", "c-ares-devel", "json-c-devel",
                     "perl-core", "python3-devel", "pam-devel", "systemd-devel",
                     "net-snmp-devel", "pkgconfig")

    install_libyang(output_dir)

    frrouting_src = os.path.join(output_dir, "frr-%s" % FRRoutingVersion)
    frrouting_tar = frrouting_src + ".tar.gz"
    sh("wget https://github.com/FRRouting/frr/releases/download/frr-{v}/"
       "frr-{v}.tar.gz".format(v=FRRoutingVersion),
       "tar -zxvf '%s'" % frrouting_tar,
       cwd=output_dir)

    frrouting_install = os.path.join(output_dir, "frr")
    sh("./configure '--prefix=%s'" % frrouting_install,
       "make",
       "make install",
       cwd=frrouting_src)

    sh("rm -r '%s' '%s'" % (frrouting_src, frrouting_tar))

    sh("groupadd frr", may_fail=True)
    sh("groupadd frrvty", may_fail=True)
    sh("usermod -a -G frr root", may_fail=True)
    sh("usermod -a -G frrvty root", may_fail=True)

    for root, _, files in os.walk(os.path.join(frrouting_install, "sbin")):
        for f in files:
            link = os.path.join("/usr/sbin", os.path.basename(f))
            if os.path.exists(link):
                os.remove(link)
            os.symlink(os.path.join(root, f), link)
        break
    for root, _, files in os.walk(os.path.join(frrouting_install, "bin")):
        for f in files:
            link = os.path.join("/usr/bin", os.path.basename(f))
            if os.path.exists(link):
                os.remove(link)
            os.symlink(os.path.join(root, f), link)
        break


def install_openr(output_dir: str, may_fail=False):
    # It's not possible to get a build script with pinned dependencies from the
    # OpenR github repository. The checked-in build script has the dependencies
    # pinned manually. Builds and installs OpenR release rc-20190419-11514.
    # https://github.com/facebook/openr/releases/tag/rc-20190419-11514
    script_name = "build_openr-rc-20190419-11514.sh"
    openr_buildscript = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     script_name)
    # Execute build script
    p = sh(openr_buildscript,
           cwd=output_dir,
           shell=True,
           executable="/bin/bash",
           may_fail=may_fail)
    # We should end here only if may_fail is True
    if p.returncode != 0:
        print("WARNING: Ignoring failed OpenR installation.", file=sys.stderr)


def update_grub():
    if dist.NAME == "Fedora":
        cmd = "grub2-mkconfig --output=/boot/grub2/grub.cfg"
    elif dist.NAME == "Ubuntu" or dist.NAME == "Debian":
        cmd = "update-grub"
    else:
        return
    sh(cmd)


def enable_ipv6():
    if dist.NAME == "Debian":
        dist.install("grub-common")

    grub_cfg = "/etc/default/grub"
    with open(grub_cfg, "r+") as f:
        data = f.read()
        f.seek(0)
        f.write(data.replace("ipv6.disable=1 ", ""))
        f.truncate()
    update_grub()

    sysctl_cfg = "/etc/sysctl.conf"
    with open(sysctl_cfg, "r+") as f:
        data = f.read()
        f.seek(0)
        # Comment out lines
        f.write(re.sub(r'\n(.*disable_ipv6.*)', r'\n#\g<1>', data))
        f.truncate()
    sh("sysctl -p")


# Force root

if os.getuid() != 0:
    print("This program must be run as root")
    sys.exit(1)

# Identify the distribution

dist = identify_distribution()
if dist is None:
    supported = ", ".join([d.NAME for d in supported_distributions()])
    print("The installation script only supports %s" % supported)
    sys.exit(1)
dist.update()
