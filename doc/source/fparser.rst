.. -*- rest -*-

..
    Copyright (c) 2017-2023 Science and Technology Facilities Council.

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

.. _fparser:

fparser
=======

Getting Going
^^^^^^^^^^^^^

fparser was the original parser provided by the fparser package and
was implemented to parse Fortran code written in Fortran 66, 70 or 90
syntax. It is gradually being extended on an as-required basis in
order to support some of the aspects of more recent versions of
Fortran (see :ref:`beyond_f90`). In order to use it you will need to
have installed the fparser package which is available from the Python
Packagage Index (pypi) or github (https://github.com/stfc/fparser).

Once installed, you should be able to open the python interpreter and
try it out, e.g.:

::

  >>> from fparser.api import parse
  >>> code = """
  ... c comment
  ...       subroutine foo(a)
  ...       integer a
  ...       print*,"a=",a
  ...       end
  ... """
  >>> tree = parse(code, isfree=False)
  >>> print tree
        !BEGINSOURCE <cStringIO.StringI object at 0xb75ac410> mode=fix90
          SUBROUTINE foo(a)
            INTEGER a
            PRINT *, "a=", a
          END SUBROUTINE foo
  >>>
  >>> tree
        BeginSource
          blocktype='beginsource'
          name='<cStringIO.StringI object at 0xb75ac410> mode=fix90'
          a=AttributeHolder:
        external_subprogram=<dict with keys ['foo']>
          content:
            Subroutine
              args=['a']
              item=Line('subroutine foo(a)',(3, 3),'')
              a=AttributeHolder:
          variables=<dict with keys ['a']>
              content:
                Integer
                  selector=('', '')
                  entity_decls=['a']
                  item=Line('integer a',(4, 4),'')
                Print
                  item=Line('print*,"a=",a',(5, 5),'')
            EndSubroutine
              blocktype='subroutine'
              name='foo'
              item=Line('end',(6, 6),'')

As indicated by the above output, the `fparser.api.parse()` function
returns a `Statement` tree representation of the parsed source code.
This `parse()` function is actually a convenience method that wraps
the creation of a reader for Fortran source code (either
`FortranStringReader` or `FortranFileReader`) followed by a call to use
that reader to create the tree, e.g.:

::

  >>> from fparser.common.readfortran import FortranStringReader
  >>> from fparser.one.parsefortran import FortranParser
  >>> reader = FortranStringReader(code, FortranFormat(isfree, isstrict))
  >>> parser = FortranParser(reader)
  >>> parser.parse()
  >>> print parser.block
        !BEGINSOURCE <cStringIO.StringI object at 0xb751d500> mode=fix77
          SUBROUTINE foo(a)
            PRINT *, "a=", a
          END SUBROUTINE foo

The full interface to the `parse()` function is:

.. autofunction:: fparser.api.parse

The `FortranParser` class holds the parser information while
iterating over items returned by a `FortranReaderBase` iterator.
The parsing information, collected when calling `.parse()` method,
is saved in the `.block` attribute as an instance
of the `BeginSource` class defined in the `block_statements.py` file.

.. _beyond_f90:

Support for Fortran Standards beyond Fortran90
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

fparser has full support for Fortran conforming to the 66, 70 or 90
standards. Support for Fortran following more recent standards is
being added on an as-required basis and currently consists of:

* The SELECT TYPE block, including the TYPE IS, CLASS IS and CLASS
  DEFAULT clauses (Fortran 2003)
* Calls to type-bound procedures (Fortran 2003), e.g.

  ::

     call an_array(3)%a_proc(an_arg)
* Declaration of a CLASS variable (Fortran 2003), e.g.
  ::

     class(my_class) var
* Declaration of a procedure (Fortran 2003), e.g.
  ::

     procedure(interface_name) :: proc

Logging
^^^^^^^

fparser uses the standard Python logging package in order to note various
events which occur while parsing. Following standard Python practice it uses a
logger named after the module which raises the event. As such they all have
their root in the name "fparser". This name may be used by the calling program
to handle logged messages as it sees fit.

For instance, to just dump them to a file the following may be used::

  handler = logging.FileHandler(filename, mode='a')
  logging.getLogger('fparser').addhandler(handler)

Fparser sets a default `NullHandler`. This prevents missing handler errors but
also eats all logged messages. You will need to add additional handlers if you
wish to do something with these messages.

If you want to intercept fparser's messages and handle them as part of your own
logging regime you will need to write a handler which repeats them::

  class MyHandler(logging.Handler):
      def emit(self, record):
          logging.getLogger(__name__).handle(record)

Reference
^^^^^^^^^

The fparser package contains the following modules:

 * :ref:`api`
 * :ref:`readfortran`
 * :ref:`parsefortran`

The functionality of each of these is described in the sections below.

.. _api :

api.py
------

`This file`_ provides the public API to fparser. It exposes
`Statement` subclasses and a function, `parse`.

.. _This file: https://github.com/stfc/fparser/blob/master/src/fparser/api.py

Function `parse(<input>, ..)` parses, analyzes and returns a `Statement`
tree of Fortran input. 

.. _readfortran :

readfortran.py
--------------

`This file`__ contains tools for reading Fortran codes from file and
from string objects.

__ https://github.com/stfc/fparser/blob/master/src/fparser/common/readfortran.py

To read Fortran code from a file, use the `FortranFileReader` class.
The `FortranFileReader` class is an iterator over Fortran code lines
and is derived from the `FortranReaderBase` class.
It automatically handles line continuations and comments, as
well as detecting whether a Fortran file is in free or fixed format.

For example,

::

  >>> from fparser.common.readfortran import *
  >>> import os
  >>> reader = FortranFileReader(os.path.expanduser('~/src/blas/daxpy.f'))
  >>> reader.next()
  Line('subroutine daxpy(n,da,dx,incx,dy,incy)',(1, 1),'')
  >>> reader.next()
  Comment('c     constant times a vector plus a vector.\nc     uses unrolled loops for increments equal to one.\nc     jack dongarra, linpack, 3/11/78.\nc     modified 12/3/93, array(1) declarations changed to array(*)',(3, 6))
  >>> reader.next()
  Line('double precision dx(*),dy(*),da',(8, 8),'')
  >>> reader.next()
  Line('integer i,incx,incy,ix,iy,m,mp1,n',(9, 9),'')

Owing to its origins in the f2py project, the reader contains functionality
to identify the format of the provided source by examining Python-style
encoding information (c.f. `PEP 263`). Since this is not a part of the Fortran
standard, this functionality is disabled by default. It can be enabled by
providing the argument `ignore_encoding=False` to the reader.

.. _PEP 263: https://peps.python.org/pep-0263/

Note that the `FortranReaderBase.next()` method may return `Line`,
`SyntaxErrorLine`, `Comment`, `MultiLine`, or `SyntaxErrorMultiLine`
instances.

A `Line` instance has the following attributes:

  * `.line` - contains Fortran code line
  * `.span` - a 2-tuple containing the span of line numbers containing
    Fortran code in the original Fortran file
  * `.label` - the label of Fortran code line
  * `.reader` - the `FortranReaderBase` class instance
  * `.strline` - if it is not `None` then it contains Fortran code line
    with parenthesis
    content and string literal constants saved in the `.strlinemap` dictionary.
  * `.is_f2py_directive` - `True` if line starts with the f2py directive
    comment.

and the following methods:

  * `.get_line()` - returns `.strline` (also evalutes it if None). Also
    handles Hollerith contstants in the fixed F77 mode.
  * `.isempty()`  - returns `True` if Fortran line contains no code.
  * `.copy(line=None, apply_map=False)` - returns a `Line` instance
    with given `.span`, `.label`, `.reader` information but the line content
    replaced with `line` (when not `None`) and applying `.strlinemap`
    mapping (when `apply_map` is `True`).
  * `.apply_map(line)` - apply `.strlinemap` mapping to line content.
  * `.has_map()` - returns `True` if `.strlinemap` mapping exists.

For example,

::

  >>> item = reader.next()
  >>> item
  Line('if(n.le.0)return',(11, 11),'')
  >>> item.line
  'if(n.le.0)return'
  >>> item.strline
  'if(F2PY_EXPR_TUPLE_4)return'
  >>> item.strlinemap
  {'F2PY_EXPR_TUPLE_4': 'n.le.0'}
  >>> item.label
  ''
  >>> item.span 
  (11, 11)
  >>> item.get_line()
  'if(F2PY_EXPR_TUPLE_4)return'
  >>> item.copy('if(F2PY_EXPR_TUPLE_4)pause',True)
  Line('if(n.le.0)pause',(11, 11),'')

A `Comment` instance has the following attributes:

  * `.comment` - a comment string
  * `.span` - a 2-tuple containing the span of line numbers containing
    Fortran comment in the original Fortran file
  * `.reader` - the `FortranReaderBase` class instance

and `.isempty()` method.

A `MultiLine` class represents multiline syntax in the .pyf files::

  <prefix>'''<lines>'''<suffix>

A `MultiLine` instance has the following attributes:

  * `.prefix` - the content of `<prefix>`
  * `.block` - a list of lines
  * `.suffix` - the content of `<suffix>`
  * `.span` - a 2-tuple containing the span of line numbers containing
    multiline syntax in the original Fortran file
  * `.reader` - the `FortranReaderBase` class instance

and a `.isempty()` method.

`SyntaxErrorLine` and `SyntaxErrorMultiLine` are like `Line` and `MultiLine`
classes, respectively, with a functionality of issuing an error
message to `sys.stdout` when constructing an instance of the corresponding
class.

To read a Fortran code from a string, use `FortranStringReader` class::

  reader = FortranStringReader(<string>, <isfree>, <isstrict>)

where the second and third arguments are used to specify the format
of the given `<string>` content. When `<isfree>` and `<isstrict>` are both
`True`, the content of a .pyf file is assumed. For example,

::

  >>> code = """
  ... c      comment
  ...       subroutine foo(a)
  ...       print*, "a=",a
  ...       end
  ... """
  >>> reader = FortranStringReader(code, False, True)
  >>> reader.next()
  Comment('c      comment',(2, 2))
  >>> reader.next()
  Line('subroutine foo(a)',(3, 3),'')
  >>> reader.next()
  Line('print*, "a=",a',(4, 4),'')
  >>> reader.next()
  Line('end',(5, 5),'')

An instance of `FortranReaderBase` has the following attributes:

  * `.source` - a file-like object with a `.next()` method to retrive 
    a source code line
  * `.source_lines` - a list of read source lines
  * `.reader` - a `FortranReaderBase` instance for reading files
    from INCLUDE statements.
  * `.include_dirs` - a list of directories where INCLUDE files
    are searched. Default is `['.']`.

and the following methods:

  * `.set_mode(isfree, isstrict)` - set Fortran code format information
  * `.close_source()` - called when `.next()` raises `StopIteration` exception.

.. _parsefortran :


Model for Fortran Code Statements
---------------------------------

The model for representing Fortran code statements is defined in files
`block_statements.py`__, `base_classes.py`__,
`typedecl_statements.py`__ and `statements.py`__.
It consists of a tree of `Statement` classes defined in
`base_classes.py`. There are two types of statements: one-line
statements and block statements. Block statements consists of start
and end statements, and content statements in between that can be of
both types again.

__ https://github.com/stfc/fparser/blob/master/src/fparser/one/block_statements.py
__ https://github.com/stfc/fparser/blob/master/src/fparser/common/base_classes.py
__ https://github.com/stfc/fparser/blob/master/src/fparser/one/typedecl_statements.py
__ https://github.com/stfc/fparser/blob/master/src/fparser/one/statements.py

A `Statement` instance has the following attributes:

  * `.parent`  - either the parent block-type statement or the `FortranParser`
    instance.
  * `.item`    - a `Line` instance containing Fortran statement line
    information, see above.
  * `.isvalid` - when `False` then processing of this `Statement` instance will
    be skipped. e.g. when the content of `.item` does not match with
    the `Statement` class.
  * `.ignore`  - when `True` then the `Statement` instance will be ignored.
  * `.modes`   - a list of Fortran format modes where the `Statement`
    instance is valid.

and the following methods:

  * `.info(message)`, `.warning(message)`, `.error(message)` - to spit out
    messages to the `sys.stderr` stream.
  * `.get_variable(name)` - get `Variable` instance by name that is defined in
    current namespace. If name is not defined, then the corresponding
    `Variable` instance is created.
  * `.analyze()` - calculate various information about the `Statement`,
    this information is saved in `.a` attribute that is an instance of
    `AttributeHolder`.

All statement classes are derived from the `Statement` class. Block
statements are derived from the `BeginStatement` class and are assumed
to end with an `EndStatement` instance in the `.content` attribute
list. `BeginStatement` and `EndStatement` instances have the following
attributes:

  * `.name`      - name of the block, blocks without names use line label
    as the name.
  * `.blocktype` - type of the block (derived from class name)
  * `.content`   - a list of `Statement` (or `Line`) instances.

and the following methods:

  * `.__str__()` - returns a string representation of the Fortran code.

A number of statements may declare a variable that is used in other
statement expressions. Variables are represented via the `Variable` class
and its instances have the following attributes:

  * `.name`      - name of the variable
  * `.typedecl`  - type declaration
  * `.dimension` - list of dimensions
  * `.bounds`    - list of bounds
  * `.length`    - length specs
  * `.attributes` - list of attributes
  * `.bind`      - list of bind information
  * `.intent`    - list of intent information
  * `.check`     - list of check expressions
  * `.init`      - initial value of the variable
  * `.parent`    - statement instance declaring the variable
  * `.parents`   - list of statements that specify variable information

and the following methods:

  * `.is_private()`
  * `.is_public()`
  * `.is_allocatable()`
  * `.is_external()`
  * `.is_intrinsic()`
  * `.is_parameter()`
  * `.is_optional()`
  * `.is_required()`

Block Statements
~~~~~~~~~~~~~~~~

The following block statements are defined in `block_statements.py`:

  `BeginSource`, `Module`, `PythonModule`, `Program`, `BlockData`, `Interface`,
  `Subroutine`, `Function`, `Select`, `Where`, `Forall`, `IfThen`, `If`, `Do`,
  `Associate`, `TypeDecl (Type)`, `Enum`

Block statement classes may have different properties which are declared via
deriving them from the following classes:

  `HasImplicitStmt`, `HasUseStmt`, `HasVariables`, `HasTypeDecls`,
  `HasAttributes`, `HasModuleProcedures`, `ProgramBlock`

In summary, the `.a` attribute may hold different information sets as follows:

  * `BeginSource` - `.module`, `.external_subprogram`, `.blockdata`
  * `Module` - `.attributes`, `.implicit_rules`, `.use`, `.use_provides`,
    `.variables`, `.type_decls`, `.module_subprogram`, `.module_data`
  * `PythonModule` - `.implicit_rules`, `.use`, `.use_provides`
  * `Program` - `.attributes`, `.implicit_rules`, `.use`, `.use_provides`
  * `BlockData` - `.implicit_rules`, `.use`, `.use_provides`, `.variables`
  * `Interface` - `.implicit_rules`, `.use`, `.use_provides`,
    `.module_procedures`
  * `Function`, `Subroutine` - `.implicit_rules`, `.attributes`, `.use`,
    `.use_statements`, `.variables`, `.type_decls`, `.internal_subprogram`
  * `TypeDecl` - `.variables`, `.attributes`

Block statements have the following methods:

  * `.get_classes()` - returns a list of `Statement` classes that are valid
    as a content of the given block statement.

Type-declaration Statements
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following type-declaration statements are defined in
`typedecl_statements.py`:

  `Integer`, `Real`, `DoublePrecision`, `Complex`, `DoubleComplex`, `Logical`,
  `Character`, `Byte`, `Type`, `Class`

and they have the following attributes:

  * `.selector`   - contains length and kind specs
  * `.entity_decls`, `.attrspec`

and methods:

  * `.tostr()` - return string representation of Fortran type declaration
  * `.astypedecl()` - pure type declaration instance, it has no `.entity_decls`
    and `.attrspec`.
  * `.analyze()` - processes `.entity_decls` and `.attrspec` attributes and adds
    `Variable` instance to `.parent.a.variables` dictionary.

Statements
~~~~~~~~~~

The following one-line statements are defined:

  `Implicit`, `TypeDeclarationStatement` derivatives (see above),
  `Assignment`, `PointerAssignment`, `Assign`, `Call`, `Goto`, `ComputedGoto`,
  `AssignedGoto`, `Continue`, `Return`, `Stop`, `Print`, `Read`, `Write`, `Flush`,
  `Wait`, `Contains`, `Allocate`, `Deallocate`, `ModuleProcedure`, `Access`,
  `Public`, `Private`, `Close`, `Cycle`, `Backspace`, `Endfile`, `Reeinf`, `Open`,
  `Format`, `Save`, `Data`, `Nullify`, `Use`, `Exit`, `Parameter`, `Equivalence`,
  `Dimension`, `Target`, `Pointer`, `Protected`, `Volatile`, `Value`,
  `ArithmeticIf`, `Intrinsic`, `Inquire`, `Sequence`, `External`, `Namelist`,
  `Common`, `Optional`, `Intent`, `Entry`, `Import`, `Forall`,
  `SpecificBinding`, `GenericBinding`, `FinalBinding`, `Allocatable`,
  `Asynchronous`, `Bind`, `Else`, `ElseIf`, `Case`, `Where`, `ElseWhere`,
  `Enumerator`, `FortranName`, `Threadsafe`, `Depend`, `Check`,
  `CallStatement`, `CallProtoArgument`, `Pause`
