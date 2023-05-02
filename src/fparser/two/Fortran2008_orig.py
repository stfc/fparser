# Modified work Copyright (c) 2018-2023 Science and Technology
# Facilities Council.
# Original work Copyright (c) 1999-2008 Pearu Peterson

# All rights reserved.

# Modifications made as part of the fparser project are distributed
# under the following license:

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:

# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# --------------------------------------------------------------------

# The original software (in the f2py project) was distributed under
# the following license:

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

#   a. Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#   b. Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#   c. Neither the name of the F2PY project nor the names of its
#      contributors may be used to endorse or promote products derived from
#      this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.

"""The file implements the Fortran2008 rules as defined in
    https://j3-fortran.org/doc/year/10/10-007r1.pdf

"""
# pylint: disable=invalid-name
# pylint: disable=arguments-differ
# pylint: disable=undefined-variable
# pylint: disable=eval-used
# These warnings are due to the auto-generation of classes when this
# module is first imported.
# pylint: disable=exec-used
# pylint: disable=unused-import
import inspect
import sys

from fparser.common.splitline import string_replace_map, splitparen
from fparser.two import pattern_tools as pattern
from fparser.two.utils import (
    BracketBase,
    CALLBase,
    KeywordValueBase,
    NoMatchError,
    ScopingRegionMixin,
    SeparatorBase,
    StmtBase,
    STRINGBase,
    Type_Declaration_StmtBase,
    WORDClsBase,
)

from fparser.two.Fortran2003 import (
    Base,
    BlockBase,
    Component_Decl_List,
    Declaration_Construct,
    Declaration_Type_Spec,
    EndStmtBase,
    Entity_Decl_List,
    Errmsg_Variable,
    Execution_Part_Construct,
    File_Name_Expr,
    File_Unit_Number,
    Implicit_Part,
    Implicit_Part_Stmt,
    Import_Stmt,
    Iomsg_Variable,
    Label,
    Module_Subprogram_Part,
    Name,
    SequenceBase,
    Source_Expr,
    Specification_Part,
    Stat_Variable,
    Stop_Code,
    Use_Stmt,
)

# Import of F2003 classes that are updated in this standard.
from fparser.two.Fortran2003 import (
    Action_Stmt as Action_Stmt_2003,
    Action_Stmt_C201 as Action_Stmt_C201_2003,
    Action_Stmt_C802 as Action_Stmt_C802_2003,
    Action_Stmt_C824 as Action_Stmt_C824_2003,
    Alloc_Opt as Alloc_Opt_2003,
    Allocate_Stmt as Allocate_Stmt_2003,
    Attr_Spec as Attr_Spec_2003,
    Component_Attr_Spec as Component_Attr_Spec_2003,
    Connect_Spec as Connect_Spec_2003,
    Data_Component_Def_Stmt as Data_Component_Def_Stmt_2003,
    Do_Term_Action_Stmt as Do_Term_Action_Stmt_2003,
    If_Stmt as If_Stmt_2003,
    Open_Stmt as Open_Stmt_2003,
    Procedure_Stmt as Procedure_Stmt_2003,
    Type_Declaration_Stmt as Type_Declaration_Stmt_2003,
)


class Action_Stmt(Action_Stmt_2003):  # R214
    """
    Fortran 2008 rule R214.

    .. code-block:: fortran

        action-stmt is allocate-stmt
                        or assignment-stmt
                        or backspace-stmt
                        or call-stmt
                        or close-stmt
                        or continue-stmt
                        or cycle-stmt
                        or deallocate-stmt
                        or end-function-stmt
                        or end-mp-subprogram-stmt
                        or end-program-stmt
                        or end-subroutine-stmt
                        or endfile-stmt
                        or error-stop-stmt
                        or exit-stmt
                        or flush-stmt
                        or forall-stmt
                        or goto-stmt
                        or if-stmt
                        or inquire-stmt
                        or lock-stmt
                        or nullify-stmt
                        or open-stmt
                        or pointer-assignment-stmt
                        or print-stmt
                        or read-stmt
                        or return-stmt
                        or rewind-stmt
                        or stop-stmt
                        or sync-all-stmt
                        or sync-images-stmt
                        or sync-memory-stmt
                        or unlock-stmt
                        or wait-stmt
                        or where-stmt
                        or write-stmt
                        or arithmetic-if-stmt
                        or computed-goto-stmt

    The implementation of this rule adds the relevant subclass names
    for new statements added in Fortran 2008.

    Associated constraints are:

    "C201 (R208) An execution-part shall not contain an end-function-stmt,
          end-mp-subprogram-stmt, end-program-stmt, or end-subroutine-stmt."

    NB: The following statements are not yet implemented:
    end-mp-subprogram-stmt, endfile-stmt, lock-stmt, sync-all-stmt,
    sync-images-stmt, sync-memory-stmt, unlock-stmt.

    """

    # Fortran 2008 adds a few additional action-stmt. We therefore
    # extend the Fortran 2003 specification
    subclass_names = Action_Stmt_2003.subclass_names[:]
    subclass_names.append("Error_Stop_Stmt")


class Action_Stmt_C201(Action_Stmt_C201_2003):
    """
    action-stmt-c201 is action-stmt
    C201 is applied.
    """

    subclass_names = Action_Stmt.subclass_names[:]
    subclass_names.remove("End_Function_Stmt")
    subclass_names.remove("End_Subroutine_Stmt")


class Action_Stmt_C816(Action_Stmt_C824_2003):
    """
    action-stmt-c816 is action-stmt
    C816 is applied.
    """

    subclass_names = Action_Stmt.subclass_names[:]
    subclass_names.remove("Arithmetic_If_Stmt")
    subclass_names.remove("Continue_Stmt")
    subclass_names.remove("Cycle_Stmt")
    subclass_names.remove("End_Function_Stmt")
    subclass_names.remove("End_Subroutine_Stmt")
    subclass_names.remove("Error_Stop_Stmt")
    subclass_names.remove("Exit_Stmt")
    subclass_names.remove("Goto_Stmt")
    subclass_names.remove("Return_Stmt")
    subclass_names.remove("Stop_Stmt")


