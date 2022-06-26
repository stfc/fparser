#!/usr/bin/env python

# -----------------------------------------------------------------------------
# BSD 3-Clause License
#
# Copyright (c) 2020, Science and Technology Facilities Council.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ------------------------------------------------------------------------------
# Author: Joerg Henrichs, Bureau of Meteorology

"""This file contains an fparser script that parses Fortran files
and output the dependencies between these files suitable for a Makefile.

It assumes that the module name in the use statement corresponds to the
name of the file (adding one of .F90/.f90/.x90). Only files in the current
directory will be tested, so external dependencies will not be listed.

Usage:  create_dependencies.py  file1.f90 file2.F90 ...
"""


import os
import sys

from fparser.common.readfortran import FortranFileReader
from fparser.two.Fortran2003 import Use_Stmt
from fparser.two.parser import ParserFactory
from fparser.two.utils import walk


# -----------------------------------------------------------------------------
def usage():
    """This function prints the usage information and exits. It is called if
    incorrect input parameters are supplied.
    """
    print("{0} file1 [file2...]".format(sys.argv[0]))
    sys.exit(-1)


# -----------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()

    # Apparently pylint thinks that `all_files` is a constant, and complains
    # that it should be capitalised.
    # pylint: disable=invalid-name
    all_files = sys.argv[1:]

    # Sort the input file names, so that they are output alphabetically
    all_files.sort()
    for filename in all_files:

        # Parse the current source file:
        try:
            reader = FortranFileReader(filename)
        except IOError:
            print("Could not open file '{0}'.".format(filename), file=sys.stderr)
            sys.exit(-1)

        parser = ParserFactory().create(std="f2003")
        parse_tree = parser(reader)

        # Collect all used modules in a list
        all_use = []
        for node in walk(parse_tree, Use_Stmt):
            use_name = str(node.items[2])
            # Nothing else to do if the name is already in the list:
            if use_name + ".o" in all_use:
                continue

            # If you want to implement a specific naming convention,
            # you can modify the content of 'use_name' here. For example,
            # you could remove a '_mod' at the end if your file names do
            # not contains this.
            if (
                os.path.isfile(use_name + ".f90")
                or os.path.isfile(use_name + ".x90")
                or os.path.isfile(use_name + ".F90")
            ):
                all_use.append(use_name + ".o")

        # Now output all dependencies for this file (if any):
        if all_use:

            # Sort all module names on which this file depends,
            # so they are listed alphabetically
            all_use.sort()

            # Assemble the output in a list of strings. You start with
            # listing this file first:
            l_out = [os.path.splitext(filename)[0] + ".o: "]
            for dep_name in all_use:
                # Start the next line if we would exceed 80 characters:
                if len(l_out[-1]) + len(dep_name) > 80:
                    l_out.append("")

                l_out[-1] = l_out[-1] + dep_name
                # If this is not the last module, add a space:
                if dep_name != all_use[-1]:
                    l_out[-1] = l_out[-1] + " "

            print("\\\n\t".join(l_out))
