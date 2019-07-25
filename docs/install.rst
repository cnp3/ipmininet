Installation
============


IPMininet needs at minimum:

- Python_ (with pip) **2.7+** or **3.5+**
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

    $ vagrant init ipmininet/ubuntu-16.04
    $ vagrant up

This will create the VM. To access the VM with SSH, just issue the
following command in the same directory as the two previous one:

.. code-block:: bash

    $ vagrant ssh

.. _vagrant box: https://app.vagrantup.com/ipmininet/boxes/ubuntu-16.04
.. _Vagrant: https://www.vagrantup.com/downloads.html
.. _Virtualbox: https://www.virtualbox.org/wiki/Downloads

Manual installation from PyPI
-----------------------------

You can download and install IPMininet.
If you have pip above **18.1**, execute:

.. code-block:: bash

    $ sudo pip install ipmininet

If you have an older version of pip, use:

.. code-block:: bash

    $ sudo pip install --process-dependency-links ipmininet

Then, you can install all the daemons:

.. code-block:: bash

    $ sudo python -m ipmininet.install -af

You can choose to install only a subset of the daemons
by changing the options on the installation script.
For the option documentations, use the ``-h`` option.

.. _documentation: http://mininet.org/download/

Manual installation from sources
--------------------------------

To manually install IPMininet from source, first get the source code:

.. code-block:: bash

    $ git clone https://github.com/cnp3/ipmininet.git
    $ cd ipmininet
    $ git checkout <version>

Then, install IPMininet.
If you have pip above **18.1**, execute:

.. code-block:: bash

    $ sudo pip install .

If you have an older version of pip, use:

.. code-block:: bash

    $ sudo pip install --process-dependency-links .

Finally, you can install all the daemons:

.. code-block:: bash

    $ sudo python -m ipmininet.install -af

You can choose to install only a subset of the daemons
by changing the options on the installation script.
For the option documentations, use the ``-h`` option.