class Action_Stmt_C828(Action_Stmt_C802_2003):
    """
    action-stmt-c828 is action-stmt
    C828 is applied.
    """

    subclass_names = Action_Stmt.subclass_names[:]
    subclass_names.remove("End_Function_Stmt")
    subclass_names.remove("End_Subroutine_Stmt")
    subclass_names.remove("If_Stmt")


class Data_Component_Def_Stmt(Data_Component_Def_Stmt_2003):  # R436
    """
    Fortran 2008 rule 436.

    .. code-block:: fortran

        data-component-def-stmt is declaration-type-spec [
                 [ , component-attr-spec-list ] :: ] component-decl-list

    The implementation of this rule does not add anything to the Fortran 2003
    variant but reimplements the match method identical to Fortran 2003 as
    otherwise the generated Fortran 2008 variant of `Component_Attr_Spec_List`
    would not be used. Unfortunately, the required `attr_spec_list_cls` can not
    simply be provided as a class property since the relevant class is only
    generated at the end of this file using the `use_names` class property of
    this class.

    Associated constraints are:

    "C439 (R436)  No component-attr-spec shall appear more than once in a given
          component-def-stmt."
    "C440 (R436)  If neither the POINTER nor the ALLOCATABLE attribute is
          specified, the declaration-type-spec in the component-def-stmt shall
          specify an intrinsic type or a previously defined derived type."
    "C441 (R436)  If the POINTER or ALLOCATABLE attribute is specified, each
          component-array-spec shall be a deferred-shape-spec-list."
    "C442 (R436)  If a coarray-spec appears, it shall be a
          deferred-coshape-spec-list and the component shall have the
          ALLOCATABLE attribute."
    "C443 (R436)  If a coarray-spec appears, the component shall not be of type
          C_PTR or C_FUNPTR."
    "C445 (R436)  If neither the POINTER nor the ALLOCATABLE attribute is
          specified, each component-array-spec shall be an
          explicit-shape-spec-list."
    "C447 (R436)  A component shall not have both the ALLOCATABLE and POINTER
          attributes."
    "C448 (R436)  If the CONTIGUOUS attribute is specified, the component shall
          be an array with the POINTER attribute."
    "C457 (R436)  If component-initialization appears, a double-colon separator
          shall appear before the component-decl-list."
    "C458 (R436)  If component-initialization appears, every type parameter and
          array bound of the component shall be a colon or constant expression.
    "C459 (R436)  If => appears in component-initialization, POINTER shall
          appear in the component-attr-spec-list. If = appears in
          component-initialization, neither POINTER nor ALLOCATABLE shall
          appear in the component-attr-spec-list."

    C439-C443, C445, C447-C448, C457-C459 are currently not checked
    - issue #258.

    """

    @staticmethod
    def match(string):
        """Implements the matching of a data component definition statement.

        :param str string: the reader or string to match as a data \
                           component definition statement.

        :return: a 3-tuple containing declaration type specification, \
                 component attribute specification and component declaration \
                 list if there is a match or None if there is no match.
        :rtype: `NoneType` or \
            (:py:class:`fparser.two.Fortran2003.Declaration_Type_Spec`, \
             :py:class:`fparser.two.Fortran2008.Component_Attr_Spec_List`, \
             :py:class:`fparser.two.Fortran2003.Component_Decl_List`)

        """
        #from fparser.two.Fortran2008 import Component_Attr_Spec_List, Component_Decl_List
        from fparser.two.Fortran2008 import Component_Attr_Spec_List
        return Type_Declaration_StmtBase.match(
            Declaration_Type_Spec, Component_Attr_Spec_List, Component_Decl_List, string
        )


class Component_Attr_Spec(Component_Attr_Spec_2003):  # R437
    """
    Fortran 2008 rule R437.

    .. code-block:: fortran

        component-attr-spec is access-spec
                               or ALLOCATABLE
                               or CODIMENSION lbracket coarray-spec rbracket
                               or CONTIGUOUS
                               or DIMENSION ( component-array-spec )
                               or POINTER

    In the spec above, lbracket and rbracket are left and right square
    brackets `[]` but not printed explicitly to avoid misinterpretation
    as optional parts.

    This rule adds CODIMENSION and CONTIGUOUS attributes to Fortran2003's R441.

    """

    subclass_names = Component_Attr_Spec_2003.subclass_names[:]
    subclass_names.append("Codimension_Attr_Spec")
    attributes = Component_Attr_Spec_2003.attributes[:]
    attributes.append("CONTIGUOUS")


class Type_Declaration_Stmt(Type_Declaration_Stmt_2003):  # R501
    """
    Fortran 2008 rule 501.

    .. code-block:: fortran

        type-declaration-stmt is declaration-type-spec [ [ , attr-spec ] ... :: ]
                                 entity-decl-list

    The implementation of this rule does not add anything to the Fortran 2003
    variant but overwrites :py:meth:`get_attr_spec_list_cls` to use
    the Fortran 2008 variant of :py:class:`Attr_Spec_List`.

    Associated constraints are:

    "C501 (R501)  The same attr-spec shall not appear more than once in a given
          type-declaration-stmt."
    "C502 (R501)  If a language-binding-spec with a NAME= specifier appears,
          the entity-decl-list shall consist of a single entity-decl."
    "C503 (R501)  If a language-binding-spec is specified, the entity-decl-list
          shall not contain any procedure names."
    "C505 (R501)  If initialization appears, a double-colon separator shall
          appear before the entity-decl-list."

    C501-C503, C505 are currently not checked - issue #259.

    """

    @staticmethod
    def get_attr_spec_list_cls():
        """Return the type used to match the attr-spec-list

        This overwrites the Fortran 2003 type with the Fortran 2008 variant.

        """
        from fparser.two.Fortran2008 import Attr_Spec_List
        return Attr_Spec_List


