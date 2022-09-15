# Modified work Copyright (c) 2018-2022 Science and Technology
# Facilities Council
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
# pylint: disable=exec-used
# pylint: disable=unused-import
from fparser.common.splitline import string_replace_map
from fparser.two import pattern_tools as pattern

from fparser.two.utils import (
    STRINGBase,
    BracketBase,
    WORDClsBase,
    SeparatorBase,
    Type_Declaration_StmtBase,
    StmtBase,
)
from fparser.two.Fortran2003 import (
    EndStmtBase,
    BlockBase,
    SequenceBase,
    Base,
    Specification_Part,
    Stat_Variable,
    Errmsg_Variable,
    Source_Expr,
    KeywordValueBase,
    Module_Subprogram_Part,
    Implicit_Part,
    Implicit_Part_Stmt,
    Declaration_Construct,
    Use_Stmt,
    Import_Stmt,
    Declaration_Type_Spec,
    Entity_Decl_List,
    Component_Decl_List,
    Stop_Code,
)

# Import of F2003 classes that are updated in this standard.
from fparser.two.Fortran2003 import (
    Program_Unit as Program_Unit_2003,
    Attr_Spec as Attr_Spec_2003,
    Alloc_Opt as Alloc_Opt_2003,
    Allocate_Stmt as Allocate_Stmt_2003,
    Type_Declaration_Stmt as Type_Declaration_Stmt_2003,
    Component_Attr_Spec as Component_Attr_Spec_2003,
    Data_Component_Def_Stmt as Data_Component_Def_Stmt_2003,
    Action_Stmt as Action_Stmt_2003,
    Action_Stmt_C201 as Action_Stmt_C201_2003,
    Action_Stmt_C802 as Action_Stmt_C802_2003,
    Action_Stmt_C824 as Action_Stmt_C824_2003,
    If_Stmt as If_Stmt_2003,
    Do_Term_Action_Stmt as Do_Term_Action_Stmt_2003,
    Executable_Construct as Executable_Construct_2003,
    Executable_Construct_C201 as Executable_Construct_C201_2003,
)


class Program_Unit(Program_Unit_2003):  # R202
    """
    Fortran 2008 rule R202
    program-unit is main-program
                    or external-subprogram
                    or module
                    or submodule
                    or block-data

    """

    # Fortran2008 adds the concept of submodules to a program-unit. We
    # therefore extend the Fortran2003 specification
    subclass_names = Program_Unit_2003.subclass_names[:]
    subclass_names.append("Submodule")


class Executable_Construct(Executable_Construct_2003):  # R213
    # pylint: disable=invalid-name
    """
    Fortran 2003 rule R213
    executable-construct is action-stmt
                         or associate-construct
                         or block-construct
                         or case-construct
                         or critical-construct
                         or do-construct
                         or forall-construct
                         or if-construct
                         or select-type-construct
                         or where-construct

    Associated constraints are:

    "C201 (R208) An execution-part shall not contain an end-function-stmt,
          end-mp-subprogram-stmt, end-program-stmt, or end-subroutine-stmt."

    NB: The new block-construct and critical-construct are not yet implemented.
    TODO: Implement missing F2008 executable-construct (#320)

    """
    subclass_names = [
        "Action_Stmt",
        "Associate_Construct",
        "Case_Construct",
        "Do_Construct",
        "Forall_Construct",
        "If_Construct",
        "Select_Type_Construct",
        "Where_Construct",
    ]


class Executable_Construct_C201(Executable_Construct_C201_2003):
    """
    executable-construct-c201 is executable construct.
    This applies C201.
    """

    subclass_names = Executable_Construct.subclass_names[:]
    subclass_names[subclass_names.index("Action_Stmt")] = "Action_Stmt_C201"


