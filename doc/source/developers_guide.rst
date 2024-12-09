..  Copyright (c) 2017-2023 Science and Technology Facilities Council.

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

.. _developers:

Developer Guide
===============

Reading Fortran
---------------

A key part of the fparser package is support for reading Fortran code.
`fparser.common.readfortran.FortranFileReader` provides this functionality
for source files while `FortranStringReader` supports Fortran source
provided as a string. Both of these classes sub-class `FortranReaderBase`:

.. autoclass:: fparser.common.readfortran.FortranReaderBase

Note that the setting for `ignore_comments` provided here can be overridden
on a per-call basis by methods such as `get_single_line`.
The 'mode' of the reader is controlled by passing in a suitable instance of
the `FortranFormat` class:

.. autoclass:: fparser.common.sourceinfo.FortranFormat

Due to its origins in the f2py project, the reader contains support
for recognising `f2py` directives
(https://numpy.org/devdocs/f2py/signature-file.html). However, this
functionality is disabled by default.

A convenience script called read.py is provided in the scripts
directory which takes a filename as input and returns the file
reader's representation of that file. This could be useful for
debugging purposes.

Invalid input
-------------

The file reader uses :py:func:`open` to open a Fortran file. If
invalid input is found then Python raises a `UnicodeDecodeError`
exception by default. Since we typically wish to skip invalid
characters (on the principle that, for valid Fortran, they can only
occur in comments) while logging their presence, a bespoke error
handler named "fparser-logging" is implemented in
``fparser/__init__.py`` and registered using
:py:func:`codecs.register_error`.  This handler may be specified when
using :py:func:`open` to open a file by supplying the
``errors='fparser-logging'`` argument.

Fparser2
--------

Fparser2 supports Fortran2003 and is being extended to support
Fortran2008. Fparser2 is being actively developed and will fully
replace fparser1 in the future.

.. _rules:

Rules
+++++

Each version of the Fortran language is defined as a set of rules in a
specification document. The Fortran2003 rules are specified here
https://wg5-fortran.org/N1601-N1650/N1601.pdf and the Fortran2008
rules are specified here
https://j3-fortran.org/doc/year/10/10-007r1.pdf.

Each rule has a number, for example the Fortran2003 document includes
the following top level rules `R201` and `R202`
::

    R201 program is program-unit
                    [ program-unit ] ...

    R202 program-unit is main-program
                         or external-subprogram
                         or module
                         or block-data

It can be seen that the right hand side of these rules consist of more
rules. Note, `[]` means that the content is optional. At some point in
the rule hierarchy rules start to be defined by text. For example,
taking a look at the specification of a module
::

    R1104 module is module-stmt
                    [ specification-part ]
                    [ module-subprogram-part ]
                    end-module-stmt

    R1105 module-stmt is MODULE module-name

    R1106 end-module-stmt is END [ MODULE [ module-name ] ]

it can be seen that rules `R1105` and `R1106` specify the actual code to
write e.g. `MODULE`. Here `module-name` is a type of `name` which has
a rule specifying what is valid syntax (see the specification document
for more details).

Therefore Fortran is specified as rules which reference other rules,
or specify a particular syntax. The top level rule of this hierarchy
is rule `R201`, which defines a program, see above.


Classes
+++++++

In fparser2 each rule is implemented in a class with the class names
closely following the rule names. For example, `program` is
implemented by the `Program` class and `program-unit` is implemented
by the `Program_Unit` class. In general, the name of the class
corresponding to a given rule can be obtained by replacing '-' with
'_' and capitalising each word.

The Fortran2003 classes exist in the Fortran2003.py file and the
Fortran2008 classes exist in the Fortran2008.py file (see
:ref:`Fortran2008` section for Fortran2008-specific implementation
details).

The Fortran2003 and Fortran2008 classes can inherit from a set of
pre-existing base classes which implement certain rule patterns in a
generic way. The base classes are contained in the `utils.py` file.

The base classes and rule patterns are discussed more in the
:ref:`base-classes` section.

The primary components of classes i.e. the parts that developers
typically need to be concerned with are:

1) the `subclass_names` list
2) the `use_names` list
3) the static `match` method
4) the `tostr` method

A `subclass_names` list of classes should be provided when the rule is
a simple choice between classes. In this case the `Base` class ensures that each
child class is tested for a match and the one that matches is
returned. An example of a simple choice rule is `R202`. See the
:ref:`program-unit-class` section for a description of its
implementation.

