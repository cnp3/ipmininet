#!/bin/bash

# This script is intended to install Mininet and IPMininet into
# a brand-new Ubuntu virtual machine,
# to create a fully usable "tutorial" VM.
set -e

export LC_ALL=C
export DEBIAN_FRONTEND=noninteractive

MN_VERSION="2.3.0"
MN_INSTALL_SCRIPT_REMOTE="https://raw.githubusercontent.com/mininet/mininet/${MN_VERSION}/util/vm/install-mininet-vm.sh"
DEPS="python3 \
      python3-pip \
      git"

IPMN_REPO="${IPMN_REPO:-https://github.com/cnp3/ipmininet.git}"
IPMN_BRANCH="${IPMN_BRANCH:-master}"
IPMN_DIR="${IPMN_DIR:-ipmininet}"

# Upgrade system and install dependencies
sudo apt update -yq && sudo apt upgrade -yq
sudo apt install -yq ${DEPS}

# Set mininet-vm in hosts since mininet install will change the hostname
sudo sed -i -e 's/^\(127\.0\.1\.1\).*/\1\tmininet-vm/' /etc/hosts

# Install mininet
pushd $HOME
source <(curl -sL ${MN_INSTALL_SCRIPT_REMOTE}) ${MN_VERSION}

# Update pip install
sudo pip3 install --upgrade pip
sudo apt remove -yq python3-pip

# Install ipmininet

[ ! -d "$IPMN_DIR" ] && git clone ${IPMN_REPO} ${IPMN_DIR}
pushd ${IPMN_DIR}
git checkout -B ${IPMN_BRANCH} -t origin/${IPMN_BRANCH} || >&2 cat <<-EOF
	WARN: Command 'git checkout -B ${IPMN_BRANCH} -t origin/${IPMN_BRANCH}' failed.
	Please check the ipmininet repository.
EOF

sudo pip3 install .
sudo python3 -m ipmininet.install -af6
popd
popd