class Codimension_Attr_Spec(WORDClsBase):  # R502.d
    """
    codimension-attr-spec is CODIMENSION lbracket coarray-spec rbracket

    In the spec above, lbracket and rbracket are left and right square
    brackets `[]` but not printed explicitly to avoid misinterpretation
    as optional parts.

    """

    subclass_names = []
    use_names = ["Coarray_Bracket_Spec"]

    @staticmethod
    def match(string):
        """
        Implements the matching for the CODIMENSION attribute.

        :param str string: the string to match as the attribute.

        :return: `None` if there is no match, otherwise a 2-tuple \
                 containing `CODIMENSION` as a string and the matched \
                 coarray-spec..
        :rtype: `NoneType` or \
            (`str`, :py:class:`fparser.two.Fortran2008.Coarray_Bracket_Spec`,)

        """
        return WORDClsBase.match(
            "CODIMENSION", Coarray_Bracket_Spec, string, colons=False, require_cls=True
        )


class Coarray_Bracket_Spec(BracketBase):  # R502.d.0
    """
    coarray-bracket-spec is lbracket coarray-spec rbracket

    In the spec above, lbracket and rbracket are left and right square
    brackets `[]` but not printed explicitly to avoid misinterpretation
    as optional parts.

    """

    subclass_names = []
    use_names = ["Coarray_Spec"]

    @staticmethod
    def match(string):
        """
        Implements the matching for the coarray specification
        including the square brackets.

        :param str string: the string to match as the specification.

        :return: `None` if there is no match, otherwise a 3-tuple \
                 containing the left bracket, the matched coarray-spec, \
                 and the right bracket.
        :rtype: `NoneType` or \
            (`str`, :py:class:`fparser.two.Fortran2008.Coarray_Spec`, `str`)

        """
        return BracketBase.match("[]", Coarray_Spec, string)


class Attr_Spec(Attr_Spec_2003):  # R502
    """
    Fortran 2008 rule R502.

    .. code-block:: fortran

        attr-spec is access-spec
                     or ALLOCATABLE
                     or ASYNCHRONOUS
                     or CODIMENSION lbracket coarray-spec rbracket
                     or CONTIGUOUS
                     or DIMENSION ( array-spec )
                     or EXTERNAL
                     or INTENT ( intent-spec )
                     or INTRINSIC
                     or language-binding-spec
                     or OPTIONAL
                     or PARAMETER
                     or POINTER
                     or PROTECTED
                     or SAVE
                     or TARGET
                     or VALUE
                     or VOLATILE

    In the spec above, lbracket and rbracket are left and right square
    brackets `[]` but not printed explicitly to avoid misinterpretation
    as optional parts.

    This rule adds CODIMENSION and CONTIGUOUS attributes to Fortran2003's R503.

    """

    subclass_names = Attr_Spec_2003.subclass_names[:]
    subclass_names.append("Codimension_Attr_Spec")
    use_names = []

    @staticmethod
    def match(string):
        """
        Implements the matching for attributes of types.

        :param str string: the string to match as attribute.

        :return: `None` if there is no match, otherwise a 1-tuple \
                 containing the matched string.
        :rtype: `NoneType` or (`str`,)

        """
        return STRINGBase.match(pattern.abs_attr_spec_f08, string)


class Coarray_Spec(Base):  # R509
    """
    Fortran 2008 rule R509.

    .. code-block:: fortran

        coarray-spec is deferred-coshape-spec-list
                        or explicit-coshape-spec-list

    """

    subclass_names = ["Explicit_Coshape_Spec", "Deferred_Coshape_Spec_List"]


class Deferred_Coshape_Spec(SeparatorBase):  # R510
    """
    Fortran 2008 rule R510
    deferred-coshape-spec is :

    """

    subclass_names = []

    @staticmethod
    def match(string):
        """
        Implements the matching for deferred coarray shape specification.

        :param str string: the string to match as deferred shape.

        :return: `None` if there is no match, otherwise a 2-tuple \
                 containing `None`.
        :rtype: `NoneType` or (`None`, `None`)

        """
        if string == ":":
            return (None, None)
        return None


class Explicit_Coshape_Spec(SeparatorBase):  # R511
    """
    Fortran 2008 rule R511
    explicit-coshape-spec is [ coshape-spec-list , ] [ lower-cobound : ] *

    Associated constraint is:

    "C529 (R511)  A lower-cobound or upper-cobound that  is  not  a  constant
          expression shall appear only in a subprogram, BLOCK construct, or
          interface body."

    C529 is currently not checked - issue #259.

    """

    subclass_names = []
    use_names = ["Coshape_Spec_List", "Lower_Cobound"]

    @staticmethod
    def match(string):
        """
        Implements the matching for explicit coarray shape specification.

        :param str string: the string to match as deferred shape.

        :return: `None` if there is no match, otherwise a 2-tuple \
                 containing matched coshape-spec-list or `None` and \
                 matched lower-cobound or `None`.
        :rtype: `NoneType` or \
            (:py:class:`fparser.two.Fortran2008.Coshape_Spec_List` or `None`, \
             :py:class:`fparser.two:Fortran2008.Lower_Cobound` or `None`)

        """
        from fparser.two.Fortran2008 import Coshape_Spec_List
        if not string.endswith("*"):
            return None
        line = string[:-1].rstrip()
        if not line:
            return (None, None)
        if line.endswith(":"):
            line, repmap = string_replace_map(line[:-1].rstrip())
            sep_pos = line.rfind(",")
            if sep_pos == -1:
                return (None, Lower_Cobound(repmap(line)))
            return (
                Coshape_Spec_List(repmap(line[:sep_pos].rstrip())),
                Lower_Cobound(repmap(line[sep_pos + 1 :].lstrip())),
            )
        if not line.endswith(","):
            return None
        line = line[:-1].rstrip()
        return (Coshape_Spec_List(line), None)

    def tostr(self):
        """
        Converts the explicit coarray shape specification to string.

        :return: the shape specification as string.
        :rtype: str

        """
        s = ""
        if self.items[0]:
            s += str(self.items[0]) + ", "
        if self.items[1]:
            s += str(self.items[1]) + " : "
        s += "*"
        return s