The `use_names` list should contain any classes that are referenced by the
implementation of the current class. These lists of names are aggregated
(along with `subclass_names`) and used to ensure that all necessary `Scalar_`,
`_List` and `_Name` classes are generated (in code at the end of the
`Fortran2003` and `Fortran2008` modules - see :ref:`class-generation`).

When the rule is not a simple choice the developer needs to supply a
static `match` method. An example of this is rule `R201`. See the
:ref:`program-class` section for a description of its implementation.

.. note::

   A `tostr` description, explanation and example needs to be added.

Class Relationships
+++++++++++++++++++

When a rule is a simple choice, the class implementing this rule
provides a list of classes to be matched in the `subclass_names` list
(or potentially `use_names` list). These class names are provided as
strings, not references to the classes themselves.

In fparser2 these strings are used to create class references to allow
matching to be performed. The creation of class references is
implemented by the `create` method of the `ParserFactory` object.

The `create` method of the `ParserFactory` class also links to
appropriate classes to create parsers compliant to the specified
standard.

.. note::

   The ParserFactory implementation needs to be explained.

A parser conforming to a particular Fortran standard is created by a
ParserFactory object. For example::

    >>> from fparser.two.parser import ParserFactory
    >>> parser_f2003 = ParserFactory().create(std="f2003")

The `create` method returns a `Program` *class* (called `parser_f2003`
in the above example) which contains a `subclasses` dictionary
(declared in its base class - called `Base`) configured with *all* the
Fortran2003 class relationships specified by the `subclass_names` and
`use_names` lists in each class.

As all classes inherit from the `Base` class, the `subclasses`
dictionary is available to all classes. If, for example, we query the
dictionary for the `Program` class relationships we get an empty list
as it has no `subclass_names` or `use_names` entries specified (see
:ref:`program-class`). If however, we query the dictionary for the
`Program_unit` relationships we get the list of classes specified in
that classes `subclass_names` list (see :ref:`program-unit-class`)::

    >>> parser_f2003.__name__
    'Program'
    >>> parser_f2003.subclasses['Program']
    []
    >>> parser_f2003.subclasses['Program_Unit']
    [<class 'fparser.two.Fortran2003.Main_Program'>, <class 'fparser.two.Fortran2003.Function_Subprogram'>, <class 'fparser.two.Fortran2003.Subroutine_Subprogram'>, <class 'fparser.two.Fortran2003.Module'>, <class 'fparser.two.Fortran2003.Block_Data'>]

Symbol Table
++++++++++++

There are many situations when it is not possible to disambiguate the
precise form of the Fortran being parsed without additional type
information (e.g. whether code of the form `a(i,j)` is an array
access or a function call).  Therefore fparser2 contains a single,
global instance of a `SymbolTables` class, accessed as
`fparser.two.symbol_table.SYMBOL_TABLES`. As its name implies, this
holds a collection of symbol tables, one for each top-level scoping
unit (e.g. module or program unit). This is implemented as a
dictionary where the keys are the names of the scoping units e.g. the
name of the associated module, program, subroutine or function. The
corresponding dictionary entries are instances of the `SymbolTable`
class:

.. autoclass:: fparser.two.symbol_table.SymbolTable
   :members:

The entries in these tables are instances of the named tuple,
`SymbolTable.Symbol` which currently has the properties:

 * name
 * primitive_type

Both of these are stored as strings. In future, support for more
properties (e.g. kind, shape, visibility) will be added and strings
replaced with enumerations where it makes sense. Similarly, support
will be added for other types of symbols (e.g. those representing
program/subroutine names or reserved Fortran keywords).

Symbols available in the scoping region of a module may be made
available in another scoping region through one or more `USE` statements.
In a `SymbolTable` such uses are captured as instances of `ModuleUse`:

.. autoclass:: fparser.two.symbol_table.ModuleUse

These instances are created by calling:

.. automethod:: fparser.two.symbol_table.SymbolTable.add_use_symbols

Fortran has support for nested scopes - e.g. variables declared within
a module are in scope within any routines defined within that
module. Therefore, when searching for the definition a symbol, we
require the ability to search up through all symbol tables accessible
from the current scope. In order to support this functionality, each
`SymbolTable` instance therefore has a `parent` property. This holds a
reference to the table that contains the current table (if any).

