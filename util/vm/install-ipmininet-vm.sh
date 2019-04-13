#!/bin/bash

# This script is intended to install Mininet into
# a brand-new Ubuntu virtual machine,
# to create a fully usable "tutorial" VM.
set -e

LC_ALL=C

MN_INSTALL_SCRIPT_REMOTE="https://raw.githubusercontent.com/mininet/mininet/master/util/vm/install-mininet-vm.sh"
DEPS="python \
      python-dev \
      python3 \
      python3-dev"
PIP_BOOTSTRAP_SCRIPT_REMOTE="https://bootstrap.pypa.io/get-pip.py"

# Upgrade system and install dependencies
sudo apt update -yq && sudo apt upgrade -yq
sudo apt install -yq $DEPS

# Install pip
curl -sLo /tmp/get-pip.py $PIP_BOOTSTRAP_SCRIPT_REMOTE
sudo python /tmp/get-pip.py

# Install python dependencies
sudo pip install --upgrade pip
sudo pip install setuptools

# Set mininet-vm in hosts since mininet install will change the hostname
sudo sed -i -e 's/^\(127\.0\.1\.1\).*/\1\tmininet-vm/' /etc/hosts

# Install mininet
source <(curl -sL $MN_INSTALL_SCRIPT_REMOTE)

# Install ipmininet
cd $BUILD_DIR
pushd $(pwd)
git clone https://github.com/cnp3/ipmininet.git
cd ipmininet
sudo python setup.py install
popd

# Install quagga
sudo apt install -yq quagga
sudo ln -s /usr/lib/quagga/* /usr/bin/

# Install radvd
sudo apt install -yq radvd