class Coshape_Spec(SeparatorBase):  # R511.a
    """
    coshape-spec is [ lower-cobound : ] upper-cobound

    """

    subclass_names = []
    use_names = ["Lower_Cobound", "Upper_Cobound"]

    @staticmethod
    def match(string):
        """
        Implements the matching for a coarray shape.

        :param str string: the string to match as shape.

        :return: `None` if there is no match, otherwise a 2-tuple with \
                 lower bound if given or `None`, and upper bound.
        :rtype: `NoneType` or \
            (`None`, :py:class:`fparser.two.Fortran2008.Upper_Cobound`) or \
            (:py:class:`fparser.two.Fortran2008.Lower_Cobound`, \
             :py:class:`fparser.two.Fortran2008.Upper_Cobound`)

        """
        line, repmap = string_replace_map(string)
        if ":" not in line:
            return (None, Upper_Cobound(string))
        lower, upper = line.split(":", 1)
        lower = lower.rstrip()
        upper = upper.lstrip()
        if not upper:
            return None
        if not lower:
            return None
        return (Lower_Cobound(repmap(lower)), Upper_Cobound(repmap(upper)))

    def tostr(self):
        """
        Converts the Shape specification to string.

        :return: the shape specification as string.
        :rtype: str

        """
        if self.items[0] is None:
            return str(self.items[1])
        return SeparatorBase.tostr(self)


class Lower_Cobound(Base):  # R512
    """
    Fortran 2008 rule R512
    lower-cobound is specification-expr

    """

    subclass_names = ["Specification_Expr"]


class Upper_Cobound(Base):  # R513
    """
    Fortran 2008 rule R513
    upper-cobound is specification-expr

    """

    subclass_names = ["Specification_Expr"]


class Do_Term_Action_Stmt(Do_Term_Action_Stmt_2003):  # R826
    """
    Fortran 2008 rule R826.

    do-term-action-stmt is action-stmt

    Associated constraints are:

    "C816 (R826) A do-term-action-stmt shall not be an arithmetic-if-stmt,
          continue-stmt, cycle-stmt, end-function-stmt, end-mp-subprogram-stmt,
          end-program-stmt, end-subroutine-stmt, error-stop-stmt, exit-stmt,
          goto-stmt, return-stmt, or stop-stmt."
    """

    subclass_names = ["Action_Stmt_C816"]


class Alloc_Opt(Alloc_Opt_2003):
    """
    Fortran2008 rule R627.

    .. code-block:: fortran

        alloc-opt is ERRMSG = errmsg-variable
                  or MOLD = source-expr
                  or SOURCE = source-expr
                  or STAT = stat-variable

    Extends the Fortran2003 version of this class by updating the keyword
    pairs (used in match) with support for MOLD.

    """

    _keyword_pairs = [
        ("STAT", Stat_Variable),
        ("ERRMSG", Errmsg_Variable),
        ("SOURCE", Source_Expr),
        ("MOLD", Source_Expr),
    ]


class Allocate_Stmt(Allocate_Stmt_2003):  # R626
    """
    Fortran 2008 rule R626.

    .. code-block:: fortran

        allocate-stmt is ALLOCATE ( [ type-spec :: ] allocation-list
                                    [, alloc-opt-list ] )

    The implementation of this rule simply ensures that the Fortran2008 version
    of Alloc_Opt is used.

    """

    subclass_names = []
    use_names = ["Type_Spec", "Allocation_List", "Alloc_Opt_List"]

    @classmethod
    def alloc_opt_list(cls):
        """
        :returns: the Fortran2008 flavour of Alloc_Opt_List.
        :rtype: type
        """
        from fparser.two.Fortran2008 import Alloc_Opt_List
        return Alloc_Opt_List


class If_Stmt(If_Stmt_2003):  # R837
    """
    Fortran 2008 rule R837
    if-stmt is IF ( scalar-logical-expr ) action-stmt

    The implementation of this rule only replaces the :py:attr:`use_names` and
    :py:attr:`action_stmt_class` attributes to use the Fortran 2008 variant
    :py:class:`Action_Stmt_C828` instead of
    :py:class:`fparser.two.Fortran2003.Action_Stmt_C802`.

    Associated constraints are:

    C828 (R837) The action-stmt in the if-stmt shall not be an end-function-stmt,
          end-mp-subprogram-stmt, end-program-stmt, end-subroutine-stmt, or if-stmt.

    """

    use_names = ["Scalar_Logical_Expr", "Action_Stmt_C828"]
    action_stmt_cls = Action_Stmt_C828


class Error_Stop_Stmt(StmtBase, WORDClsBase):  # R856
    """
    Fortran 2008 rule R856
    error-stop-stmt is ERROR STOP [ stop-code ]

    """

    subclass_names = []
    use_names = ["Stop_Code"]

    @staticmethod
    def match(string):
        """Check whether the input matches the rule

        :param str string: Text that we are trying to match.

        :returns: None if there is no match or, if there is a match, a \
            2-tuple containing a string matching 'ERROR STOP' and an \
            instance of :py:class:`fparser.two.Fortran2003.Stop_Code` \
            (or None if an instance of 'Stop_Code' is not required and \
            not provided).
        :rtype: (str, :py:class:`fparser.two.Fortran2003.Stop_Code` or None) \
            or NoneType

        """
        return WORDClsBase.match("ERROR STOP", Stop_Code, string)