Since fparser2 relies heavily upon recursion, it is important that the
current scoping unit always be available from any point in the code.
Therefore, the `SymbolTables` class has the `current_scope` property
which contains a reference to the current `SymbolTable`. Obviously,
this property must be updated as the parser enters and leaves scoping
units.  This is handled for all cases bar one within the `BlockBase`
base class since this is sub-classed by all classes which represent a
block of code and that therefore includes all those which define a
scoping region. The exception is the helper class
`Fortran2003.Main_Program0` which represents Program units that do not
include the (optional) program-stmt (see R1101 in the Fortran
standard).  The creation of a scoping unit for such a program is
handled within the `Fortran2003.Main_Program0.match()` method. Since
there is no name associated with such a program, the corresponding
symbol table is given the name "fparser2:main_program", chosen so as
to prevent any clashes with other Fortran names.

Those classes which define scoping regions must subclass the
`ScopingRegionMixin` class:

.. autoclass:: fparser.two.utils.ScopingRegionMixin


.. _class-generation:

Class Generation
++++++++++++++++

Some classes that are specified as strings in the `subclass_names` or
`use_names` variables do not require class implementations. There are 3
categories of these:

1) classes of the form '\*\_Name'
2) classes of the form '\*\_List'
3) classes of the form 'Scalar\_\*'

The reason for this is that such classes can be written in a generic,
boiler-plate way so it is simpler if these are generated rather than
them having to be hand written.

At the end of the Fortran2003.py and Fortran2008.py files there is
code that is executed when the file is imported. This code generates
the required classes described above in the local file.

.. note::

   The way this is implemented needs to be described.

As a practical example, consider rule `R1106`
::

   R1106 end-module-stmt is END [ MODULE [ module-name ] ]

which is implemented in the following way
::

    class End_Module_Stmt(EndStmtBase):  # R1106
        ''' <description> '''
        subclass_names = []
        use_names = ['Module_Name']

        @staticmethod
        def match(string):
            return EndStmtBase.match('MODULE', Module_Name, string)

It can be seen that the `Module_Name` class is specified as a string
in the `use_names` variable. The `Module_Name` class has no
implementation in the Fortran2003.py file, the class is
generated. This code generation is performed when the file is
imported.

.. note::

   At the moment the same code-generation code is replicated in both
   the Fortran2003.py and Fortran2008.py files. It would be better to
   import this code from a separate file if it is possible to do so.

.. _base-classes:

Base classes
++++++++++++

There are a number of base classes implemented to support matching
certain types of pattern in a rule. The two most commonly used are
given below. As mentioned earlier, the class `Base` supports a choice
between classes. The class `BlockBase` supports an initial and final
match with optional subclasses inbetween (useful for matching rules
such as programs, subroutines, if statements etc.).

.. autoclass:: fparser.two.utils.Base
               :members:
               :noindex:

.. autoclass:: fparser.two.utils.BlockBase
               :members:
               :noindex:

.. note::

   The `BlockBase` `match` method is complicated. One way to simplify this
   would be to create a `NamedBlockBase` which subclasses `BlockBase`. This
   would include the code associated with a block having a name.

.. _Fortran2008:

Fortran2008 implementation
++++++++++++++++++++++++++

As Fortran2008 is a superset of Fortran2003, the Fortran2008 classes
are implemented as extensions to the Fortran2003 classes where
possible. For example, the Fortran2003 rule for a program-unit is::
   
    R202 program-unit is main-program
                         or external-subprogram
                         or module
                         or block-data

and for Fortran2008 it is
::
   
    R202 program-unit is main-program
                         or external-subprogram
                         or module
                         or submodule
                         or block-data

Therefore to implement the Fortran2008 version of this class, the
Fortran2003 version needs to be extended with the `subclass_names`
list being extended to include a `Submodule` class as a string (of
course the `Submodule` class also needs to be implemented!)
::

    >>> from fparser.two.Fortran2003 import Program_Unit as Program_Unit_2003

    >>> class Program_Unit(Program_Unit_2003):  # R202
    >>>       ''' <description> '''
    >>>       subclass_names = Program_Unit_2003.subclass_names[:]
    >>>       subclass_names.append("Submodule")


.. _program-class:

Program Class (rule R201)
+++++++++++++++++++++++++

As discussed earlier, Fortran rule `R201` is the 'top level' Fortran
rule. There are no other rules that reference rule `R201`. The rule
looks like this::

    R201 program is program-unit
                    [ program-unit ] ...

