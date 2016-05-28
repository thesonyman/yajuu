"""Provides entry point main()."""

import sys
import pkg_resources


__version__ = pkg_resources.require('yajuu')[0].version


def main():
    print("List of argument strings: %s" % sys.argv[1:])

    if len(sys.argv[1:]) > 0 and sys.argv[1] == 'version':
        print('Version: {}'.format(__version__))
