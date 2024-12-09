.. -*- rest -*-

..
    Copyright (c) 2024 Science and Technology Facilities Council.

    All rights reserved.

    Modifications made as part of the fparser project are distributed
    under the following license:

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are
    met:

    1. Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in the
    documentation and/or other materials provided with the distribution.

    3. Neither the name of the copyright holder nor the names of its
    contributors may be used to endorse or promote products derived from
    this software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
    A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
    HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
    SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
    LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
    DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
    THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


.. _examples:

Examples
========

The distribution comes with a set of examples showing how fparser can
be used. At the same time, some of these examples are actually useful tools
that are used in other projects.


fparser2_f2008.py
^^^^^^^^^^^^^^^^^
This is a very small example code that shows how a Fortran code, given as
a string, is parsed, and then converted back into Fortran. It just prints
out the re-created Fortran source code.


create_dependencies.py
^^^^^^^^^^^^^^^^^^^^^^
This file analyses the dependencies between a set of Fortran files, based on
the ``Use`` statements in each file. It assumes that the module name in the
``use`` statement corresponds to the name of the file (adding one of
.F90/.f90/.x90). Only files in the current directory will be tested, so
external dependencies will not be listed. Its output
is in a format that can be immediately used in a Makefile::

    ../create_dependencies.py  *.f90
    b.o: a.o
    c.o: a.o b.o


Ignoring error handling, the simplified main part of this code
that is related to fparser is::

    reader = FortranFileReader(filename)
    parser = ParserFactory().create(std="f2003")
    parse_tree = parser(reader)

    # Collect all used modules in a list
    all_use = set()
    for node in walk(parse_tree, Use_Stmt):
        use_name = str(node.items[2])
        # A more sophisticated mapping could be used here.
        # But for now just assume that the name in the use statement
        # with an added ".o" is the required object file:
        obj_dependency = use_name + ".o"
        all_use.add(use_name)
    # Now ``all_use`` contains all .o files that ``filename`` depends on

The rest of the example is related to creating the proper format for
a Makefile.

.. note:: It would be straight-forward to loop over all files twice, first
          to collect the module names provided by each file, then use this
          information


make_public.py
^^^^^^^^^^^^^^
This example removes all ``private`` and ``protected`` attributes in any
declaration. In general these attributes are important and should
obviously not be removed in order to give the compiler more information
about intended use of the variables. But `PSyclone 
<https://github.com/stfc/PSyclone>`_ offers a feature called
Kernel Extraction, which automatically writes all variables read and written
in a code section to a file. It also then creates a stand-alone driver program
that will read this file, execute the kernel, and compare the results with
the original results.

Since PSyclone will follow the call tree, the code must be able to read even
variables declared as ``private`` (to write them into the output file), and
a driver program must be able to modify ``private`` and ``protected``
variables in modules. If the driver creation is used, the 
`Fab <https://github.com/MetOffice/fab>`_ based build system will
remove all ``private`` and ``protected`` attributes in a separate build phase,
so that the kernel extraction and driver creation works as expected.

A short example, which shows how a ``Access_Stmt`` like ``private :: a`` is
removed::

    for node in walk(parse_tree, Access_Stmt):
        if node.items[0] == "PRIVATE":
            # Find the node in the parent, and remove it:
            node.parent.children.remove(node)


Modifying some of the fparser data structures can be more difficult, since
they are often based on Python tuples, which cannot be modified. The following
example from ``make_public.py`` shows how the middle element of a three-element
tuple is replaced with None::

    type_decl.items = (type_decl.items[0], None, type_decl.items[2])


split_file.py
~~~~~~~~~~~~~
This script splits one Fortran source file into several files, each containing
one top level module, subroutine, function or program. Each file uses the name
of the program unit (module-, subroutine-, function-, program name). The
extension will be ``.F90`` if there are preprocessor directives in the file,
and ``.f90`` otherwise.

Additionally, ``split_file.py`` will create a Makefile to build either the
binary (if a program is found in the file), or all object files. If any of
the environment variables ``F90``, ``F90FLAGS``, and ``LDFLAGS`` are set at
run time of the script, it will use these values as default values in the
makefile. But by setting these environment variables when running ``make``,
these defaults can always be overwritten. The Makefile also has a ``clean``
target, which will remove all ``.mod``, object, and the program file (if
available). It uses the ``create_dependencies.py`` script to add the
required dependencies to the Makefile.
