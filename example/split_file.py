#!/usr/bin/env python

# -----------------------------------------------------------------------------
# BSD 3-Clause License
#
# Copyright (c) 2024, Science and Technology Facilities Council.
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

"""This file contains an fparser script that splits a source file that contains
several modules and/or subroutines into individual files. If a file that needs
to be created already exists, the script will abort.

Usage:  split_file.py  file.f90
"""


import os
import subprocess
import sys

from fparser.common.readfortran import FortranFileReader
from fparser.two import C99Preprocessor, Fortran2003
from fparser.two.parser import ParserFactory
from fparser.two.utils import walk


# -----------------------------------------------------------------------------
def usage():
    """This function prints the usage information and exits. It is called if
    incorrect input parameters are supplied.
    """
    print(f"{sys.argv[0]} file1")
    sys.exit(-1)


# -----------------------------------------------------------------------------
def create_makefile(main_name, all_objs, all_filenames):
    """This function creates a Makefile to compile (and if a main_name is
    given to link) the binaries. It uses the create_dependencies.py script
    to add the actual dependencies between the modules to the makefile.

    :param str main_name: name of the program, or "" if no program was
        contained in the original file.
    :param List[str] all_objs: the list of all objects to compile.
    :param List[str] all_filenames: the list of all file names, used to
        call the `create_dependency.py` script

    """
    file_path = os.path.dirname(os.path.realpath(__file__))
    completed = subprocess.run(
        [f"{file_path}/create_dependencies.py"] + all_filenames,
        capture_output=True,
        check=True,
    )

    # Query some environment flags which will define the
    # defaults in the Makefile
    f90 = os.getenv("F90", "gfortran")
    f90flags = os.getenv("F90FLAGS", "-g -O0")
    ldflags = os.getenv("LDFLAGS", "")

    makefile = "Makefile"
    if os.path.exists(makefile):
        print(f"The file '{makefile}' already exists - aborting.")
        sys.exit(-1)

    # Now create a makefile
    if main_name:
        default_target = (
            f"default: {main_name}\n\n"
            f"{main_name}: $(OBJS)\n"
            f"\t$(F90) $(F90FLAGS) $(OBJS) -o {main_name} "
            f"$(LDFLAGS)"
        )
        clean_actions = f"\trm -f {main_name} $(OBJS) *.mod"
    else:
        default_target = "default: $(OBJS)"
        clean_actions = "\trm -f $(OBJS) *.mod"

    with open(makefile, mode="w", encoding="utf-8") as f_out:
        f_out.write(
            f"""
F90 ?= {f90}
# We have to enforce this setting, since using ?= will not
# change the value of CPP, which will then be using `cc -E`, which
# in turn does not handle indented preprocessor lines.
CPP = cpp
# Don't use traditional, it does also not accept indented preprocessor lines
CPPFLAGS ?= -P
F90FLAGS ?= {f90flags}
LDFLAGS ?= {ldflags}

OBJS={' '.join(all_objs)}

{default_target}

# Dependencies
# ============
{completed.stdout.decode("utf-8")}

# Preprocessing (required since some compilers do not
# handle the indented preprocessor directives of fparser)
# =======================================================
%.f90: %.F90
\t$(CPP) $(CPPFLAGS) $< > $@

# Compilation rules
# =================
%.o: %.f90
\t$(F90) $(F90FLAGS) -c $<

# Cleanup
# =======
clean:
{clean_actions}
"""
        )


# -----------------------------------------------------------------------------
def main():
    """The main program. Having this as a dedicated function solves many
    pylint complains.

    """
    if len(sys.argv) != 2:
        usage()

    try:
        reader = FortranFileReader(sys.argv[1])
    except IOError:
        print(f"Could not open file '{sys.argv[1]}'.", file=sys.stderr)
        sys.exit(-1)

    Parser = ParserFactory().create(std="f2008")
    parse_tree = Parser(reader)

    # Get a list of all preprocessor classes (which will determine
    # the extension to be used: F90/f90
    all_cpp_classes = tuple(
        getattr(C99Preprocessor, i) for i in C99Preprocessor.CPP_CLASS_NAMES
    )
    all_filenames = []
    all_objs = []
    main_name = ""
    for unit in parse_tree.children:
        # For Module, Subroutine_Subprogram, Function_Subprogram, Main_Program
        # we always get the name using this:
        unit_name = unit.children[0].items[1].string.lower()

        # Save the name of the main program if we have one, which will be
        # used in the Makefile created later
        if isinstance(unit, Fortran2003.Main_Program):
            main_name = unit_name
        if any(walk(unit, all_cpp_classes)):
            ext = ".F90"
        else:
            ext = ".f90"

        filename = f"{unit_name}{ext}"
        if os.path.exists(filename):
            print(f"The file '{filename}' already exists - aborting.")
            sys.exit(-1)
        with open(filename, mode="w", encoding="utf-8") as f_out:
            f_out.write(str(unit))
            f_out.write("\n")
        all_filenames.append(filename)
        all_objs.append(f"{unit_name}.o")

    # Now create the makefile
    create_makefile(main_name, all_objs, all_filenames)


# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # Using a function here avoids pylint warnings
    main()