class Specification_Part_C1112(Specification_Part):  # C1112
    """Fortran 2008 constraint C1112
    C1112 A submodule specification-part shall not contain a
    format-stmt, entry-stmt, or stmt-function-stmt.

    These statements are found in the following rule hierarchy

    format-stmt Specification_Part/implicit_part/implicit_part_stmt/format_stmt
                Specification_Part/declaration_construct/format_stmt
    entry-stmt Specification_Part/implicit_part/implicit_part_stmt/entry_stmt
               Specification_Part/declaration_construct/entry_stmt
    stmt-function-stmt Specification_Part/declaration_construct/
                       stmt-function-stmt

    Therefore we need to specialise implicit_part, implicit_part_stmt
    and declaration_construct

    """

    use_names = [
        "Use_Stmt",
        "Import_Stmt",
        "Implicit_Part_C1112",
        "Declaration_Construct_C1112",
    ]

    @staticmethod
    def match(reader):
        """Check whether the input matches the rule

        param reader: the fortran file reader containing the line(s)
                      of code that we are trying to match
        :type reader: :py:class:`fparser.common.readfortran.FortranFileReader` \
            | :py:class:`fparser.common.readfortran.FortranStringReader`

        :returns: `tuple` containing a single `list` which contains
                 instance of the classes that have matched if there is
                 a match or `None` if there is no match
        :rtype: Optional[Tuple[List[:py:class:`fparser.two.utils.Base`]]]
        """
        return BlockBase.match(
            None,
            [Use_Stmt, Import_Stmt, Implicit_Part_C1112, Declaration_Construct_C1112],
            None,
            reader,
        )


class Implicit_Part_C1112(Implicit_Part):  # C1112
    """Fortran 2008 constraint C1112
    C1112 A submodule specification-part shall not contain a
    format-stmt, entry-stmt, or stmt-function-stmt.

    This class specialises 'Implicit_Part' so that the specialised
    'Implicit_Part_Stmt_C1112' is called rather than the original
    'Implicit_Part_Stmt'

    """

    use_names = ["Implicit_Part_Stmt_C1112", "Implicit_Stmt"]

    @staticmethod
    def match(reader):
        """Check whether the input matches the rule

        param reader: the fortran file reader containing the line(s)
                      of code that we are trying to match
        :type reader: :py:class:`fparser.common.readfortran.FortranFileReader`
                      or
                      :py:class:`fparser.common.readfortran.FortranStringReader`
        :return: `tuple` containing a single `list` which contains
                 instance of the classes that have matched if there is
                 a match or `None` if there is no match

        """
        return BlockBase.match(None, [Implicit_Part_Stmt_C1112], None, reader)


class Implicit_Part_Stmt_C1112(Implicit_Part_Stmt):  # C1112
    """Fortran 2008 constraint C1112
    C1112 A submodule specification-part shall not contain a
    format-stmt, entry-stmt, or stmt-function-stmt.

    This class specialises 'Implicit_Part_Stmt' to remove
    'Format_Stmt' and 'Entry_Stmt'

    """

    subclass_names = Implicit_Part_Stmt.subclass_names[:]
    subclass_names.remove("Format_Stmt")
    subclass_names.remove("Entry_Stmt")


class Declaration_Construct_C1112(Declaration_Construct):  # C1112
    """Fortran 2008 constraint C1112
    C1112 A submodule specification-part shall not contain a
    format-stmt, entry-stmt, or stmt-function-stmt.

    This class specialises 'Declaration_Construct' to remove
    'Format_Stmt', 'Entry_Stmt' and 'Stmt_Function_Stmt'

    """

    subclass_names = Declaration_Construct.subclass_names[:]
    subclass_names.remove("Format_Stmt")
    subclass_names.remove("Entry_Stmt")
    # Commented out Stmt_Function_Stmt as it can falsely match an
    # access to an array or function. Reintroducing statement
    # functions is captured in issue #202.
    # subclass_names.remove('Stmt_Function_Stmt')


class Submodule(BlockBase):  # R1116 [C1112,C1114]
    """Fortran 2008 rule R1116.

    .. code-block:: fortran

        submodule is submodule-stmt
                     [ specification-part ]
                     [ module-subprogram-part ]
                     end-submodule-stmt

    C1112 A submodule specification-part shall not contain a
    format-stmt, entry-stmt, or stmt-function-stmt.
    This constraint is handled by specialising the Specification_Part
    class.

    C1114 If a submodule-name appears in the end-submodule-stmt, it
    shall be identical to the one in the submodule-stmt.
    This constraint is handled by the Base class with the names being
    provided by the 'Submodule_Stmt and 'End_Submodule_Stmt' classes
    via a `get_name` method.

    """

    subclass_names = []
    use_names = [
        "Submodule_Stmt",
        "Specification_Part_C1112",
        "Module_Subprogram_Part",
        "End_Submodule_Stmt",
    ]

    @staticmethod
    def match(reader):
        """Check whether the input matches the rule

        param reader: the fortran file reader containing the line(s)
                      of code that we are trying to match
        :type reader: :py:class:`fparser.common.readfortran.FortranFileReader`
                      or
                      :py:class:`fparser.common.readfortran.FortranStringReader`
        :return: `tuple` containing a single `list` which contains
                 instance of the classes that have matched if there is
                 a match or `None` if there is no match

        """
        result = BlockBase.match(
            Submodule_Stmt,
            [Specification_Part_C1112, Module_Subprogram_Part],
            End_Submodule_Stmt,
            reader,
        )
        return result


