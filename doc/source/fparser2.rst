..  Copyright (c) 2017-2024 Science and Technology Facilities Council.

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

.. _fparser2 :

fparser2
========

Fparser2 provides support for parsing Fortran up to and including
Fortran 2003. This is implemented in the Fortran2003.py `file`__ and
contains an entirely separate parser to fparser1 that includes rules
for Fortran 2003 syntax. Support for Fortran 2008 is being added in
the Fortran2008.py `file`__ which extends the Fortran2003 rules
appropriately. At this time fparser2 supports the following
Fortran2008 features: submodules, co-arrays, the 'mold' argument to
allocate, the 'contiguous' keyword, the 'BLOCK' construct, the
'CRITICAL' construct, the optional '::' for a procedure statement and
the 'do concurrent' construct.

__ https://github.com/stfc/fparser/blob/master/src/fparser/two/Fortran2003.py
__ https://github.com/stfc/fparser/blob/master/src/fparser/two/Fortran2008.py


Getting Going : Script
----------------------

Once installed, fparser2 can be run from the command line by using the
`fparser2` script. One or more input files can be provided. These
files are parsed in turn and the parsed Fortran is output to the
screen (most likely with a different formatting to the input as
fparser2 does not preserve format), or an appropriate error is output.
::

   > cat simple.f90
   program simple
   end
   > fparser2 simple.f90
   PROGRAM simple
   END PROGRAM simple
   > cat error.f90
   prog error
   end
   > fparser2 error.f90
   File: 'error.f90'
   Syntax error: at line 1
   >>>prog error

fparser2 provides a number of command line options
::

   > fparser2 -h
   Usage: fparser2 [options] <Fortran files>

   Description:
     fparser2 parses Fortran code.

   Options:
     -h, --help     show this help message and exit
     --task=TASK    Specify parsing result task. Default: show.
     --std=STD      Specify the Fortran standard to use. Default: f2003.

The ``--task`` option supports `show` (the default) which outputs the
parsed code to stdout, `repr` which outputs the fparser2
representation of its internal parse tree and `none` which outputs
nothing.

The ``--std`` option chooses the flavour of Fortran to parse. Valid
options are currently limited to `f2003` (the default) and `f2008`.

Getting Going : Python
----------------------

As with the other parser (:ref:`fparser`), the source code to parse
must be provided via a Fortran reader which is an instance of either
`FortranFileReader` or `FortranStringReader` (see
:ref:`readfortran`).

The required parser is then created using an instance of the
`ParserFactory` class. `ParserFactory` either returns a
Fortran2003-compliant parser or a Fortran2008-compliant parser
depending on the `std` argument provided to its create method.

Finally the parser is provided with the Fortran reader and returns an
abstract representation (a parse-tree) of the code,
if the code is valid Fortran. This parse-tree can be output as Fortran by
printing it. The parse-tree hierarchy can also be output in textual form by
executing it. For example:

