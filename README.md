# IPMininet [![Pypi Version](https://img.shields.io/pypi/v/ipmininet.svg)](https://pypi.python.org/pypi/ipmininet/) [![Build Status](https://jenkins-mininet.info.ucl.ac.be/buildStatus/icon?job=ipmininet%2Fpythonversion%3Dipmininet-py2&subject=Python2.7)](https://jenkins-mininet.info.ucl.ac.be/job/ipmininet/pythonversion=ipmininet-py2/)

This is a python library, extending [Mininet](http://mininet.org), in order
to support emulation of (complex) IP networks. As such it provides new classes,
such as Routers, auto-configures all properties not set by the user, such as
IP addresses or router configuration files, ...

[ipmininet/examples/README](ipmininet/examples/README.md) 
contains a description of the examples that come with this library.

## Installation

### Virtual Machine

We maintain a [vagrant box](https://app.vagrantup.com/ipmininet/boxes/ubuntu-16.04)
packaged with all the daemons.
To use it, first install [Vagrant](https://www.vagrantup.com/downloads.html)
and [Virtualbox](https://www.virtualbox.org/wiki/Downloads)
and then, execute the following commands:
```bash
$ vagrant init ipmininet/ubuntu-16.04
$ vagrant up
```
This will create the VM. To access the VM with SSH, just issue the
following command in the same directory as the two previous one:
```bash
$ vagrant ssh
```

### Manual installation from sources

To manually install IPMininet from source, first get the source code:

```bash
$ git clone https://github.com/cnp3/ipmininet.git
$ cd ipmininet
$ git checkout <version>
```

Then, install IPMininet, Mininet and all the daemons:

```bash
$ sudo python util/install.py -iamf
```

You can choose to install only a subset of the daemons
by changing the options on the installation script.
For the option documentations, use the ``-h`` option.

### Manual installation from PyPI

Install Mininet by following its
[documentation](http://mininet.org/download/).

Then, you can download and install IPMininet.

```bash
$ sudo pip install ipmininet
```

Finally, you can install all the daemons:

```bash
$ sudo python util/install.py -af
```

You can choose to install only a subset of the daemons
by changing the options on the installation script.
For the option documentations, use the ``-h`` option.

## Contributions

If you want to contribute, feel free to open a Pull Request.
[ipmininet/tests/README](ipmininet/tests/README.md)
contains the instructions to run the test suite of the library.