class Submodule_Stmt(Base, ScopingRegionMixin):  # R1117
    """
    Fortran 2008 rule R1117::

        submodule-stmt is SUBMODULE ( parent-identifier ) submodule-name

    """

    subclass_names = []
    use_names = ["Submodule_Name", "Parent_Identifier"]

    @staticmethod
    def match(fstring):
        """Check whether the input matches the rule

        :param st fstring: contains the Fortran that we are trying to match.

        :returns: instances of the Classes that have matched if there is a \
                  match or `None` if there is no match.
        :rtype: Optional[Tuple[:py:class:`fparser.two.Fortran2008.Parent_Identifier`, \
                               :py:class:`fparser.two.Fortran2008.Submodule_Name`]]

        """
        from fparser.two.Fortran2008 import Submodule_Name
        # First look for "SUBMODULE"
        name = "SUBMODULE"
        if fstring[: len(name)].upper() != name:
            # the string does not start with SUBMODULE so does not
            # match
            return None
        # "SUBMODULE is found so strip it out and split the remaining
        # line by parenthesis
        splitline = splitparen(fstring[len(name) :].lstrip())
        # We expect 2 entries, the first being parent_identifier with
        # brackets and the second submodule_name. However for some
        # reason we get an additional empty 1st entry when using
        # splitline
        if len(splitline) != 3:
            # format is not ( parent_identifier ) submodule_name
            return None
        spurious = splitline[0]
        parent_id_brackets = splitline[1]
        submodule_name = splitline[2]
        if spurious:
            # this should be empty
            return None
        # Make sure the parent identifier contained in splitline[1] is
        # enclosed with round brackets
        if parent_id_brackets[0] != "(":
            return None
        if parent_id_brackets[-1] != ")":
            return None
        parent_id = parent_id_brackets[1:-1].lstrip().rstrip()
        # Format is OK from this Class' perspective. Pass on
        # parent_identifier and submodule name to appropriate classes
        return Parent_Identifier(parent_id), Submodule_Name(submodule_name)

    def tostr(self):
        """return the fortran representation of this object"""
        # return self.string  # this returns the original code
        return f"SUBMODULE ({self.items[0]}) {self.items[1]}"

    def get_name(self):  # C1114
        """Fortran 2008 constraint C1114
        return the submodule name. This is used by the base class to check
        whether the submodule name matches the name used for the end
        submodule statement if one is provided.

        :return: the name of the submodule stored in a Name class
        :return type: :py:class:`fparser.two.Fortran2003.Name`
        """
        return self.items[1]


class End_Submodule_Stmt(EndStmtBase):  # R1119
    """
    Fortran 2008 rule R1119
    end-submodule-stmt is END [ SUBMODULE [ submodule-name ] ]

    """

    subclass_names = []
    use_names = ["Submodule_Name"]

    @staticmethod
    def match(fstring):
        """Check whether the input matches the rule

        param string fstring : contains the Fortran that we are trying
        to match

        :return: instances of the Classes that have matched if there
        is a match or `None` if there is no match

        """
        from fparser.two.Fortran2008 import Submodule_Name
        return EndStmtBase.match("SUBMODULE", Submodule_Name, fstring)

    def get_name(self):  # C1114
        """Fortran 2008 constraint C1114 return the submodule name as
        specified by the end submodule statement or `None` if one is
        not specified. This is used by the base class to check whether
        this name matches the submodule name.

        :return: the name of the submodule stored in a Name class
        :return type: :py:class:`fparser.two.Fortran2003.Name` or `None`

        """
        return self.items[1]


class Parent_Identifier(Base):  # R1118 (C1113)
    """Fortran 2008 rule R1118
    parent-identifier is ancestor-module-name [ : parent-submodule-name ]

    C1113 The ancestor-module-name shall be the name of a nonintrinsic
    module; the parent-submodule name shall be the name of a
    descendant of that module.
    This constraint can not be tested by fparser in general as the
    module or submodule may be in a different file. We therefore do
    not check this constraint in fparser.

    """

    use_names = ["Ancestor_Module_Name", "Parent_SubModule_Name"]

    @staticmethod
    def match(fstring):
        """Check whether the input matches the rule

        param string fstring : contains the Fortran that we are trying
        to match

        :return: instances of the Classes that have matched if there
        is a match or `None` if there is no match

        """
        from fparser.two.Fortran2008 import Ancestor_Module_Name, Parent_SubModule_Name
        split_string = fstring.split(":")
        len_split_string = len(split_string)
        lhs_name = split_string[0].lstrip().rstrip()
        if len_split_string == 1:
            return Ancestor_Module_Name(lhs_name), None
        if len_split_string == 2:
            rhs_name = split_string[1].lstrip().rstrip()
            return Ancestor_Module_Name(lhs_name), Parent_SubModule_Name(rhs_name)
        # we expect at most one ':' in our input so the match fails
        return None

    def tostr(self):
        """return the fortran representation of this object"""
        # return self.string  # this returns the original code
        if self.items[1]:
            return f"{self.items[0]}:{self.items[1]}"
        return str(self.items[0])


class Open_Stmt(Open_Stmt_2003):  # R904
    """
    Fortran2008 Rule R904.

    open-stmt is OPEN ( connect-spec-list )

    """

    subclass_names = []
    use_names = ["Connect_Spec_List"]

    @staticmethod
    def match(string):
        """
        Attempts to match the supplied string as an Open_Stmt.

        :param str string: the string to attempt to match.

        :returns: a new Open_Stmt object if the match is successful, None otherwise.
        :rtype: Optional[:py:class:`fparser.two.Fortran2008.Open_Stmt]

        """
        # The Connect_Spec_List class is generated automatically
        # by code at the end of this module
        from fparser.two.Fortran2008 import Connect_Spec_List
        obj = CALLBase.match("OPEN", Connect_Spec_List, string, require_rhs=True)
        if not obj:
            return None

        # Apply constraints now that we have the full Connect_Spec_List.
        have_unit = False
        have_newunit = False
        connect_specs = []
        spec_list = obj[1].children
        for spec in spec_list:
            if spec.children[0] in connect_specs:
                # C903 - no specifier can appear more than once.
                return None
            connect_specs.append(spec.children[0])
            if spec.children[0] == "UNIT":
                have_unit = True
            elif spec.children[0] == "NEWUNIT":
                have_newunit = True
            if have_unit and have_newunit:
                # C906 - cannot have both UNIT and NEWUNIT
                return None
        if not (have_unit or have_newunit):
            # C904 - a file unit number must be specified.
            return None
        return obj