which specifies that a Fortran program can consist of one or more program
units. Note, the above rule does not capture the fact that it is valid
to have an arbitrary number of comments before the first program-unit,
inbetween program-units and after the final program-unit.

As the above rule is not a simple choice between different rules a
static `match` method is required for the associated fparser2
`Program` class.

As discussed earlier there are a number of base classes implemented to
support matching certain types of pattern in a rule. The obvious one
to use here would be `BlockBase` as it supports a compulsory first
class, an arbitrary number of optional intermediate classes (provided
as a list) and a final class. Therefore, subclassing `BlockBase` and
setting the first class to `Program_Unit`, the intermediate classes to
`[Program_Unit]`, and the final class to `None` would seem to perform
the required functionality (and this was how it was implemented in
earlier versions of fparser2).

However, there is a problem using `BlockBase`. In the case where there
is no final class (which is the situation here) it is valid for the
first class to match and for an optional class to **fail** to
match. This is not the required behaviour for the `Program` class as, if an
optional `Program_Unit` exists then it must be a valid `Program_Unit`
or the code is invalid. For example, the following code is invalid as
there is a misspelling of `subroutine`::

    program test
    end
    subroutin broken
    end

To implement the required functionality for the `Program` class, the
static `match` method is written manually. A `while` loop is used to
ensure that there is no match if any `Program_Unit` is invalid.

There are also two contraints that must be adhered to by the `Program`
class:

1) Only one program unit may be a main program
2) Any name used by a program-unit (e.g. program fred) must be
   distinct from names used in other program-units.

At the moment neither of these two contraints are enforced in
fparser2. Therefore two xfailing tests `test_one_main1` and
`test_multiple_error1` have been added to the
`tests/fortran2003/test_program_r201.py` file to demonstrate these
limitations.

Further, in Fortran the `program` declaration is actually
optional. For example, the following is a valid (minimal) Fortran
program::

    end

fparser2 does not support the above syntax in its `Program_Unit`
class. Therefore as a workaround, a separate `Program_Unit0` class has
been implemented and added as a final test to the `Program` match
method. This does make use of `BlockBase` to match and therefore
requires the `Program` class to subclass `BlockBase`.

.. note::
   
   It would be much better if `Program_Unit` was coded to support
   optional program declarations and this option should be
   investigated.

The current implementation also has a limitation in that
multiple program-units with one of them not having a program
declaration are not supported. The xfailing test
`test_missing_prog_multi` has been added to the
`tests/fortran2003/test_program_r201.py` file to demonstrate this
limitation.

A final issue is that the line numbers and line information output is
incorrect in certain cases where there is a syntax error in the code
and there are 5 spaces before a statement. The xfailing tests
`test_single2` and `test_single3` have been added to the
`tests/fortran2003/test_program_r201.py` file to demonstrate this
error.

.. _program-unit-class:

Program_Unit Class (rule R202)
++++++++++++++++++++++++++++++

Fortran2003 rule `r202` is specified as
::

    R202 program-unit is main-program
                         or external-subprogram
                         or module
                         or block-data

As the above rule is a simple choice between different rules, the
appropriate matching code is already implemented in one of the base
classes (`Base`) and therefore does not need to be written.  Instead,
the rules on the right hand side can be provided as **strings** in the
`subclass_names` list. The `use_names` list should be empty and the
`tostr` method is not required (as there is no text to output because
this rule is simply used to decide what other rules to use).

.. note::

    it is currently unclear when to use `subclass_names` and when to use
    `use_names`. At the moment the pragmatic suggestion is to follow the
    way it is currently done.

Therefore to implement rule `R202` the following needs to
be specified
::
   
    class Program_Unit(Base):  # R202
        ''' <description> '''
        subclass_names = ['Comment', 'Main_Program', 'External_Subprogram',
                          'Module', 'Block_Data']

In this way fparser2 captures the `R202` rule hierarchy in its
`Program_Unit` class.

.. _exceptions:

Exceptions
++++++++++

There are 7 types of exception raised in fparser2: `NoMatchError`,
`FortranSyntaxError`, `ValueError`, `InternalError`, `AssertionError` and
`NotImplementedError`.

A baseclass `FparserException` is included which `NoMatchError`,
`FortranSyntaxError` and `InternalError` subclass. The reason for this
is to allow external tools to more simply manage fparser if it is used
as a library.

Each of the exceptions are now discussed in turn.

