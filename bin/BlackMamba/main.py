#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from optparse import OptionParser

def _test(verbose=None):
    import doctest
    doctest.testmod(verbose=verbose)

def _profile_main(filename=None):
    import cProfile, pstats
    prof = cProfile.Profile()
    ctx = """_main(filename)"""
    prof = prof.runctx(ctx, globals(), locals())
    stats = pstats.Stats(prof)
    stats.sort_stats("time")
    stats.print_stats(10)

def _blurt(s, f):
    pass

def _main(filename=None):
    # YOUR CODE HERE
    return 0

if __name__ == "__main__":
    usage = "usage: %prog [options] [filename]"
    parser = OptionParser(usage=usage)
    parser.add_option('--profile', '-P',
                       help    = "Print out profiling stats",
                       action  = 'store_true')
    parser.add_option('--test', '-t',
                       help   ='Run doctests',
                       action = 'store_true')
    parser.add_option('--verbose', '-v',
                       help   ='print debugging output',
                       action = 'store_true')

    (options, args) = parser.parse_args()

    if options.verbose:
        def really_blurt(s, f=()):
            sys.stderr.write(s % f + '\n')
        _blurt = really_blurt

    # Assign non-flag arguments here.
    filename = None

    if options.profile:
        _profile_main(filename)
        exit()

    if options.test:
        _test(verbose=options.verbose)
        exit()

    sys.exit(_main(filename))