class Connect_Spec(Connect_Spec_2003):
    """
    Fortran2008 rule R905.

    connect-spec is [ UNIT = ] file-unit-number
                     or ACCESS = scalar-default-char-expr
                     or ACTION = scalar-default-char-expr
                     or ASYNCHRONOUS = scalar-default-char-expr
                     or BLANK = scalar-default-char-expr
                     or DECIMAL = scalar-default-char-expr
                     or DELIM = scalar-default-char-expr
                     or ENCODING = scalar-default-char-expr
                     or ERR = label
                     or FILE = file-name-expr
                     or FORM = scalar-default-char-expr
                     or IOMSG = iomsg-variable
                     or IOSTAT = scalar-int-variable
                     or NEWUNIT = scalar-int-variable
                     or PAD = scalar-default-char-expr
                     or POSITION = scalar-default-char-expr
                     or RECL = scalar-int-expr
                     or ROUND = scalar-default-char-expr
                     or SIGN = scalar-default-char-expr
                     or STATUS = scalar-default-char-expr

    R906 file-name-expr is scalar-default-char-expr
    R907 iomsg-variable is scalar-default-char-variable
    C903 No specifier shall appear more than once in a given connect-spec-list.

    C904 (R904) If the NEWUNIT= specifier does not appear, a file-unit-number
         shall be specified; if the optional characters UNIT= are omitted, the
         file-unit-number shall be the first item in the connect-spec-list.

    C905 (R904) The label used in the ERR= specifier shall be the statement label
         of a branch target statement that appears in the same inclusive scope as
         the OPEN statement.

    C906 (R904) If a NEWUNIT= specifier appears, a file-unit-number shall not
         appear.

    The constraints listed above are checked for in the Open_Stmt.match() method
    as we don't have access to the full list of Connect_Spec elements here.
    The exceptions are the second part of C904 (un-named file-unit-number must
    be first in the list) and C905: these are not currently checked.

    """

    subclass_names = []
    use_names = [
        "File_Unit_Number",
        "Scalar_Default_Char_Expr",
        "Label",
        "File_Name_Expr",
        "Iomsg_Variable",
        "Scalar_Int_Expr",
        "Scalar_Int_Variable",
    ]

    @staticmethod
    def match(string):
        """
        :param str string: Fortran code to check for a match

        :returns: 2-tuple containing the keyword and value or None if the
                  supplied string is not a match
        :rtype: Optional[Tuple[str, Any]]
        """
        if "=" not in string:
            # The only argument which need not be named is the unit number
            return "UNIT", File_Unit_Number(string)
        # We have a keyword-value pair. Check whether it is valid...
        from fparser.two.Fortran2008 import Scalar_Default_Char_Expr, Scalar_Int_Variable, Scalar_Int_Expr
        for keyword, value in [
            (
                [
                    "ACCESS",
                    "ACTION",
                    "ASYNCHRONOUS",
                    "BLANK",
                    "DECIMAL",
                    "DELIM",
                    "ENCODING",
                    "FORM",
                    "PAD",
                    "POSITION",
                    "ROUND",
                    "SIGN",
                    "STATUS",
                ],
                Scalar_Default_Char_Expr,
            ),
            ("ERR", Label),
            ("FILE", File_Name_Expr),
            ("IOSTAT", Scalar_Int_Variable),
            ("IOMSG", Iomsg_Variable),
            ("RECL", Scalar_Int_Expr),
            ("UNIT", File_Unit_Number),
            ("NEWUNIT", File_Unit_Number),
        ]:
            try:
                obj = KeywordValueBase.match(keyword, value, string, upper_lhs=True)
            except NoMatchError:
                obj = None
            if obj is not None:
                return obj
        return None


class Block_Construct(BlockBase):
    """
    Fortran 2008 Rule 807.

    block-construct is block-stmt
                            [ specification-part ]
                            block
                            end-block-stmt

    TODO #394: Should disallow COMMON, EQUIVALENCE, IMPLICIT, INTENT,
    NAMELIST, OPTIONAL, VALUE, and statement functions (C806) (which are all
    valid members of Specification_Part).
    """

    subclass_names = []
    use_names = [
        "Block_Stmt",
        "Specification_Part",
        "Execution_Part_Construct",
        "End_Block_Stmt",
    ]

    @staticmethod
    def match(reader):
        return BlockBase.match(
            Block_Stmt,
            [Specification_Part, Execution_Part_Construct],
            End_Block_Stmt,
            reader,
            match_names=True,  # C810
            strict_match_names=True,  # C810
        )


class Block_Stmt(StmtBase, WORDClsBase, ScopingRegionMixin):
    """
    Fortran 2008 Rule 808.

    block-stmt is [ block-construct-name : ] BLOCK

    """

    subclass_names = []
    use_names = ["Block_Construct_Name"]
    counter = 0

    @staticmethod
    def match(string):
        """
        Attempts to match the supplied text with this rule.

        :param str string: the text to match.

        :returns: a tuple of the matched node and instance of Counter or \
                  None if there is no match.
        :rtype: Tuple["BLOCK", \
                      :py:class:`fparser.two.Fortran2008.Block_Stmt.Counter`] \
                | NoneType
        """
        found = WORDClsBase.match("BLOCK", None, string)
        if not found:
            return None
        block, _ = found
        # Construct a unique name for this BLOCK (in case it isn't named). We
        # ensure the name is not a valid Fortran name so that it can't clash
        # with any regions named in the code.
        scope_name = f"block:{Block_Stmt.counter}"
        Block_Stmt.counter += 1
        # TODO #397. Ideally we'd have the name associated with the Block
        # Construct here (if any) so that it could be displayed in repr.
        # As it is, repr will show scope_name which will not be the same
        # as any explicit name given to the Block. (This name *is* shown
        # in the repr of the End_Block_Stmt.) This problem is common to
        # other block constructs such as Block_Nonlabel_Do_Construct.
        return block, scope_name

    def get_scope_name(self):
        """
        :returns: the name of this scoping region.
        :rtype: str
        """
        if self.item.name:
            return self.item.name
        return self.items[1]

    def get_start_name(self):
        """
        :returns: the name associated with this Block construct or None.
        :rtype: str | NoneType
        """
        return self.item.name

    def tostr(self):
        """
        :returns: the string representation of this node.
        :rtype: str
        """
        return "BLOCK"