`NoMatchError` can be raised by a class when the text it is given does
not match the pattern for the class. A class can also return an empty
return value to indicate no match. It is currently unclear when it is
appropriate to do one or the other.

`NoMatchError` (or an empty return value) does not necessarily mean that
the text is invalid, just that the text does not match this class. For
example, it may be that some text should match one of a set of
rules. In this case all rules would fail to match except one. It is
only invalid text if none of the possible rules match.

Usually `NoMatchError` is raised by a class with no textual information
(a string provided as an argument to the exception), as textual
information is not required. When textual information is provided this
is ignored.

.. note::

   `NoMatchError` is the place where we can get context-specific
   information about a syntax error. The problem is that there are
   typically many `NoMatchError`s associated with invalid code. The
   reason for this is that every (relevant) rule needs to be matched
   with the associated invalid code. Each of these will return a
   `NoMatchError`. One option would be to always return
   context-specific information from `NoMatchError` and somehow
   aggregate this information until it is known that there is a syntax
   error. At this point a `FortranSyntaxError` is raised and the
   aggregated messages could be used to determine the correct
   message(s) to return. As a simple example, imagine parsing the
   following code: `us mymodule`.  This is probably meant to mean `use
   mymodule`. The associated rule might return a `NoMatchError` saying
   something like `use not found`. However, there might be a missing
   `=` and it could be that an assignment would would also return a
   `NoMatchError` saying something like `invalid assignment`. It is
   unclear which was the programmers intention. In general, it is
   probable that the further into a rule one gets the more likely it
   is a syntax error for that rule, so it may be possible to prune out
   many `NoMatchError`s. There may even be some rule about this
   i.e. if a hierarchy of rules is matched to a certain depth then it
   must be a syntax error associated with this rule. However, in
   general it will not be possible to prune `NoMatchError`s down to one.
   The first step could be to return context information from
   `NoMatchError` for all failures to match and then look at whether
   there is an obvious way to prune these when raising a
   `FortranSyntaxError`.

.. note::

   Need to add an explanation about when `NoMatchError` exceptions are
   used and when a null return is used.

A `FortranSyntaxError` exception should be raised if the parser does
not recognise the syntax. `FortranSyntaxError` takes two
arguments. The first argument is a reader object which allows the line
number and text of the line in question to be output. The second
argument is text which can be used to give details of the error.

Currently the main use of `FortranSyntaxError` is to catch either an
`InternalSyntaxError` exception or the final `NoMatchError` exception
and re-raise it with line number and the text of the line to be
output. These exceptions are caught and re-raised by overriding the
`Base` class `__new__` method in the top level `Program` class. A
limitation of the `NoMatchError` exception (but not the
`InternalSyntaxError` exception) is that it is not able to give any
details of the error, as it knows nothing about which rules failed to
match.

`FortranSyntaxError` should also be used when it is known that there
is a match, the match has a syntax error and the line number
information is available via the reader object. One issue is that when
`FortranSyntaxError` is raised from such a location, the `fparser2.py`
script may not be able to use the reader's fifo buffer to extract
position information. In this case, position information is not
provided in the output. It is possible that if the lines were pushed
back into the buffer in the parser code then this problem would not
occur.

.. note::

   more information about the error could be determined by inspecting
   the FortranReader object. In particular, a match can be over a
   number of lines and the first line could be returned as well as the
   last. At the moment the last line and the line number are returned.

An `InternalSyntaxError` exception should be raised when it is known
that there is a match and that a syntax error has occured but it is
not possible to use the `FortranSyntaxError` exception as the line
number information is not known (typically because the match is part
of a line rather than a full line so the input to the associated match
method is a string not a reader object). As mentioned earlier, this
exception is subsequently picked up and re-raised as a
`FortranSyntaxError` exception with line number information added.
   
A `ValueError` exception is raised if an invalid standard is passed to
the `create` method of the `ParserFactory` class.

An `InternalError` exception is raised when an unexpected condition is
found. Such errors currently specify where there error was, why it
happened and request that the authors are contacted.

.. note::
   
   An additional future idea would be to also wrap the whole code with
   a general exception handler which subsequently raised an
   InternalError. This would catch any additional unforseen errors
   e.g. errors due to the wrong type of data being passed. One
   implementation would be to have this as the the only place an
   InternalError is raised, however, it is considered better to check
   for exceptions where they might happen e.g. a dangling else clause,
   as appropriate contextual information can be given in the
   associated error message.

