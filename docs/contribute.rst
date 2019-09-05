Developer Guide
===============

This section details some essential points to contribute to the code base.
Don't hesitate to ask for advice by opening an issue on Github.

Setting up the development environment
--------------------------------------

To develop a new feature, you have to install IPMininet from source
in development mode.

First get the source code of your fork:

.. code-block:: bash

    $ git clone <your-fork-url>
    $ cd ipmininet

Then, install your version of IPMininet in development mode.
If you have pip above **18.1**, execute:

.. code-block:: bash

    $ sudo pip -e install .

If you have an older version of pip, use:

.. code-block:: bash

    $ sudo pip -e install --process-dependency-links .

Finally, you can install all the daemons:

.. code-block:: bash

    $ sudo python -m ipmininet.install -af

Running the tests
-----------------

The `pytest <https://docs.pytest.org/en/latest/index.html>`_ framework is used
for the test suite and are `integrated within setuptools
<https://docs.pytest.org/en/latest/goodpractices.html
#integrating-with-setuptools-python-setup-py-test-pytest-runner>`_.
Currently the suite has end-to-end tests that check if the daemons work as
expected. Therefore, the tests require an operating environment, i.e. daemons
have to be installed and must be in PATH.

To run the whole test suite go the top level directory and run:

.. code-block:: bash

    sudo pytest

You can also run a single test by passing options to pytest:

.. code-block:: bash

    sudo pytest ipmininet/tests/test_sshd.py --fulltrace


Building the documentation
--------------------------

First, you have to install the requirements to build the project.
When at the root of the documentation, run:

.. code-block:: bash

    pip install -r requirements.txt

Then you can generate the html documentation
in the folder ``docs/_build/html/`` with:

.. code-block:: bash

    make html

The examples in the documentation can also be tested when changing the code base
with the following command:

.. code-block:: bash

    sudo make doctest

.. _contribute_example:

Adding a new example
--------------------

When adding a new example of topology to IPMininet,
you have to perform the following tasks:

- Create a new ``IPTopo`` subclass in the folder ``ipmininet/examples/``.
- Add the new class to the dictionary ``TOPOS``
  of ``ipmininet/examples/__main__.py``.
- Document its layout in the ``build()`` method docstring.
- Document the example in ``ipmininet/examples/README.md``.
- Add a test to check the correctness of the example.

Adding a new daemon
-------------------

When adding a new daemon to IPMininet, you have to perform the following tasks:

- Create a new `mako template <https://www.makotemplates.org/>`_
  in the folder ``ipmininet/router/config/templates/`` or
  ``ipmininet/host/config/templates/`` for the daemon configuration.
- Create a new ``RouterDaemon`` or ``HostDaemon`` subclass in the folder ``ipmininet/router/config/``
  or ``ipmininet/host/config/``.
  The following things are required in this new subclass:

  * Set the class variable ``NAME`` with a unique name.
  * Set the class variable ``KILL_PATTERNS`` that lists
    all the process names that have to be cleaned
    if a user uses the cleaning command in :ref:`getting_started_cleaning`.
  * Extend the property ``startup_line`` that gives the command line
    to launch the daemon.
  * Extend the property ``dry_run`` that gives the command line
    to check the generated configuration.
  * Extend the method ``set_defaults()`` to set default configuration values
    and document them all in the method docstring.
  * Extend the method ``build()`` to set the ConfigDict object
    that will be fed to the template.
  * Declare the daemon and its helper classes
    in ``ipmininet/router/config/__init__.py`` or ``ipmininet/host/config/__init__.py``.

- Add at least one example for the users (see :ref:`contribute_example`).
- Implement the tests to prove the correct configuration of the daemon.
- Update the setup of IPMininet to install the new daemon by updating
  ``ipmininet/install/__main__.py`` and ``ipmininet/install/install.py``.
- Document the daemon and its configuration options
  in the sphinx documentation in ``docs/daemons.rst``.