class End_Block_Stmt(EndStmtBase):  # R809
    """
    Fortran 2008 Rule 809.

    end-block-stmt is END BLOCK [ block-construct-name ]

    """

    subclass_names = []
    use_names = ["Block_Construct_Name"]

    @staticmethod
    def match(string):
        """
        :param str string: Fortran code to check for a match

        :return: 2-tuple containing "BLOCK" and, optionally, an associated \
            Name or None if no match.
        :rtype: Optional[Tuple[
            str,
            Optional[:py:class:`fparser.two.Fortran2003.Block_Construct_Name`]]]

        """
        from fparser.two.Fortran2008 import Block_Construct_Name
        return EndStmtBase.match(
            "BLOCK", Block_Construct_Name, string, require_stmt_type=True
        )


class Critical_Construct(BlockBase):
    """
    Fortran 2008 Rule 810.

    critical-construct is critical-stmt
                            block
                            end-critical-stmt

    TODO: Should disallow RETURN (C809) and CYCLE or EXIT to outside block (C811)
    """

    subclass_names = []
    use_names = ["Critical_Stmt", "Execution_Part_Construct", "End_Critical_Stmt"]

    @staticmethod
    def match(reader):
        """
        Attempt to match the supplied content with this Rule.

        :param reader: the fortran file reader containing the line(s)
                      of code that we are trying to match
        :type reader: :py:class:`fparser.common.readfortran.FortranFileReader` \
            | :py:class:`fparser.common.readfortran.FortranStringReader`

        :returns: instance of class that has matched or `None` if no match.
        :rtype: :py:class:`fparser.two.utils.BlockBase` | NoneType

        """
        return BlockBase.match(
            Critical_Stmt,
            [Execution_Part_Construct],
            End_Critical_Stmt,
            reader,
            match_names=True,  # C810
            strict_match_names=True,  # C810
        )


class Critical_Stmt(StmtBase, WORDClsBase):
    """
    Fortran 2008 Rule R811.

    critical-stmt is [ critical-construct-name : ] CRITICAL

    """

    subclass_names = []
    use_names = ["Critical_Construct_Name"]

    @staticmethod
    def match(string):
        """
        Attempts to match the supplied string as a CRITICAL statement.

        :param str string: the string to attempt to match.

        :returns: 2-tuple containing the matched word "CRITICAL" and None or \
                  None if no match.
        :rtype: Tuple[str, NoneType] or NoneType

        """
        return WORDClsBase.match("CRITICAL", None, string)

    def get_start_name(self):
        """
        :returns: the name associated with the start of this CRITICAL region (if any)
        :rtype: str | NoneType
        """
        return self.item.name

    def tostr(self):
        """
        :returns: the string representation of this node.
        :rtype: str
        """
        return "CRITICAL"


class End_Critical_Stmt(EndStmtBase):
    """
    Fortran 2008 Rule 812.

    end-critical-stmt is END CRITICAL [ critical-construct-name ]

    """

    subclass_names = []
    use_names = ["Critical_Construct_Name"]

    @staticmethod
    def match(string):
        """
        :param str string: Fortran code to check for a match

        :returns: 2-tuple containing "CRITICAL" and, optionally, an associated \
            Name or None if there is no match.
        :rtype: Optional[Tuple[
            str, \
            Optional[:py:class:`fparser.two.Fortran2003.Critical_Construct_Name`]]]

        """
        from fparser.two.Fortran2008 import Critical_Construct_Name
        return EndStmtBase.match(
            "CRITICAL", Critical_Construct_Name, string, require_stmt_type=True
        )


class Procedure_Stmt(Procedure_Stmt_2003):  # R1206
    """
    Fortran 2008 Rule 1206.

    procedure-stmt is [ MODULE ] PROCEDURE [ :: ] procedure-name-list

    """

    @staticmethod
    def match(string):
        """:param str string: Fortran code to check for a match

        :returns: 3-tuple containing a boolean indicating whether the \
            optional MODULE keyword is included, a boolean indicating \
            whether the optional '::' is included and a Procedure_Name_List \
            instance, or None if there is no match.
        :rtype: Optional[Tuple[ \
            bool, bool, \
            :py:class:`fparser.two.Fortran2003.Procedure_Name_List`]]]

        """
        from fparser.two.Fortran2008 import Procedure_Name_List
        line = string.lstrip()
        optional_module = None
        if line[:6].upper() == "MODULE":
            line = line[6:].lstrip()
            optional_module = "MODULE"
        if line[:9].upper() != "PROCEDURE":
            return None
        line = line[9:].lstrip()
        optional_colons = None
        if line[:2] == "::":
            line = line[2:].lstrip()
            optional_colons = "::"
        return (Procedure_Name_List(line), optional_module, optional_colons)

    def tostr(self):
        """
        :returns: the string representation of this node.
        :rtype: str
        """
        result = "PROCEDURE"
        if self.items[1]:
            result = f"MODULE {result}"
        if self.items[2]:
            result = f"{result} ::"
        return f"{result} {self.items[0]}"