::
   
    >>> from fparser.two.parser import ParserFactory
    >>> from fparser.common.readfortran import FortranFileReader
    >>> reader = FortranFileReader("compute_unew_mod.f90",
                                   ignore_comments=False)
    >>> f2008_parser = ParserFactory().create(std="f2008")
    >>> parse_tree = f2008_parser(reader)
    >>> print parse_tree
    MODULE compute_unew_mod
      USE :: kind_params_mod
      USE :: kernel_mod
      USE :: argument_mod
      USE :: grid_mod
      USE :: field_mod
      IMPLICIT NONE
      PRIVATE
      PUBLIC :: invoke_compute_unew
      PUBLIC :: compute_unew, compute_unew_code
      TYPE, EXTENDS(kernel_type) :: compute_unew
      ...
    >>> parse_tree
    Program(Module(Module_Stmt('MODULE', Name('compute_unew_mod')),Spec
    ification_Part(Use_Stmt(None, Name('kind_params_mod'), '', None),Us
    e_Stmt(None, Name('kernel_mod'), '', None),Use_Stmt(None, Name('arg
    ument_mod'), '', None),Use_Stmt(None, Name('grid_mod'), '', None),U
    se_Stmt(None, Name('field_mod'), '', None),Implicit_Part(Implicit_S
    tmt('NONE')), Access_Stmt('PRIVATE', None),Access_Stmt('PUBLIC', Na
    me('invoke_compute_unew')),Access_Stmt('PUBLIC', Access_Id_List(','
    , (Name('compute_unew'),Name('compute_unew_code')))),Derived_Type_D
    ef(Derived_Type_Stmt(Type_Attr_Spec('EXTENDS',Name('kernel_type')),
    Type_Name('compute_unew'), None), ...

Note that the two readers will ignore (and dispose of) comments by
default. If you wish comments to be retained then you must set
`ignore_comments=False` when creating the reader. The parse tree
created by fparser2 will then have `Comment` nodes representing any
comments found in the code. Nodes representing in-line comments will
be added immediately following the node representing the code in which
they were encountered.

Preprocessing directives are retained as `CppDirective` objects by the
readers and are represented by matching nodes in the parse tree created
by fparser2. See section `Preprocessing Directives`_ for more details.

If the optional parameter `include_omp_conditional_lines` is set to `True`,
then any source code line that contains a conditional OpenMP sentinel
(e.g. `!$` at the beginning of a line) will be handled as if OpenMP is
enabled - i.e. the sentinel will be replaced by spaces, and the remainder
of the line is parsed. In this case, the lines will not be returned
as comment lines, nor would they be ignored even if
`ignore_comments` is set to `True`.

Note that empty input, or input that consists of purely white space
and/or newlines, is not treated as invalid Fortran and an empty parse
tree is returned. Whilst this is not strictly valid, most compilers
have this behaviour so we follow their lead.

If the code is invalid Fortran then a `FortranSyntaxError` exception
will be raised which indicates the offending line of code and its line
number. For example:

::
   
   >>> from fparser.common.readfortran import FortranStringReader
   >>> code = "program test\nen"
   >>> reader = FortranStringReader(code)
   >>> from fparser.two.parser import ParserFactory
   >>> f2008_parser = ParserFactory().create(std="f2008")
   >>> parse_tree = f2008_parser(reader)
   Traceback (most recent call last):
     File "<stdin>", line 1, in <module>
     File "fparser/two/Fortran2003.py", line 1300, in __new__
       raise FortranSyntaxError(error)
   fparser.two.Fortran2003.FortranSyntaxError: at line 2
   >>>en

Matching Multiple Rules
-----------------------

There are a number of situations where more than one Fortran rule
could match some input text. For example, the following text could be
an array section or a substring::

  a(1:2)

The Fortran specifications deal with such ambiguities by specifying
constraints. In this case, constraint `C608` in the Fortran2003
specification states that this text can only be a substring if the
variable `a` is of type `character`.

At the moment, fparser2 attempts to match rules but does very little
constraint checking and is implemented such that when there is a
choice of rules, the first matching rule in the associated internal
rule-list is returned. This approach is fine for parsing and
de-parsing code, but it does means that the resultant parse tree might
not be what would be expected. This problem is therefore passed on to
any tool that makes use of the parse tree.

For example, the text `a(1:2)` would always match an array section
(Fortran2003 rule R617) and never a substring (Fortran2003 rule
R609), even when variable `a` is declared as type `character`. The
reason for this is that Fortran2003 rule R603 specifies the matching
of array section before the matching of substring which is how it is
implemented in fparser2.

In many cases any ambiguity in rule matching can and will be removed
by adding constraint checking to fparser2 and the first step in
supporting this is the subject of issue #201.

However, in some situations it is not possible to disambiguate rules
via constraints by simply parsing a valid Fortran file. As an
illustration, if we again take the example of the text `a(1:2)` and
constraint `C608` where we need to determine whether the variable `a`
is of type `character`, it may be that this variable is brought into
scope via a `use` statement and so its datatype is unknown without
finding its declaration in another module.

Fortran compilers deal with this problem by requiring code associated
with use statements to have already been compiled creating `mod` files
which contain the required information. It has not yet been
decided how to deal with this problem in fparser2, but it is likely
that some on-demand parsing of other files will be used to determine
appropriate types.

Situations where fparser2 is known to choose the wrong parsing rule
are given in the following sections.

Array element, array section or substring
+++++++++++++++++++++++++++++++++++++++++

A substring will always be matched as an array element. An array
section will also be matched as an array element unless the array
section contains an additional substring range (see Fortran 2003 rule
R617).

Array or function
+++++++++++++++++

A function will always be matched as an array element unless that
function is an intrinsic. An array access with the same name as an
intrinsic function will be matched as an intrinsic function but will
raise an exception if the number of dimensions of the array does not
match the number of arguments expected by the intrinsic.

Statement function or array assignment
++++++++++++++++++++++++++++++++++++++

Fparser2 is currently not able to distinguish between statement
functions and array assignments when one or more array assignment
statements are the first statements after a declaration section. This
limitation would lead to these particular array assignments being
incorrectly parsed as statement functions.

To avoid this behaviour, support for statement functions has
been temporarily removed from fparser2. However, with this change,
statement functions will now be incorrectly parsed as array assignments
when one or more statement function statements are the last statements
in a declaration section.

Whilst any incorrect behaviour should be avoided, the behaviour of
this temporary change is considered preferable to the former case, as
array assignments are more common than statement functions.

Extensions
----------

Many compilers support extensions to standard Fortran and codes often
make use of them. This section documents the extensions to the
standard that are supported by fparser2.

Cray Pointers
+++++++++++++

Cray pointers are part of a non-standard extension that provides a
C-like pointer in Fortran. This is accomplished through a pair of
variables: an integer "pointer" that holds a memory address, and a
"pointee" that is used to dereference the pointer. For example::

  pointer (my_pointer, my_pointee)

For a specification and a more detailed explanation see
http://pubs.cray.com/content/S-3901/8.6/cray-fortran-reference-manual-s-3901-86/types
or https://gcc.gnu.org/onlinedocs/gfortran/Cray-pointers.html.


X Format
++++++++

An X edit descriptor in a format statement specifies the position
(forward from the current position) at which the next character will
be transmitted to or from a record. In standard Fortran2003 the X edit
descriptor must be preceeded by an integer which specifies how far
forward from the current position. The 'x-format' extension allows the
X edit descriptor to be specified without a preceeding integer. When
omitted, the value is implicitly assumed to be one. For example::

  100 format (x)

For more information see
https://gcc.gnu.org/onlinedocs/gfortran/X-format-descriptor-without-count-field.html

Hollerith Constant
++++++++++++++++++

A Hollerith constant is a way of specifying a string as a sequence of
characters preceded by the string length and separated by an 'H'. For
example::
  
  5Hhello
  11Hhello there

Hollerith constants were used in Fortran before character strings were
introduced in Fortran 77. In Fortran 77 the use of Hollerith constants
was deprecated and in Fortran 95 they were removed from the
language. However, many compilers still support Hollerith constants
for legacy Fortran code.
  
The 'hollerith' extension adds support in fparser for Hollerith
constants. This support is currently limited to those specified in
format statements. There is currently no support for 1) constants in
DATA statements and 2) constant actual arguments in subroutine CALL
statements (which are its other uses as specified in the Fortran 66
standard).

For more information see
https://gcc.gnu.org/onlinedocs/gfortran/Hollerith-constants-support.html
or https://en.wikipedia.org/wiki/Hollerith_constant

Dollar Descriptor
+++++++++++++++++

A dollar descriptor is used to specify that the carriage return in a
write statement should be suppressed. For example::

  100 FORMAT ('Enter your name ',$)

This extension is not specified in the Fortran standard but is
implemented by a number of compilers. The 'dollar-descriptor'
extension adds support for the dollar descriptor in fparser.

For more information see
https://software.intel.com/en-us/fortran-compiler-developer-guide-and-reference-dollar-sign-and-backslash-editing

CONVERT argument to OPEN
++++++++++++++++++++++++

The CONVERT argument may be used to specify how unformatted data being read
from file is to be converted before being stored. For example::

  OPEN(unit=23, file="some_data", form='unformatted',access='sequential', &
       convert="LITTLE_ENDIAN")

This extension is supported by (at least) the Gnu, Intel and Cray compilers
but is not a part of any Fortran standard. More details can be found at
https://gcc.gnu.org/onlinedocs/gfortran/CONVERT-specifier.html

Extended arguments for STOP
+++++++++++++++++++++++++++

Many compilers support extended arguments for the STOP statement before Fortran 2008.
Examples are negative numbers, and string operations::

    STOP -1
    STOP str1 // str2

This extension will accept these expressions in Fortran 2003. Note that the
Fortran 2008 standard changes the definition of the stop code to accept even
more flexible expressions.

Classes
-------

.. autoclass:: fparser.common.readfortran.FortranFileReader
    :members:


.. autoclass:: fparser.common.readfortran.FortranStringReader
    :members:


.. autoclass:: fparser.two.parser.ParserFactory
    :members:

Includes
--------

Fortran supports the `include` statement in order to inline code from
other locations into the current file.

The interpretation of where the include content comes from is defined
as being processor dependent in the Fortran standard. Fparser assumes
that the content comes from another another file. For example ::

  program x
  include 'content.inc'
  end program

implies that ``content.inc`` is a file containing Fortran code. For
example ::

  print *, "Hello"

The above example would then be equivalent to the following Fortran
code ::

  program x
  print *, "Hello"
  end program

The Fortran standard specifies that the `include` statement is not a
Fortran statement, rather it indicates that when the code is processed
the contents of the `include` file should replace the include
statement as the code is parsed.

fparser supports `include` statements in its reader classes
(`FortranStringReader` and `FortranFileReader`), so the parser itself
need not be aware of the original `include` statements.

The directory locations in which to search for `include` files can be
specified to a reader class instance via the optional `include_dirs`
argument, which should be iterable. For example::

  reader = FortranFileReader(my_file, include_dirs=["dir1", "dir2"])

If a relative directory is specified then the location is with respect
to the input file.  The reader class instance will search in the
specified directory order and include the contents of the first
matching file found.

If no include_dirs argument is supplied then the default search
location is ``['.']``. Therefore include files would need to be in the
same directory as the input file for them to be found.

.. note:: At the moment it is not possible to specify include
          directories in the fparser2 script.

In a compiler, all include files must be found otherwise there is an
error. However, with a code parser this is not necessarily the case. A
user might not want to include all files when parsing, perhaps for
simplicity, or perhaps because the files are not readily available. To
support this, fparser has been extended to recognise `include`
statements as part of the parse tree. If a particular `include` file
is not found then the associated `include` statement will be parsed
like a standard Fortran statement. If we again consider the simple
example from earlier::

  program x
  include 'content.inc'
  end program

with ``content.inc`` containing the following Fortran code::

  print *, "Hello"

then if the ``content.inc`` file is found the output of fparser
would be::

  PROGRAM x
  PRINT *, "Hello"
  END PROGRAM x

but if the ``content.inc`` file is not found then the output of
fparser would be::

  PROGRAM x
  INCLUDE 'content.inc'  
  END PROGRAM x
  
Clearly in the latter case the parser does require the code to be
valid with the `include` statement in it. For example, assuming the
content of ``endprogram.inc`` is ``end program`` then the following
example would be parsed successfully if the `endprogram.inc` include
file was found but would fail if the include file was not found::

  program x
  include 'endprogram.inc'

Preprocessing Directives
------------------------

Preprocessing directives are language constructs that specify how a
source file should be processed upon compilation or translation.
They are most commonly used to conditionally include or exclude parts
of a source file, include other source files in place, or define
macros for expansion. As part of the compilation process these
directives are interpreted to produce a preprocessed variant of the
source file before translating it to the target language (e.g.,
assembly or machine code). Most compilers have a separate program
("preprocessor") that is invoked by the compiler to carry out
preprocessing.

While directives are not specified in any Fortran standard itself,
Fortran compilers often support preprocessing of Fortran source files
nonetheless. Consequently, the extent and limitations of this support
depends on the compiler toolchain used.

fparser2 does not support preprocessing of source files but it allows
to represent preprocessor directives as dedicated nodes in the parse
tree.

.. note:: With all preprocessor directives removed the source code
          must reduce to valid Fortran. This is due to the fact that
          fparser2 only keeps directives but does not interpret them
          (thus essentially treats them like comments).

The support for preprocessing directives in fparser2 comprises that
defined by the `C99 standard`__. Left out are pragma directives as
those are typically specified in the form of comments in Fortran.
Preprocessing directives consist of the character `#` as the first
character in a line (optionally after white space containing no
new-line characters) followed by the actual directive and is ended
by a new-line character. Line continuation is specified by a single
backslash character `\\` at the end of the line.

__ http://www.open-std.org/jtc1/sc22/wg14/www/docs/n1256.pdf#page=157

The implementation of directives is in the C99Preprocessor.py `file`__
with support for the following::

  #if ...
  #ifdef ...
  #ifndef ...
  #elif ...
  #else
  #endif
  #include ...
  #define ...
  #undef ...
  #line ...
  #error
  #warning
  #

__ https://github.com/stfc/fparser/blob/master/src/fparser/two/C99Preprocessor.py


Walking the Parse Tree
----------------------

Properties and Methods of Nodes
+++++++++++++++++++++++++++++++

The majority of the nodes in the parse tree produced by fparser2 are
instances of (sub-classes of) the ``fparser.two.utils.Base``
class. This class provides the ``parent`` and ``children`` properties
which return the *immediate* parent/children of a given node.
		
In addition to these properties, the ``Base`` class also provides the method:

.. automethod:: fparser.two.utils.Base.get_root

.. note:: The parse tree produced by fparser2 can contain some nodes that are
	  *not* instances of ``fparser.two.utils.Base`` (e.g. ``None`` or
	  ``str``). Obviously such nodes do not have the ``parent`` and
	  ``children`` properties.

Utilities
+++++++++

The ``utils`` module of fparser2 provides two utility functions to
support the traversal of the parse tree that it constructs:

.. autofunction:: fparser.two.utils.walk
.. autofunction:: fparser.two.utils.get_child
