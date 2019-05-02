import argparse
import os
import sys
import stat
import re

from utils import supported_distributions, identify_distribution, sh

MininetVersion = "master"
QuaggaVersion = "1.2.4"
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
    parser.add_argument("-q", "--install-quagga", help="Install Quagga (version %s) daemons" % QuaggaVersion,
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
       cwd=args.output_dir)


def install_quagga():
    dist.install("autoconf", "automake", "libtool", "make", "gcc", "gawk", "pkg-config")

    if dist.NAME == "Ubuntu" or dist.NAME == "Debian":
        dist.install("libreadline-dev", "libc-ares-dev")
    elif dist.NAME == "Fedora":
        dist.install("readline-devel", "c-ares-devel")

    quagga_src = os.path.join(args.output_dir, "quagga-%s" % QuaggaVersion)
    quagga_tar = quagga_src + ".tar.gz"
    sh("wget http://download.savannah.gnu.org/releases/quagga/quagga-%s.tar.gz" % QuaggaVersion,
       "tar -zxvf '%s'" % quagga_tar,
       cwd=args.output_dir)

    quagga_install = os.path.join(args.output_dir, "quagga")
    sh("./configure '--prefix=%s'" % quagga_install,
       "make",
       "make install",
       cwd=quagga_src)

    sh("rm -r '%s' '%s'" % (quagga_src, quagga_tar))

    sh("groupadd quagga", may_fail=True)
    sh("usermod -a -G quagga root", may_fail=True)

    for root, _, files in os.walk(os.path.join(quagga_install, "sbin")):
        for f in files:
            link = os.path.join("/usr/sbin", os.path.basename(f))
            if os.path.exists(link):
                os.remove(link)
            os.symlink(os.path.join(root, f), link)
        break
    for root, _, files in os.walk(os.path.join(quagga_install, "bin")):
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

dist.install("python-pip")

if args.install_mininet:
    install_mininet()

if args.all or args.install_quagga:
    install_quagga()

if args.all or args.install_radvd:
    dist.install("radvd")

if args.all or args.install_sshd:
    dist.install("openssh-server")

# Install IPMininet

if args.install_ipmininet:
    ipmininet_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sh("pip2 -q install %s/" % ipmininet_folder)

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

# Install OpenR

if args.install_openr:
    if dist.NAME == "Ubuntu":
        install_openr()
    else:
        print("OpenR build currently only available on Ubuntu. Skipping installing OpenR.")
        pass