.. note::

   Information needs to be added about the use of
   `NotImplementedError` and `AssertionError` and/or the code needs to
   be modified. These exceptions come from pre-existing code and it is
   likely that we would want to remove the `AssertionError` from
   fparser. There has also been discussion about using a logger for
   messages, however, there are currently no known situations where it
   makes sense to output messages.

Object Hierarchy
++++++++++++++++

Fortran code is parsed by creating the `Program` object with a
`FortranReader` object as its argument. If the code is parsed
successfully then a hierarchy of objects is returned associated with
the structure of the original code. For example::

    >>> from fparser.common.readfortran import FortranStringReader
    >>> code = "program test\nend"
    >>> reader = FortranStringReader(code)
    >>> ast = parser_f2003(reader)
    >>> ast
    Program(Main_Program(Program_Stmt('PROGRAM', Name('test')), End_Program_Stmt('PROGRAM', None)))

Therefore the above example creates a `Program` object, which contains
a `Main_Program` object. The `Main_Program` object contains a
`Program_Stmt` object followed by an `End_Program_Stmt` object. The
`Program_Stmt` object contains the `PROGRAM` text and a `Name`
object. The `Name` object contains the name of the program
i.e. `test`. The `End_Program_Stmt` object contains the `PROGRAM` text
and a `None` for the name as it is not supplied in the original code.

As one might expect, the object hierarchy adheres to the Fortran rule
hierarchy presented in the associated Fortran specification document
(as each class implements a rule). If one were to manually follow the
rules in the specification document to confirm a code was compliant
and write down the rules visited on a piece of paper in a hierarchical
manner (i.e. also write down which rules triggered subsequent rules)
then there would be a one-to-one correspondance between the rules and
rule hierarchy written on paper and the objects and object hierarchy
returned by fparser2.

Extensions
++++++++++

Compilers often support extensions to the Fortran standard. fparser2
also does this in certain cases. The suggested way to support this in
fparser2 is to add an appropriate name to the `EXTENSIONS` list in
`utils.py` and then support this extension in the appropriate class if
the name is found in the `EXTENSIONS` list. This will allow this list
to be modified in the future (e.g. a `-std` option could force the
compiler to throw out any non-standard Fortran).

.. note::

   A number of extensions do not currently follow this convention and
   are always supported in fparser2 (e.g. support for `$` in
   names). At some point these need to be modified to use the new
   approach. Eventually, the concept of extensions is expected to be
   implemented as a configuration file rather than a static list.

Include files
+++++++++++++

fparser has been extended to support include files as part of the
Fortran syntax. This has been implemented in two new classes
`fparser.two.Fortran2003.Include_Stmt` and
`fparser.two.Fortran2003.Include_Filename`. This allows fparser to
parse code with unresolved include files.

The filename matching pattern implemented in fparser is that the
filename must start with a non-space character and end with a
non-space character. This is purposely a very loose restriction
because many characters can be used in filenames and different
characters may be valid in different operating systems. Note that
whilst the term filename is used here it can be a filepath.

The include statement rule is added to the start of the `BlockBase`
match method by integrating it with the `comments` rule in the
`add_c_and_i()` function. This means that any includes before a
BlockBase will be matched.

The include statement rule is also added to the subclasses to match in
the `BlockBase` match method by simply appending it to the existing
subclasses (the valid classes between the start and end classes) in
the same way that the Comments class is added. This means that any
includes within a `BlockBase` will be matched.

All Fortran rules that are responsible for matching whole line
statements (apart from the top level Program rule R201) make use of
the `BlockBase` match method. Therefore by adding support for includes
at the beginning and within a BlockBase class we support includes at
all possible locations (apart from after the very last statement).

The top level Program rule R201 supports includes at the level of
multiple program units by again making use of the `add_c_and_i()`
function before any 'program units', between 'program units' and after
any 'program units'. This completes all valid locations for include
statements, including the missing last statement mentioned in the
previous paragraph.

Preprocessing Directives
++++++++++++++++++++++++

fparser2 retains preprocessing directives as nodes in the parse tree
but does not interpret them. This has been implemented in
`C99Preprocessor.py` as a number of classes that have names with the
prefix `Cpp_`. This allows fparser2 to parse code successfully that
contains preprocessing directives but reduces to valid Fortran if the
directives are omitted.