class Action_Stmt(Action_Stmt_2003):  # R214
    """
    Fortran 2008 rule R214
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
    Fortran 2008 rule 436
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
        return Type_Declaration_StmtBase.match(
            Declaration_Type_Spec, Component_Attr_Spec_List, Component_Decl_List, string
        )


class Component_Attr_Spec(Component_Attr_Spec_2003):  # R437
    """
    Fortran 2008 rule R437
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
    Fortran 2008 rule 501
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
    Fortran 2008 rule R502
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
    Fortran 2008 rule R509
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
    Fortran 2008 rule R826
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
    Fortran2008 rule R627
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
    Fortran 2008 rule R626
    allocate-stmt is ALLOCATE ( [ type-spec :: ] allocation-list
                                [, alloc-opt-list ] )

    The implementation of this rule simply ensures that the Fortran2008 version
    of Alloc_Opt is used.

    """

    subclass_names = []
    use_names = ["Type_Spec", "Allocation_List", "Alloc_Opt_List"]


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
        :type reader: :py:class:`fparser.common.readfortran.FortranFileReader`
                      or
                      :py:class:`fparser.common.readfortran.FortranStringReader`
        :return: `tuple` containing a single `list` which contains
                 instance of the classes that have matched if there is
                 a match or `None` if there is no match

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
    """Fortran 2008 rule R1116
    submodule is submodule-stmt
                 [ specification-part ]
                 [ module-subprogram-part ]
                 end-submodule-stmt

    C1112 A submodule specification-part shall not contain a
    format-stmt, entry-stmt, or stmt-function-stmt.
    This constraint is handled by specialising the Specification_Part
    class

    C1114 If a submodule-name appears in the end-submodule-stmt, it
    shall be identical to the one in the submodule-stmt.
    This constraint is handled by the Base class with the names being
    provided by the 'Submodule_Stmt and 'End_Submodule_Stmt' classes
    via a `get_name` method

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


class Submodule_Stmt(Base):  # R1117
    """
    Fortran 2008 rule R1117
    submodule-stmt is SUBMODULE ( parent-identifier ) submodule-name

    """

    subclass_names = []
    use_names = ["Submodule_Name", "Parent_Identifier"]

    @staticmethod
    def match(fstring):
        """Check whether the input matches the rule

        param string fstring : contains the Fortran that we are trying
        to match

        :return: instances of the Classes that have matched if there
        is a match or `None` if there is no match

        """
        # First look for "SUBMODULE"
        name = "SUBMODULE"
        if fstring[: len(name)].upper() != name:
            # the string does not start with SUBMODULE so does not
            # match
            return None
        # "SUBMODULE is found so strip it out and split the remaining
        # line by parenthesis
        from fparser.common.splitline import splitparen

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
        return "SUBMODULE ({0}) {1}".format(self.items[0], self.items[1])

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
        split_string = fstring.split(":")
        len_split_string = len(split_string)
        lhs_name = split_string[0].lstrip().rstrip()
        if len_split_string == 1:
            return Ancestor_Module_Name(lhs_name), None
        elif len_split_string == 2:
            rhs_name = split_string[1].lstrip().rstrip()
            return Ancestor_Module_Name(lhs_name), Parent_SubModule_Name(rhs_name)
        # we expect at most one ':' in our input so the match fails
        return None

    def tostr(self):
        """return the fortran representation of this object"""
        # return self.string  # this returns the original code
        if self.items[1]:
            return "{0}:{1}".format(self.items[0], self.items[1])
        return str(self.items[0])


#
# GENERATE Scalar_, _List, _Name CLASSES
#


ClassType = type(Base)
_names = dir()
for clsname in _names:
    cls = eval(clsname)
    if not (
        isinstance(cls, ClassType)
        and issubclass(cls, Base)
        and not cls.__name__.endswith("Base")
    ):
        continue

    names = getattr(cls, "subclass_names", []) + getattr(cls, "use_names", [])
    for n in names:
        if n in _names:
            continue
        if n.endswith("_List"):
            _names.append(n)
            n = n[:-5]
            # Generate 'list' class
            exec(
                """\
class %s_List(SequenceBase):
    subclass_names = [\'%s\']
    use_names = []
    @staticmethod
    def match(string): return SequenceBase.match(r\',\', %s, string)
"""
                % (n, n, n)
            )
        elif n.endswith("_Name"):
            _names.append(n)
            n = n[:-5]
            exec(
                """\
class %s_Name(Base):
    subclass_names = [\'Name\']
"""
                % (n)
            )
        elif n.startswith("Scalar_"):
            _names.append(n)
            n = n[7:]
            exec(
                """\
class Scalar_%s(Base):
    subclass_names = [\'%s\']
"""
                % (n, n)
            )
