"""This module defines a modular host that is able to support
   multiple daemons
"""

from .__host import IPHost, CPULimitedHost

__all__ = ['IPHost', 'CPULimitedHost']