Similarly to comments, the readers represent preprocessing directives
by a dedicated class `CppDirective`, which is a subclass of `Line`.
This allows directives to be detected early and matches to be limited
to source lines that are instances of `CppDirective`. Matching of directives
is performed in the same place as include statements to make sure that they
are recognized at all locations in a source file.

Most directives are implemented as subclasses of `WORDClsBase` or
`StringBase` (with the only exceptions being macro definition and
null directive).

Conditional inclusion directives (`#if...[#elif...]...#endif` or their
variants `#ifdef`/`#ifndef`) are represented as individual nodes by
classes `fparser.two.C99Preprocessor.Cpp_If_Stmt`,
`fparser.two.C99Preprocessor.Cpp_Elif_Stmt`,
`fparser.two.C99Preprocessor.Cpp_Else_Stmt`, and
`fparser.two.C99Preprocessor.Cpp_Endif_Stmt` but
currently not grouped together in any way since directives can appear
at any point in a file and thus the span of conditional inclusions may
be orthogonal to a Fortran block. In `#if(n)def` directives the
identifier is matched using
`fparser.two.C99Preprocessor.Cpp_Macro_Identifier`
and may contain only letters and underscore. In `#if` or `#elif`
directives the constant expression is matched very loosely by
`fparser.two.C99Preprocessor.Cpp_Pp_Tokens`
which accepts any non-empty string.

Include directives (`#include`) are handled similarly to Fortran
include statements with the matching of filenames being done by the
same class and therefore with the same (loose) restrictions.

Directives that define macro replacements (`#define`) contain a
macro identifier that is matched using `Cpp_Macro_Identifier`.
This is followed by an optional identifier list in parentheses
(and without white space separating identifier and opening
parenthesis) that defines parameters to the macro for use in the
replacement expression. The identifier list is matched by
`fparser.two.C99Preprocessor.Cpp_Macro_Identifier_List`
which, however, does not treat individual identifiers as separate
names but matches the entire list as a single string.
The replacement expression is matched and represented as
`Cpp_Pp_Tokens`.

The matching of `#undef` statements is implemented in class
`fparser.two.C99Preprocessor.Cpp_Undef_Stmt` with the identifier again
matched by `Cpp_Macro_Identifier`.

Directives `#line`, `#error`, and `#warning` are implemented in classes
`fparser.two.C99Preprocessor.Cpp_Line_Stmt`,
`fparser.two.C99Preprocessor.Cpp_Error_Stmt`, and
`fparser.two.C99Preprocessor.Cpp_Warning_Stmt` with the corresponding
right hand sides matched by `Cpp_Pp_Tokens`.

A single preprocessing directive token `#` without any directive is
a null statement and is matched by
`fparser.two.C99Preprocessor.Cpp_Null_Stmt`.

Utils
+++++

fparser2 includes a `utils.py` file. This file contains the base
classes (discussed in the :ref:`base-classes` section), the
fparser2-specific exceptions (discussed in the :ref:`exceptions`
section), a list of extensions (see previous section) and a tree-walk
utility that can be used to traverse the AST produced by fparser2 for
a valid Fortran program.

.. note::

   the tree-walk utility currently fails if the parent node of the
   tree is provided. The solution is to provide the parent's
   children. This should be fixed at some point.


.. skip
   # Constraints
   # +++++++++++
   # TBD
   # Comment Class
   # +++++++++++++
   # TBD

.. _tokenisation:

Tokenisation
++++++++++++

In order to simplify the problem of parsing code containing
potentially complex expressions, fparser2 performs some limited
tokenisation of a string before proceeding to attempt to match it.
Currently, this tokenisation replaces three different types of quantity with
simple names:

 1. the content of strings;
 2. expressions in parentheses;
 3. literal constants involving exponents (e.g. ``1.0d-3``)

This tokenisation is performed by the `string_replace_map` function:

.. autofunction:: fparser.common.splitline.string_replace_map

In turn, this function uses `splitquote` and `splitparen` (in the same
module) to split a supplied string into quanties within quotes or
parentheses, respectively. The matching for literal constants involving
exponents is implemented using a regular expression.

`string_replace_map` is used in the `match()` method of many of the classes
that implement the various language rules. Note that the tokenisation must
be undone before passing a given string on to a child class (or returning
it). This is performed using the reverse-map that `string_replace_map`
returns, e.g.::

    line, repmap = string_replace_map(string)
    ...
    type_spec = Declaration_Type_Spec(repmap(line[:i].rstrip()))

