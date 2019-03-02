"""This module has a hard dependency against mininet, check here that it is
actually installed. This will yield a better (?) error message than just a raw
ImportError nested somewhere ..."""
try:
    import mininet  # noqa
except ImportError as e:
    import sys
    sys.stderr.write('Failed to import mininet!\n'
                     'Using the mininetlib module requires mininet to be '
                     'installed.\n'
                     'Visit www.mininet.org to learn how to do so.\n')
    sys.exit(1)

# Define basestring for python 2 & 3 compatibility
try:
    basestring = basestring
except NameError:
    basestring = str

# Define global constants
MIN_IGP_METRIC = 1
OSPF_DEFAULT_AREA = '0.0.0.0'
DEBUG_FLAG = False
