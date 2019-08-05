import argparse
import os
import sys
import stat
import re

from utils import supported_distributions, identify_distribution, sh

MininetVersion = "master"
FRRoutingVersion = "7.1"
OpenrRelease = "rc-20190419-11514"

os.environ["PATH"] = "%s:/sbin:/usr/sbin/:/usr/local/sbin" % os.environ["PATH"]


def parse_args():
    parser = argparse.ArgumentParser(description="Install IPMininet with its dependencies")
    parser.add_argument("-o", "--output-dir", help="Path to the directory that will store the dependencies",
                        default=os.environ["HOME"])
    parser.add_argument("-i", "--install-ipmininet", help="Install IPMininet", action="store_true")
    parser.add_argument("-m", "--install-mininet", help="Install the last version of mininet and its dependencies",
                        action="store_true")
    parser.add_argument("-a", "--all", help="Install all daemons", action="store_true")
    parser.add_argument("-q", "--install-frrouting", help="Install FRRouting (version %s) daemons" % FRRoutingVersion,
                        action="store_true")
    parser.add_argument("-r", "--install-radvd", help="Install the RADVD daemon",
                        action="store_true")
    parser.add_argument("-s", "--install-sshd", help="Install the OpenSSH server", action="store_true")
    parser.add_argument("-6", "--enable-ipv6", help="Enable IPv6", action="store_true")
    parser.add_argument("-f", "--install-openr",
                        help="Install OpenR. OpenR is not installed with '-a' option since the build takes quite long.\
                        We also experienced that the build requires a substantial amount of memory (~4GB).",
                        action="store_true")
    return parser.parse_args()


def install_mininet():
    dist.install("git")

    if dist.NAME == "Fedora":
        mininet_opts = "-fnp"
        dist.install("openvswitch", "openvswitch-devel", "openvswitch-test")
        sh("systemctl enable openvswitch")
        sh("systemctl start openvswitch")
    else:
        mininet_opts = "-a"

    sh("git clone https://github.com/mininet/mininet.git", cwd=args.output_dir)
    sh("git checkout %s" % MininetVersion, cwd=os.path.join(args.output_dir, "mininet"))
    sh("mininet/util/install.sh %s -s ." % mininet_opts,
       "pip2 -q install mininet/",
       "pip3 -q install mininet/",
       cwd=args.output_dir)


def install_libyang():

    packages = []

    if dist.NAME == "Ubuntu" or dist.NAME == "Debian":
        dist.install("libpcre16-3", "libpcre3-dev", "libpcre32-3", "libpcrecpp0v5")
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
           cwd=args.output_dir)


def install_frrouting():
    dist.install("autoconf", "automake", "libtool", "make", "gcc", "groff",
                 "patch", "make", "bison", "flex", "gawk",
                 "python3-pytest")

    if dist.NAME == "Ubuntu" or dist.NAME == "Debian":
        dist.install("libreadline-dev", "libc-ares-dev", "libjson-c-dev",
                     "perl", "python3-dev", "libpam0g-dev", "libsystemd-dev",
                     "libsnmp-dev", "pkg-config")
    elif dist.NAME == "Fedora":
        dist.install("readline-devel", "c-ares-devel", "json-c-devel",
                     "perl-core", "python3-devel", "pam-devel", "systemd-devel",
                     "net-snmp-devel", "pkgconfig")

    install_libyang()

    frrouting_src = os.path.join(args.output_dir, "frr-%s" % FRRoutingVersion)
    frrouting_tar = frrouting_src + ".tar.gz"
    sh("wget https://github.com/FRRouting/frr/releases/download/frr-{v}/frr-{v}.tar.gz".format(v=FRRoutingVersion),
       "tar -zxvf '%s'" % frrouting_tar,
       cwd=args.output_dir)

    frrouting_install = os.path.join(args.output_dir, "frr")
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


def install_openr(openr_release=OpenrRelease,
                  openr_remote="https://github.com/facebook/openr.git"):
    dist.install("git")
    openr_install = os.path.join(args.output_dir, "openr")
    openr_build = os.path.join(openr_install, "build")
    openr_buildscript = os.path.join(openr_build, "build_openr_debian.sh")
    debian_system_builder = "debian_system_builder/debian_system_builder.py"
    sh("git clone %s" % openr_remote,
       cwd=args.output_dir)
    sh("git checkout %s" % openr_release,
       cwd=openr_install)
    # Generate build script
    with open(openr_buildscript, "w+") as f:
        sh("python %s" % debian_system_builder,
           stdout=f,
           cwd=openr_build).wait()
    # Make build script executable
    os.chmod(openr_buildscript, stat.S_IRWXU)
    # Execute build script
    sh(openr_buildscript,
       cwd=openr_build,
       shell=True,
       executable="/bin/bash")


def update_grub():
    if dist.NAME == "Fedora":
        cmd = "grub2-mkconfig --output=/boot/grub2/grub.cfg"
    elif dist.NAME == "Ubuntu" or dist.NAME == "Debian":
        cmd = "update-grub"
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


args = parse_args()
args.output_dir = os.path.normpath(os.path.abspath(args.output_dir))

if os.getuid() != 0:
    print("This program must be run as root")
    sys.exit(1)

# Identify the distribution

dist = identify_distribution()
if dist is None:
    print("The installation script only supports %s" % ", ".join([d.NAME for d in supported_distributions()]))
    sys.exit(1)
dist.update()

# Install dependencies

dist.install("python-pip", "python3-pip")

if args.install_mininet:
    install_mininet()

if args.all or args.install_frrouting:
    install_frrouting()

if args.all or args.install_radvd:
    if dist.NAME == "Ubuntu" or dist.NAME == "Debian":
        dist.install("resolvconf")
    dist.install("radvd")

if args.all or args.install_sshd:
    dist.install("openssh-server")

# Install IPMininet

if args.install_ipmininet:
    ipmininet_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sh("pip2 -q install %s/" % ipmininet_folder)
    sh("pip3 -q install %s/" % ipmininet_folder)

# Enable IPv6 (disabled by mininet installation)

if args.all or args.enable_ipv6:
    enable_ipv6()

# Install test dependencies

dist.install("bridge-utils", "traceroute")
if dist.NAME == "Fedora":
    dist.install("nc")
else:
    dist.install("netcat-openbsd")

sh("pip2 -q install pytest")
sh("pip3 -q install pytest")

# Install OpenR

if args.install_openr:
    if dist.NAME == "Ubuntu":
        install_openr()
    else:
        print("OpenR build currently only available on Ubuntu. Skipping installing OpenR.")
        pass
