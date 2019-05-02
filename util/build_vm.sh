#!/bin/bash

# This script is intended to install Mininet and IPMininet into
# a brand-new Ubuntu virtual machine,
# to create a fully usable "tutorial" VM.
set -e

export LC_ALL=C

MN_VERSION="master"
MN_INSTALL_SCRIPT_REMOTE="https://raw.githubusercontent.com/mininet/mininet/${MN_VERSION}/util/vm/install-mininet-vm.sh"
DEPS="python \
      python-pip \
      python3 \
      python3-pip \
      git"

# Upgrade system and install dependencies
sudo apt update -yq && sudo apt upgrade -yq
sudo apt install -yq ${DEPS}

# Set mininet-vm in hosts since mininet install will change the hostname
sudo sed -i -e 's/^\(127\.0\.1\.1\).*/\1\tmininet-vm/' /etc/hosts

# Install mininet
pushd $HOME
source <(curl -sL ${MN_INSTALL_SCRIPT_REMOTE})
sudo pip2 install mininet/

# Install ipmininet
git clone https://github.com/cnp3/ipmininet.git
pushd ipmininet
sudo python util/install.py -iaf
popd
popd

# Fix setuptools version issue
sudo pip2 install --upgrade pip
sudo apt-get remove -y python-pip
sudo pip2 install --upgrade setuptools
