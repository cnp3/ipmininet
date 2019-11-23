import os

from .install import parse_args, dist, install_mininet, install_frrouting, \
    enable_ipv6, install_openr

if __name__ == "__main__":

    args = parse_args()
    args.output_dir = os.path.normpath(os.path.abspath(args.output_dir))

    dist.require_pip(2)
    dist.require_pip(3)

    if args.install_mininet:
        install_mininet(args.output_dir)

    if args.all or args.install_frrouting:
        install_frrouting(args.output_dir)

    if args.all or args.install_radvd:
        if dist.NAME == "Ubuntu" or dist.NAME == "Debian":
            dist.install("resolvconf")
        dist.install("radvd")

    if args.all or args.install_sshd:
        dist.install("openssh-server")

    if args.all or args.install_named:
        if dist.NAME == "Ubuntu" or dist.NAME == "Debian":
            dist.install("bind9")
        elif dist.NAME == "Fedora":
            dist.install("bind")

    # Install IPMininet

    if args.install_ipmininet:
        dist.install("git")
        source_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dist.pip_install(2, source_dir)
        dist.pip_install(3, source_dir)

    # Enable IPv6 (disabled by mininet installation)

    if args.all or args.enable_ipv6:
        enable_ipv6()

    # Install test dependencies

    dist.install("bridge-utils", "traceroute")
    if dist.NAME == "Fedora":
        dist.install("nc")
    else:
        dist.install("netcat-openbsd")

    dist.pip_install(2, "pytest")
    dist.pip_install(3, "pytest")

    # Install OpenR

    if args.install_openr:
        if dist.NAME == "Ubuntu":
            install_openr(args.output_dir)
        else:
            print("OpenR build currently only available on Ubuntu."
                  " Skipping installing OpenR.")
