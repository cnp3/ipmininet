Installation
============


IPMininet needs at minimum:

- Python_ (with pip) **3.6+**
- Mininet_

IPMininet needs some daemon executables to be installed
and accessible through the PATH environment variable:

- FRRouting_ daemons: zebra, ospfd, ospf6d, bgpd, pimd
- RADVD_
- SSHD_

.. _Python: https://www.python.org
.. _Mininet: http://www.mininet.org
.. _FRRouting: https://frrouting.org
.. _RADVD: http://www.litech.org/radvd
.. _SSHD: https://www.openssh.com

You can either download them by hand or rely
on one the following methods:

Virtual Machine
---------------

We maintain a `vagrant box`_ packaged with all the daemons.
To use it, first install `Vagrant`_ and `Virtualbox`_
and then, execute the following commands:

.. code-block:: bash

    $ vagrant init ipmininet/ubuntu-18.04
    $ vagrant up

This will create the VM. To access the VM with SSH, just issue the
following command in the same directory as the two previous one:

.. code-block:: bash

    $ vagrant ssh

.. _vagrant box: https://app.vagrantup.com/ipmininet/boxes/ubuntu-18.04
.. _Vagrant: https://www.vagrantup.com/downloads.html
.. _Virtualbox: https://www.virtualbox.org/wiki/Downloads

Manual installation
-------------------

You can download and install IPMininet.
You can change the installed version by replacing "v0.9" in the following commands.
If you have pip above **18.1**, execute:

.. code-block:: bash

    $ sudo pip install --upgrade git+https://github.com/cnp3/ipmininet.git@v0.9

If you have an older version of pip, use:

.. code-block:: bash

    $ sudo pip install --process-dependency-links --upgrade git+https://github.com/cnp3/ipmininet.git@v0.9

Then, you can install all the daemons:

.. code-block:: bash

    $ sudo python -m ipmininet.install -af

You can choose to install only a subset of the daemons
by changing the options on the installation script.
For the option documentations, use the ``-h`` option.

.. _documentation: http://mininet.org/download/
