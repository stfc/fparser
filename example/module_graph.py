#!/usr/bin/env python
# -----------------------------------------------------------------------------
# BSD 3-Clause License
#
# Copyright (c) 2026, Science and Technology Facilities Council.
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
# Author: A. R. Porter, STFC Daresbury Laboratory

import sys
from typing import Optional

from fparser.common.readfortran import FortranFileReader
from fparser.two.Fortran2003 import Module, Module_Stmt, Use_Stmt
from fparser.two.parser import ParserFactory
from fparser.two.utils import walk

"""
A bare-bones example that uses fparser to get the modules and USE
statements from the provided source files and then constructs a
dot graph of their dependencies.

The result can be visualised using e.g. `dotty` if small. For larger
or fancier visualisation other tools are available, e.g.
Graphia - https://github.com/graphia-app/graphia
"""


def build_graph(files: list[str],
                exclude: Optional[list[str]] = None) -> str:
    """
    :param files: the Fortran source files to process.
    :param exclude: optional list of module names to ignore.

    :returns: text containing the dot graph.

    """
    # Those modules we want to exclude from the graph.
    exclusions = set() if not exclude else set(exclude)

    # dict to hold the list of modules USEd by each module.
    deps: dict[str, list[str]] = {}

    parser = ParserFactory().create(std="f2008")

    for filename in files:

        # Parse the current source file:
        try:
            reader = FortranFileReader(filename)
        except IOError:
            print(f"Could not open file '{filename}'.", file=sys.stderr)
            sys.exit(-1)

        parse_tree = parser(reader)

        # Look at every module definition in the file.
        for fmod in walk(parse_tree, Module):

            mod_name = fmod.children[0].children[1].string.lower()

            if mod_name in exclusions:
                continue

            print(f"Examining module '{mod_name}' from file '{filename}'",
                  file=sys.stdout)

            # Look at all the use statements within this module.
            deps[mod_name] = []
            for use_stmt in walk(fmod, Use_Stmt):
                imported_name = use_stmt.children[2].string.lower()
                if imported_name in exclusions:
                    continue
                deps[mod_name].append(imported_name)

    # Create the graph.
    lines: list[str] = []

    for mod_name in deps:
        for import_name in deps[mod_name]:
            # Add the edges to the graph
            lines.append(f"{mod_name} -> {import_name};")

    # Close the graph and return it
    output = "\n".join(["digraph module_dependencies {"] + lines + ["}"])
    return output


if __name__ == "__main__":
    # The default list of modules to exclude is useful for NEMO.
    text = build_graph(sys.argv[1:],
                       exclude=["mpi", "timing", "lib_mpp",
                                "ieee_arithmetic"])
    with open("mod_deps.dot", mode="w", encoding="utf-8") as gfile:
        gfile.write(text)
    print("Graph written to mod_deps.dot\n")
