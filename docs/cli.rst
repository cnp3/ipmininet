Command-Line interface
======================

Most of the IPMininet CLI functionality is similar to Mininet CLI.
We extended it to support IPv6 addressing and routers.
For instance, the `pingall` command will test
both IPv4 and IPv6 connectivity between all hosts.

You can find more documentation (valid for both CLIs) on:

- `Interact with hosts and switch <http://mininet.org/walkthrough/#interact-with-hosts-and-switches>`_
- `Test connectivity between hosts <http://mininet.org/walkthrough/#test-connectivity-between-hosts>`_
- `Xterm display <http://mininet.org/walkthrough/#xterm-display>`_
- `Other details <http://mininet.org/walkthrough/#part-3-mininet-command-line-interface-cli-commands>`_

However, the `mn` command won't start a IPMininet topology but a Mininet one.
If you want to try the IPMininet CLI, you can launch the following command:

.. code-block:: bash

    $ sudo python -m ipmininet.examples --topo simple_ospf_network

To get the complete list of commands, when in the CLI, run:

.. code-block:: bash

    mininet> help

To get details about a specific command, run:

.. code-block:: bash

    mininet> help <command>
