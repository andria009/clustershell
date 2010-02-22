#!/usr/bin/env python
#
# Copyright CEA/DAM/DIF (2008, 2009)
#  Contributor: Stephane THIELL <stephane.thiell@cea.fr>
#
# This file is part of the ClusterShell library.
#
# This software is governed by the CeCILL-C license under French law and
# abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL-C
# license as circulated by CEA, CNRS and INRIA at the following URL
# "http://www.cecill.info".
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and,  more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-C license and that you accept its terms.
#
# $Id$

"""
Usage: nodeset [COMMAND] [OPTIONS] [ns1 [-ixX] ns2|...]

Commands:
    --count, -c <nodeset> [nodeset ...]
        Return the number of nodes in nodesets.
    --expand, -e <nodeset> [nodeset ...]
        Expand nodesets to separate nodes.
    --fold, -f <nodeset> [nodeset ...]
        Compact/fold nodesets (or separate nodes) into one nodeset.
Options:
    --autostep=<number>, -a <number>
        Specify auto step threshold number when folding nodesets.
        If not specified, auto step is disabled.
        Example: autostep=4, "node2 node4 node6" folds in node[2,4,6]
                 autostep=3, "node2 node4 node6" folds in node[2-6/2]
    --help, -h
        This help page.
    --quiet, -q
        Quiet mode, hide any parse error messages (on stderr).
    --rangeset, -R
        Switch to RangeSet instead of NodeSet. Useful when working on
        numerical cluster ranges, eg. 1,5,18-31.
    --separator=<string>, -S <string>
        Use specified separator string when expanding nodesets (default
        is ' ').
    --version, -v
        Show ClusterShell version and exit.
Operations (default is union):
        The default operation is the union of node or nodeset.
    --exclude=<nodeset>, -x <nodeset>
        Exclude provided node or nodeset.
    --intersection, -i
        Calculate nodesets intersection.
    --xor, -X
        Calculate symmetric difference (XOR) between two nodesets.
"""

import getopt
import signal
import sys

from ClusterShell.NodeSet import NodeSet, NodeSetParseError
from ClusterShell.NodeSet import RangeSet, RangeSetParseError
from ClusterShell import __version__

def process_stdin(result, autostep):
    """Process standard input"""
    for line in sys.stdin.readlines():
        # Support multi-lines and multi-nodesets per line
        line = line[0:line.find('#')].strip()
        for node in line.split():
            result.update(result.__class__(node, autostep=autostep))

def run_nodeset(args):
    """
    Main script function.
    """
    autostep = None
    command = None
    quiet = False
    class_set = NodeSet
    separator = ' '

    # Parse getoptable options
    try:
        opts, args = getopt.getopt(args[1:], "a:cefhqvRS:",
            ["autostep=", "count", "expand", "fold", "help",
             "quiet", "rangeset", "version", "separator="])
    except getopt.error, err:
        if err.opt in [ "i", "intersection", "x", "exclude", "X", "xor" ]:
            print >> sys.stderr, "option -%s not allowed here" % err.opt
        else:
            print >> sys.stderr, err.msg
        print >> sys.stderr, "Try `%s -h' for more information." % args[0]
        sys.exit(2)

    for k, val in opts:
        if k in ("-a", "--autostep"):
            try:
                autostep = int(val)
            except ValueError, exc:
                print >> sys.stderr, exc
        elif k in ("-c", "--count"):
            command = "count"
        elif k in ("-e", "--expand"):
            command = "expand"
        elif k in ("-f", "--fold"):
            command = "fold"
        elif k in ("-h", "--help"):
            print __doc__
            sys.exit(0)
        elif k in ("-q", "--quiet"):
            quiet = True
        elif k in ("-R", "--rangeset"):
            class_set = RangeSet
        elif k in ("-S", "--separator"):
            separator = val
        elif k in ("-v", "--version"):
            print __version__
            sys.exit(0)

    # Check for command presence
    if not command:
        print >> sys.stderr, "ERROR: no command specified."
        print __doc__
        sys.exit(1)

    # Instantiate RangeSet or NodeSet object
    result = class_set()

    # No need to specify '-' to read stdin if no argument at all
    if not args:
        process_stdin(result, autostep)
        
    # Process operations
    while args:
        arg = args.pop(0)
        if arg in ("-i", "--intersection"):
            result.intersection_update(class_set(args.pop(0),
                                                 autostep=autostep))
        elif arg in ("-x", "--exclude"):
            result.difference_update(class_set(args.pop(0),
                                               autostep=autostep))
        elif arg in ("-X", "--xor"):
            result.symmetric_difference_update(class_set(args.pop(0),
                                                         autostep=autostep))
        elif arg == '-':
            process_stdin(result, autostep)
        else:
            result.update(class_set(arg, autostep=autostep))

    # Interprate special characters
    try:
        separator = eval('\'%s\'' % separator, {"__builtins__":None}, {})
    except SyntaxError:
        print >> sys.stderr, "ERROR: invalid separator."
        sys.exit(1)

    try:
        # Display result according to command choice
        if command == "expand":
            print separator.join(result)
        elif command == "fold":
            print result
        else:
            print len(result)
    except (NodeSetParseError, RangeSetParseError), exc:
        if not quiet:
            print >> sys.stderr, "%s parse error:" % class_set.__name__, e
            # In some case, NodeSet might report the part of the string
            # that causes problem.  For RangeSet it is always included
            # in the error message.
            if hasattr(e, 'part') and e.part:
                print >> sys.stderr, ">>", e.part
        sys.exit(1)

if __name__ == '__main__':
    try:
        run_nodeset(sys.argv)
        sys.exit(0)
    except AssertionError, e:
        print >> sys.stderr, "ERROR:", e
        sys.exit(1)
    except IndexError:
        print >> sys.stderr, "ERROR: syntax error"
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(128 + signal.SIGINT)