(The reverse map is an instance of `fparser.common.splitline.StringReplaceDict`
which subclasses`dict` and makes it callable.)

   
Expression matching
+++++++++++++++++++

The Fortran2003 rules specify a hierarchy of expressions (specified in
levels). In summary::

    R722 expr is [ expr defined-binary-op ] level-5-expr
    R717 level-5-expr is [ level-5-expr equiv-op ] equiv-operand
    R716 equiv-operand is [ equiv-operand or-op ] or-operand
    R715 or-operand is [ or-operand and-op ] and-operand
    R714 and-operand is [ not-op ] level-4-expr
    R712 level-4-expr is [ level-3-expr rel-op ] level-3-expr    
    R710 level-3-expr is [ level-3-expr concat-op ] level-2-expr
    R706 level-2-expr is [[level-2-expr] add_op ] add-operand
    R705 add-operand is [ add-operand mult-op ] mult-operand
    R704 mult-operand is level-1-expr [ power-op mult-operand ]
    R702 level-1-expr is [ defined-unary-op ] primary

As can hopefully be seen, the "top level" rule is `expr`, this depends
on a `level-5_expr`, which depends on an `equiv-operand` and so on in
a hierarchy in the order listed.

Fparser2 naturally follows this hierarchy, attempting to match in the
order specified. This works well apart from one case, which is the
matching of a Level-2 expression::

    R706 level-2-expr is [[level-2-expr] add_op ] add-operand

The problem is to do with falsely matching an exponent in a
literal. Take the following example::

    a - 1.0e-1

When searching for a match, the following pattern is a valid candidate
and will be the candidate used in fparser2 as fparser2 matches from the
right hand side of a string by default::

    level-2-expr = "a - 1.0e"
    add-op = "-"
    add-operand = "1"

As expected, this would fail to match, due to the level-2 expression
("a - 1.0e") being invalid. However, once R706 failed to match it
would not be called again as fparser2 follows the rule hierarchy
mentioned earlier. Therefore fparser2 would fail to match this string.

To solve this problem, fparser2 performs limited tokenisation of a string
before attempting to perform a match. Amongst other things, this tokenisation
replaces any numerical constants containing exponents with simple symbols
(see :ref:`tokenisation` for more details). For the example above this means
that the code being matched would now look like::

    a - F2PY_REAL_CONSTANT_1_

which is readily matched as a level-2 expression.

Continuous Integration
----------------------

GitHub Actions are used to run the test suite for a number of different
Python versions and the coverage reports are uploaded automatically to CodeCov
(https://codecov.io/gh/stfc/fparser). The configuration for this is in the
`.github/workflows/unit-tests.yml` file.

In addition, an Action is also used check that all of the code conforms
to Black (https://black.readthedocs.io) formatting. It is up to the developer
to ensure that this passes (e.g. by running `black` locally and committing
the results). Note that it is technically possibly to have the Action
actually make the changes and commit them but this was found to break
the Github review process since the automated commit is not permitted to
trigger further Actions and this then leaves GitHub thinking that the
various checks have not run.

Automatic Packaging
-------------------

A GitHub Action (https://github.com/pypa/gh-action-pypi-publish)
is also used to automate the process of uploading a new
release of fparser to the Python Package Index (pypi). This action is
configured in the `.github/workflows/python_publish.yml` file and is
triggered by the creation of a new release on GitHub.

Test Fixtures
-------------

Various pytest fixtures
(https://docs.pytest.org/en/stable/fixture.html) are provided so as to
aid in the mock-up of a suitable environment in which to run
tests. These are defined in `two/tests/conftest.py`:

=================== ======================= ===================================
Name                Returns                 Purpose
=================== ======================= ===================================
f2003_create        --                      Sets-up the class hierarchy for the
                                            Fortran2003 parser.
f2003_parser        `Fortran2003.Program`   Sets-up the class hierarchy for the
                                            Fortran2003 parser and returns the
                                            top-level Program object.
clear_symbol_table  --                      Removes all stored symbol tables.
fake_symbol_table   --                      Creates a fake scoping region and
                                            associated symbol table.
=================== ======================= ===================================


Performance Benchmark
---------------------

The fparser scripts folder contains a benchmarking script to assess the
performance of the parser by generating a synthetic Fortran file with
multiple subroutines and the associated subroutine calls. It can be executed
with the following command::

    ./src/fparser/scripts/fparser2_bench.py

