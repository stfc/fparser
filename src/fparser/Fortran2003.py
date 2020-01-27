#!/usr/bin/env python

# Modified work Copyright (c) 2017-2020 Science and Technology
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

"""Fortran 2003 Syntax Rules.
"""
# Original author: Pearu Peterson <pearu@cens.ioc.ee>
# First version created: Oct 2006

import re
import logging
from fparser.common.splitline import string_replace_map
from fparser.two import pattern_tools as pattern
from fparser.common.readfortran import FortranReaderBase

from fparser.two.utils import Base, BlockBase, StringBase, WORDClsBase, \
    NumberBase, STRINGBase, BracketBase, StmtBase, EndStmtBase, \
    BinaryOpBase, Type_Declaration_StmtBase, CALLBase, CallBase, \
    KeywordValueBase, SeparatorBase, SequenceBase, UnaryOpBase, walk
from fparser.two.utils import NoMatchError, FortranSyntaxError, \
    InternalSyntaxError, InternalError, show_result, py2_encode_list_items

#
# SECTION  1
#

# R101: <xyz-list> = <xyz> [ , <xyz> ]...
# R102: <xyz-name> = <name>
# R103: <scalar-xyz> = <xyz>

#
# SECTION  2
#


class Comment(Base):
    '''
    Represents a Fortran Comment.
    '''
    subclass_names = []

    @show_result
    def __new__(cls, string, parent_cls=None):
        """
        Create a new Comment instance.

        :param type cls: the class of object to create.
        :param string: (source of) Fortran string to parse.
        :type string: str or :py:class:`FortranReaderBase`
        :param parent_cls: the parent class of this object.
        :type parent_cls: :py:type:`type`

        """
        from fparser.common import readfortran

        if isinstance(string, readfortran.Comment):
            # We were after a comment and we got a comment. Construct
            # one manually to avoid recursively calling this __new__
            # method again...
            obj = object.__new__(cls)
            obj.init(string)
            return obj
        elif isinstance(string, FortranReaderBase):
            reader = string
            item = reader.get_item()
            if item is None:
                return
            if isinstance(item, readfortran.Comment):
                # This effectively recursively calls this routine
                return Comment(item)
            else:
                # We didn't get a comment so put the item back in the FIFO
                reader.put_item(item)
                return
        else:
            # We didn't get a comment
            return

    def init(self, comment):
        '''
        Initialise this Comment

        :param  comment: The comment object produced by the reader
        :type comment: :py:class:`readfortran.Comment`
        '''
        self.items = [comment.comment]
        self.item = comment

    def tostr(self):
        '''
        :returns: this comment as a string.
        :rtype: :py:class:`six.text_type`
        '''
        import six
        return six.text_type(self.items[0])

    def restore_reader(self, reader):
        '''
        Undo the read of this comment by putting its content back
        into the reader (which has a FIFO buffer)

        :param reader: the reader instance to return the comment to
        :type reader: :py:class:`fparser.readfortran.FortranReaderBase`
        '''
        reader.put_item(self.item)


def add_comments_includes(content, reader):
    '''Creates comment and/or include objects and adds them to the content
    list. Comment and/or include objects are added until a line that
    is not a comment or include is found.

    :param content: a `list` of matched objects. Any matched comments \
                    or includes in this routine are added to this list.
    :param reader: the fortran file reader containing the line(s) \
                   of code that we are trying to match
    :type reader: :py:class:`fparser.common.readfortran.FortranFileReader` \
                  or \
                  :py:class:`fparser.common.readfortran.FortranStringReader`

    '''
    obj = Comment(reader)
    obj = Include_Stmt(reader) if not obj else obj
    while obj:
        content.append(obj)
        obj = Comment(reader)
        obj = Include_Stmt(reader) if not obj else obj


class Program(BlockBase):  # R201
    '''
    Fortran 2003 rule R201
    program is program-unit
               [ program-unit ] ...

    '''
    subclass_names = []
    use_names = ['Program_Unit']

    @show_result
    def __new__(cls, string):
        '''Wrapper around base class __new__ to catch an internal NoMatchError
        exception and raise it as an external FortranSyntaxError exception.

        :param type cls: the class of object to create
        :param string: (source of) Fortran string to parse
        :type string: :py:class:`FortranReaderBase`
        :raises FortranSyntaxError: if the code is not valid Fortran

        '''
        # pylint: disable=unused-argument
        try:
            return Base.__new__(cls, string)
        except NoMatchError:
            # At the moment there is no useful information provided by
            # NoMatchError so we pass on an empty string.
            raise FortranSyntaxError(string, "")
        except InternalSyntaxError as excinfo:
            # InternalSyntaxError is used when a syntax error has been
            # found in a rule that does not have access to the reader
            # object. This is then re-raised here as a
            # FortranSyntaxError, adding the reader object (which
            # provides line number information).
            raise FortranSyntaxError(string, excinfo)

    @staticmethod
    def match(reader):
        '''Implements the matching for a Program. Whilst the rule looks like
        it could make use of BlockBase, the parser must not match if an
        optional program_unit has a syntax error, which the BlockBase
        match implementation does not do.

        :param reader: the fortran file reader containing the line(s)
                       of code that we are trying to match
        :type reader: :py:class:`fparser.common.readfortran.FortranFileReader`
                      or
                      :py:class:`fparser.common.readfortran.FortranStringReader`
        :return: `tuple` containing a single `list` which contains
                 instance of the classes that have matched if there is
                 a match or `None` if there is no match

        '''
        content = []
        add_comments_includes(content, reader)
        try:
            while True:
                obj = Program_Unit(reader)
                content.append(obj)
                add_comments_includes(content, reader)
                # cause a StopIteration exception if there are no more lines
                next_line = reader.next()
                # put the line back in the case where there are more lines
                reader.put_item(next_line)
        except NoMatchError:
            # Found a syntax error for this rule. Now look to match
            # (via Main_Program0) with a program containing no program
            # statement as this is optional in Fortran.
            #
            return BlockBase.match(Main_Program0, [], None, reader)
        except StopIteration:
            # Reader has no more lines.
            pass
        return content,


class Include_Filename(StringBase):  # pylint: disable=invalid-name

    '''Implements the matching of a filename from an include statement.'''
    # There are no other classes. This is a simple string match.
    subclass_names = []

    @staticmethod
    def match(string):
        '''Match the string with the regular expression file_name in the
        pattern_tools file. The only content that is not accepted is
        an empty string or white space at the start or end of the
        string.

        :param str string: the string to match with the pattern rule.
        :return: a tuple of size 1 containing a string with the \
        matched name if there is a match, or None if there is not.
        :rtype: (str) or NoneType

        '''
        return StringBase.match(pattern.file_name, string)


class Include_Stmt(Base):  # pylint: disable=invalid-name

    '''Implements the matching of a Fortran include statement. There is no
    rule for this as the compiler is expected to inline any content
    from an include statement when one is found. However, for a parser
    it can make sense to represent an include statement in a parse
    tree.

    include-stmt is INCLUDE ['filename' or "filename"]

    '''
    use_names = ['Include_Filename']

    @staticmethod
    def match(string):
        '''Implements the matching for an include statement.

        :param str string: the string to match with as an include \
        statement.
        :returns: a tuple of size 1 containing an Include_Filename \
        object with the matched filename if there is a match, or None \
        if there is not.
        :rtype: (:py:class:`fparser.two.Fortran2003.Include_Filename`) \
        or NoneType

        '''
        if not string:
            return None
        line = string.strip()
        if line[:7].upper() != 'INCLUDE':
            # The line does not start with the include token and/or the line
            # is too short.
            return None
        rhs = line[7:].strip()
        if not rhs:
            # There is no content after the include token
            return None
        if len(rhs) < 3:
            # The content after the include token is too short to be
            # valid (it must at least contain quotes and one
            # character.
            return None
        if not ((rhs[0] == "'" and rhs[-1] == "'") or
                (rhs[0] == '"' and rhs[-1] == '"')):
            # The filename should be surrounded by single or double
            # quotes but this is not the case.
            return None
        # Remove the quotes.
        file_name = rhs[1:-1]
        # Pass the potential filename to the relevant class.
        name = Include_Filename(file_name)
        if not name:
            raise InternalError(
                "Fotran2003.py:Include_Stmt:match Include_Filename should "
                "never return None or an empty name")
        return (name,)

    def tostr(self):
        '''
        :return: this include_stmt as a string
        :rtype: str
        '''

        return ("INCLUDE '{0}'".format(self.items[0]))


class Program_Unit(Base):  # R202
    """
:F03R:`202`::
    <program-unit> = <main-program>
                     | <external-subprogram>
                     | <module>
                     | <block-data>
    """
    subclass_names = ['Comment', 'Main_Program', 'External_Subprogram',
                      'Module', 'Block_Data']


class External_Subprogram(Base):  # R203
    """
:F03R:`203`::
    <external-subprogram> = <function-subprogram>
                            | <subroutine-subprogram>
    """
    subclass_names = ['Comment', 'Function_Subprogram',
                      'Subroutine_Subprogram']


class Specification_Part(BlockBase):  # R204
    """
:F03R:`204`::
    <specification-part> = [ <use-stmt> ]...
                             [ <import-stmt> ]...
                             [ <implicit-part> ]
                             [ <declaration-construct> ]...
    """
    subclass_names = []
    use_names = ['Use_Stmt', 'Import_Stmt', 'Implicit_Part',
                 'Declaration_Construct']

    @staticmethod
    def match(reader):
        return BlockBase.match(None, [Use_Stmt, Import_Stmt,
                                      Implicit_Part, Declaration_Construct],
                               None, reader)


class Implicit_Part(BlockBase):  # R205
    """
:F03R:`205`::
    <implicit-part> = [ <implicit-part-stmt> ]...
                        <implicit-stmt>
    """
    subclass_names = []
    use_names = ['Implicit_Part_Stmt', 'Implicit_Stmt']

    @staticmethod
    def match(reader):
        return BlockBase.match(None, [Implicit_Part_Stmt], None, reader)


class Implicit_Part_Stmt(Base):  # R206
    """
:F03R:`206`::
    <implicit-part-stmt> = <implicit-stmt>
                           | <parameter-stmt>
                           | <format-stmt>
                           | <entry-stmt>
    """
    subclass_names = ['Comment', 'Implicit_Stmt', 'Parameter_Stmt',
                      'Format_Stmt', 'Entry_Stmt']


class Declaration_Construct(Base):  # R207
    '''Fortran 2003 rule R207

    declaration-construct is derived-type-def
                           or entry-stmt
                           or enum-def
                           or format-stmt
                           or interface-block
                           or parameter-stmt
                           or procedure-declaration-stmt
                           or specification-stmt
                           or type-declaration-stmt
                           or stmt-function-stmt

    Note, stmt-function-stmt is not currently matched.

    '''
    # Commented out Stmt_Function_Stmt as it can falsely match an
    # access to an array or function. Reintroducing statement
    # functions is captured in issue #202.

    #                   'Type_Declaration_Stmt', 'Stmt_Function_Stmt']
    subclass_names = ['Derived_Type_Def', 'Entry_Stmt', 'Enum_Def',
                      'Format_Stmt', 'Interface_Block', 'Parameter_Stmt',
                      'Procedure_Declaration_Stmt', 'Specification_Stmt',
                      'Type_Declaration_Stmt']


class Execution_Part(BlockBase):  # R208
    """:F03R:`208`::
    <execution-part> = <executable-construct>
                       | [ <execution-part-construct> ]...

    <execution-part> shall not contain <end-function-stmt>,
    <end-program-stmt>, <end-subroutine-stmt>

    """
    subclass_names = []
    use_names = ['Executable_Construct_C201', 'Execution_Part_Construct_C201']

    def match(string):
        return BlockBase.match(Executable_Construct_C201,
                               [Execution_Part_Construct_C201],
                               None, string)
    match = staticmethod(match)


class Execution_Part_Construct(Base):  # R209
    """
    <execution-part-construct> = <executable-construct>
                                 | <format-stmt>
                                 | <entry-stmt>
                                 | <data-stmt>
    """
    subclass_names = ['Comment', 'Executable_Construct', 'Format_Stmt',
                      'Entry_Stmt', 'Data_Stmt']


class Execution_Part_Construct_C201(Base):
    subclass_names = ['Comment', 'Executable_Construct_C201', 'Format_Stmt',
                      'Entry_Stmt', 'Data_Stmt']


class Internal_Subprogram_Part(BlockBase):  # R210
    """
    <internal-subprogram-part> = <contains-stmt>
                                   <internal-subprogram>
                                   [ <internal-subprogram> ]...
    """
    subclass_names = []
    use_names = ['Contains_Stmt', 'Internal_Subprogram']

    @staticmethod
    def match(reader):
        return BlockBase.match(Contains_Stmt, [Internal_Subprogram],
                               None, reader)


class Internal_Subprogram(Base):  # R211
    """
    <internal-subprogram> = <function-subprogram>
                            | <subroutine-subprogram>
    """
    subclass_names = ['Function_Subprogram', 'Subroutine_Subprogram']


class Specification_Stmt(Base):  # R212
    """
    <specification-stmt> = <access-stmt>
                           | <allocatable-stmt>
                           | <asynchronous-stmt>
                           | <bind-stmt>
                           | <common-stmt>
                           | <data-stmt>
                           | <dimension-stmt>
                           | <equivalence-stmt>
                           | <external-stmt>
                           | <intent-stmt>
                           | <intrinsic-stmt>
                           | <namelist-stmt>
                           | <optional-stmt>
                           | <pointer-stmt>
                           | <protected-stmt>
                           | <save-stmt>
                           | <target-stmt>
                           | <volatile-stmt>
                           | <value-stmt>
    """
    subclass_names = [
        'Access_Stmt', 'Allocatable_Stmt', 'Asynchronous_Stmt', 'Bind_Stmt',
        'Comment', 'Common_Stmt', 'Data_Stmt', 'Dimension_Stmt',
        'Equivalence_Stmt',
        'External_Stmt', 'Intent_Stmt', 'Intrinsic_Stmt', 'Namelist_Stmt',
        'Optional_Stmt', 'Pointer_Stmt', 'Cray_Pointer_Stmt',
        'Protected_Stmt', 'Save_Stmt', 'Target_Stmt', 'Volatile_Stmt',
        'Value_Stmt']


class Executable_Construct(Base):  # R213
    # pylint: disable=invalid-name
    '''
    Fortran 2003 rule R213
    executable-construct is action-stmt
                         or associate-construct
                         or case-construct
                         or do-construct
                         or forall-construct
                         or if-construct
                         or select-type-construct
                         or where-construct

    '''
    subclass_names = [
        'Action_Stmt', 'Associate_Construct', 'Case_Construct',
        'Do_Construct', 'Forall_Construct', 'If_Construct',
        'Select_Type_Construct', 'Where_Construct']


class Executable_Construct_C201(Base):
    subclass_names = Executable_Construct.subclass_names[:]
    subclass_names[subclass_names.index('Action_Stmt')] = 'Action_Stmt_C201'


class Action_Stmt(Base):  # R214
    """
    <action-stmt> = <allocate-stmt>
                    | <assignment-stmt>
                    | <backspace-stmt>
                    | <call-stmt>
                    | <close-stmt>
                    | <continue-stmt>
                    | <cycle-stmt>
                    | <deallocate-stmt>
                    | <endfile-stmt>
                    | <end-function-stmt>
                    | <end-program-stmt>
                    | <end-subroutine-stmt>
                    | <exit-stmt>
                    | <flush-stmt>
                    | <forall-stmt>
                    | <goto-stmt>
                    | <if-stmt>
                    | <inquire-stmt>
                    | <nullify-stmt>
                    | <open-stmt>
                    | <pointer-assignment-stmt>
                    | <print-stmt>
                    | <read-stmt>
                    | <return-stmt>
                    | <rewind-stmt>
                    | <stop-stmt>
                    | <wait-stmt>
                    | <where-stmt>
                    | <write-stmt>
                    | <arithmetic-if-stmt>
                    | <computed-goto-stmt>
    """
    subclass_names = ['Allocate_Stmt', 'Assignment_Stmt', 'Backspace_Stmt',
                      'Call_Stmt', 'Close_Stmt', 'Comment', 'Continue_Stmt',
                      'Cycle_Stmt', 'Deallocate_Stmt', 'Endfile_Stmt',
                      'End_Function_Stmt', 'End_Subroutine_Stmt', 'Exit_Stmt',
                      'Flush_Stmt', 'Forall_Stmt', 'Goto_Stmt', 'If_Stmt',
                      'Inquire_Stmt', 'Nullify_Stmt', 'Open_Stmt',
                      'Pointer_Assignment_Stmt', 'Print_Stmt', 'Read_Stmt',
                      'Return_Stmt', 'Rewind_Stmt', 'Stop_Stmt', 'Wait_Stmt',
                      'Where_Stmt', 'Write_Stmt', 'Arithmetic_If_Stmt',
                      'Computed_Goto_Stmt']


class Action_Stmt_C201(Base):
    """
    <action-stmt-c201> = <action-stmt>
    C201 is applied.
    """
    subclass_names = Action_Stmt.subclass_names[:]
    subclass_names.remove('End_Function_Stmt')
    subclass_names.remove('End_Subroutine_Stmt')
    # subclass_names.remove('End_Program_Stmt')


class Action_Stmt_C802(Base):
    """
    <action-stmt-c802> = <action-stmt>
    C802 is applied.
    """
    subclass_names = Action_Stmt.subclass_names[:]
    subclass_names.remove('End_Function_Stmt')
    subclass_names.remove('End_Subroutine_Stmt')
    subclass_names.remove('If_Stmt')


class Action_Stmt_C824(Base):
    """
    <action-stmt-c824> = <action-stmt>
    C824 is applied.
    """
    subclass_names = Action_Stmt.subclass_names[:]
    subclass_names.remove('End_Function_Stmt')
    subclass_names.remove('End_Subroutine_Stmt')
    subclass_names.remove('Continue_Stmt')
    subclass_names.remove('Goto_Stmt')
    subclass_names.remove('Return_Stmt')
    subclass_names.remove('Stop_Stmt')
    subclass_names.remove('Exit_Stmt')
    subclass_names.remove('Cycle_Stmt')
    subclass_names.remove('Arithmetic_If_Stmt')


class Keyword(Base):  # R215
    """
    <keyword> = <name>
    """
    subclass_names = ['Name']

#
# SECTION  3
#

# R301: <character> = <alphanumeric-character> | <special-character>
# R302: <alphanumeric-character> = <letter> | <digit> | <underscore>
# R303: <underscore> = _


class Name(StringBase):  # R304
    '''
    Fortran 2003 rule R304
    name is letter [ alphanumeric_character ]...

    '''
    # There are no other classes. This is a simple string match.
    subclass_names = []

    @staticmethod
    def match(string):
        '''Match the string with the regular expression abs_name in the
        pattern_tools file.

        :param str string: the string to match with the pattern rule.
        :return: a tuple of size 1 containing a string with the \
        matched name if there is a match, or None if there is not.
        :rtype: (str) or None

        '''
        return StringBase.match(pattern.abs_name, string.strip())


class Constant(Base):  # R305
    """
    <constant> = <literal-constant>
                 | <named-constant>
    """
    subclass_names = ['Literal_Constant', 'Named_Constant']


class Literal_Constant(Base):  # R306
    """
    <literal-constant> = <int-literal-constant>
                         | <real-literal-constant>
                         | <complex-literal-constant>
                         | <logical-literal-constant>
                         | <char-literal-constant>
                         | <boz-literal-constant>
    """
    subclass_names = [
        'Int_Literal_Constant', 'Real_Literal_Constant',
        'Complex_Literal_Constant', 'Logical_Literal_Constant',
        'Char_Literal_Constant', 'Boz_Literal_Constant']


class Named_Constant(Base):  # R307
    """
    <named-constant> = <name>
    """
    subclass_names = ['Name']


class Int_Constant(Base):  # R308
    """
    <int-constant> = <constant>
    """
    subclass_names = ['Constant']


class Char_Constant(Base):  # R309
    """
    <char-constant> = <constant>
    """
    subclass_names = ['Constant']

# R310: <intrinsic-operator> = <power-op> | <mult-op> | <add-op> |
# <concat-op> | <rel-op> | <not-op> | <and-op> | <or-op> | <equiv-op>
# Rule 310 is defined in pattern_tools.py. As it is only used by Rule
# 312 it does not need to be defined explicitly as a class. Note, it
# could be created as a class if it were useful for code
# manipulation. We could additionally create each of the operators
# themselves as classes.


class Defined_Operator(Base):  # pylint: disable=invalid-name
    '''Fortran 2003 rule R311
    R311 defined-operator is defined-unary-op
                          or defined-binary-op
                          or extended-intrinsic-op

    Note, defined-operator is defined in pattern_tools.py so could be
    called directly via a stringbase match. However, the defined unary
    and binary op rules have constraints which would not be checked if
    we did this.

    Note, whilst we subclass for both Defined Unary and Binary ops,
    the match is the same so we will only ever match with the first
    (so the second is not really necessary here). This is OK from a
    parsing point of view as they both return a Defined_Op class, so
    are identical from the parsers point of view.

    '''
    subclass_names = ['Defined_Unary_Op', 'Defined_Binary_Op',
                      'Extended_Intrinsic_Op']


class Extended_Intrinsic_Op(StringBase):  # pylint: disable=invalid-name
    '''Fortran 2003 rule R312
    R312 extended-intrinsic-op is intrinsic-operator

    Note, extended-intrinsic-op is only ever used by R311 and is
    defined in pattern_tools.py so could be matched directly in the
    Defined_Operator class (by changing it to STRINGBase and moving
    the match in this class into the Defined_Operator class). This
    would mean that this class would not be required. However, the
    parse tree would then not have the concept of an
    Extended_Intrinsic_Op which might be useful for code manipulation
    tools.

    '''
    @staticmethod
    def match(string):
        '''Implements the matching for the extended-intrinsic-op
        rule. Matches the string with the regular expression
        extended_intrinsic_operator in the pattern_tools file.

        :param str string: the string to match with the pattern rule.
        :return: a tuple of size 1 containing a string with the \
        matched name if there is a match, or None if there is not.
        :rtype: (str) or None

        '''
        return StringBase.match(pattern.extended_intrinsic_operator, string)


class Label(StringBase):  # R313
    """
::
    <label> = <digit> [ <digit> [ <digit> [ <digit> [ <digit> ] ] ] ]

Attributes
----------
string : str
    """
    subclass_names = []

    @staticmethod
    def match(string):
        return StringBase.match(pattern.abs_label, string)

    def __int__(self):
        return int(self.string)

#
# SECTION  4
#


class Type_Spec(Base):  # R401
    """
    <type-spec> = <intrinsic-type-spec>
                  | <derived-type-spec>
    """
    subclass_names = ['Intrinsic_Type_Spec', 'Derived_Type_Spec']


class Type_Param_Value(StringBase):  # R402
    """
    <type-param-value> = <scalar-int-expr>
                       | *
                       | :
    """
    subclass_names = ['Scalar_Int_Expr']
    use_names = []

    def match(string):
        return StringBase.match(['*', ':'], string)
    match = staticmethod(match)


class Intrinsic_Type_Spec(WORDClsBase):  # R403
    """
    <intrinsic-type-spec> = INTEGER [ <kind-selector> ]
                            | REAL [ <kind-selector> ]
                            | DOUBLE COMPLEX
                            | COMPLEX [ <kind-selector> ]
                            | CHARACTER [ <char-selector> ]
                            | LOGICAL [ <kind-selector> ]
    Extensions:
                            | DOUBLE PRECISION
                            | BYTE
    """
    subclass_names = []
    use_names = ['Kind_Selector', 'Char_Selector']

    def match(string):
        for w, cls in [('INTEGER', Kind_Selector),
                       ('REAL', Kind_Selector),
                       ('COMPLEX', Kind_Selector),
                       ('LOGICAL', Kind_Selector),
                       ('CHARACTER', Char_Selector),
                       (pattern.abs_double_complex_name, None),
                       (pattern.abs_double_precision_name, None),
                       ('BYTE', None)]:
            try:
                obj = WORDClsBase.match(w, cls, string)
            except NoMatchError:
                obj = None
            if obj is not None:
                return obj
        return
    match = staticmethod(match)


class Kind_Selector(Base):  # R404
    '''
    Fortran 2003 rule R404
    kind-selector is ( [ KIND = ] scalar-int-initialization-expr )
    A non-standard extension is also supported here:
                      | * char-length

    There is an associated constraint that we can't enforce in fparser:

    'C404 (R404) The value of scalar-int-initialization-expr shall be
    nonnegative and shall specify a representation method that
    exists on the processor.'

    '''
    subclass_names = []
    use_names = ['Char_Length', 'Scalar_Int_Initialization_Expr']

    @staticmethod
    def match(string):
        '''Implements the matching for a Kind_Selector.

        :param str string: a string containing the code to match
        :return: `None` if there is no match, otherwise a `tuple` of \
        size 3 containing a '(', a single `list` which contains an \
        instance of classes that have matched and a ')', or a `tuple` \
        of size 2 containing a '*' and an instance of classes that \
        have matched.
        :rtype: `NoneType` or ( str, [ MatchedClasses ], str) or ( \
        str, :py:class:`fparser.two.Fortran2003.Char_Length`)

        :raises InternalError: if None is passed instead of a \
        string. The parent rule should not pass None and the logic in \
        this routine relies on a valid string.

        :raises InternalError: if the string passed is <=1 characters \
        long. The parent rule passing this string should ensure the \
        string is at least 2 characters long and the logic in this \
        routine relies on this. The reason there is a minimum of two \
        is that the pattern '*n' where 'n' is a number is the smallest \
        valid pattern. The other valid pattern must have at least a \
        name with one character surrounded by brackets e.g. '(x)' so \
        should be at least 3 characters long.

        '''
        if string is None:
            raise InternalError(
                "String argument in class Kind_Selector method match() "
                "is None.")
        if len(string) <= 1:
            raise InternalError(
                "String argument '{0}' in class Kind_Selector method "
                "match() is too short to be valid.".format(string))

        # remove any leading or trailing white space
        string = string.strip()

        if string[0]+string[-1] != '()':
            # must be the '*n' extension
            if not string.startswith('*'):
                return None
            return '*', Char_Length(string[1:].lstrip())
        # remove left and right brackets and subsequently any leading
        # or trailing spaces
        string = string[1:-1].strip()
        # check for optional 'kind='
        if len(string) > 5:
            # string is long enough to potentially contain 'kind=...'
            if string[:4].upper() == 'KIND' and string[4:].lstrip()[0] == "=":
                # found 'kind=' so strip it out, including any leading spaces
                string = string[4:].lstrip()[1:].lstrip()
        return '(', Scalar_Int_Initialization_Expr(string), ')'

    def tostr(self):
        '''
        :return: this kind_selector as a string
        :rtype: str
        '''
        if len(self.items) == 2:
            result = "{0[0]}{0[1]}".format(self.items)
        elif len(self.items) == 3:
            result = "{0[0]}KIND = {0[1]}{0[2]}".format(self.items)
        else:
            raise InternalError(
                "Class Kind_Selector method tostr() has '{0}' items, "
                "but expecting 2 or 3.".format(len(self.items)))
        return result


class Signed_Int_Literal_Constant(NumberBase):  # R405
    """
    <signed-int-literal-constant> = [ <sign> ] <int-literal-constant>
    """
    # never used because sign is included in pattern
    subclass_names = ['Int_Literal_Constant']

    def match(string):
        return NumberBase.match(
            pattern.abs_signed_int_literal_constant_named, string)
    match = staticmethod(match)


class Int_Literal_Constant(NumberBase):  # R406
    """
    <int-literal-constant> = <digit-string> [ _ <kind-param> ]
    """
    subclass_names = []

    def match(string):
        return NumberBase.match(
            pattern.abs_int_literal_constant_named, string)
    match = staticmethod(match)


class Digit_String(NumberBase):
    """
    <digit-string> = <digit> [ <digit> ]...
    """
    subclass_names = []

    def match(string):
        return NumberBase.match(pattern.abs_digit_string_named, string)
    match = staticmethod(match)

# R407: <kind-param> = <digit-string> | <scalar-int-constant-name>
# R408: <signed-digit-string> = [ <sign> ] <digit-string>
# R409: <digit-string> = <digit> [ <digit> ]...
# R410: <sign> = + | -


class Boz_Literal_Constant(Base):  # R411
    """
    <boz-literal-constant> = <binary-constant>
                             | <octal-constant>
                             | <hex-constant>
    """
    subclass_names = ['Binary_Constant', 'Octal_Constant', 'Hex_Constant']


class Binary_Constant(STRINGBase):  # R412
    """
    <binary-constant> = B ' <digit> [ <digit> ]... '
                        | B \" <digit> [ <digit> ]... \"
    """
    subclass_names = []

    def match(string):
        return STRINGBase.match(pattern.abs_binary_constant, string)
    match = staticmethod(match)


class Octal_Constant(STRINGBase):  # R413
    """
    <octal-constant> = O ' <digit> [ <digit> ]... '
                       | O \" <digit> [ <digit> ]... \"
    """
    subclass_names = []

    def match(string):
        return STRINGBase.match(pattern.abs_octal_constant, string)
    match = staticmethod(match)


class Hex_Constant(STRINGBase):  # R414
    """
    <hex-constant> = Z ' <digit> [ <digit> ]... '
                     | Z \" <digit> [ <digit> ]... \"
    """
    subclass_names = []

    def match(string):
        return STRINGBase.match(pattern.abs_hex_constant, string)
    match = staticmethod(match)

# R415: <hex-digit> = <digit> | A | B | C | D | E | F


class Signed_Real_Literal_Constant(NumberBase):  # R416
    """
    <signed-real-literal-constant> = [ <sign> ] <real-literal-constant>
    """
    subclass_names = ['Real_Literal_Constant']  # never used

    def match(string):
        return NumberBase.match(
            pattern.abs_signed_real_literal_constant_named, string)
    match = staticmethod(match)


class Real_Literal_Constant(NumberBase):  # R417
    """
    """
    subclass_names = []

    def match(string):
        return NumberBase.match(
            pattern.abs_real_literal_constant_named, string)
    match = staticmethod(match)

# R418: <significand> = <digit-string> . [ <digit-string> ]  | . <digit-string>
# R419: <exponent-letter> = E | D
# R420: <exponent> = <signed-digit-string>


class Complex_Literal_Constant(Base):  # R421
    """
    <complex-literal-constant> = ( <real-part>, <imag-part> )
    """
    subclass_names = []
    use_names = ['Real_Part', 'Imag_Part']

    def match(string):
        if not string or string[0]+string[-1] != '()':
            return
        if not pattern.abs_complex_literal_constant.match(string):
            return
        r, i = string[1:-1].split(',')
        return Real_Part(r.strip()), Imag_Part(i.strip())
    match = staticmethod(match)

    def tostr(self):
        return '(%s, %s)' % tuple(self.items)


class Real_Part(Base):  # R422
    """
    <real-part> = <signed-int-literal-constant>
                  | <signed-real-literal-constant>
                  | <named-constant>
    """
    subclass_names = ['Signed_Int_Literal_Constant',
                      'Signed_Real_Literal_Constant',
                      'Named_Constant']


class Imag_Part(Base):  # R423
    """
    <imag-part> = <real-part>
    """
    subclass_names = ['Signed_Int_Literal_Constant',
                      'Signed_Real_Literal_Constant',
                      'Named_Constant']


class Char_Selector(Base):  # R424
    """
    <char-selector> = <length-selector>
                      | ( LEN = <type-param-value> ,
                         KIND = <scalar-int-initialization-expr> )
                      | ( <type-param-value> ,
                         [ KIND = ] <scalar-int-initialization-expr> )
                      | ( KIND = <scalar-int-initialization-expr>
                        [ , LEN = <type-param-value> ] )
    """
    subclass_names = ['Length_Selector']
    use_names = ['Type_Param_Value', 'Scalar_Int_Initialization_Expr']

    def match(string):
        if string[0] + string[-1] != '()':
            return
        line, repmap = string_replace_map(string[1:-1].strip())
        if line[:3].upper() == 'LEN' and line[3:].lstrip().startswith('='):
            line = line[3:].lstrip()
            line = line[1:].lstrip()
            i = line.find(',')
            if i == -1:
                return
            v = line[:i].rstrip()
            line = line[i+1:].lstrip()
            if line[:4].upper() != 'KIND':
                return
            line = line[4:].lstrip()
            if not line.startswith('='):
                return
            line = line[1:].lstrip()
            v = repmap(v)
            line = repmap(line)
            return Type_Param_Value(v), Scalar_Int_Initialization_Expr(line)
        elif line[:4].upper() == 'KIND' and line[4:].lstrip().startswith('='):
            line = line[4:].lstrip()
            line = line[1:].lstrip()
            i = line.find(',')
            if i == -1:
                return None, Scalar_Int_Initialization_Expr(line)
            v = line[i+1:].lstrip()
            line = line[:i].rstrip()
            if v[:3].upper() != 'LEN':
                return
            v = v[3:].lstrip()
            if not v.startswith('='):
                return
            v = v[1:].lstrip()
            return Type_Param_Value(v), Scalar_Int_Initialization_Expr(line)
        else:
            i = line.find(',')
            if i == -1:
                return
            v = line[:i].rstrip()
            line = line[i+1:].lstrip()
            if line[:4].upper() == 'KIND' and \
               line[4:].lstrip().startswith('='):
                line = line[4:].lstrip()
                line = line[1:].lstrip()
            return Type_Param_Value(v), Scalar_Int_Initialization_Expr(line)
        return
    match = staticmethod(match)

    def tostr(self):
        if self.items[0] is None:
            return '(KIND = %s)' % (self.items[1])
        return '(LEN = %s, KIND = %s)' % (self.items[0], self.items[1])


class Length_Selector(Base):  # R425
    """
    <length -selector> = ( [ LEN = ] <type-param-value> )
                        | * <char-length> [ , ]
    """
    subclass_names = []
    use_names = ['Type_Param_Value', 'Char_Length']

    def match(string):
        if string[0]+string[-1] == '()':
            line = string[1:-1].strip()
            if line[:3].upper() == 'LEN' and line[3:].lstrip().startswith('='):
                line = line[3:].lstrip()
                line = line[1:].lstrip()
            return '(', Type_Param_Value(line), ')'
        if not string.startswith('*'):
            return
        line = string[1:].lstrip()
        if string[-1] == ',':
            line = line[:-1].rstrip()
        return '*', Char_Length(line)
    match = staticmethod(match)

    def tostr(self):
        if len(self.items) == 2:
            return '%s%s' % tuple(self.items)
        return '%sLEN = %s%s' % tuple(self.items)


class Char_Length(BracketBase):  # R426
    """
    <char-length> = ( <type-param-value> )
                    | <scalar-int-literal-constant>
    """
    subclass_names = ['Scalar_Int_Literal_Constant']
    use_names = ['Type_Param_Value']

    def match(string): return BracketBase.match('()', Type_Param_Value, string)
    match = staticmethod(match)


class Char_Literal_Constant(Base):  # pylint: disable=invalid-name
    '''
    Fortran 2003 rule R427

    char-literal-constant is [ kind-param _ ] ' rep-char '
                          or [ kind-param _ ] " rep-char "
    '''
    subclass_names = []
    rep = pattern.char_literal_constant

    @staticmethod
    def match(string):
        '''Implements the matching for a Char_Literal_Constant. For example

        "hello"
        'hello'
        nondefaultcharset_"nondefaultchars"

        There is an associated constraint C422: "The value of
        kind-param shall specify a representation method that exists
        on the processor." However, this cannot be validated by
        fparser so no checks are performed.

        :param str string: a string containing the code to match.
        :return: `None` if there is no match, otherwise a `tuple` of
                 size 2 containing the character constant and the kind
                 value as strings.
        :rtype: `NoneType` or (`str`, `NoneType`) or (`str`, `str`)

        '''
        if not string:
            return None
        strip_string = string.strip()
        if not strip_string:
            # the string is empty or only contains blank space
            return None
        if strip_string[-1] not in '"\'':
            return None
        if strip_string[-1] == '"':
            abs_a_n_char_literal_constant_named = \
                    pattern.abs_a_n_char_literal_constant_named2
        else:
            abs_a_n_char_literal_constant_named = \
                    pattern.abs_a_n_char_literal_constant_named1
        line, repmap = string_replace_map(strip_string)
        match = abs_a_n_char_literal_constant_named.match(line)
        if not match:
            return None
        kind_param = match.group('kind_param')
        line = match.group('value')
        line = repmap(line)
        return line, kind_param

    def tostr(self):
        '''
        :return: this Char_Literal_Constant as a string.
        :rtype: str

        :raises InternalError: if the internal items list variable is \
                not the expected size.
        :raises InternalError: if the first element of the internal \
                items list is None or is an empty string.
        '''
        import six

        if len(self.items) != 2:
            raise InternalError(
                "Class Char_Literal_Constant method tostr() has '{0}' items, "
                "but expecting 2.".format(len(self.items)))
        if not self.items[0]:
            # items[0] is the value of the constant so is required. It
            # also can't be empty as it needs to include the
            # surrounding quotes to be valid
            raise InternalError(
                "Class Char_Literal_Constant method tostr(). 'Items' entry 0 "
                "should not be empty")
        if six.PY2:
            # In Python2 we must return a byte str and the contents of this
            # string may include non-ASCII characters
            char_str = self.items[0].encode('utf-8')
        else:
            char_str = str(self.items[0])
        if not self.items[1]:
            return char_str
        # The character constant has a kind specifier
        if six.PY2:
            kind_str = self.items[1].encode('utf-8')
            return kind_str + "_".encode('utf-8') + char_str
        kind_str = str(self.items[1])
        return "{0}_{1}".format(kind_str, char_str)


class Logical_Literal_Constant(NumberBase):  # R428
    """
    <logical-literal-constant> = .TRUE. [ _ <kind-param> ]
                                 | .FALSE. [ _ <kind-param> ]
    """
    subclass_names = []

    def match(string):
        return NumberBase.match(pattern.abs_logical_literal_constant_named,
                                string)
    match = staticmethod(match)


class Derived_Type_Def(BlockBase):  # R429
    """
    <derived-type-def> = <derived-type-stmt>
                           [ <type-param-def-stmt> ]...
                           [ <private-or-sequence> ]...
                           [ <component-part> ]
                           [ <type-bound-procedure-part> ]
                           <end-type-stmt>
    """
    subclass_names = []
    use_names = ['Derived_Type_Stmt', 'Type_Param_Def_Stmt',
                 'Private_Or_Sequence', 'Component_Part',
                 'Type_Bound_Procedure_Part', 'End_Type_Stmt']

    @staticmethod
    def match(reader):
        return BlockBase.match(Derived_Type_Stmt,
                               [Type_Param_Def_Stmt, Private_Or_Sequence,
                                Component_Part, Type_Bound_Procedure_Part],
                               End_Type_Stmt, reader,
                               match_names=True  # C431
                               )


class Derived_Type_Stmt(StmtBase):  # pylint: disable=invalid-name
    '''
    Fortran 2003 rule R430

    derived-type-stmt is TYPE [ [ , type-attr-spec-list ] :: ]
                         type-name [ ( type-param-name-list ) ]

    '''
    subclass_names = []
    use_names = ['Type_Attr_Spec_List', 'Type_Name', 'Type_Param_Name_List']

    @staticmethod
    def match(string):
        '''Implements the matching for a Derived Type Statement.

        :param str string: a string containing the code to match
        :return: `None` if there is no match, otherwise a `tuple` of \
                 size 3 containing an `Attribute_Spec_List` (or `None` if \
                 there isn't one), the name of the type (in a `Name` \
                 class) and a `Parameter_Name_List` (or `None` is there \
                 isn't one).
        :rtype: ( `Type_Attr_Spec_List` or `None`, `Name`, \
                  `Type_Param_Name_List` or `None` ) or `None`

        '''
        string_strip = string.strip()
        if string_strip[:4].upper() != 'TYPE':
            return None
        line = string_strip[4:].lstrip()
        position = line.find('::')
        attr_specs = None
        if position != -1:
            if line.startswith(','):
                lstrip = line[1:position].strip()
                if not lstrip:
                    # There is no content after the "," and before the
                    # "::"
                    return None
                attr_specs = Type_Attr_Spec_List(lstrip)
            elif line[:position].strip():
                # There is invalid content between and 'TYPE' and '::'
                return None
            line = line[position+2:].lstrip()
        match = pattern.name.match(line)
        if not match:
            # There is no content after the "TYPE" or the "::"
            return None
        name = Type_Name(match.group())
        line = line[match.end():].lstrip()
        if not line:
            return attr_specs, name, None
        if line[0] + line[-1] != '()':
            return None
        return attr_specs, name, Type_Param_Name_List(line[1:-1].strip())

    def tostr(self):
        '''
        :return: this derived type statement as a string
        :rtype: str
        :raises InternalError: if items array is not the expected size
        :raises InternalError: if items array[1] has no content

        '''
        if len(self.items) != 3:
            raise InternalError(
                "Derived_Type_Stmt.tostr(). 'items' should be of size 3 but "
                "found '{0}'.".format(len(self.items)))
        if not self.items[1]:
            raise InternalError(
                "Derived_Type_Stmt.tostr(). 'items[1]' should be a Name "
                "instance containing the derived type name but it is empty")
        string = 'TYPE'
        if self.items[0]:
            string += ", {0} :: {1}".format(self.items[0], self.items[1])
        else:
            string += " :: {0}".format(self.items[1])
        if self.items[2]:
            string += "({0})".format(self.items[2])
        return string

    def get_start_name(self):
        '''
        :return: this derived type statement's name as a string
        :rtype: str

        '''
        return self.items[1].string


class Type_Name(Name):  # C424
    """
    <type-name> = <name>
    <type-name> shall not be DOUBLEPRECISION or the name of intrinsic type
    """
    subclass_names = []
    use_names = []

    def match(string):
        if pattern.abs_intrinsic_type_name.match(string):
            return
        return Name.match(string)
    match = staticmethod(match)


class Type_Attr_Spec(Base):  # R431
    """
    <type-attr-spec> = <access-spec>
                       | EXTENDS ( <parent-type-name> )
                       | ABSTRACT
                       | BIND (C)
    """
    subclass_names = ['Access_Spec', 'Language_Binding_Spec'][:-1]
    use_names = ['Parent_Type_Name']

    @staticmethod
    def match(string):
        if len(string) == 8 and string.upper() == 'ABSTRACT':
            return 'ABSTRACT', None
        if string[:4].upper() == 'BIND':
            line = string[4:].lstrip()
            if not line or line[0]+line[-1] != '()':
                return
            line = line[1:-1].strip()
            if line.upper() == 'C':
                return 'BIND', 'C'
        elif string[:7].upper() == 'EXTENDS':
            line = string[7:].lstrip()
            if not line or line[0]+line[-1] != '()':
                return
            return 'EXTENDS', Parent_Type_Name(line[1:-1].strip())

    def tostr(self):
        if self.items[1] is None:
            return '%s' % (self.items[0])
        return '%s(%s)' % (self.items)


class Private_Or_Sequence(Base):  # R432
    """
    <private-or-sequence> = <private-components-stmt>
                            | <sequence-stmt>
    """
    subclass_names = ['Private_Components_Stmt', 'Sequence_Stmt']


class End_Type_Stmt(EndStmtBase):  # R433
    """
    <end-type-stmt> = END TYPE [ <type-name> ]
    """
    subclass_names = []
    use_names = ['Type_Name']

    @staticmethod
    def match(string):
        return EndStmtBase.match('TYPE', Type_Name, string,
                                 require_stmt_type=True)


class Sequence_Stmt(STRINGBase):  # R434
    """
    <sequence-stmt> = SEQUENCE
    """
    subclass_names = []

    @staticmethod
    def match(string):
        return STRINGBase.match('SEQUENCE', string)


class Type_Param_Def_Stmt(StmtBase):  # R435
    """
    <type-param-def-stmt> = INTEGER [ <kind-selector> ] ,
        <type-param-attr-spec> :: <type-param-decl-list>
    """
    subclass_names = []
    use_names = ['Kind_Selector', 'Type_Param_Attr_Spec',
                 'Type_Param_Decl_List']

    def match(string):
        if string[:7].upper() != 'INTEGER':
            return
        line, repmap = string_replace_map(string[7:].lstrip())
        if not line:
            return
        i = line.find(',')
        if i == -1:
            return
        kind_selector = repmap(line[:i].rstrip()) or None
        line = repmap(line[i+1:].lstrip())
        i = line.find('::')
        if i == -1:
            return
        l1 = line[:i].rstrip()
        l2 = line[i+2:].lstrip()
        if not l1 or not l2:
            return
        if kind_selector:
            kind_selector = Kind_Selector(kind_selector)
        return kind_selector, Type_Param_Attr_Spec(l1), \
            Type_Param_Decl_List(l2)
    match = staticmethod(match)

    def tostr(self):
        s = 'INTEGER'
        if self.items[0] is not None:
            s += '%s, %s :: %s' % tuple(self.items)
        else:
            s += ', %s :: %s' % tuple(self.items[1:])
        return s


class Type_Param_Decl(BinaryOpBase):  # R436
    """
    <type-param-decl> = <type-param-name>
        [ = <scalar-int-initialization-expr> ]
    """
    subclass_names = ['Type_Param_Name']
    use_names = ['Scalar_Int_Initialization_Expr']

    def match(string):
        if '=' not in string:
            return
        lhs, rhs = string.split('=', 1)
        lhs = lhs.rstrip()
        rhs = rhs.lstrip()
        if not lhs or not rhs:
            return
        return Type_Param_Name(lhs), '=', Scalar_Int_Initialization_Expr(rhs)
    match = staticmethod(match)


class Type_Param_Attr_Spec(STRINGBase):  # R437
    """
    <type-param-attr-spec> = KIND
                             | LEN
    """
    subclass_names = []

    def match(string):
        return STRINGBase.match(['KIND', 'LEN'], string)
    match = staticmethod(match)


class Component_Part(BlockBase):  # R438
    """
    <component-part> is [ <component-def-stmt> ]...
    """
    subclass_names = []
    use_names = ['Component_Def_Stmt']

    def match(reader):
        content = []
        while 1:
            try:
                obj = Component_Def_Stmt(reader)
            except NoMatchError:
                obj = None
            if obj is None:
                break
            content.append(obj)
        if content:
            return content,
        return
    match = staticmethod(match)

    def tofortran(self, tab='', isfix=None):
        '''
        Converts this node (and all children) into Fortran.

        :param str tab: white space to prefix to output.
        :param bool isfix: whether or not to generate fixed-format output.

        :returns: Fortran code.
        :rtype: str

        '''
        mylist = []
        for item in self.content:
            mylist.append(item.tofortran(tab=tab, isfix=isfix))
        py2_encode_list_items(mylist)
        return '\n'.join(mylist)


class Component_Def_Stmt(Base):  # R439
    """
    <component-def-stmt> is <data-component-def-stmt>
                         or <proc-component-def-stmt>
    """
    subclass_names = ['Data_Component_Def_Stmt', 'Proc_Component_Def_Stmt']


class Data_Component_Def_Stmt(Type_Declaration_StmtBase):  # R440
    """
    <data-component-def-stmt> is <declaration-type-spec> [
             [ , <component-attr-spec-list> ] :: ] <component-decl-list>
    """
    subclass_names = []
    use_names = ['Declaration_Type_Spec', 'Component_Attr_Spec_List',
                 'Component_Decl_List']

    @staticmethod
    def match(string):
        return Type_Declaration_StmtBase.match(
            Declaration_Type_Spec, Component_Attr_Spec_List,
            Component_Decl_List, string)


class Dimension_Component_Attr_Spec(CALLBase):
    """
    <dimension-component-attr-spec> = DIMENSION ( <component-array-spec> )
    """
    subclass_names = []
    use_names = ['Component_Array_Spec']

    def match(string):
        return CALLBase.match('DIMENSION', Component_Array_Spec, string)
    match = staticmethod(match)


class Component_Attr_Spec(STRINGBase):  # R441
    """
    <component-attr-spec> = POINTER
                            | DIMENSION ( <component-array-spec> )
                            | ALLOCATABLE
                            | <access-spec>
    """
    subclass_names = ['Access_Spec', 'Dimension_Component_Attr_Spec']
    use_names = []

    @staticmethod
    def match(string):
        return STRINGBase.match(['POINTER', 'ALLOCATABLE'], string)


class Component_Decl(Base):  # R442
    """
    <component-decl> = <component-name> [ ( <component-array-spec> ) ]
        [ * <char-length> ] [ <component-initialization> ]
    """
    subclass_names = []
    use_names = ['Component_Name', 'Component_Array_Spec',
                 'Char_Length', 'Component_Initialization']

    def match(string):
        m = pattern.name.match(string)
        if m is None:
            return
        name = Component_Name(m.group())
        newline = string[m.end():].lstrip()
        if not newline:
            return name, None, None, None
        array_spec = None
        char_length = None
        init = None
        if newline.startswith('('):
            line, repmap = string_replace_map(newline)
            i = line.find(')')
            if i == -1:
                return
            array_spec = Component_Array_Spec(repmap(line[1:i].strip()))
            newline = repmap(line[i+1:].lstrip())
        if newline.startswith('*'):
            line, repmap = string_replace_map(newline)
            i = line.find('=')
            if i != -1:
                char_length = repmap(line[1:i].strip())
                newline = repmap(newline[i:].lstrip())
            else:
                char_length = repmap(newline[1:].strip())
                newline = ''
            char_length = Char_Length(char_length)
        if newline.startswith('='):
            init = Component_Initialization(newline)
        else:
            assert newline == '', repr(newline)
        return name, array_spec, char_length, init
    match = staticmethod(match)

    def tostr(self):
        s = str(self.items[0])
        if self.items[1] is not None:
            s += '(' + str(self.items[1]) + ')'
        if self.items[2] is not None:
            s += '*' + str(self.items[2])
        if self.items[3] is not None:
            s += ' ' + str(self.items[3])
        return s


class Component_Array_Spec(Base):  # R443
    """
    <component-array-spec> = <explicit-shape-spec-list>
                             | <deferred-shape-spec-list>
    """
    subclass_names = ['Explicit_Shape_Spec_List', 'Deferred_Shape_Spec_List']


class Component_Initialization(Base):  # R444
    """
    <component-initialization> =  = <initialization-expr>
                                 | => <null-init>
    """
    subclass_names = []
    use_names = ['Initialization_Expr', 'Null_Init']

    def match(string):
        if string.startswith('=>'):
            return '=>', Null_Init(string[2:].lstrip())
        if string.startswith('='):
            return '=', Initialization_Expr(string[1:].lstrip())
        return
    match = staticmethod(match)

    def tostr(self):
        return '%s %s' % tuple(self.items)


class Proc_Component_Def_Stmt(StmtBase):  # R445
    """
    <proc-component-def-stmt> is PROCEDURE ( [ <proc-interface> ] )
        , <proc-component-attr-spec-list> :: <proc-decl-list>

    where

        proc-component-attr-spec is POINTER
                                 or PASS [ (arg-name) ]
                                 or NOPASS
                                 or access-spec

    The standard specifies the following constraints:

    "C448 The same proc-component-attr-spec shall not appear more than once
          in a given proc-component-def-stmt." Not checked by fparser - #232.

    "C449 POINTER shall appear in each proc-component-attr-spec-list."

    "C450 If the procedure pointer component has an implicit interface or
          has no arguments, NOPASS shall be specified." Not checked by
          fparser - #232.

    "C451 If PASS (arg-name) appears, the interface shall have a dummy argument
          named arg-name." Not checked by fparser - #232.

    "C452 PASS and NOPASS shall not both appear in the same
          proc-component-attr-spec-list." Not checked by fparser - #232.
    """
    subclass_names = []
    use_names = ['Proc_Interface', 'Proc_Component_Attr_Spec_List',
                 'Proc_Decl_List']

    @staticmethod
    def match(string):
        '''
        Attempts to match the supplied string with the pattern for a
        declaration of a procedure part of a component.

        :param str string: the string to test for a match.

        :returns: None (if no match) or a tuple consisting of the procedure \
                  interface, the list of attributes and a list of procedure \
                  names or None.
        :rtype: NoneType or \
           (:py:class:`fparser.two.Fortran2003.Proc_Interface`, \
            :py:class:`fparser.two.Fortran2003.Proc_Component_Attr_Spec_List`,\
            :py:class:`fparser.two.Fortran2003.Proc_Decl_List`)
        '''
        if string[:9].upper() != 'PROCEDURE':
            return None
        line, repmap = string_replace_map(string[9:].lstrip())
        if not line.startswith('('):
            return None
        idx = line.find(')')
        if idx == -1:
            return None
        pinterface = repmap(line[:idx+1])[1:-1].strip() or None
        if pinterface:
            pinterface = Proc_Interface(pinterface)
        line = line[idx+1:].lstrip()
        if not line.startswith(','):
            return None
        line = line[1:].strip()
        idx = line.find('::')
        if idx == -1:
            return None
        attr_spec_list = Proc_Component_Attr_Spec_List(
            repmap(line[:idx].rstrip()))
        # C449 POINTER must be present in the attribute list
        if Proc_Component_Attr_Spec('POINTER') not in attr_spec_list.items:
            return None
        return pinterface, attr_spec_list, Proc_Decl_List(
            repmap(line[idx+2:].lstrip()))

    def tostr(self):
        if self.items[0] is not None:
            return 'PROCEDURE(%s), %s :: %s' % (self.items)
        return 'PROCEDURE(), %s :: %s' % (self.items[1:])


class Proc_Component_PASS_Arg_Name(CALLBase):
    """
    <proc-component-PASS-arg-name> = PASS ( <arg-name> )
    """
    subclass_names = []
    use_names = ['Arg_Name']

    def match(string):
        return CALLBase.match('PASS', Arg_Name, string)
    match = staticmethod(match)


class Proc_Component_Attr_Spec(STRINGBase):  # R446
    """
    <proc-component-attr-spec> = POINTER
                                 | PASS [ ( <arg-name> ) ]
                                 | NOPASS
                                 | <access-spec>
    """
    subclass_names = ['Access_Spec', 'Proc_Component_PASS_Arg_Name']

    def match(string):
        return STRINGBase.match(['POINTER', 'PASS', 'NOPASS'],
                                string.upper())
    match = staticmethod(match)


class Private_Components_Stmt(STRINGBase):  # pylint: disable=invalid-name
    '''
    :F03R:`447`::

    Fortran 2003 rule R447
    that specifies support for private components statement
    within a derived type.

    <private-components-stmt> = PRIVATE
    '''
    subclass_names = []

    @staticmethod
    def match(string):
        '''
        :param str string: Fortran code to check for a match
        :return: keyword  "PRIVATE" or None if no match is found
        :rtype: str or None
        '''
        return StringBase.match('PRIVATE', string.upper())


class Type_Bound_Procedure_Part(BlockBase):  # pylint: disable=invalid-name
    '''
    :F03R:`448`::

    Fortran 2003 rule R448
    that specifies the type-bound procedure part of a derived type.

    <type-bound-procedure-part> = <contains-stmt>
                                      [ <binding-private-stmt> ]
                                      <proc-binding-stmt>
                                      [ <proc-binding-stmt> ]...
    '''
    subclass_names = []
    use_names = ['Contains_Stmt', 'Binding_Private_Stmt', 'Proc_Binding_Stmt']

    @staticmethod
    def match(reader):
        '''
        :param reader: the Fortran reader containing the line(s) of code \
        that we are trying to match
        :type reader: :py:class:`fparser.common.readfortran.FortranReaderBase`
        :return: code block containing instances of the classes that match \
                 the syntax of the type-bound procedure part of a derived type.
        :rtype: ([`Contains_Stmt`, `Specific_Binding`, `str`, `Name`, \
                  `Name`]) or `None`
        '''
        return BlockBase.match(Contains_Stmt,
                               [Binding_Private_Stmt, Proc_Binding_Stmt],
                               None, reader)


class Binding_Private_Stmt(StmtBase,
                           STRINGBase):  # pylint: disable=invalid-name
    '''
    :F03R:`449`::

    Fortran 2003 rule R449
    for binding private statement within the type-bound procedure
    part of a derived type.

    <binding-private-stmt> = PRIVATE
    '''
    subclass_names = []

    @staticmethod
    def match(string):
        '''
        :param str string: Fortran code to check for a match
        :return: keyword  "PRIVATE" or None if no match is found
        :rtype: str or None
        '''
        return StringBase.match('PRIVATE', string.upper())


class Proc_Binding_Stmt(Base):  # pylint: disable=invalid-name
    '''
    :F03R:`450`::

    Fortran 2003 rule R450
    that specifies procedure binding for the type-bound procedures
    within a derived type.

    <proc-binding-stmt> = <specific-binding>
                          | <generic-binding>
                          | <final-binding>
    '''
    subclass_names = ['Specific_Binding', 'Generic_Binding', 'Final_Binding']


class Specific_Binding(StmtBase):  # pylint: disable=invalid-name
    ''':F03R:`451`::

    Fortran 2003 rule R451
    that specifies syntax of specific binding for a type-bound
    procedure within a derived type.

    <specific-binding> = PROCEDURE [ ( <interface-name> ) ] [
        [ , <binding-attr-list> ] :: ] <binding-name> [ => <procedure-name> ]

    The following are associated constraints:

    "C456 (R451) If => procedure-name appears, the double-colon
    separator shall appear."

    "C457 (R451) If => procedure-name appears, interface-name shall not
    appear."

    "C458 (R451) The procedure-name shall be the name of an accessible
    module procedure or an external procedure that has an explicit
    interface." Note, this is not checked by fparser.

    '''
    subclass_names = []
    use_names = ['Interface_Name', 'Binding_Attr_List',
                 'Binding_Name', 'Procedure_Name']

    @staticmethod
    def match(string):
        '''
        :param str string: Fortran code to check for a match
        :return: 5-tuple containing strings and instances of the classes
                 describing a specific type-bound procedure (optional
                 interface name, optional binding attribute list,
                 optional double colon delimiter, mandatory binding
                 name and optional procedure name)
        :rtype: 5-tuple of objects (1 mandatory and 4 optional)
        '''
        # Remove any leading, trailing spaces.
        string_strip = string.strip()
        if string_strip[:9].upper() != 'PROCEDURE':
            # There is no 'PROCEDURE' statement.
            return None
        if len(string_strip) < 11:
            # Line is too short to be valid
            return None
        # Remember whether there was a space after the keyword
        space_after = False
        if string_strip[9] == " ":
            space_after = True
        line = string_strip[9:].lstrip()
        # Find optional interface name if it exists.
        iname = None
        if line.startswith('('):
            index = line.find(')')
            if index == -1:
                # Left brace has no corresponding right brace
                return None
            iname = Interface_Name(line[1:index].strip())
            line = line[index+1:].lstrip()
        # Look for optional double colon and binding attribute list.
        dcolon = None
        mylist = None
        index = line.find('::')
        if index != -1:
            dcolon = '::'
            if line.startswith(','):
                mylist = Binding_Attr_List(line[1:index].strip())
            elif line[:index].strip():
                # There is content between procedure (with optional
                # interface) and :: that does not start with a ','
                # which is a syntax error.
                return None
            line = line[index+2:].lstrip()
        if not iname and not dcolon:
            # there is no interface name or double colon between the
            # keyword and the binding name. Therefore we expect a
            # space between the two.
            if not space_after:
                # No space was found so return to indicate an
                # error.
                return None
        # Find optional procedure name.
        index = line.find('=>')
        pname = None
        if index != -1:
            pname = Procedure_Name(line[index+2:].lstrip())
            line = line[:index].rstrip()
            if not dcolon:
                # Constraint C456 requires '::' if there is a
                # procedure-name.
                return None
        if iname and pname:
            # Constraint C457 disallows interface-name if there is a
            # procedure-name.
            return None
        # Return class arguments.
        return iname, mylist, dcolon, Binding_Name(line), pname

    def tostr(self):
        '''
        :return: parsed representation of a specific type-bound procedure
        :rtype: `str`

        '''
        if len(self.items) != 5:
            raise InternalError(
                "Class Specific_Binding method tostr() has '{0}' items, "
                "but expecting 5.".format(len(self.items)))

        stmt = "PROCEDURE"
        # Add optional interface name
        if self.items[0]:
            stmt += "({0})".format(self.items[0])
        # Add optional double colon and binding attribute list
        # (if the list is present)
        if self.items[1] and self.items[2]:
            stmt += ", {0} {1}".format(self.items[1], self.items[2])
        elif not self.items[1] and self.items[2]:
            stmt += " {0}".format(self.items[2])
        # Add mandatory Binding_Name
        stmt += " {0}".format(self.items[3])
        # Add optional procedure name
        if self.items[4]:
            stmt += " => {0}".format(self.items[4])
        return stmt


class Binding_PASS_Arg_Name(CALLBase):
    # pylint: disable=invalid-name
    '''
    :F03R:`453_help`::

    Fortran 2003 helper rule (for R453)
    that specifies syntax of passed-object dummy argument for a
    specific type-bound procedure.

    <binding-PASS-arg-name> = PASS ( <arg-name> )
    '''
    subclass_names = []
    use_names = ['Arg_Name']

    @staticmethod
    def match(string):
        '''
        :param str string: Fortran code to check for a match
        :return: keyword  "PASS" with the name of a passed-object
                 dummy argument or nothing if no match is found
        :rtype: str
        '''
        return CALLBase.match('PASS', Arg_Name, string)


class Generic_Binding(StmtBase):
    # pylint: disable=invalid-name
    '''
    :F03R:`452`::

    Fortran 2003 rule R452
    that specifies syntax of generic binding for a type-bound
    procedure within a derived type.

    <generic-binding> = GENERIC [ , <access-spec> ] ::
        <generic-spec> => <binding-name-list>
    '''
    subclass_names = []
    use_names = ['Access_Spec', 'Generic_Spec', 'Binding_Name_List']

    @staticmethod
    def match(string):
        '''
        :param str string: Fortran code to check for a match
        :return: 3-tuple containing strings and instances of the
                 classes describing a generic type-bound procedure
                 (optional access specifier, mandatory generic
                 identifier and mandatory binding name list)
        :rtype: 3-tuple of objects (2 mandatory and 1 optional)
        '''
        # Incorrect 'GENERIC' statement
        if string[:7].upper() != 'GENERIC':
            return
        line = string[7:].lstrip()
        i = line.find('::')
        # No mandatory double colon
        if i == -1:
            return
        aspec = None
        # Return optional access specifier (PRIVATE or PUBLIC)
        if line.startswith(','):
            aspec = Access_Spec(line[1:i].strip())
        line = line[i+2:].lstrip()
        i = line.find('=>')
        if i == -1:
            return
        # Return mandatory Generic_Spec and Binding_Name_List
        return aspec, Generic_Spec(line[:i].rstrip()), \
            Binding_Name_List(line[i+3:].lstrip())

    def tostr(self):
        '''
        :return: parsed representation of a "GENERIC" type-bound procedure
        :rtype: str
        '''
        if self.items[0] is None:
            return 'GENERIC :: %s => %s' % (self.items[1:])
        return 'GENERIC, %s :: %s => %s' % (self.items)


class Binding_Attr(STRINGBase):  # pylint: disable=invalid-name

    '''
    :F03R:`453`::

    Fortran 2003 rule R453
    that specifies syntax of allowed binding attributes for a
    specific type-bound procedure binding.

    <binding-attr> = PASS [ ( <arg-name> ) ]
                     | NOPASS
                     | NON_OVERRIDABLE
                     | DEFERRED
                     | <access-spec>
    '''
    subclass_names = ['Access_Spec', 'Binding_PASS_Arg_Name']

    @staticmethod
    def match(string):
        '''
        :return: keywords for allowed binding attributes or
                 nothing if no match is found
        :rtype: str
        '''
        return STRINGBase.match(['PASS', 'NOPASS',
                                 'NON_OVERRIDABLE', 'DEFERRED'], string)


class Final_Binding(StmtBase, WORDClsBase):  # pylint: disable=invalid-name

    '''
    :F03R:`454`::

    Fortran 2003 rule R454
    that specifies syntax of final binding for a type-bound
    procedure within a derived type.

    <final-binding> = FINAL [ :: ] <final-subroutine-name-list>
    '''
    subclass_names = []
    use_names = ['Final_Subroutine_Name_List']

    @staticmethod
    def match(string):
        '''
        :return: keyword  "FINAL" with the list of "FINAL" type-bound
                 procedures or nothing if no match is found
        :rtype: str
        '''
        return WORDClsBase.match(
            'FINAL', Final_Subroutine_Name_List, string, colons=True,
            require_cls=True)

    # String representation with optional double colons included
    tostr = WORDClsBase.tostr_a


class Derived_Type_Spec(CallBase):  # R455
    """
    <derived-type-spec> = <type-name> [ ( <type-param-spec-list> ) ]
    """
    subclass_names = ['Type_Name']
    use_names = ['Type_Param_Spec_List']

    def match(string):
        return CallBase.match(Type_Name, Type_Param_Spec_List, string)
    match = staticmethod(match)


class Type_Param_Spec(KeywordValueBase):  # R456
    """
    <type-param-spec> = [ <keyword> = ] <type-param-value>
    """
    subclass_names = ['Type_Param_Value']
    use_names = ['Keyword']

    def match(string):
        return KeywordValueBase.match(Keyword, Type_Param_Value, string)
    match = staticmethod(match)


class Structure_Constructor_2(KeywordValueBase):  # R457.b
    """
    <structure-constructor-2> = [ <keyword> = ] <component-data-source>
    """
    subclass_names = ['Component_Data_Source']
    use_names = ['Keyword']

    def match(string):
        return KeywordValueBase.match(Keyword, Component_Data_Source, string)
    match = staticmethod(match)


class Structure_Constructor(CallBase):  # R457
    """
    <structure-constructor> = <derived-type-spec> ( [ <component-spec-list> ] )
                            | <structure-constructor-2>
    """
    subclass_names = ['Structure_Constructor_2']
    use_names = ['Derived_Type_Spec', 'Component_Spec_List']

    def match(string):
        return CallBase.match(Derived_Type_Spec, Component_Spec_List, string)
    match = staticmethod(match)


class Component_Spec(KeywordValueBase):  # R458
    """
    <component-spec> = [ <keyword> = ] <component-data-source>
    """
    subclass_names = ['Component_Data_Source']
    use_names = ['Keyword']

    def match(string):
        return KeywordValueBase.match(Keyword, Component_Data_Source, string)
    match = staticmethod(match)


class Component_Data_Source(Base):  # R459
    """
    <component-data-source> = <expr>
                              | <data-target>
                              | <proc-target>
    """
    subclass_names = ['Proc_Target', 'Data_Target', 'Expr']


class Enum_Def(BlockBase):  # R460
    """
    <enum-def> = <enum-def-stmt>
                     <enumerator-def-stmt>
                     [ <enumerator-def-stmt> ]...
                     <end-enum-stmt>
    """
    subclass_names = []
    use_names = ['Enum_Def_Stmt', 'Enumerator_Def_Stmt', 'End_Enum_Stmt']

    @staticmethod
    def match(reader):
        return BlockBase.match(Enum_Def_Stmt, [Enumerator_Def_Stmt],
                               End_Enum_Stmt, reader)


class Enum_Def_Stmt(StmtBase):  # R461
    """
    <enum-def-stmt> = ENUM, BIND(C)
    """
    subclass_names = []
    use_names = []

    @staticmethod
    def match(string):
        if string.upper().replace(' ', '') != 'ENUM,BIND(C)':
            return
        return 'ENUM, BIND(C)',

    def tostr(self):
        return '%s' % (self.items[0])


class Enumerator_Def_Stmt(StmtBase, WORDClsBase):  # R462
    """
    <enumerator-def-stmt> = ENUMERATOR [ :: ] <enumerator-list>
    """
    subclass_names = []
    use_names = ['Enumerator_List']

    def match(string):
        return WORDClsBase.match(
            'ENUMERATOR', Enumerator_List, string,
            colons=True, require_cls=True)
    match = staticmethod(match)
    tostr = WORDClsBase.tostr_a


class Enumerator(BinaryOpBase):  # R463
    """
    <enumerator> = <named-constant> [ = <scalar-int-initialization-expr> ]
    """
    subclass_names = ['Named_Constant']
    use_names = ['Scalar_Int_Initialization_Expr']

    def match(string):
        if '=' not in string:
            return
        lhs, rhs = string.split('=', 1)
        return Named_Constant(
            lhs.rstrip()), '=', Scalar_Int_Initialization_Expr(rhs.lstrip())
    match = staticmethod(match)


class End_Enum_Stmt(EndStmtBase):  # R464
    """
    <end-enum-stmt> = END ENUM
    """
    subclass_names = []

    def match(string):
        return EndStmtBase.match('ENUM', None, string, require_stmt_type=True)
    match = staticmethod(match)


class Array_Constructor(BracketBase):  # R465
    """
    <array-constructor> = (/ <ac-spec> /)
                          | <left-square-bracket> <ac-spec>
                            <right-square-bracket>

    """
    subclass_names = []
    use_names = ['Ac_Spec']

    def match(string):
        try:
            obj = BracketBase.match('(//)', Ac_Spec, string)
        except NoMatchError:
            obj = None
        if obj is None:
            obj = BracketBase.match('[]', Ac_Spec, string)
        return obj
    match = staticmethod(match)


class Ac_Spec(Base):  # R466
    """
    <ac-spec> = <type-spec> ::
                | [ <type-spec> :: ] <ac-value-list>
    """
    subclass_names = ['Ac_Value_List']
    use_names = ['Type_Spec']

    def match(string):
        if string.endswith('::'):
            return Type_Spec(string[:-2].rstrip()), None
        line, repmap = string_replace_map(string)
        i = line.find('::')
        if i == -1:
            return
        ts = line[:i].rstrip()
        line = line[i+2:].lstrip()
        ts = repmap(ts)
        line = repmap(line)
        return Type_Spec(ts), Ac_Value_List(line)
    match = staticmethod(match)

    def tostr(self):
        if self.items[0] is None:
            return str(self.items[1])
        if self.items[1] is None:
            return str(self.items[0]) + ' ::'
        return '%s :: %s' % self.items

# R467: <left-square-bracket> = [
# R468: <right-square-bracket> = ]


class Ac_Value(Base):  # R469
    """
    <ac-value> = <expr>
                 | <ac-implied-do>
    """
    subclass_names = ['Ac_Implied_Do', 'Expr']


class Ac_Implied_Do(Base):  # R470
    """
    <ac-implied-do> = ( <ac-value-list> , <ac-implied-do-control> )
    """
    subclass_names = []
    use_names = ['Ac_Value_List', 'Ac_Implied_Do_Control']

    def match(string):
        if string[0] + string[-1] != '()':
            return
        line, repmap = string_replace_map(string[1:-1].strip())
        i = line.rfind('=')
        if i == -1:
            return
        j = line[:i].rfind(',')
        assert j != -1
        s1 = repmap(line[:j].rstrip())
        s2 = repmap(line[j+1:].lstrip())
        return Ac_Value_List(s1), Ac_Implied_Do_Control(s2)
    match = staticmethod(match)

    def tostr(self):
        return '(%s, %s)' % tuple(self.items)


class Ac_Implied_Do_Control(Base):  # R471
    """
    <ac-implied-do-control> = <ac-do-variable> = <scalar-int-expr> ,
        <scalar-int-expr> [ , <scalar-int-expr> ]
    """
    subclass_names = []
    use_names = ['Ac_Do_Variable', 'Scalar_Int_Expr']

    def match(string):
        i = string.find('=')
        if i == -1:
            return
        s1 = string[:i].rstrip()
        line, repmap = string_replace_map(string[i+1:].lstrip())
        t = line.split(',')
        if not (2 <= len(t) <= 3):
            return
        t = [Scalar_Int_Expr(s.strip()) for s in t]
        return Ac_Do_Variable(s1), t
    match = staticmethod(match)

    def tostr(self):
        return '%s = %s' % (self.items[0], ', '.join(map(str, self.items[1])))


class Ac_Do_Variable(Base):  # R472
    """
    <ac-do-variable> = <scalar-int-variable>
    <ac-do-variable> shall be a named variable
    """
    subclass_names = ['Scalar_Int_Variable']

#
# SECTION  5
#


class Type_Declaration_Stmt(Type_Declaration_StmtBase):  # R501
    """
    <type-declaration-stmt> = <declaration-type-spec> [
        [ , <attr-spec> ]... :: ] <entity-decl-list>
    """
    subclass_names = []
    use_names = ['Declaration_Type_Spec', 'Attr_Spec_List', 'Entity_Decl_List']

    @staticmethod
    def match(string):
        return Type_Declaration_StmtBase.match(
            Declaration_Type_Spec, Attr_Spec_List, Entity_Decl_List, string)

    @staticmethod
    def match2(string):
        line, repmap = string_replace_map(string)
        i = line.find('::')
        if i != -1:
            j = line[:i].find(',')
            if j != -1:
                i = j
        else:
            if line[:6].upper() == 'DOUBLE':
                m = re.search(r'\s[a-z_]', line[6:].lstrip(), re.I)
                if m is None:
                    return
                i = m.start() + len(line) - len(line[6:].lstrip())
            else:
                m = re.search(r'\s[a-z_]', line, re.I)
                if m is None:
                    return
                i = m.start()
        type_spec = Declaration_Type_Spec(repmap(line[:i].rstrip()))
        if type_spec is None:
            return
        line = line[i:].lstrip()
        if line.startswith(','):
            i = line.find('::')
            if i == -1:
                return
            attr_specs = Attr_Spec_List(repmap(line[1:i].strip()))
            if attr_specs is None:
                return
            line = line[i:]
        else:
            attr_specs = None
        if line.startswith('::'):
            line = line[2:].lstrip()
        entity_decls = Entity_Decl_List(repmap(line))
        if entity_decls is None:
            return
        return type_spec, attr_specs, entity_decls

    def tostr(self):
        if self.items[1] is None:
            return '%s :: %s' % (self.items[0], self.items[2])
        else:
            return '%s, %s :: %s' % self.items


class Declaration_Type_Spec(Base):  # R502
    """
    <declaration-type-spec> = <intrinsic-type-spec>
                              | TYPE ( <derived-type-spec> )
                              | CLASS ( <derived-type-spec> )
                              | CLASS ( * )
    """
    subclass_names = ['Intrinsic_Type_Spec']
    use_names = ['Derived_Type_Spec']

    @staticmethod
    def match(string):
        '''Implements the matching of a declaration type specification.

        :param str string: the reader or string to match as a \
        declaration type specification.

        :return: A tuple of size 2 containing a string with the value \
        'TYPE' or 'CLASS' and a 'Derived_Type_Spec' instance if there \
        is a match or None if not.
        :rtype: (str, \
        py:class:`fparser.two.Fortran2003.Derived_Type_Spec`,) or \
        NoneType

        '''
        if not string:
            return None
        if string[-1] != ')':
            return None
        start = string[:4].upper()
        if start == 'TYPE':
            line = string[4:].lstrip()
            if not line.startswith('('):
                return None
            return 'TYPE', Derived_Type_Spec(line[1:-1].strip())
        start = string[:5].upper()
        if start == 'CLASS':
            line = string[5:].lstrip()
            if not line.startswith('('):
                return None
            line = line[1:-1].strip()
            if line == '*':
                return 'CLASS', '*'
            return 'CLASS', Derived_Type_Spec(line)
        return None

    def tostr(self):
        return '%s(%s)' % self.items


class Dimension_Attr_Spec(CALLBase):  # R503.d
    """
    <dimension-attr-spec> = DIMENSION ( <array-spec> )
    """
    subclass_names = []
    use_names = ['Array_Spec']

    def match(string):
        return CALLBase.match('DIMENSION', Array_Spec, string)
    match = staticmethod(match)


class Intent_Attr_Spec(CALLBase):  # R503.f
    """
    <intent-attr-spec> = INTENT ( <intent-spec> )
    """
    subclass_names = []
    use_names = ['Intent_Spec']

    def match(string):
        return CALLBase.match('INTENT', Intent_Spec, string)
    match = staticmethod(match)


class Attr_Spec(STRINGBase):  # R503
    """
    <attr-spec> = <access-spec>
                  | ALLOCATABLE
                  | ASYNCHRONOUS
                  | DIMENSION ( <array-spec> )
                  | EXTERNAL
                  | INTENT ( <intent-spec> )
                  | INTRINSIC
                  | <language-binding-spec>
                  | OPTIONAL
                  | PARAMETER
                  | POINTER
                  | PROTECTED
                  | SAVE
                  | TARGET
                  | VALUE
                  | VOLATILE
    """
    subclass_names = ['Access_Spec', 'Language_Binding_Spec',
                      'Dimension_Attr_Spec', 'Intent_Attr_Spec']
    use_names = []

    def match(string):
        return STRINGBase.match(pattern.abs_attr_spec, string)
    match = staticmethod(match)


class Entity_Decl(Base):  # R504
    """
    <entity-decl> = <object-name> [ ( <array-spec> ) ]
        [ * <char-length> ] [ <initialization> ]
                    | <function-name> [ * <char-length> ]
    """
    subclass_names = []
    use_names = ['Object_Name', 'Array_Spec', 'Char_Length',
                 'Initialization', 'Function_Name']

    def match(string, target=False):
        m = pattern.name.match(string)
        if m is None:
            return
        name = Name(m.group())
        newline = string[m.end():].lstrip()
        if not newline:
            return name, None, None, None
        array_spec = None
        char_length = None
        init = None
        if newline.startswith('('):
            line, repmap = string_replace_map(newline)
            i = line.find(')')
            if i == -1:
                return
            array_spec = Array_Spec(repmap(line[1:i].strip()))
            newline = repmap(line[i+1:].lstrip())
        if target:
            if newline:
                return
            return name, array_spec, None, None
        if newline.startswith('*'):
            line, repmap = string_replace_map(newline)
            i = line.find('=')
            if i != -1:
                char_length = repmap(line[1:i].strip())
                newline = repmap(newline[i:].lstrip())
            else:
                char_length = repmap(newline[1:].strip())
                newline = ''
            char_length = Char_Length(char_length)
        if newline.startswith('='):
            init = Initialization(newline)
        elif newline:
            return
        else:
            assert newline == '', repr((newline, string))
        return name, array_spec, char_length, init
    match = staticmethod(match)

    def tostr(self):
        s = str(self.items[0])
        if self.items[1] is not None:
            s += '(' + str(self.items[1]) + ')'
        if self.items[2] is not None:
            s += '*' + str(self.items[2])
        if self.items[3] is not None:
            s += ' ' + str(self.items[3])
        return s


class Object_Name(Base):  # R505
    """
    <object-name> = <name>
    """
    subclass_names = ['Name']


class Initialization(Base):  # R506
    """
    <initialization> =  = <initialization-expr>
                       | => <null-init>
    """
    subclass_names = []
    use_names = ['Initialization_Expr', 'Null_Init']

    def match(string):
        if string.startswith('=>'):
            return '=>', Null_Init(string[2:].lstrip())
        if string.startswith('='):
            return '=', Initialization_Expr(string[1:].lstrip())
        return
    match = staticmethod(match)

    def tostr(self):
        return '%s %s' % self.items


class Null_Init(STRINGBase):  # R507
    """
    <null-init> = <function-reference>

    <function-reference> shall be a reference to the NULL
        intrinsic function with no arguments.
    """
    subclass_names = ['Function_Reference']

    def match(string):
        return STRINGBase.match('NULL', string)
    match = staticmethod(match)


class Access_Spec(STRINGBase):  # R508
    """
:F03R:`508`::
    <access-spec> = PUBLIC
                    | PRIVATE
    """
    subclass_names = []

    def match(string):
        return STRINGBase.match(['PUBLIC', 'PRIVATE'], string)
    match = staticmethod(match)


class Language_Binding_Spec(Base):  # R509
    """
:F03R:`509`::
    <language-binding-spec> = BIND ( C [ ,
        NAME = <scalar-char-initialization-expr> ] )
    """
    subclass_names = []
    use_names = ['Scalar_Char_Initialization_Expr']

    def match(string):
        start = string[:4].upper()
        if start != 'BIND':
            return
        line = string[4:].lstrip()
        if not line or line[0] + line[-1] != '()':
            return
        line = line[1:-1].strip()
        if not line:
            return
        start = line[0].upper()
        if start != 'C':
            return
        line = line[1:].lstrip()
        if not line:
            return None,
        if not line.startswith(','):
            return
        line = line[1:].lstrip()
        start = line[:4].upper()
        if start != 'NAME':
            return
        line = line[4:].lstrip()
        if not line.startswith('='):
            return
        return Scalar_Char_Initialization_Expr(line[1:].lstrip()),
    match = staticmethod(match)

    def tostr(self):
        if self.items[0] is None:
            return 'BIND(C)'
        return 'BIND(C, NAME = %s)' % (self.items[0])


class Array_Spec(Base):  # R510
    """
:F03R:`510`::
    <array-spec> = <explicit-shape-spec-list>
                   | <assumed-shape-spec-list>
                   | <deferred-shape-spec-list>
                   | <assumed-size-spec>
    """
    subclass_names = ['Assumed_Size_Spec', 'Explicit_Shape_Spec_List',
                      'Assumed_Shape_Spec_List',
                      'Deferred_Shape_Spec_List']


class Explicit_Shape_Spec(SeparatorBase):  # R511
    """
    <explicit-shape-spec> = [ <lower-bound> : ] <upper-bound>
    """
    subclass_names = []
    use_names = ['Lower_Bound', 'Upper_Bound']

    def match(string):
        line, repmap = string_replace_map(string)
        if ':' not in line:
            return None, Upper_Bound(string)
        lower, upper = line.split(':', 1)
        lower = lower.rstrip()
        upper = upper.lstrip()
        if not upper:
            return
        if not lower:
            return
        return Lower_Bound(repmap(lower)), Upper_Bound(repmap(upper))
    match = staticmethod(match)

    def tostr(self):
        if self.items[0] is None:
            return str(self.items[1])
        return SeparatorBase.tostr(self)


class Lower_Bound(Base):  # R512
    """
    <lower-bound> = <specification-expr>
    """
    subclass_names = ['Specification_Expr']


class Upper_Bound(Base):  # R513
    """
    <upper-bound> = <specification-expr>
    """
    subclass_names = ['Specification_Expr']


class Assumed_Shape_Spec(SeparatorBase):  # R514
    """
:F03R:`514`::
    <assumed-shape-spec> = [ <lower-bound> ] :
    """
    subclass_names = []
    use_names = ['Lower_Bound']

    def match(string):
        return SeparatorBase.match(Lower_Bound, None, string)
    match = staticmethod(match)


class Deferred_Shape_Spec(SeparatorBase):  # R515
    """
:F03R:`515`::
    <deferred_shape_spec> = :
    """
    subclass_names = []

    def match(string):
        if string == ':':
            return None, None
        return
    match = staticmethod(match)


class Assumed_Size_Spec(Base):  # R516
    """
:F03R:`516`::
    <assumed-size-spec> = [ <explicit-shape-spec-list> , ]
        [ <lower-bound> : ] *
    """
    subclass_names = []
    use_names = ['Explicit_Shape_Spec_List', 'Lower_Bound']

    def match(string):
        if not string.endswith('*'):
            return
        line = string[:-1].rstrip()
        if not line:
            return None, None
        if line.endswith(':'):
            line, repmap = string_replace_map(line[:-1].rstrip())
            i = line.rfind(',')
            if i == -1:
                return None, Lower_Bound(repmap(line))
            return Explicit_Shape_Spec_List(
                repmap(line[:i].rstrip())), \
                Lower_Bound(repmap(line[i+1:].lstrip()))
        if not line.endswith(','):
            return
        line = line[:-1].rstrip()
        return Explicit_Shape_Spec_List(line), None
    match = staticmethod(match)

    def tostr(self):
        s = ''
        if self.items[0] is not None:
            s += str(self.items[0]) + ', '
        if self.items[1] is not None:
            s += str(self.items[1]) + ' : '
        s += '*'
        return s


class Intent_Spec(STRINGBase):  # R517
    """
    <intent-spec> = IN
                    | OUT
                    | INOUT
    """
    subclass_names = []

    def match(string):
        return STRINGBase.match(pattern.abs_intent_spec, string)
    match = staticmethod(match)


class Access_Stmt(StmtBase, WORDClsBase):  # R518
    """
:F03R:`518`::
    <access-stmt> = <access-spec> [ [ :: ] <access-id-list> ]
    """
    subclass_names = []
    use_names = ['Access_Spec', 'Access_Id_List']

    def match(string):
        return WORDClsBase.match(
            ['PUBLIC', 'PRIVATE'],
            Access_Id_List, string, colons=True,
            require_cls=False)
    match = staticmethod(match)
    tostr = WORDClsBase.tostr_a


class Access_Id(Base):  # R519
    """
:F03R:`519`::
    <access-id> = <use-name>
                  | <generic-spec>
    """
    subclass_names = ['Use_Name', 'Generic_Spec']


class Object_Name_Deferred_Shape_Spec_List_Item(CallBase):
    """
    <..> =  <object-name> [ ( <deferred-shape-spec-list> ) ]
    """
    subclass_names = ['Object_Name']
    use_names = ['Deferred_Shape_Spec_List']

    def match(string):
        return CallBase.match(
            Object_Name, Deferred_Shape_Spec_List, string,
            require_rhs=True)
    match = staticmethod(match)


class Allocatable_Stmt(StmtBase, WORDClsBase):  # R520
    """
:F03R:`520`::
    <allocateble-stmt> = ALLOCATABLE [ :: ] <object-name> [
        ( <deferred-shape-spec-list> ) ] [ , <object-name>
        [ ( <deferred-shape-spec-list> ) ] ]...
    """
    subclass_names = []
    use_names = ['Object_Name_Deferred_Shape_Spec_List_Item_List']

    def match(string):
        return WORDClsBase.match(
            'ALLOCATABLE', Object_Name_Deferred_Shape_Spec_List_Item_List,
            string, colons=True, require_cls=True)
    match = staticmethod(match)


class Asynchronous_Stmt(StmtBase, WORDClsBase):  # R521
    """
:F03R:`521`::
    <asynchronous-stmt> = ASYNCHRONOUS [ :: ] <object-name-list>
    """
    subclass_names = []
    use_names = ['Object_Name_List']

    def match(string):
        return WORDClsBase.match(
            'ASYNCHRONOUS', Object_Name_List, string, colons=True,
            require_cls=True)
    match = staticmethod(match)


class Bind_Stmt(StmtBase):  # R522
    """
:F03R:`522`::
    <bind-stmt> = <language-binding-spec> [ :: ] <bind-entity-list>
    """
    subclass_names = []
    use_names = ['Language_Binding_Spec', 'Bind_Entity_List']

    def match(string):
        i = string.find('::')
        if i == -1:
            i = string.find(')')
            if i == -1:
                return
            lhs, rhs = string[:i], string[i+1:]
        else:
            lhs, rhs = string.split('::', 1)
        lhs = lhs.rstrip()
        rhs = rhs.lstrip()
        if not lhs or not rhs:
            return
        return Language_Binding_Spec(lhs), Bind_Entity_List(rhs)
    match = staticmethod(match)

    def tostr(self):
        return '%s :: %s' % self.items


class Bind_Entity(BracketBase):  # R523
    """
    <bind-entity> = <entity-name>
                    | / <common-block-name> /
    """
    subclass_names = ['Entity_Name']
    use_names = ['Common_Block_Name']

    def match(string):
        return BracketBase.match('//', Common_Block_Name, string)
    match = staticmethod(match)


class Data_Stmt(StmtBase):  # R524
    """
:F03R:524::
    <data-stmt> = DATA <data-stmt-set> [ [ , ] <data-stmt-set> ]...
    """
    subclass_names = []
    use_names = ['Data_Stmt_Set']

    @staticmethod
    def match(string):
        if string[:4].upper() != 'DATA':
            return
        line, repmap = string_replace_map(string[4:].lstrip())
        i = line.find('/')
        if i == -1:
            return
        i = line.find('/', i + 1)
        if i == -1:
            return
        items = [Data_Stmt_Set(repmap(line[:i+1]))]
        line = line[i+1:].lstrip()
        while line:
            if line.startswith(','):
                line = line[1:].lstrip()
            i = line.find('/')
            if i == -1:
                return
            i = line.find('/', i + 1)
            if i == -1:
                return
            items.append(Data_Stmt_Set(repmap(line[:i+1])))
            line = line[i+1:].lstrip()
        return tuple(items)

    def tostr(self):
        return 'DATA ' + ', '.join(map(str, self.items))


class Data_Stmt_Set(Base):  # R525
    """
:F03R:525::
    <data-stmt-set> = <data-stmt-object-list> / <data-stmt-value-list> /
    """
    subclass_names = []
    use_names = ['Data_Stmt_Object_List', 'Data_Stmt_Value_List']

    @staticmethod
    def match(string):
        if not string.endswith('/'):
            return
        line, repmap = string_replace_map(string)
        i = line.find('/')
        if i == -1:
            return
        data_stmt_object_list = Data_Stmt_Object_List(
            repmap(line[:i].rstrip()))
        data_stmt_value_list = Data_Stmt_Value_List(
            repmap(line[i+1:-1].strip()))
        return data_stmt_object_list, data_stmt_value_list

    data_stmt_object_list = property(lambda self: self.items[0])
    data_stmt_value_list = property(lambda self: self.items[1])

    def tostr(self):
        return '%s / %s /' % tuple(self.items)


class Data_Stmt_Object(Base):  # R526
    """
:F03R:526::
    <data-stmt-object> = <variable>
                         | <data-implied-do>
    """
    subclass_names = ['Variable', 'Data_Implied_Do']


class Data_Implied_Do(Base):  # R527
    """
:F03R:527::
    <data-implied-do> = ( <data-i-do-object-list> ,
        <data-i-do-variable> = <scalar-int-expr > ,
        <scalar-int-expr> [ , <scalar-int-expr> ] )
    """
    subclass_names = []
    use_names = ['Data_I_Do_Object_List', 'Data_I_Do_Variable',
                 'Scalar_Int_Expr']

    @staticmethod
    def match(string):
        if not (string.startswith('(') and string.endswith(')')):
            return
        line, repmap = string_replace_map(string[1:-1].strip())
        s = line.split('=', 1)
        if len(s) != 2:
            return
        lhs = s[0].rstrip()
        rhs = s[1].lstrip()
        s1 = lhs.rsplit(',', 1)
        if len(s1) != 2:
            return
        s2 = rhs.split(',')
        if len(s2) not in [2, 3]:
            return
        data_i_do_object_list = Data_I_Do_Object_List(repmap(s1[0].rstrip()))
        data_i_do_variable = Data_I_Do_Variable(repmap(s1[1].lstrip()))
        scalar_int_expr1 = Scalar_Int_Expr(repmap(s2[0].rstrip()))
        scalar_int_expr2 = Scalar_Int_Expr(repmap(s2[1].strip()))
        if len(s2) == 3:
            scalar_int_expr3 = Scalar_Int_Expr(repmap(s2[2].lstrip()))
        else:
            scalar_int_expr3 = None
        return data_i_do_object_list, data_i_do_variable, \
            scalar_int_expr1, scalar_int_expr2, scalar_int_expr3

    data_i_do_object_list = property(lambda self: self.items[0])
    data_i_do_variable = property(lambda self: self.items[1])
    scalar_int_expr1 = property(lambda self: self.items[2])
    scalar_int_expr2 = property(lambda self: self.items[3])
    scalar_int_expr3 = property(lambda self: self.items[4])

    def tostr(self):
        tmp = '%s, %s = %s, %s' % tuple(self.items[:4])
        if self.items[4] is not None:
            tmp += ', %s' % (self.items[4])
        return '(' + tmp + ')'


class Data_I_Do_Object(Base):  # R528
    """
    <data-i-do-object> = <array-element>
                         | <scalar-structure-component>
                         | <data-implied-do>
    """
    subclass_names = ['Array_Element', 'Scalar_Structure_Component',
                      'Data_Implied_Do']


class Data_I_Do_Variable(Base):  # R529
    """
    <data-i-do-variable> = <scalar-int-variable>
    """
    subclass_names = ['Scalar_Int_Variable']


class Data_Stmt_Value(Base):  # R530
    """
    <data-stmt-value> = [ <data-stmt-repeat> * ] <data-stmt-constant>
    """
    subclass_names = ['Data_Stmt_Constant']
    use_names = ['Data_Stmt_Repeat']

    def match(string):
        line, repmap = string_replace_map(string)
        s = line.split('*', 1)
        if len(s) != 2:
            return
        lhs = repmap(s[0].rstrip())
        rhs = repmap(s[1].lstrip())
        if not lhs or not rhs:
            return
        return Data_Stmt_Repeat(lhs), Data_Stmt_Constant(rhs)
    match = staticmethod(match)

    def tostr(self):
        return '%s * %s' % self.items


class Data_Stmt_Repeat(Base):  # R531
    """
    <data-stmt-repeat> = <scalar-int-constant>
                         | <scalar-int-constant-subobject>
    """
    subclass_names = ['Scalar_Int_Constant', 'Scalar_Int_Constant_Subobject']


class Data_Stmt_Constant(Base):  # R532
    """
    <data-stmt-constant> = <scalar-constant>
                           | <scalar-constant-subobject>
                           | <signed-int-literal-constant>
                           | <signed-real-literal-constant>
                           | <null-init>
                           | <structure-constructor>
    """
    subclass_names = ['Scalar_Constant', 'Scalar_Constant_Subobject',
                      'Signed_Int_Literal_Constant',
                      'Signed_Real_Literal_Constant',
                      'Null_Init', 'Structure_Constructor']


class Int_Constant_Subobject(Base):  # R533
    """
    <int-constant-subobject> = <constant-subobject>
    """
    subclass_names = ['Constant_Subobject']


class Constant_Subobject(Base):  # R534
    """
    <constant-subobject> = <designator>
    """
    subclass_names = ['Designator']


class Dimension_Stmt(StmtBase):  # R535
    """
    <dimension-stmt> = DIMENSION [ :: ] <array-name> ( <array-spec> )
        [ , <array-name> ( <array-spec> ) ]...
    """
    subclass_names = []
    use_names = ['Array_Name', 'Array_Spec']

    def match(string):
        if string[:9].upper() != 'DIMENSION':
            return
        line, repmap = string_replace_map(string[9:].lstrip())
        if line.startswith('::'):
            line = line[2:].lstrip()
        decls = []
        for s in line.split(','):
            s = s.strip()
            if not s.endswith(')'):
                return
            i = s.find('(')
            if i == -1:
                return
            decls.append((Array_Name(repmap(s[:i].rstrip())),
                          Array_Spec(repmap(s[i+1:-1].strip()))))
        if not decls:
            return
        return decls,
    match = staticmethod(match)

    def tostr(self):
        return 'DIMENSION :: ' + ', '.join(['%s(%s)'
                                            % ns for ns in self.items[0]])


class Intent_Stmt(StmtBase):  # R536
    """
    <intent-stmt> = INTENT ( <intent-spec> ) [ :: ] <dummy-arg-name-list>
    """
    subclass_names = []
    use_names = ['Intent_Spec', 'Dummy_Arg_Name_List']

    def match(string):
        if string[:6].upper() != 'INTENT':
            return
        line = string[6:].lstrip()
        if not line or not line.startswith('('):
            return
        i = line.rfind(')')
        if i == -1:
            return
        spec = line[1:i].strip()
        if not spec:
            return
        line = line[i+1:].lstrip()
        if line.startswith('::'):
            line = line[2:].lstrip()
        if not line:
            return
        return Intent_Spec(spec), Dummy_Arg_Name_List(line)
    match = staticmethod(match)

    def tostr(self):
        return 'INTENT(%s) :: %s' % self.items


class Optional_Stmt(StmtBase, WORDClsBase):  # R537
    """
    <optional-stmt> = OPTIONAL [ :: ] <dummy-arg-name-list>
    """
    subclass_names = []
    use_names = ['Dummy_Arg_Name_List']

    def match(string):
        return WORDClsBase.match(
            'OPTIONAL', Dummy_Arg_Name_List, string, colons=True,
            require_cls=True)
    match = staticmethod(match)
    tostr = WORDClsBase.tostr_a


class Parameter_Stmt(StmtBase, CALLBase):  # R538
    """
    <parameter-stmt> = PARAMETER ( <named-constant-def-list> )
    """
    subclass_names = []
    use_names = ['Named_Constant_Def_List']

    def match(string):
        return CALLBase.match('PARAMETER', Named_Constant_Def_List,
                              string, require_rhs=True)
    match = staticmethod(match)


class Named_Constant_Def(KeywordValueBase):  # R539
    """
    <named-constant-def> = <named-constant> = <initialization-expr>
    """
    subclass_names = []
    use_names = ['Named_Constant', 'Initialization_Expr']

    def match(string):
        return KeywordValueBase.match(Named_Constant, Initialization_Expr,
                                      string)
    match = staticmethod(match)


class Cray_Pointer_Stmt(StmtBase, WORDClsBase):  # pylint: disable=invalid-name
    '''
    cray-pointer-stmt is POINTER cray-pointer-decl-list
    '''
    subclass_names = []
    use_names = ['Cray_Pointer_Decl_List']

    @staticmethod
    def match(string):
        '''Implements the matching for a Cray-pointer statement.

        :param string: the reader or string to match as a Cray-pointer \
        statement.
        :type string: \
        :py:class:`fparser.common.readfortran.FortranReaderBase` or \
        `str`
        :return: a tuple of size 2 containing a string with the name \
        "POINTER" and a cray-pointer-decl-list, if there is a match, \
        or `None` if there is not.
        :rtype: (str, Cray_Pointer_Decl_List) or None

        '''
        from fparser.two.utils import EXTENSIONS
        if 'cray-pointer' not in EXTENSIONS:
            return None
        return WORDClsBase.match('POINTER', Cray_Pointer_Decl_List, string,
                                 require_cls=True)


class Cray_Pointer_Decl(Base):  # pylint: disable=invalid-name
    '''
    cray-pointer-decl is ( cray-pointer-name, cray-pointee-decl )
    '''
    use_names = ['Cray_Pointer_Name', 'Cray_Pointee_Name', 'Cray_Pointee_Decl']

    @staticmethod
    def match(string):
        '''Implements the matching for a Cray-pointer declaration.

        :param str string: the string to match as a Cray-pointer \
        declaration.
        :return: None if there is no match, otherwise a tuple of size \
        2 containing the name of the pointer as the first argument and \
        either the name of the pointee as the second argument or a \
        Cray-pointee declaration.
        :rtype: None, (Name, Name) or (Name, Cray_Pointee_Decl)

        '''
        if not string:
            return None
        strip_string = string.strip()
        if not strip_string:
            return None
        if not strip_string[0] == "(":
            return None
        if not strip_string[-1] == ")":
            return None
        strip_string_nobr = strip_string[1:-1].strip()
        line, repmap = string_replace_map(strip_string_nobr)
        split_list = line.split(',')
        if len(split_list) != 2:
            return None
        pointer_name = repmap(split_list[0]).strip()
        pointee_str = repmap(split_list[1]).strip()
        if pointee_str[-1] == ")":
            return Cray_Pointer_Name(pointer_name), \
                Cray_Pointee_Decl(pointee_str)
        return Cray_Pointer_Name(pointer_name), Cray_Pointee_Name(pointee_str)

    def tostr(self):
        '''
        :return: this Cray-pointee declaration as a string
        :rtype: str
        :raises InternalError: if the internal items list variable is \
        not the expected size.
        :raises InternalError: if the first element of the internal \
        items list is None or is empty.
        :raises InternalError: if the second element of the internal \
        items list is None or is empty.
        '''
        if len(self.items) != 2:
            raise InternalError(
                "Cray_Pointer_Decl.tostr(). 'Items' should be of size 2 but "
                "found '{0}'.".format(len(self.items)))
        if not self.items[0]:
            raise InternalError("Cray_Pointer_Decl_Stmt.tostr(). 'Items' "
                                "entry 0 should be a pointer name but it is "
                                "empty")
        if not self.items[1]:
            raise InternalError("Cray_Pointer_Decl_Stmt.tostr(). 'Items' "
                                "entry 1 should be a pointee name or pointee "
                                "declaration but it is empty")
        return "({0}, {1})".format(self.items[0], self.items[1])


class Cray_Pointee_Decl(CallBase):  # pylint: disable=invalid-name
    '''
    cray-pointee-decl is cray-pointee-name ( cray-pointee-array-spec )

    '''
    subclass_names = []
    use_names = ['Cray_Pointee_Name', 'Cray_Pointee_Array_Spec']

    @staticmethod
    def match(string):
        '''Implements the matching for a Cray-pointee declaration.

        :param str string: the string to match as a Cray-pointee \
        declaration.
        :return: None if there is no match, otherwise a tuple of size \
        2 containing the name of the pointee as the first argument and \
        a Cray-pointee array spec as the second argument.
        :rtype: None or (Name, Cray_Pointee_Array_Spec)

        '''
        return CallBase.match(
            Cray_Pointee_Name, Cray_Pointee_Array_Spec, string,
            require_rhs=True)


class Cray_Pointee_Array_Spec(Base):  # pylint: disable=invalid-name
    '''cray-pointee-array-spec is explicit-shape-spec-list
                            or assumed-size-spec

    The above two forms of declaration are the only ones allowed
    according to
    http://pubs.cray.com/content/S-3901/8.6/
    cray-fortran-reference-manual-s-3901-86/types) or
    https://docs.oracle.com/cd/E19957-01/805-4941/z40000a54ba7/index.html

    '''
    subclass_names = ['Assumed_Size_Spec', 'Explicit_Shape_Spec_List']


class Pointer_Stmt(StmtBase, WORDClsBase):  # R540
    """
    <pointer-stmt> = POINTER [ :: ] <pointer-decl-list>
    """
    subclass_names = []
    use_names = ['Pointer_Decl_List']

    def match(string):
        return WORDClsBase.match('POINTER', Pointer_Decl_List, string,
                                 colons=True, require_cls=True)
    match = staticmethod(match)
    tostr = WORDClsBase.tostr_a


class Pointer_Decl(CallBase):  # R541
    """
    <pointer-decl> = <object-name> [ ( <deferred-shape-spec-list> ) ]
                     | <proc-entity-name>
    """
    subclass_names = ['Proc_Entity_Name', 'Object_Name']
    use_names = ['Deferred_Shape_Spec_List']

    def match(string):
        return CallBase.match(Object_Name, Deferred_Shape_Spec_List,
                              string, require_rhs=True)
    match = staticmethod(match)


class Protected_Stmt(StmtBase, WORDClsBase):  # R542
    """
    <protected-stmt> = PROTECTED [ :: ] <entity-name-list>
    """
    subclass_names = []
    use_names = ['Entity_Name_List']

    def match(string):
        return WORDClsBase.match(
            'PROTECTED', Entity_Name_List, string, colons=True,
            require_cls=True)
    match = staticmethod(match)
    tostr = WORDClsBase.tostr_a


class Save_Stmt(StmtBase, WORDClsBase):  # R543
    """
    <save-stmt> = SAVE [ [ :: ] <saved-entity-list> ]
    """
    subclass_names = []
    use_names = ['Saved_Entity_List']

    def match(string):
        return WORDClsBase.match(
            'SAVE', Saved_Entity_List, string, colons=True,
            require_cls=False)
    match = staticmethod(match)
    tostr = WORDClsBase.tostr_a


class Saved_Entity(BracketBase):  # R544
    """
    <saved-entity> = <object-name>
                     | <proc-pointer-name>
                     | / <common-block-name> /
    """
    subclass_names = ['Object_Name', 'Proc_Pointer_Name']
    use_names = ['Common_Block_Name']

    def match(string):
        return BracketBase.match('//', Common_Block_Name, string)
    match = staticmethod(match)


class Proc_Pointer_Name(Base):  # R545
    """
    <proc-pointer-name> = <name>
    """
    subclass_names = ['Name']


class Target_Entity_Decl(Entity_Decl):
    """
    <target-entity-decl> = <object-name> [ ( <array-spec> ) ]
    """
    subclass_names = []
    use_names = ['Object_Name', 'Array_Spec']

    @staticmethod
    def match(string):
        return Entity_Decl.match(string, target=True)


class Target_Stmt(StmtBase):  # R546
    """
    <target-stmt> = TARGET [ :: ] <target-entity-decl-list>
    """
    subclass_names = []
    use_names = ['Target_Entity_Decl_List']

    @staticmethod
    def match(string):
        if string[:6].upper() != 'TARGET':
            return
        line = string[6:].lstrip()
        if line.startswith('::'):
            line = line[2:].lstrip()
        return Target_Entity_Decl_List(line),

    def tostr(self):
        return 'TARGET :: %s' % (self.items[0])


class Value_Stmt(StmtBase, WORDClsBase):  # R547
    """
    <value-stmt> = VALUE [ :: ] <dummy-arg-name-list>
    """
    subclass_names = []
    use_names = ['Dummy_Arg_Name_List']

    @staticmethod
    def match(string):
        return WORDClsBase.match(
            'VALUE', Dummy_Arg_Name_List, string, colons=True,
            require_cls=True)
    tostr = WORDClsBase.tostr_a


class Volatile_Stmt(StmtBase, WORDClsBase):  # R548
    """
    <volatile-stmt> = VOLATILE [ :: ] <object-name-list>
    """
    subclass_names = []
    use_names = ['Object_Name_List']

    @staticmethod
    def match(string):
        return WORDClsBase.match(
            'VOLATILE', Object_Name_List, string, colons=True,
            require_cls=True)
    tostr = WORDClsBase.tostr_a


class Implicit_Stmt(StmtBase):  # R549
    """
::
    <implicit-stmt> = IMPLICIT <implicit-spec-list>
                      | IMPLICIT NONE

Attributes
----------
items : ({'NONE', Implicit_Spec_List},)
    """
    subclass_names = []
    use_names = ['Implicit_Spec_List']

    @staticmethod
    def match(string):
        if string[:8].upper() != 'IMPLICIT':
            return
        line = string[8:].lstrip()
        if len(line) == 4 and line.upper() == 'NONE':
            return 'NONE',
        return Implicit_Spec_List(line),
        for w, cls in [(pattern.abs_implicit_none, None),
                       ('IMPLICIT', Implicit_Spec_List)]:
            try:
                obj = WORDClsBase.match(w, cls, string)
            except NoMatchError:
                obj = None
            if obj is not None:
                return obj
        return

    def tostr(self):
        return 'IMPLICIT %s' % (self.items[0])


class Implicit_Spec(CallBase):  # R550
    """
    <implicit-spec> = <declaration-type-spec> ( <letter-spec-list> )
    """
    subclass_names = []
    use_names = ['Declaration_Type_Spec', 'Letter_Spec_List']

    def match(string):
        if not string.endswith(')'):
            return
        i = string.rfind('(')
        if i == -1:
            return
        s1 = string[:i].rstrip()
        s2 = string[i+1:-1].strip()
        if not s1 or not s2:
            return
        return Declaration_Type_Spec(s1), Letter_Spec_List(s2)
    match = staticmethod(match)


class Letter_Spec(Base):  # R551
    """
    <letter-spec> = <letter> [ - <letter> ]
    """
    subclass_names = []

    def match(string):
        if len(string) == 1:
            lhs = string.upper()
            if 'A' <= lhs <= 'Z':
                return lhs, None
            return
        if '-' not in string:
            return
        lhs, rhs = string.split('-', 1)
        lhs = lhs.strip().upper()
        rhs = rhs.strip().upper()
        if not len(lhs) == len(rhs) == 1:
            return
        if not ('A' <= lhs <= rhs <= 'Z'):
            return
        return lhs, rhs
    match = staticmethod(match)

    def tostr(self):
        if self.items[1] is None:
            return str(self.items[0])
        return '%s - %s' % tuple(self.items)


class Namelist_Stmt(StmtBase):  # R552
    """
::
    <namelist-stmt> = NAMELIST / <namelist-group-name> /
        <namelist-group-object-list> [ [ , ] / <namelist-group-name> /
        <namelist-group-object-list> ]...

Attributes
----------
items : (Namelist_Group_Name, Namelist_Group_Object_List)-tuple
    """
    subclass_names = []
    use_names = ['Namelist_Group_Name', 'Namelist_Group_Object_List']

    @staticmethod
    def match(string):
        if string[:8].upper() != 'NAMELIST':
            return
        line = string[8:].lstrip()
        parts = line.split('/')
        items = []
        fst = parts.pop(0)
        assert not fst, repr((fst, parts))
        while len(parts) >= 2:
            name, lst = parts[:2]
            del parts[:2]
            name = name.strip()
            lst = lst.strip()
            if lst.endswith(','):
                lst = lst[:-1].rstrip()
            items.append(
                (Namelist_Group_Name(name), Namelist_Group_Object_List(lst)))
        assert not parts, repr(parts)
        return tuple(items)

    def tostr(self):
        return 'NAMELIST ' + ', '.join('/%s/ %s' % (name_lst)
                                       for name_lst in self.items)


class Namelist_Group_Object(Base):  # R553
    """
    <namelist-group-object> = <variable-name>
    """
    subclass_names = ['Variable_Name']


class Equivalence_Stmt(StmtBase, WORDClsBase):  # R554
    """
    <equivalence-stmt> = EQUIVALENCE <equivalence-set-list>
    """
    subclass_names = []
    use_names = ['Equivalence_Set_List']

    def match(string):
        return WORDClsBase.match('EQUIVALENCE', Equivalence_Set_List, string)
    match = staticmethod(match)


class Equivalence_Set(Base):  # R555
    """
    <equivalence-set> = ( <equivalence-object> , <equivalence-object-list> )
    """
    subclass_names = []
    use_names = ['Equivalence_Object', 'Equivalence_Object_List']

    def match(string):
        if not string or string[0] + string[-1] != '()':
            return
        line = string[1:-1].strip()
        if not line:
            return
        tmp = Equivalence_Object_List(line)
        obj = tmp.items[0]
        tmp.items = tmp.items[1:]
        if not tmp.items:
            return
        return obj, tmp
    match = staticmethod(match)

    def tostr(self):
        return '(%s, %s)' % tuple(self.items)


class Equivalence_Object(Base):  # R556
    """
    <equivalence-object> = <variable-name>
                           | <array-element>
                           | <substring>
    """
    subclass_names = ['Variable_Name', 'Array_Element', 'Substring']


class Common_Stmt(StmtBase):  # R557
    """
    <common-stmt> = COMMON [ / [ <common-block-name> ] / ]
        <common-block-object-list> [ [ , ] / [ <common-block-name> ]
        / <common-block-object-list> ]...
    """
    subclass_names = []
    use_names = ['Common_Block_Name', 'Common_Block_Object_List']

    def match(string):
        if string[:6].upper() != 'COMMON':
            return
        line = string[6:]
        if not line or 'A' <= line[0].upper() <= 'Z' or line[0] == '_':
            return
        line, repmap = string_replace_map(line.lstrip())
        items = []
        if line.startswith('/'):
            i = line.find('/', 1)
            if i == -1:
                return
            name = line[1:i].strip() or None
            if name is not None:
                name = Common_Block_Name(name)
            line = line[i+1:].lstrip()
            i = line.find('/')
            if i == -1:
                lst = Common_Block_Object_List(repmap(line))
                line = ''
            else:
                tmp = line[:i].rstrip()
                if tmp.endswith(','):
                    tmp = tmp[:-1].rstrip()
                if not tmp:
                    return
                lst = Common_Block_Object_List(repmap(tmp))
                line = line[i:].lstrip()
        else:
            name = None
            i = line.find('/')
            if i == -1:
                lst = Common_Block_Object_List(repmap(line))
                line = ''
            else:
                tmp = line[:i].rstrip()
                if tmp.endswith(','):
                    tmp = tmp[:-1].rstrip()
                if not tmp:
                    return
                lst = Common_Block_Object_List(repmap(tmp))
                line = line[i:].lstrip()
        items.append((name, lst))
        while line:
            if line.startswith(','):
                line = line[1:].lstrip()
            if not line.startswith('/'):
                return
            i = line.find('/', 1)
            name = line[1:i].strip() or None
            if name is not None:
                name = Common_Block_Name(name)
            line = line[i+1:].lstrip()
            i = line.find('/')
            if i == -1:
                lst = Common_Block_Object_List(repmap(line))
                line = ''
            else:
                tmp = line[:i].rstrip()
                if tmp.endswith(','):
                    tmp = tmp[:-1].rstrip()
                if not tmp:
                    return
                lst = Common_Block_Object_List(repmap(tmp))
                line = line[i:].lstrip()
            items.append((name, lst))
        return items,
    match = staticmethod(match)

    def tostr(self):
        s = 'COMMON'
        for (name, lst) in self.items[0]:
            if name is not None:
                s += ' /%s/ %s' % (name, lst)
            else:
                s += ' // %s' % (lst)
        return s


class Common_Block_Object(CallBase):  # R558
    """
    <common-block-object> = <variable-name> [ ( <explicit-shape-spec-list> ) ]
                            | <proc-pointer-name>
    """
    subclass_names = ['Proc_Pointer_Name', 'Variable_Name']
    use_names = ['Variable_Name', 'Explicit_Shape_Spec_List']

    def match(string):
        return CallBase.match(
            Variable_Name, Explicit_Shape_Spec_List, string,
            require_rhs=True)
    match = staticmethod(match)

#
# SECTION  6
#


class Variable(Base):  # R601
    """
    <variable> = <designator>
    """
    subclass_names = ['Designator']


class Variable_Name(Base):  # R602
    """
    <variable-name> = <name>
    """
    subclass_names = ['Name']


class Designator(Base):  # R603
    """
    <designator> = <object-name>
                   | <array-element>
                   | <array-section>
                   | <structure-component>
                   | <substring>
    <substring-range> = [ <scalar-int-expr> ] : [ <scalar-int-expr> ]
    <structure-component> = <data-ref>
    """
    subclass_names = ['Object_Name', 'Array_Section', 'Array_Element',
                      'Structure_Component', 'Substring'
                      ]


class Logical_Variable(Base):  # R604
    """
    <logical-variable> = <variable>
    """
    subclass_names = ['Variable']


class Default_Logical_Variable(Base):  # R605
    """
    <default-logical-variable> = <variable>
    """
    subclass_names = ['Variable']


class Char_Variable(Base):  # R606
    """
    <char-variable> = <variable>
    """
    subclass_names = ['Variable']


class Default_Char_Variable(Base):  # R607
    """
    <default-char-variable> = <variable>
    """
    subclass_names = ['Variable']


class Int_Variable(Base):  # R608
    """
    <int-variable> = <variable>
    """
    subclass_names = ['Variable']


class Substring(CallBase):  # R609
    """
    <substring> = <parent-string> ( <substring-range> )
    """
    subclass_names = []
    use_names = ['Parent_String', 'Substring_Range']

    def match(string):
        return CallBase.match(
            Parent_String, Substring_Range, string, require_rhs=True)
    match = staticmethod(match)


class Parent_String(Base):  # R610
    """
    <parent-string> = <scalar-variable-name>
                      | <array-element>
                      | <scalar-structure-component>
                      | <scalar-constant>
    """
    subclass_names = ['Scalar_Variable_Name', 'Array_Element',
                      'Scalar_Structure_Component', 'Scalar_Constant']


class Substring_Range(SeparatorBase):  # R611
    """
    <substring-range> = [ <scalar-int-expr> ] : [ <scalar-int-expr> ]
    """
    subclass_names = []
    use_names = ['Scalar_Int_Expr']

    @staticmethod
    def match(string):
        return SeparatorBase.match(Scalar_Int_Expr, Scalar_Int_Expr, string)


class Data_Ref(SequenceBase):
    '''
    Fortran 2003 Rule R612

    data-ref is part-ref [ % part-ref ] ...

    If there is only one part-ref then return a 'Part_Ref' object (or
    another object from a matching sub-rule). If there is more than
    one part-ref then return a 'Data_Ref' object containing the
    part-ref's.

    '''
    subclass_names = ['Part_Ref']
    use_names = []

    @staticmethod
    def match(string):
        '''Implements the matching for a data-reference. This defines a series
        of dereferences e.g. a%b%c.

        If there is more than one part-ref then return a 'Data_Ref'
        object containing the part-ref's, otherwise return 'None'. A
        single 'part-ref' is purposely not matched here.

        :param str string: Fortran code to check for a match

        :return: `None` if there is no match, or a tuple containing \
                 the matched operator as a string and another tuple \
                 containing the matched subclasses.

        :rtype: NoneType or (str, (obj, obj, ...))

        '''
        # Use SequenceBase as normal, then force no match when there is
        # only one entry in the sequence.
        result = SequenceBase.match(r'%', Part_Ref, string)
        entries = result[1]
        if len(entries) > 1:
            # There is more than one part-ref so return a Data_Ref
            # object containing the part-refs.
            return result
        # There is only one part-ref so return None to indicate there
        # is no match and allow the subclass_names Part_Ref class to
        # match instead.
        return None


class Part_Ref(CallBase):  # R613
    """
    <part-ref> = <part-name> [ ( <section-subscript-list> ) ]
    """
    subclass_names = ['Part_Name']
    use_names = ['Section_Subscript_List']

    def match(string):
        return CallBase.match(
            Part_Name, Section_Subscript_List, string, require_rhs=True)
    match = staticmethod(match)


class Structure_Component(Base):  # R614
    """
    <structure-component> = <data-ref>
    """
    subclass_names = ['Data_Ref']


class Type_Param_Inquiry(BinaryOpBase):  # R615
    """
    <type-param-inquiry> = <designator> % <type-param-name>
    """
    subclass_names = []
    use_names = ['Designator', 'Type_Param_Name']

    def match(string):
        return BinaryOpBase.match(
            Designator, pattern.percent_op.named(), Type_Param_Name, string)
    match = staticmethod(match)


class Array_Element(Base):  # R616
    """
    <array-element> = <data-ref>
    """
    subclass_names = ['Data_Ref']


class Array_Section(CallBase):  # R617
    """
    <array-section> = <data-ref> [ ( <substring-range> ) ]
    """
    subclass_names = ['Data_Ref']
    use_names = ['Substring_Range']

    def match(string):
        return CallBase.match(
            Data_Ref, Substring_Range, string, require_rhs=True)
    match = staticmethod(match)


class Subscript(Base):  # R618
    """
    <subscript> = <scalar-int-expr>
    """
    subclass_names = ['Scalar_Int_Expr']


class Section_Subscript(Base):  # R619
    """
    <section-subscript> = <subscript>
                          | <subscript-triplet>
                          | <vector-subscript>
    """
    subclass_names = ['Subscript_Triplet', 'Vector_Subscript', 'Subscript']


class Subscript_Triplet(Base):  # R620
    """
    <subscript-triplet> = [ <subscript> ] : [ <subscript> ] [ : <stride> ]
    """
    subclass_names = []
    use_names = ['Subscript', 'Stride']

    def match(string):
        line, repmap = string_replace_map(string)
        t = line.split(':')
        if len(t) <= 1 or len(t) > 3:
            return
        lhs_obj, rhs_obj, stride_obj = None, None, None
        if len(t) == 2:
            lhs, rhs = t[0].rstrip(), t[1].lstrip()
        else:
            lhs, rhs, stride = t[0].rstrip(), t[1].strip(), t[2].lstrip()
            if stride:
                stride_obj = Stride(repmap(stride))
        if lhs:
            lhs_obj = Subscript(repmap(lhs))
        if rhs:
            rhs_obj = Subscript(repmap(rhs))
        return lhs_obj, rhs_obj, stride_obj
    match = staticmethod(match)

    def tostr(self):
        s = ''
        if self.items[0] is not None:
            s += str(self.items[0]) + ' :'
        else:
            s += ':'
        if self.items[1] is not None:
            s += ' ' + str(self.items[1])
        if self.items[2] is not None:
            s += ' : ' + str(self.items[2])
        return s


class Stride(Base):  # R621
    """
    <stride> = <scalar-int-expr>
    """
    subclass_names = ['Scalar_Int_Expr']


class Vector_Subscript(Base):  # R622
    """
    <vector-subscript> = <int-expr>
    """
    subclass_names = ['Int_Expr']


class Allocate_Stmt(StmtBase):  # R623
    """
    <allocate-stmt> = ALLOCATE ( [ <type-spec> :: ] <allocation-list>
        [ , <alloc-opt-list> ] )
    """
    subclass_names = []
    use_names = ['Type_Spec', 'Allocation_List', 'Alloc_Opt_List']

    @staticmethod
    def match(string):
        if string[:8].upper() != 'ALLOCATE':
            return
        line = string[8:].lstrip()
        if not line or line[0] != '(' or line[-1] != ')':
            return
        line, repmap = string_replace_map(line[1:-1].strip())
        i = line.find('::')
        spec = None
        if i != -1:
            spec = Type_Spec(repmap(line[:i].rstrip()))
            line = line[i+2:].lstrip()
        i = line.find('=')
        opts = None
        if i != -1:
            j = line[:i].rfind(',')
            assert j != -1, repr((i, j, line))
            opts = Alloc_Opt_List(repmap(line[j+1:].lstrip()))
            line = line[:j].rstrip()
        return spec, Allocation_List(repmap(line)), opts

    def tostr(self):
        spec, lst, opts = self.items
        if spec is not None:
            if opts is not None:
                return 'ALLOCATE(%s::%s, %s)' % (spec, lst, opts)
            else:
                return 'ALLOCATE(%s::%s)' % (spec, lst)
        elif opts is not None:
            return 'ALLOCATE(%s, %s)' % (lst, opts)
        else:
            return 'ALLOCATE(%s)' % (lst)


class Alloc_Opt(KeywordValueBase):  # R624
    """
    <alloc-opt> = STAT = <stat-variable>
                  | ERRMSG = <errmsg-variable>
                  | SOURCE = <source-expr>
    """
    subclass_names = []
    use_names = ['Stat_Variable', 'Errmsg_Variable', 'Source_Expr']

    def match(string):
        for (k, v) in [('STAT', Stat_Variable),
                       ('ERRMSG', Errmsg_Variable),
                       ('SOURCE', Source_Expr)]:
            try:
                obj = KeywordValueBase.match(k, v, string, upper_lhs=True)
            except NoMatchError:
                obj = None
            if obj is not None:
                return obj
        return
    match = staticmethod(match)


class Stat_Variable(Base):  # R625
    """
    <stat-variable> = <scalar-int-variable>
    """
    subclass_names = ['Scalar_Int_Variable']


class Errmsg_Variable(Base):  # R626
    """
    <errmsg-variable> = <scalar-default-char-variable>
    """
    subclass_names = ['Scalar_Default_Char_Variable']


class Source_Expr(Base):  # R627
    """
    <source-expr> = <expr>
    """
    subclass_names = ['Expr']


class Allocation(CallBase):  # R628
    """
    <allocation> = <allocate-object> [ ( <allocate-shape-spec-list> ) ]
                 | <variable-name>
    """
    subclass_names = ['Variable_Name', 'Allocate_Object']
    use_names = ['Allocate_Shape_Spec_List']

    def match(string):
        return CallBase.match(
            Allocate_Object, Allocate_Shape_Spec_List, string,
            require_rhs=True)
    match = staticmethod(match)


class Allocate_Object(Base):  # R629
    """
    <allocate-object> = <variable-name>
                        | <structure-component>
    """
    subclass_names = ['Variable_Name', 'Structure_Component']


class Allocate_Shape_Spec(SeparatorBase):  # R630
    """
    <allocate-shape-spec> = [ <lower-bound-expr> : ] <upper-bound-expr>
    """
    subclass_names = []
    use_names = ['Lower_Bound_Expr', 'Upper_Bound_Expr']

    def match(string):
        line, repmap = string_replace_map(string)
        if ':' not in line:
            return None, Upper_Bound_Expr(string)
        lower, upper = line.split(':', 1)
        lower = lower.rstrip()
        upper = upper.lstrip()
        if not upper:
            return
        if not lower:
            return
        return Lower_Bound_Expr(repmap(lower)), Upper_Bound_Expr(repmap(upper))
    match = staticmethod(match)

    def tostr(self):
        if self.items[0] is None:
            return str(self.items[1])
        return SeparatorBase.tostr(self)


class Lower_Bound_Expr(Base):  # R631
    """
    <lower-bound-expr> = <scalar-int-expr>
    """
    subclass_names = ['Scalar_Int_Expr']


class Upper_Bound_Expr(Base):  # R632
    """
    <upper-bound-expr> = <scalar-int-expr>
    """
    subclass_names = ['Scalar_Int_Expr']


class Nullify_Stmt(StmtBase, CALLBase):  # R633
    """
    <nullify-stmt> = NULLIFY ( <pointer-object-list> )
    """
    subclass_names = []
    use_names = ['Pointer_Object_List']

    def match(string):
        return CALLBase.match(
            'NULLIFY', Pointer_Object_List, string, require_rhs=True)
    match = staticmethod(match)


class Pointer_Object(Base):  # R634
    """
    <pointer-object> = <variable-name>
                       | <structure-component>
                       | <proc-pointer-name>
    """
    subclass_names = ['Variable_Name', 'Structure_Component',
                      'Proc_Pointer_Name']


class Deallocate_Stmt(StmtBase):  # R635
    """
    <deallocate-stmt> = DEALLOCATE ( <allocate-object-list> [
        , <dealloc-opt-list> ] )
    """
    subclass_names = []
    use_names = ['Allocate_Object_List', 'Dealloc_Opt_List']

    @staticmethod
    def match(string):
        if string[:10].upper() != 'DEALLOCATE':
            return
        line = string[10:].lstrip()
        if not line or line[0] != '(' or line[-1] != ')':
            return
        line, repmap = string_replace_map(line[1:-1].strip())
        i = line.find('=')
        opts = None
        if i != -1:
            j = line[:i].rfind(',')
            assert j != -1, repr((i, j, line))
            opts = Dealloc_Opt_List(repmap(line[j+1:].lstrip()))
            line = line[:j].rstrip()
        return Allocate_Object_List(repmap(line)), opts

    def tostr(self):
        if self.items[1] is not None:
            return 'DEALLOCATE(%s, %s)' % (self.items)
        return 'DEALLOCATE(%s)' % (self.items[0])


class Dealloc_Opt(KeywordValueBase):  # R636
    """
    <dealloc-opt> = STAT = <stat-variable>
                    | ERRMSG = <errmsg-variable>
    """
    subclass_names = []
    use_names = ['Stat_Variable', 'Errmsg_Variable']

    def match(string):
        for (k, v) in [('STAT', Stat_Variable),
                       ('ERRMSG', Errmsg_Variable),
                       ]:
            try:
                obj = KeywordValueBase.match(k, v, string, upper_lhs=True)
            except NoMatchError:
                obj = None
            if obj is not None:
                return obj
        return
    match = staticmethod(match)


class Scalar_Char_Initialization_Expr(Base):
    subclass_names = ['Char_Initialization_Expr']

#
# SECTION  7
#


class Primary(Base):  # R701
    '''Fortran 2003 rule R701

    primary is intrinsic_function_reference
            or constant
            or designator
            or array-constructor
            or structure-constructor
            or function-reference
            or type-param-inquiry
            or type-param-name
            or ( expr )

    `intrinsic_function_reference` is not part of rule R701 but is
    required for fparser to recognise intrinsic functions. This is
    placed before array-constructor in the `subclass_names` list so
    that an intrinsic is not (incorrectly) matched as an array (as
    class `Base` matches rules in list order).

    '''
    subclass_names = [
        'Intrinsic_Function_Reference',
        'Constant', 'Designator', 'Array_Constructor',
        'Structure_Constructor', 'Function_Reference',
        'Type_Param_Inquiry', 'Type_Param_Name', 'Parenthesis',
    ]


class Parenthesis(BracketBase):  # R701.h
    """
    <parenthesis> = ( <expr> )
    """
    subclass_names = []
    use_names = ['Expr']

    def match(string):
        return BracketBase.match('()', Expr, string)
    match = staticmethod(match)


class Level_1_Expr(UnaryOpBase):  # R702
    """
    <level-1-expr> = [ <defined-unary-op> ] <primary>
    <defined-unary-op> = . <letter> [ <letter> ]... .
    """
    subclass_names = ['Primary']
    use_names = []

    def match(string):
        return UnaryOpBase.match(
            pattern.defined_unary_op.named(), Primary, string)
    # exclude_op_pattern = pattern.non_defined_binary_op)
    match = staticmethod(match)


class Defined_Unary_Op(STRINGBase):  # pylint: disable=invalid-name
    '''
    Fortran 2003 rule R703

    defined-unary-op is . letter [ letter ]... .

    C704 (R703) A defined-unary-op shall not contain more than 63
    letters and shall not be the same as any intrinsic-operator or
    logical-literal-constant.

    Implemented in Defined_Op class.

    '''
    subclass_names = ['Defined_Op']


class Defined_Op(STRINGBase):  # pylint: disable=invalid-name
    '''
    Utility class that Implements the functionality of rules R703 and
    R723 (as the rules are the same)

    defined-op is . letter [ letter ]... .

    C704 (R723) A defined-binary-op shall not contain more than 63
    letters and shall not be the same as any intrinsic-operator or
    logical-literal-constant.

    C704 (R703) A defined-unary-op shall not contain more than 63
    letters and shall not be the same as any intrinsic-operator or
    logical-literal-constant.

    '''
    subclass_names = []

    @staticmethod
    def match(string):
        '''Implements the matching for a (user) Defined Unary or Binary
        Operator.

        :param str string: Fortran code to check for a match
        :return: `None` if there is no match, or a tuple containing \
                 the matched operator as a string
        :rtype: None or (str)

        '''
        strip_string = string.strip()
        if len(strip_string) > 65:
            # C704. Must be 63 letters or fewer (Test for >65 due
            # to the two dots).
            return None
        if pattern.non_defined_binary_op.match(strip_string):
            # C704. Must not match with an intrinsic-operator or
            # logical-literal-constant
            return None
        return STRINGBase.match(pattern.abs_defined_op, strip_string)


class Mult_Operand(BinaryOpBase):  # R704
    """
    <mult-operand> = <level-1-expr> [ <power-op> <mult-operand> ]
    <power-op> = **
    """
    subclass_names = ['Level_1_Expr']
    use_names = ['Mult_Operand']

    def match(string):
        return BinaryOpBase.match(
            Level_1_Expr, pattern.power_op.named(), Mult_Operand,
            string, right=False)
    match = staticmethod(match)


class Add_Operand(BinaryOpBase):  # R705
    """
    <add-operand> = [ <add-operand> <mult-op> ] <mult-operand>
    <mult-op>  = *
                 | /
    """
    subclass_names = ['Mult_Operand']
    use_names = ['Add_Operand', 'Mult_Operand']

    def match(string):
        return BinaryOpBase.match(
            Add_Operand, pattern.mult_op.named(), Mult_Operand, string)
    match = staticmethod(match)


class Level_2_Expr(BinaryOpBase):  # R706
    """
    <level-2-expr> = [ [ <level-2-expr> ] <add-op> ] <add-operand>
    <level-2-expr> = [ <level-2-expr> <add-op> ] <add-operand>
                     | <level-2-unary-expr>
    <add-op>   = +
                 | -
    """
    subclass_names = ['Level_2_Unary_Expr']
    use_names = ['Level_2_Expr']

    def match(string):
        return BinaryOpBase.match(
            Level_2_Expr, pattern.add_op.named(), Add_Operand,
            string, is_add=True)
    match = staticmethod(match)


class Level_2_Unary_Expr(UnaryOpBase):  # R706.c
    """
    <level-2-unary-expr> = [ <add-op> ] <add-operand>
    """
    subclass_names = ['Add_Operand']
    use_names = []

    def match(string):
        return UnaryOpBase.match(
            pattern.add_op.named(), Add_Operand, string)
    match = staticmethod(match)

# R707: <power-op> = **
# R708: <mult-op> = * | /
# R709: <add-op> = + | -


class Level_3_Expr(BinaryOpBase):  # R710
    """
    <level-3-expr> = [ <level-3-expr> <concat-op> ] <level-2-expr>
    <concat-op>    = //
    """
    subclass_names = ['Level_2_Expr']
    use_names = ['Level_3_Expr']

    def match(string):
        return BinaryOpBase.match(
            Level_3_Expr, pattern.concat_op.named(),
            Level_2_Expr, string)
    match = staticmethod(match)

# R711: <concat-op> = //


class Level_4_Expr(BinaryOpBase):  # R712
    """
    <level-4-expr> = [ <level-3-expr> <rel-op> ] <level-3-expr>
    <rel-op> = .EQ. | .NE. | .LT. | .LE. | .GT. | .GE. | == |
        /= | < | <= | > | >=
    """
    subclass_names = ['Level_3_Expr']
    use_names = []

    def match(string):
        return BinaryOpBase.match(
            Level_3_Expr, pattern.rel_op.named(), Level_3_Expr,
            string)
    match = staticmethod(match)

# R713: <rel-op> = .EQ. | .NE. | .LT. | .LE. | .GT. | .GE. |
# == | /= | < | <= | > | >=


class And_Operand(UnaryOpBase):  # R714
    """
    <and-operand> = [ <not-op> ] <level-4-expr>
    <not-op> = .NOT.
    """
    subclass_names = ['Level_4_Expr']
    use_names = []

    def match(string):
        return UnaryOpBase.match(
            pattern.not_op.named(), Level_4_Expr, string)
    match = staticmethod(match)


class Or_Operand(BinaryOpBase):  # R715
    """
    <or-operand> = [ <or-operand> <and-op> ] <and-operand>
    <and-op> = .AND.
    """
    subclass_names = ['And_Operand']
    use_names = ['Or_Operand', 'And_Operand']

    @staticmethod
    def match(string):
        return BinaryOpBase.match(
            Or_Operand, pattern.and_op.named(), And_Operand, string)


class Equiv_Operand(BinaryOpBase):  # R716
    """
    <equiv-operand> = [ <equiv-operand> <or-op> ] <or-operand>
    <or-op>  = .OR.
    """
    subclass_names = ['Or_Operand']
    use_names = ['Equiv_Operand']

    def match(string):
        return BinaryOpBase.match(
            Equiv_Operand, pattern.or_op.named(), Or_Operand, string)
    match = staticmethod(match)


class Level_5_Expr(BinaryOpBase):  # R717
    """
    <level-5-expr> = [ <level-5-expr> <equiv-op> ] <equiv-operand>
    <equiv-op> = .EQV.
               | .NEQV.
    """
    subclass_names = ['Equiv_Operand']
    use_names = ['Level_5_Expr']

    def match(string):
        return BinaryOpBase.match(
            Level_5_Expr, pattern.equiv_op.named(), Equiv_Operand, string)
    match = staticmethod(match)

# R718: <not-op> = .NOT.
# R719: <and-op> = .AND.
# R720: <or-op> = .OR.
# R721: <equiv-op> = .EQV. | .NEQV.


class Expr(BinaryOpBase):  # R722
    """
    <expr> = [ <expr> <defined-binary-op> ] <level-5-expr>
    <defined-binary-op> = . <letter> [ <letter> ]... .
    """
    subclass_names = ['Level_5_Expr']
    use_names = ['Expr']

    def match(string):
        return BinaryOpBase.match(
            Expr, pattern.defined_binary_op.named(), Level_5_Expr,
            string, exclude_op_pattern=pattern.non_defined_binary_op)
    match = staticmethod(match)


class Defined_Binary_Op(STRINGBase):  # pylint: disable=invalid-name
    '''
    Fortran 2003 rule R723

    defined-binary-op is . letter [ letter ]... .

    C704 (R723) A defined-binary-op shall not contain more than 63
    letters and shall not be the same as any intrinsic-operator or
    logical-literal-constant.

    Implemented in Defined_Op class.

    '''
    subclass_names = ['Defined_Op']


class Logical_Expr(Base):  # R724
    """
    <logical-expr> = <expr>
    """
    subclass_names = ['Expr']


class Char_Expr(Base):  # R725
    """
    <char-expr> = <expr>
    """
    subclass_names = ['Expr']


class Default_Char_Expr(Base):  # R726
    """
    <default-char-expr> = <expr>
    """
    subclass_names = ['Expr']


class Int_Expr(Base):  # R727
    """
    <int-expr> = <expr>
    """
    subclass_names = ['Expr']


class Numeric_Expr(Base):  # R728
    """
    <numeric-expr> = <expr>
    """
    subclass_names = ['Expr']


class Specification_Expr(Base):  # R729
    """
    <specification-expr> = <scalar-int-expr>
    """
    subclass_names = ['Scalar_Int_Expr']


class Initialization_Expr(Base):  # R730
    """
    <initialization-expr> = <expr>
    """
    subclass_names = ['Expr']


class Char_Initialization_Expr(Base):  # R731
    """
    <char-initialization-expr> = <char-expr>
    """
    subclass_names = ['Char_Expr']


class Int_Initialization_Expr(Base):  # R732
    """
    <int-initialization-expr> = <int-expr>
    """
    subclass_names = ['Int_Expr']


class Logical_Initialization_Expr(Base):  # R733
    """
    <logical-initialization-expr> = <logical-expr>
    """
    subclass_names = ['Logical_Expr']


class Assignment_Stmt(StmtBase, BinaryOpBase):  # R734
    """
    <assignment-stmt> = <variable> = <expr>
    """
    subclass_names = []
    use_names = ['Variable', 'Expr']

    @staticmethod
    def match(string):
        return BinaryOpBase.match(Variable, '=', Expr, string, right=False)


class Pointer_Assignment_Stmt(StmtBase):  # R735
    """
    <pointer-assignment-stmt> = <data-pointer-object> [
        ( <bounds-spec-list> ) ] => <data-target>
        | <data-pointer-object> ( <bounds-remapping-list> ) => <data-target>
        | <proc-pointer-object> => <proc-target>
    """
    subclass_names = []
    use_names = ['Data_Pointer_Object', 'Bounds_Spec_List',
                 'Data_Target', 'Bounds_Remapping_List',
                 'Proc_Pointer_Object', 'Proc_Target']

    @staticmethod
    def match(string):
        line, repmap = string_replace_map(string)
        i = line.find('=>')
        if i == -1:
            return
        lhs = line[:i].rstrip()
        rhs = repmap(line[i+2:].lstrip())
        if lhs.endswith(')'):
            i = lhs.rfind('(')
            if i == -1:
                return
            o = repmap(lhs[:i].rstrip())
            tmp = repmap(lhs[i+1:-1].strip())
            try:
                return Data_Pointer_Object(o), Bounds_Spec_List(tmp), \
                    Data_Target(rhs)
            except NoMatchError as msg:
                return Data_Pointer_Object(o), Bounds_Remapping_List(tmp), \
                    Data_Target(rhs)
        else:
            lhs = repmap(lhs)
        try:
            return Data_Pointer_Object(lhs), None, Data_Target(rhs)
        except NoMatchError as msg:
            return Proc_Pointer_Object(lhs), None, Proc_Target(rhs)

    def tostr(self):
        if self.items[1] is None:
            return '%s => %s' % (self.items[0], self.items[2])
        return '%s(%s) => %s' % (self.items)


class Data_Pointer_Object(BinaryOpBase):  # R736
    """
    <data-pointer-object> = <variable-name>
                            | <variable> % <data-pointer-component-name>
    """
    subclass_names = ['Variable_Name']
    use_names = ['Variable', 'Data_Pointer_Component_Name']

    @staticmethod
    def match(string):
        return BinaryOpBase.match(
            Variable, r'%', Data_Pointer_Component_Name, string)


class Bounds_Spec(SeparatorBase):  # R737
    """
    <bounds-spec> = <lower-bound-expr> :
    """
    subclass_names = []
    use_names = ['Lower_Bound_Expr']

    def match(string):
        return SeparatorBase.match(
            Lower_Bound_Expr, None, string, require_lhs=True)
    match = staticmethod(match)


class Bounds_Remapping(SeparatorBase):  # R738
    """
    <bounds-remapping> = <lower-bound-expr> : <upper-bound-expr>
    """
    subclass_names = []
    use_classes = ['Lower_Bound_Expr', 'Upper_Bound_Expr']

    def match(string):
        return SeparatorBase.match(
            Lower_Bound_Expr, Upper_Bound_Expr, string, require_lhs=True,
            require_rhs=True)
    match = staticmethod(match)


class Data_Target(Base):  # R739
    """
    <data-target> = <variable>
                    | <expr>
    """
    subclass_names = ['Variable', 'Expr']


class Proc_Pointer_Object(Base):  # R740
    """
    <proc-pointer-object> = <proc-pointer-name>
                            | <proc-component-ref>
    """
    subclass_names = ['Proc_Pointer_Name', 'Proc_Component_Ref']


class Proc_Component_Ref(BinaryOpBase):  # R741
    """
    <proc-component-ref> = <variable> % <procedure-component-name>
    """
    subclass_names = []
    use_names = ['Variable', 'Procedure_Component_Name']

    def match(string):
        return BinaryOpBase.match(Variable, r'%', Procedure_Component_Name,
                                  string)
    match = staticmethod(match)


class Proc_Target(Base):  # R742
    """
    <proc-target> = <expr>
                    | <procedure-name>
                    | <proc-component-ref>
    """
    subclass_names = ['Proc_Component_Ref', 'Procedure_Name', 'Expr']


class Where_Stmt(StmtBase):  # R743
    """
    <where-stmt> = WHERE ( <mask-expr> ) <where-assignment-stmt>
    """
    subclass_names = []
    use_names = ['Mask_Expr', 'Where_Assignment_Stmt']

    def match(string):
        if string[:5].upper() != 'WHERE':
            return
        line, repmap = string_replace_map(string[5:].lstrip())
        if not line.startswith('('):
            return
        i = line.find(')')
        if i == -1:
            return
        stmt = repmap(line[i+1:].lstrip())
        if not stmt:
            return
        expr = repmap(line[1:i].strip())
        if not expr:
            return
        return Mask_Expr(expr), Where_Assignment_Stmt(stmt)
    match = staticmethod(match)

    def tostr(self):
        return 'WHERE (%s) %s' % tuple(self.items)


class Where_Construct(BlockBase):  # R744
    """
    <where-construct> = <where-construct-stmt>
                              [ <where-body-construct> ]...
                            [ <masked-elsewhere-stmt>
                              [ <where-body-construct> ]...
                            ]...
                            [ <elsewhere-stmt>
                              [ <where-body-construct> ]... ]
                            <end-where-stmt>
    """
    subclass_names = []
    use_names = ['Where_Construct_Stmt', 'Where_Body_Construct',
                 'Masked_Elsewhere_Stmt',
                 'Elsewhere_Stmt', 'End_Where_Stmt']

    @staticmethod
    def match(string):
        return BlockBase.match(
            Where_Construct_Stmt, [Where_Body_Construct,
                                   Masked_Elsewhere_Stmt,
                                   Where_Body_Construct,
                                   Elsewhere_Stmt,
                                   Where_Body_Construct, ],
            End_Where_Stmt, string,
            match_names=True,  # C730
            match_name_classes=(Masked_Elsewhere_Stmt, Elsewhere_Stmt,
                                End_Where_Stmt),  # C730
            enable_where_construct_hook=True)

    def tofortran(self, tab='', isfix=None):
        '''
        Converts this node (and all children) into Fortran.

        :param str tab: white space to prefix to output.
        :param bool isfix: whether or not to generate fixed-format output.

        :returns: Fortran code.
        :rtype: str

        '''
        tmp = []
        start = self.content[0]
        end = self.content[-1]
        tmp.append(start.tofortran(tab=tab, isfix=isfix))
        for item in self.content[1:-1]:
            if isinstance(item, (Masked_Elsewhere_Stmt, Elsewhere_Stmt)):
                tmp.append(item.tofortran(tab=tab, isfix=isfix))
            else:
                tmp.append(item.tofortran(tab=tab+'  ', isfix=isfix))
        tmp.append(end.tofortran(tab=tab, isfix=isfix))
        py2_encode_list_items(tmp)
        return '\n'.join(tmp)


class Where_Construct_Stmt(StmtBase):  # R745
    """
    <where-construct-stmt> = [ <where-construct-name> : ] WHERE ( <mask-expr> )
    """
    subclass_names = []
    use_names = ['Where_Construct_Name', 'Mask_Expr']

    @staticmethod
    def match(string):
        if string[:5].upper() != 'WHERE':
            return
        line = string[5:].lstrip()
        if not line:
            return
        if line[0] + line[-1] != '()':
            return
        line = line[1:-1].strip()
        if not line:
            return
        return Mask_Expr(line),

    def tostr(self):
        return 'WHERE (%s)' % tuple(self.items)

    def get_start_name(self):
        return self.item.name


class Where_Body_Construct(Base):  # R746
    """
::
    <where-body-construct> = <where-assignment-stmt>
                             | <where-stmt>
                             | <where-construct>
    """
    subclass_names = ['Where_Assignment_Stmt', 'Where_Stmt', 'Where_Construct']


class Where_Assignment_Stmt(Base):  # R747
    """
::
    <where-assignment-stmt> = <assignment-stmt>
    """
    subclass_names = ['Assignment_Stmt']


class Mask_Expr(Base):  # R748
    """
    <mask-expr> = <logical-expr>
    """
    subclass_names = ['Logical_Expr']


class Masked_Elsewhere_Stmt(StmtBase):  # R749
    """
    <masked-elsewhere-stmt> = ELSEWHERE
                              ( <mask-expr> ) [ <where-construct-name> ]
    """
    import re
    subclass_names = []
    use_names = ['Mask_Expr', 'Where_Construct_Name']

    @staticmethod
    def match(string):
        if not Elsewhere_Stmt._regex.match(string):
            return
        idx = string.upper().index("WHERE")
        line = string[idx+5:].lstrip()

        if not line.startswith('('):
            return
        i = line.rfind(')')
        if i == -1:
            return
        expr = line[1:i].strip()
        if not expr:
            return
        line = line[i+1:].rstrip()
        if line:
            return Mask_Expr(expr), Where_Construct_Name(line)
        return Mask_Expr(expr), None

    def tostr(self):
        if self.items[1] is None:
            return 'ELSEWHERE(%s)' % (self.items[0])
        return 'ELSEWHERE(%s) %s' % self.items

    def get_end_name(self):
        name = self.items[1]
        if name is not None:
            return name.string


class Elsewhere_Stmt(StmtBase, WORDClsBase):  # R750
    """
    <elsewhere-stmt> = ELSEWHERE [ <where-construct-name> ]
    """
    subclass_names = []
    use_names = ['Where_Construct_Name']
    _regex = re.compile(r'ELSE\s*WHERE', re.I)

    @staticmethod
    def match(string):
        if not Elsewhere_Stmt._regex.match(string):
            return
        idx = string.upper().index("WHERE")
        line = string[idx+5:].lstrip()
        if line:
            return "ELSEWHERE", Where_Construct_Name(line)
        return "ELSEWHERE", None

    def get_end_name(self):
        name = self.items[1]
        if name is not None:
            return name.string


class End_Where_Stmt(EndStmtBase):  # R751
    """
    <end-where-stmt> = END WHERE [ <where-construct-name> ]
    """
    subclass_names = []
    use_names = ['Where_Construct_Name']

    @staticmethod
    def match(string):
        return EndStmtBase.match(
            'WHERE', Where_Construct_Name, string, require_stmt_type=True)


class Forall_Construct(BlockBase):  # R752
    """
    <forall-construct> = <forall-construct-stmt>
                             [ <forall-body-construct> ]...
                             <end-forall-stmt>
    """
    subclass_names = []
    use_names = ['Forall_Construct_Stmt', 'Forall_Body_Construct',
                 'End_Forall_Stmt']

    @staticmethod
    def match(reader):
        return BlockBase.match(
            Forall_Construct_Stmt, [Forall_Body_Construct],
            End_Forall_Stmt, reader, match_names=True,  # C732
        )


class Forall_Construct_Stmt(StmtBase, WORDClsBase):  # R753
    """
    <forall-construct-stmt> = [ <forall-construct-name> : ]
        FORALL <forall-header>
    """
    subclass_names = []
    use_names = ['Forall_Construct_Name', 'Forall_Header']

    @staticmethod
    def match(string):
        return WORDClsBase.match(
            'FORALL', Forall_Header, string, require_cls=True)

    def get_start_name(self):
        return self.item.name


class Forall_Header(Base):  # pylint: disable=invalid-name
    '''
    Fortran 2003 rule R754
    forall-header is ( forall-triplet-spec-list [, scalar-mask-expr ] )

    '''
    subclass_names = []
    use_names = ['Forall_Triplet_Spec_List', 'Scalar_Mask_Expr']

    @staticmethod
    def match(string):
        '''Implements the matching for a Forall_Header.

        :param str string: A string containing the code to match.
        :return: `None` if there is no match, otherwise a `tuple` of \
                 size 2 containing a class of type \
                 `Forall_Triplet_Spec_List` and a class of type \
                 `Scalar_Mask_Expr` if there is a scalar mask \
                 expresssion and `None` if not.
        :rtype: (`Forall_Triplet_Spec_List`, `Scalar_Mask_Expr`) or \
                (`Forall_Triplet_Spec_List`, `None`) or `None`

        '''
        strip_string = string.strip()
        if not strip_string:
            # Input only contains white space
            return None
        if strip_string[0] + strip_string[-1] != '()':
            # Input does not start with '(' and end with ')'
            return None
        strip_string_nobr = strip_string[1:-1].strip()
        try:
            # first try to match without a scalar mask expression
            return Forall_Triplet_Spec_List(strip_string_nobr), None
        except NoMatchError:
            # The match failed so try to match with the optional
            # scalar mask expression. Use repmap to remove any
            # unexpected "," e.g. an array access a(i,j), when
            # splitting the string.
            mapped_string, repmap = string_replace_map(strip_string_nobr)
            split_string = mapped_string.rsplit(',', 1)
            if len(split_string) != 2:
                return None
            left_str = repmap(split_string[0].rstrip())
            right_str = repmap(split_string[1].lstrip())
            return (Forall_Triplet_Spec_List(left_str),
                    Scalar_Mask_Expr(right_str))

    def tostr(self):
        ''':return: this Forall Header as a string
        :rtype: str
        :raises InternalError: if the length of the internal items \
        list is not 2.
        :raises InternalError: if the first entry of the internal \
        items list has no content, as a Forall_Triplet_List is \
        expected.

        '''
        if len(self.items) != 2:
            raise InternalError(
                "Forall_Header.tostr(). 'items' should be of size 2 but "
                "found '{0}'.".format(len(self.items)))
        if not self.items[0]:
            raise InternalError(
                "Forall_Header.tostr(). 'items[0]' should be a "
                "Forall_Triplet_Spec_List instance but it is empty.")
        if not self.items[1]:
            # there is no scalar mask expression
            return "({0})".format(self.items[0])
        return "({0}, {1})".format(self.items[0], self.items[1])


class Forall_Triplet_Spec(Base):  # R755
    """
    <forall-triplet-spec> = <index-name> = <subscript> :
        <subscript> [ : <stride> ]
    """
    subclass_names = []
    use_names = ['Index_Name', 'Subscript', 'Stride']

    @staticmethod
    def match(string):
        line, repmap = string_replace_map(string)
        i = line.find('=')
        if i == -1:
            return
        n = Index_Name(repmap(line[:i].rstrip()))
        line = line[i+1:].lstrip()
        s = [repmap(s.strip()) for s in line.split(':')]
        if len(s) == 2:
            return n, Subscript(s[0]), Subscript(s[1]), None
        if len(s) == 3:
            return n, Subscript(s[0]), Subscript(s[1]), Stride(s[2])

    def tostr(self):
        if self.items[3] is None:
            return '%s = %s : %s' % (self.items[:3])
        return '%s = %s : %s : %s' % (self.items)


class Forall_Body_Construct(Base):  # R756
    """
    <forall-body-construct> = <forall-assignment-stmt>
                              | <where-stmt>
                              | <where-construct>
                              | <forall-construct>
                              | <forall-stmt>
    """
    subclass_names = ['Forall_Assignment_Stmt', 'Where_Stmt',
                      'Where_Construct', 'Forall_Construct',
                      'Forall_Stmt']


class Forall_Assignment_Stmt(Base):  # R757
    """
    <forall-assignment-stmt> = <assignment-stmt>
                               | <pointer-assignment-stmt>
    """
    subclass_names = ['Assignment_Stmt', 'Pointer_Assignment_Stmt']


class End_Forall_Stmt(EndStmtBase):  # R758
    """
    <end-forall-stmt> = END FORALL [ <forall-construct-name> ]
    """
    subclass_names = []
    use_names = ['Forall_Construct_Name']

    @staticmethod
    def match(string):
        return EndStmtBase.match(
            'FORALL', Forall_Construct_Name, string, require_stmt_type=True)


class Forall_Stmt(StmtBase):  # pylint: disable=invalid-name
    '''
    Fortran 2003 rule R759
    forall-stmt is FORALL forall-header forall-assignment-stmt

    '''
    subclass_names = []
    use_names = ['Forall_Header', 'Forall_Assignment_Stmt']

    @staticmethod
    def match(string):
        '''Implements the matching for a forall statement.

        :param string: A string or the fortran reader containing the \
                    line of code that we are trying to match.
        :type string: `str` or \
        :py:class:`fparser.common.readfortran.FortranReader`
        :return: `None` if there is no match or a `tuple` of size 2 \
        containing an instance of the Forall_Header class followed by \
        an instance of the Forall_Assignment_Stmt class.
        :rtype: `None` or ( \
        :py:class:`fparser.two.Fortran2003.Forall_Header`, \
        :py:class:`fparser.two.Fortran2003.Forall_Assignment_Stmt`)

        '''
        strip_string = string.strip()
        if strip_string[:6].upper() != 'FORALL':
            return None
        line, repmap = string_replace_map(strip_string[6:].lstrip())
        if not line.startswith('('):
            return None
        index = line.find(')')
        if index == -1:
            return None
        header = repmap(line[:index+1])
        # No need to check if header variable is empty as we know it
        # will contain brackets at least
        line = repmap(line[index+1:].lstrip())
        if not line:
            return None
        return Forall_Header(header), Forall_Assignment_Stmt(line)

    def tostr(self):
        '''
        :return: this forall statement as a string
        :rtype: str
        :raises InternalError: if the internal items list variable is \
        not the expected size.
        :raises InternalError: if the first element of the internal \
        items list is None or is an empty string.
        :raises InternalError: if the second element of the internal \
        items list is None or is an empty string.
        '''
        if len(self.items) != 2:
            raise InternalError(
                "Class Forall_Stmt method tostr() has '{0}' items, "
                "but expecting 2.".format(len(self.items)))
        if not self.items[0]:
            raise InternalError(
                "Class Forall_Stmt method tostr(). 'Items' entry 0 "
                "should be a valid Forall_Header.")
        if not self.items[1]:
            raise InternalError(
                "Class Forall_Stmt method tostr(). 'Items' entry 1 should "
                "be a valid Forall_Assignment_Stmt")
        return "FORALL {0} {1}".format(self.items[0], self.items[1])

#
# SECTION  8
#


class Block(BlockBase):  # R801
    """
    <block> = [ <execution-part-construct> ]...
    """
    subclass_names = []
    use_names = ['Execution_Part_Construct']

    @staticmethod
    def match(string):
        return BlockBase.match(None, [Execution_Part_Construct], None, string)


class If_Construct(BlockBase):  # R802
    """
    <if-construct> = <if-then-stmt>
                           <block>
                         [ <else-if-stmt>
                           <block>
                         ]...
                         [ <else-stmt>
                           <block>
                         ]
                         <end-if-stmt>
    """
    subclass_names = []
    use_names = ['If_Then_Stmt', 'Block', 'Else_If_Stmt',
                 'Else_Stmt', 'End_If_Stmt']

    @staticmethod
    def match(string):
        return BlockBase.match(
            If_Then_Stmt, [Execution_Part_Construct,
                           Else_If_Stmt,
                           Execution_Part_Construct,
                           Else_Stmt,
                           Execution_Part_Construct],
            End_If_Stmt, string,
            match_names=True,  # C801
            match_name_classes=(Else_If_Stmt, Else_Stmt, End_If_Stmt),
            enable_if_construct_hook=True)

    def tofortran(self, tab='', isfix=None):
        '''
        Converts this node (and all children) into Fortran.

        :param str tab: white space to prefix to output.
        :param bool isfix: whether or not to generate fixed-format output.

        :returns: Fortran code.
        :rtype: str

        '''
        tmp = []
        start = self.content[0]
        end = self.content[-1]
        tmp.append(start.tofortran(tab=tab, isfix=isfix))
        for item in self.content[1:-1]:
            if isinstance(item, (Else_If_Stmt, Else_Stmt)):
                tmp.append(item.tofortran(tab=tab, isfix=isfix))
            else:
                tmp.append(item.tofortran(tab=tab+'  ', isfix=isfix))
        tmp.append(end.tofortran(tab=tab, isfix=isfix))
        py2_encode_list_items(tmp)
        return '\n'.join(tmp)


class If_Then_Stmt(StmtBase):  # R803
    """
    <if-then-stmt> = [ <if-construct-name> : ]
        IF ( <scalar-logical-expr> ) THEN
    """
    subclass_names = []
    use_names = ['If_Construct_Name', 'Scalar_Logical_Expr']

    @staticmethod
    def match(string):
        if string[:2].upper() != 'IF':
            return
        if string[-4:].upper() != 'THEN':
            return
        line = string[2:-4].strip()
        if not line:
            return
        if line[0] + line[-1] != '()':
            return
        return Scalar_Logical_Expr(line[1:-1].strip()),

    def tostr(self):
        return 'IF (%s) THEN' % self.items

    def get_start_name(self):
        return self.item.name


class Else_If_Stmt(StmtBase):  # R804
    """
    <else-if-stmt> = ELSE IF ( <scalar-logical-expr> ) THEN
        [ <if-construct-name> ]
    """
    subclass_names = []
    use_names = ['Scalar_Logical_Expr', 'If_Construct_Name']

    @staticmethod
    def match(string):
        if string[:4].upper() != 'ELSE':
            return
        line = string[4:].lstrip()
        if line[:2].upper() != 'IF':
            return
        line = line[2:].lstrip()
        if not line.startswith('('):
            return
        i = line.rfind(')')
        if i == -1:
            return
        expr = line[1:i].strip()
        line = line[i+1:].lstrip()
        if line[:4].upper() != 'THEN':
            return
        line = line[4:].lstrip()
        if line:
            return Scalar_Logical_Expr(expr), If_Construct_Name(line)
        return Scalar_Logical_Expr(expr), None

    def tostr(self):
        if self.items[1] is None:
            return 'ELSE IF (%s) THEN' % (self.items[0])
        return 'ELSE IF (%s) THEN %s' % self.items

    def get_end_name(self):
        name = self.items[1]
        if name is not None:
            return name.string


class Else_Stmt(StmtBase):  # R805
    """
    <else-stmt> = ELSE [ <if-construct-name> ]
    """
    subclass_names = []
    use_names = ['If_Construct_Name']

    @staticmethod
    def match(string):
        if string[:4].upper() != 'ELSE':
            return
        line = string[4:].lstrip()
        if line:
            return If_Construct_Name(line),
        return None,

    def tostr(self):
        if self.items[0] is None:
            return 'ELSE'
        return 'ELSE %s' % self.items

    def get_end_name(self):
        name = self.items[0]
        if name is not None:
            return name.string


class End_If_Stmt(EndStmtBase):  # R806
    """
    <end-if-stmt> = END IF [ <if-construct-name> ]
    """
    subclass_names = []
    use_names = ['If_Construct_Name']

    @staticmethod
    def match(string):
        return EndStmtBase.match(
            'IF', If_Construct_Name, string, require_stmt_type=True)


class If_Stmt(StmtBase):  # R807
    """
    <if-stmt> = IF ( <scalar-logical-expr> ) <action-stmt>
    """
    subclass_names = []
    use_names = ['Scalar_Logical_Expr', 'Action_Stmt_C802']

    @staticmethod
    def match(string):
        if string[:2].upper() != 'IF':
            return
        line, repmap = string_replace_map(string)
        line = line[2:].lstrip()
        if not line.startswith('('):
            return
        i = line.find(')')
        if i == -1:
            return
        expr = repmap(line[1:i].strip())
        stmt = repmap(line[i+1:].lstrip())
        return Scalar_Logical_Expr(expr), Action_Stmt_C802(stmt)

    def tostr(self):
        return 'IF (%s) %s' % self.items


class Case_Construct(BlockBase):  # R808
    """
    <case-construct> = <select-case-stmt>
                           [ <case-stmt>
                             <block> == [<execution-part-construct>]..
                           ]..
                           <end-select-stmt>
    """
    subclass_names = []
    use_names = ['Select_Case_Stmt', 'Case_Stmt',
                 'End_Select_Stmt', 'Execution_Part_Construct']

    @staticmethod
    def match(reader):
        return BlockBase.match(
            Select_Case_Stmt, [Case_Stmt,
                               Execution_Part_Construct,
                               Case_Stmt],
            End_Select_Stmt, reader,
            match_names=True,  # C803
            enable_case_construct_hook=True  # C803
        )

    def tofortran(self, tab='', isfix=None):
        '''
        Converts this node (and all children) into Fortran.

        :param str tab: white space to prefix to output.
        :param bool isfix: whether or not to generate fixed-format output.

        :returns: Fortran code.
        :rtype: str

        '''
        tmp = []
        start = self.content[0]
        end = self.content[-1]
        tmp.append(start.tofortran(tab=tab, isfix=isfix))
        for item in self.content[1:-1]:
            if isinstance(item, Case_Stmt):
                tmp.append(item.tofortran(tab=tab, isfix=isfix))
            else:
                tmp.append(item.tofortran(tab=tab + '  ', isfix=isfix))
        tmp.append(end.tofortran(tab=tab, isfix=isfix))
        # Ensure all strings in list are encoded consistently
        py2_encode_list_items(tmp)
        return '\n'.join(tmp)


class Select_Case_Stmt(StmtBase, CALLBase):  # R809
    """
    <select-case-stmt> = [ <case-construct-name> : ]
        SELECT CASE ( <case-expr> )
    """
    subclass_names = []
    use_names = ['Case_Construct_Name', 'Case_Expr']

    @staticmethod
    def match(string):
        if string[:6].upper() != 'SELECT':
            return
        line = string[6:].lstrip()
        if line[:4].upper() != 'CASE':
            return
        line = line[4:].lstrip()
        if not line or line[0]+line[-1] != '()':
            return
        line = line[1:-1].strip()
        return Case_Expr(line),

    def tostr(self):
        return 'SELECT CASE (%s)' % (self.items[0])

    def get_start_name(self):
        return self.item.name


class Case_Stmt(StmtBase):  # R810
    """
    <case-stmt> = CASE <case-selector> [ <case-construct-name> ]
    """
    subclass_names = []
    use_names = ['Case_Selector', 'Case_Construct_Name']

    @staticmethod
    def match(string):
        if string[:4].upper() != 'CASE':
            return
        line, repmap = string_replace_map(string[4:].lstrip())
        if line.startswith('('):
            i = line.find(')')
            if i == -1:
                return
            n = line[i+1:].lstrip() or None
            if n:
                n = Case_Construct_Name(repmap(n))
            return Case_Selector(repmap(line[:i+1].rstrip())), n
        if line[:7].upper() == 'DEFAULT':
            n = repmap(line[7:].lstrip()) or None
            if n:
                n = Case_Construct_Name(repmap(n))
            return Case_Selector(line[:7]), n

    def tostr(self):
        if self.items[1] is None:
            return 'CASE %s' % (self.items[0])
        return 'CASE %s %s' % (self.items)


class End_Select_Stmt(EndStmtBase):  # R811
    """
    <end-select-stmt> = END SELECT [ <case-construct-name> ]
    """
    subclass_names = []
    use_names = ['Case_Construct_Name']

    @staticmethod
    def match(string):
        return EndStmtBase.match(
            'SELECT', Case_Construct_Name, string, require_stmt_type=True)


class Case_Expr(Base):  # R812
    """
    <case-expr> = <scalar-int-expr>
                  | <scalar-char-expr>
                  | <scalar-logical-expr>
    """
    subclass_names = []
    subclass_names = ['Scalar_Int_Expr', 'Scalar_Char_Expr',
                      'Scalar_Logical_Expr']


class Case_Selector(Base):  # R813
    """
    <case-selector> = ( <case-value-range-list> )
                      | DEFAULT
    """
    subclass_names = []
    use_names = ['Case_Value_Range_List']

    @staticmethod
    def match(string):
        if len(string) == 7 and string.upper() == 'DEFAULT':
            return None,
        if not (string.startswith('(') and string.endswith(')')):
            return
        return Case_Value_Range_List(string[1:-1].strip()),

    def tostr(self):
        if self.items[0] is None:
            return 'DEFAULT'
        return '(%s)' % (self.items[0])


class Case_Value_Range(SeparatorBase):  # R814
    """
    <case-value-range> = <case-value>
                         | <case-value> :
                         | : <case-value>
                         | <case-value> : <case-value>
    """
    subclass_names = ['Case_Value']

    @staticmethod
    def match(string):
        return SeparatorBase.match(Case_Value, Case_Value, string)


class Case_Value(Base):  # R815
    """
    <case-value> = <scalar-int-initialization-expr>
                   | <scalar-char-initialization-expr>
                   | <scalar-logical-initialization-expr>
    """
    subclass_names = ['Scalar_Int_Initialization_Expr',
                      'Scalar_Char_Initialization_Expr',
                      'Scalar_Logical_Initialization_Expr']


class Associate_Construct(BlockBase):  # R816
    """
    <associate-construct> = <associate-stmt>
                                <block> == [ <execution-part-construct> ]...
                                <end-associate-stmt>
    """
    subclass_names = []
    use_names = ['Associate_Stmt', 'Execution_Part_Construct',
                 'End_Associate_Stmt']

    @staticmethod
    def match(reader):
        return BlockBase.match(
            Associate_Stmt, [Execution_Part_Construct],
            End_Associate_Stmt, reader,
            match_names=True,  # C810
        )


class Associate_Stmt(StmtBase, CALLBase):  # R817
    """
    <associate-stmt> = [ <associate-construct-name> : ]
        ASSOCIATE ( <association-list> )
    """
    subclass_names = []
    use_names = ['Associate_Construct_Name', 'Association_List']

    @staticmethod
    def match(string):
        return CALLBase.match('ASSOCIATE', Association_List, string)

    def get_start_name(self):
        return self.item.name


class Association(BinaryOpBase):  # R818
    """
    <association> = <associate-name> => <selector>
    """
    subclass_names = []
    use_names = ['Associate_Name', 'Selector']

    @staticmethod
    def match(string):
        return BinaryOpBase.match(Associate_Name, '=>', Selector, string)


class Selector(Base):  # R819
    """
    <selector> = <expr>
                 | <variable>
    """
    subclass_names = ['Expr', 'Variable']


class End_Associate_Stmt(EndStmtBase):  # R820
    """
    <end-associate-stmt> = END ASSOCIATE [ <associate-construct-name> ]
    """
    subclass_names = []
    use_names = ['Associate_Construct_Name']

    @staticmethod
    def match(string):
        return EndStmtBase.match(
            'ASSOCIATE', Associate_Construct_Name, string,
            require_stmt_type=True)


class Select_Type_Construct(BlockBase):  # R821
    """
    <select-type-construct> = <select-type-stmt>
                                  [ <type-guard-stmt>
                                    <block> == [<execution-part-construct>]..
                                  ]...
                                  <end-select-type-stmt>
    """
    subclass_names = []
    use_names = ['Select_Type_Stmt', 'Type_Guard_Stmt',
                 'Execution_Part_Construct', 'End_Select_Type_Stmt']

    @staticmethod
    def match(reader):
        return BlockBase.match(
            Select_Type_Stmt, [Type_Guard_Stmt, Execution_Part_Construct,
                               Type_Guard_Stmt], End_Select_Type_Stmt, reader,
            match_names=True,  # C819
            enable_select_type_construct_hook=True)


class Select_Type_Stmt(StmtBase):  # R822
    """
    <select-type-stmt> = [ <select-construct-name> : ] SELECT TYPE
        ( [ <associate-name> => ] <selector> )
    """
    subclass_names = []
    use_names = ['Select_Construct_Name', 'Associate_Name', 'Selector']

    @staticmethod
    def match(string):
        if string[:6].upper() != 'SELECT':
            return
        line = string[6:].lstrip()
        if line[:4].upper() != 'TYPE':
            return
        line = line[4:].lstrip()
        if not line or line[0]+line[-1] != '()':
            return
        line = line[1:-1].strip()
        i = line.find('=>')
        if i != -1:
            return Associate_Name(
                line[:i].rstrip()), Selector(line[i+2:].lstrip())
        return None, Selector(line)

    def tostr(self):
        if self.items[0] is None:
            return 'SELECT TYPE(%s)' % (self.items[1])
        return 'SELECT TYPE(%s=>%s)' % (self.items)

    def get_start_name(self):
        return self.item.name


class Type_Guard_Stmt(StmtBase):  # R823
    """
::
    <type-guard-stmt> = TYPE IS ( <type-spec> ) [ <select-construct-name> ]
                        | CLASS IS ( <type-spec> ) [ <select-construct-name> ]
                        | CLASS DEFAULT [ <select-construct-name> ]

Attributes
----------
items : ({'TYPE IS', 'CLASS IS', 'CLASS DEFAULT'}, Type_Spec,
        Select_Construct_Name)
    """
    subclass_names = []
    use_names = ['Type_Spec', 'Select_Construct_Name']

    @staticmethod
    def match(string):
        if string[:4].upper() == 'TYPE':
            line = string[4:].lstrip()
            if not line[:2].upper() == 'IS':
                return
            line = line[2:].lstrip()
            kind = 'TYPE IS'
        elif string[:5].upper() == 'CLASS':
            line = string[5:].lstrip()
            if line[:2].upper() == 'IS':
                line = line[2:].lstrip()
                kind = 'CLASS IS'
            elif line[:7].upper() == 'DEFAULT':
                line = line[7:].lstrip()
                if line:
                    if isalnum(line[0]):
                        return
                    return 'CLASS DEFAULT', None, Select_Construct_Name(line)
                return 'CLASS DEFAULT', None, None
            else:
                return
        else:
            return
        if not line.startswith('('):
            return
        i = line.rfind(')')
        if i == -1:
            return
        tmp = line[1:i].strip()
        if not tmp:
            return
        line = line[i+1:].lstrip()
        if line:
            return kind, Type_Spec(tmp), Select_Construct_Name(line)
        return kind, Type_Spec(tmp), None

    def tostr(self):
        s = str(self.items[0])
        if self.items[1] is not None:
            s += ' (%s)' % (self.items[1])
        if self.items[2] is not None:
            s += ' %s' % (self.items[2])
        return s


class End_Select_Type_Stmt(EndStmtBase):  # R824
    """
    <end-select-type-stmt> = END SELECT [ <select-construct-name> ]
    """
    subclass_names = []
    use_names = ['Select_Construct_Name']

    @staticmethod
    def match(string):
        return EndStmtBase.match(
            'SELECT', Select_Construct_Name, string, require_stmt_type=True)


class Do_Construct(Base):  # pylint: disable=invalid-name
    """
    R825

    <do-construct> = <block-do-construct>
                     | <nonblock-do-construct>
    """
    subclass_names = ['Block_Do_Construct', 'Nonblock_Do_Construct']


class Block_Do_Construct(Base):  # pylint: disable=invalid-name
    """
    R826

    <block-do-construct> = <block-label-do-construct>
                           | <block-nonlabel-do-construct>
    """
    subclass_names = ['Block_Label_Do_Construct',
                      'Block_Nonlabel_Do_Construct']


class Block_Label_Do_Construct(BlockBase):  # pylint: disable=invalid-name
    """
    R826_1

    <block-label-do-construct> = <label-do-stmt>
                                   [ <execution-part-construct> ]...
                                   <end-do>
    """
    subclass_names = []
    use_names = ['Label_Do_Stmt', 'Execution_Part_Construct', 'End_Do']

    @staticmethod
    def match(reader):
        '''
        :param reader: instance of `FortranReaderBase` class
        :type reader: :py:class:`FortranReaderBase`
        :return: code block matching the labeled "DO" construct
        :rtype: string
        '''
        return BlockBase.match(Label_Do_Stmt, [Execution_Part_Construct],
                               End_Do, reader,
                               match_labels=True,
                               enable_do_label_construct_hook=True)

    def tofortran(self, tab='', isfix=None):
        '''
        :param str tab: tab character or empty string.
        :param bool isfix: whether the reader is in fixed format.

        :return: parsed representation of the labeled "DO" construct.
        :rtype: str
        '''
        lblock = []
        start = self.content[0]
        end = self.content[-1]
        extra_tab = '  '
        lblock.append(start.tofortran(tab=tab, isfix=isfix))
        for item in self.content[1:-1]:
            lblock.append(item.tofortran(tab=tab+extra_tab, isfix=isfix))
        if len(self.content) > 1:
            lblock.append(end.tofortran(tab=tab, isfix=isfix))
        py2_encode_list_items(lblock)
        return '\n'.join(lblock)


class Block_Nonlabel_Do_Construct(BlockBase):  # pylint: disable=invalid-name
    """
     R826_2

    <block-nonlabel-do-construct> = <nonlabel-do-stmt>
                                     [ <execution-part-construct> ]...
                                     <end-do-stmt>
    """
    subclass_names = []
    use_names = ['Nonlabel_Do_Stmt', 'Execution_Part_Construct', 'End_Do_Stmt']

    @staticmethod
    def match(reader):
        '''
        :param reader: instance of `FortranReaderBase` class
        :type reader: :py:class:`FortranReaderBase`
        :return: code block matching the nonlabeled "DO" construct
        :rtype: string
        '''
        return BlockBase.match(Nonlabel_Do_Stmt, [Execution_Part_Construct],
                               End_Do_Stmt, reader
                               )


class Do_Stmt(Base):  # pylint: disable=invalid-name
    """
    R827

    <do-stmt> = <label-do-stmt>
                | <nonlabel-do-stmt>
    """
    subclass_names = ['Label_Do_Stmt', 'Nonlabel_Do_Stmt']


class Label_Do_Stmt(StmtBase):  # pylint: disable=invalid-name
    """
    R828

    <label-do-stmt> = [ <do-construct-name> : ] DO <label> [ <loop-control> ]
    """
    subclass_names = []
    use_names = ['Do_Construct_Name', 'Label', 'Loop_Control']

    @staticmethod
    def match(string):
        '''
        :param string: (source of) Fortran string to parse
        :type string: str or :py:class:`FortranReaderBase`
        :return: 3-tuple containing strings and instances of the classes
                 determining labeled "DO" statement (optional statement name,
                 label and loop control expression if present)
        :rtype: 3-tuple of objects
        '''
        # do-construct-name is determined by reader
        if string[:2].upper() != 'DO':
            return
        line = string[2:].lstrip()
        mpat = pattern.label.match(line)
        if mpat is None:
            return
        label = mpat.group()
        line = line[mpat.end():].lstrip()
        if line:
            return None, Label(label), Loop_Control(line)
        return None, Label(label), None

    def tostr(self):
        '''
        :return: string containing Fortran code for the parsed
                 labeled "DO" statement
        :rtype: string
        '''
        # pylint: disable=unbalanced-tuple-unpacking
        name, label, loop_control = self.items
        if name is None:
            dostmt = 'DO %s' % (label)
        else:
            dostmt = '%s: DO %s' % (label)
        if loop_control is not None:
            dostmt += ' %s' % (loop_control)
        return dostmt

    def get_start_name(self):
        '''
        :return: optional labeled "DO" statement name
        :rtype: string
        '''
        return self.item.name

    def get_start_label(self):
        '''
        :return: label of "DO" statement
        :rtype: string
        '''
        return int(self.items[1])

    do_construct_name = property(lambda self: self.items[0])
    label = property(lambda self: self.items[1])
    loop_control = property(lambda self: self.items[2])


class Nonlabel_Do_Stmt(StmtBase, WORDClsBase):  # pylint: disable=invalid-name
    """
    R829

    <nonlabel-do-stmt> = [ <do-construct-name> : ] DO [ <loop-control> ]
    """
    subclass_names = []
    use_names = ['Do_Construct_Name', 'Loop_Control']

    @staticmethod
    def match(string):
        '''
        :param str string: Fortran code to check for a match
        :return: code line matching the nonlabeled "DO" statement
        :rtype: string
        '''
        return WORDClsBase.match('DO', Loop_Control, string)


class Loop_Control(Base):  # pylint: disable=invalid-name
    """
    R830

    <loop-control> = [ , ] <do-variable> = scalar-int-expr,
                                           scalar-int-expr
                                           [ , <scalar-int-expr> ]
                     | [ , ] WHILE ( <scalar-logical-expr> )
    """
    subclass_names = []
    use_names = ['Do_Variable', 'Scalar_Int_Expr', 'Scalar_Logical_Expr']

    @staticmethod
    def match(string):
        '''
        :param str string: Fortran code to check for a match
        :return: 3-tuple containing strings and instances of the classes
                 determining loop control (optional comma delimiter,
                 optional scalar logical expression describing "WHILE"
                 condition or optional counter expression containing loop
                 counter and scalar integer expression)
        :rtype: 3-tuple of objects or nothing for an "infinite loop"
        '''
        # pylint: disable=unbalanced-tuple-unpacking
        optional_delim = None
        # Match optional delimiter
        if string.startswith(','):
            line, repmap = string_replace_map(string[1:].lstrip())
            optional_delim = ", "
        else:
            line, repmap = string_replace_map(string)
        # Match "WHILE" scalar logical expression
        if line[:5].upper() == 'WHILE' and line[5:].lstrip().startswith('('):
            lbrak = line[5:].lstrip()
            i = lbrak.find(')')
            if i != -1 and i == len(lbrak)-1:
                scalar_logical_expr = \
                    Scalar_Logical_Expr(repmap(lbrak[1:i].strip()))
                return scalar_logical_expr, None, optional_delim
        # Match counter expression
        # More than one '=' in counter expression
        if line.count('=') != 1:
            return
        var, rhs = line.split('=')
        rhs = [s.strip() for s in rhs.lstrip().split(',')]
        # Incorrect number of elements in counter expression
        if not 2 <= len(rhs) <= 3:
            return
        counter_expr = (Variable(repmap(var.rstrip())),
                        list(map(Scalar_Int_Expr, list(map(repmap, rhs)))))
        return None, counter_expr, optional_delim

    def tostr(self):
        '''
        :return: parsed representation of loop control construct
        :rtype: string
        '''
        # pylint: disable=unbalanced-tuple-unpacking
        scalar_logical_expr, counter_expr, optional_delim = self.items
        # Return loop control construct containing "WHILE" condition and
        # its <scalar-logical-expr>
        if scalar_logical_expr is not None:
            loopctrl = 'WHILE (%s)' % scalar_logical_expr
        # Return loop control construct containing counter expression:
        # <do-variable> as LHS and <scalar-int-expr> list as RHS
        elif counter_expr[0] is not None and counter_expr[1] is not None:
            loopctrl = '%s = %s' % \
                (counter_expr[0], ', '.join(map(str, counter_expr[1])))
        # Add optional delimiter to loop control construct if present
        if optional_delim is not None:
            loopctrl = optional_delim + loopctrl
        return loopctrl


class Do_Variable(Base):  # pylint: disable=invalid-name
    """
    R831

    <do-variable> = <scalar-int-variable>
    """
    subclass_names = ['Scalar_Int_Variable']


class Do_Block(BlockBase):  # pylint: disable=invalid-name
    """
    R832

    <do-block> = [ <execution-part-construct> ]...
    """
    subclass_names = ['Block']
    subclass_names = []
    use_names = ['Execution_Part_Construct']

    @staticmethod
    def match(string):
        '''
        :param str string: Fortran code to check for a match
        :return: code block matching the execution part construct within
                 the "DO" block
        :rtype: string
        '''
        return BlockBase.match(None, [Execution_Part_Construct], None, string)


class End_Do(Base):  # pylint: disable=invalid-name
    """
    R833

    <end-do> = <end-do-stmt>
               | <continue-stmt>
    """
    subclass_names = ['End_Do_Stmt', 'Continue_Stmt']


class End_Do_Stmt(EndStmtBase):  # pylint: disable=invalid-name
    """
    R834

    <end-do-stmt> = END DO [ <do-construct-name> ]
    """
    subclass_names = []
    use_names = ['Do_Construct_Name']

    @staticmethod
    def match(string):
        '''
        :param str string: Fortran code to check for a match
        :return: code line matching the "END DO" statement
        :rtype: string
        '''
        return EndStmtBase.match('DO', Do_Construct_Name, string,
                                 require_stmt_type=True)


class Nonblock_Do_Construct(Base):  # pylint: disable=invalid-name
    """
    R835

    <nonblock-do-stmt> = <action-term-do-construct>
                         | <outer-shared-do-construct>
    """
    subclass_names = ['Action_Term_Do_Construct', 'Outer_Shared_Do_Construct']


class Action_Term_Do_Construct(BlockBase):  # R836
    """
::
    <action-term-do-construct> = <label-do-stmt>
                                     <do-body>
                                     <do-term-action-stmt>

::
    <action-term-do-construct> = <label-do-stmt>
                                 [ <execution-part-construct> ]...
                                 <do-term-action-stmt>
    """
    subclass_names = []
    use_names = ['Label_Do_Stmt', 'Execution_Part_Construct',
                 'Do_Term_Action_Stmt']

    @staticmethod
    def match(reader):
        return BlockBase.match(Label_Do_Stmt, [Execution_Part_Construct],
                               Do_Term_Action_Stmt, reader,
                               match_labels=True,
                               enable_do_label_construct_hook=True)

    def tofortran(self, tab='', isfix=None):
        '''
        Converts this node (and all children) into Fortran.

        :param str tab: white space to prefix to output.
        :param bool isfix: whether or not to generate fixed-format output.

        :returns: Fortran code.
        :rtype: str

        '''
        line = []
        start = self.content[0]
        end = self.content[-1]
        extra_tab = '  '
        line.append(start.tofortran(tab=tab, isfix=isfix))
        for item in self.content[1:-1]:
            line.append(item.tofortran(tab=tab+extra_tab, isfix=isfix))
            if isinstance(item, Label_Do_Stmt):
                extra_tab += '  '
        if len(self.content) > 1:
            line.append(end.tofortran(tab=tab, isfix=isfix))
        py2_encode_list_items(line)
        return '\n'.join(line)


class Do_Body(BlockBase):  # R837
    """
    <do-body> = [ <execution-part-construct> ]...
    """
    subclass_names = []
    use_names = ['Execution_Part_Construct']

    def match(string):
        return BlockBase.match(None, [Execution_Part_Construct],
                               None, string)
    match = staticmethod(match)


class Do_Term_Action_Stmt(StmtBase):  # R838
    """
::
    <do-term-action-stmt> = <action-stmt>

Notes
-----
C824: <do-term-action-stmt> shall not be <continue-stmt>, <goto-stmt>,
      <return-stmt>, <stop-stmt>, <exit-stmt>, <cycle-stmt>,
      <end-function-stmt>, <end-subroutine-stmt>, <end-program-stmt>,
      <arithmetic-if-stmt>
    """
    subclass_names = ['Action_Stmt_C824']


class Outer_Shared_Do_Construct(BlockBase):  # R839
    """
    <outer-shared-do-construct> = <label-do-stmt>
                                      <do-body>
                                      <shared-term-do-construct>
    """
    subclass_names = []
    use_names = ['Label_Do_Stmt', 'Do_Body', 'Shared_Term_Do_Construct']

    def match(reader):
        content = []
        for cls in [Label_Do_Stmt, Do_Body, Shared_Term_Do_Construct]:
            obj = cls(reader)
            if obj is None:  # todo: restore reader
                return
            content.append(obj)
        return content,
    match = staticmethod(match)


class Shared_Term_Do_Construct(Base):  # R840
    """
    <shared-term-do-construct> = <outer-shared-do-construct>
                                 | <inner-shared-do-construct>
    """
    subclass_names = ['Outer_Shared_Do_Construct', 'Inner_Shared_Do_Construct']


class Inner_Shared_Do_Construct(BlockBase):  # R841
    """
    <inner-shared-do-construct> = <label-do-stmt>
                                      <do-body>
                                      <do-term-shared-stmt>
    """
    subclass_names = []
    use_names = ['Label_Do_Stmt', 'Do_Body', 'Do_Term_Shared_Stmt']

    def match(reader):
        content = []
        for cls in [Label_Do_Stmt, Do_Body, Do_Term_Shared_Stmt]:
            obj = cls(reader)
            if obj is None:  # todo: restore reader
                return
            content.append(obj)
        return content,
    match = staticmethod(match)


class Do_Term_Shared_Stmt(StmtBase):  # R842
    """
    <do-term-shared-stmt> = <action-stmt>
    C826: see C824 above.
    """
    subclass_names = ['Action_Stmt']


class Cycle_Stmt(StmtBase, WORDClsBase):  # R843
    """
    <cycle-stmt> = CYCLE [ <do-construct-name> ]
    """
    subclass_names = []
    use_names = ['Do_Construct_Name']

    def match(string):
        return WORDClsBase.match('CYCLE', Do_Construct_Name, string)
    match = staticmethod(match)


class Exit_Stmt(StmtBase, WORDClsBase):  # R844
    """
    <exit-stmt> = EXIT [ <do-construct-name> ]
    """
    subclass_names = []
    use_names = ['Do_Construct_Name']

    def match(string):
        return WORDClsBase.match('EXIT', Do_Construct_Name, string)
    match = staticmethod(match)


class Goto_Stmt(StmtBase):  # R845
    """
    <goto-stmt> = GO TO <label>
    """
    subclass_names = []
    use_names = ['Label']

    def match(string):
        if string[:2].upper() != 'GO':
            return
        line = string[2:].lstrip()
        if line[:2].upper() != 'TO':
            return
        return Label(line[2:].lstrip()),
    match = staticmethod(match)

    def tostr(self):
        return 'GO TO %s' % (self.items[0])


class Computed_Goto_Stmt(StmtBase):  # R846
    """
    <computed-goto-stmt> = GO TO ( <label-list> ) [ , ] <scalar-int-expr>
    """
    subclass_names = []
    use_names = ['Label_List', 'Scalar_Int_Expr']

    def match(string):
        if string[:2].upper() != 'GO':
            return
        line = string[2:].lstrip()
        if line[:2].upper() != 'TO':
            return
        line = line[2:].lstrip()
        if not line.startswith('('):
            return
        i = line.find(')')
        if i == -1:
            return
        lst = line[1:i].strip()
        if not lst:
            return
        line = line[i+1:].lstrip()
        if line.startswith(','):
            line = line[1:].lstrip()
        if not line:
            return
        return Label_List(lst), Scalar_Int_Expr(line)
    match = staticmethod(match)

    def tostr(self):
        return 'GO TO (%s), %s' % self.items


class Arithmetic_If_Stmt(StmtBase):  # R847
    """
    <arithmetic-if-stmt> = IF ( <scalar-numeric-expr> ) <label> ,
        <label> , <label>
    """
    subclass_names = []
    use_names = ['Scalar_Numeric_Expr', 'Label']

    def match(string):
        if string[:2].upper() != 'IF':
            return
        line = string[2:].lstrip()
        if not line.startswith('('):
            return
        i = line.rfind(')')
        if i == -1:
            return
        labels = line[i+1:].lstrip().split(',')
        if len(labels) != 3:
            return
        labels = [Label(l.strip()) for l in labels]
        return (Scalar_Numeric_Expr(line[1:i].strip()),) + tuple(labels)
    match = staticmethod(match)

    def tostr(self):
        return 'IF (%s) %s, %s, %s' % self.items


class Continue_Stmt(StmtBase, STRINGBase):  # R848
    """
    <continue-stmt> = CONTINUE
    """
    subclass_names = []

    def match(string):
        return STRINGBase.match('CONTINUE', string)
    match = staticmethod(match)

    def get_end_label(self):
        return self.item.label


class Stop_Stmt(StmtBase, WORDClsBase):  # R849
    """
    <stop-stmt> = STOP [ <stop-code> ]
    """
    subclass_names = []
    use_names = ['Stop_Code']

    def match(string):
        return WORDClsBase.match('STOP', Stop_Code, string)
    match = staticmethod(match)


class Stop_Code(StringBase):  # R850
    """
    <stop-code> = <scalar-char-constant>
                  | <digit> [ <digit> [ <digit> [ <digit> [ <digit> ] ] ] ]
    """
    subclass_names = ['Scalar_Char_Constant']

    def match(string):
        return StringBase.match(pattern.abs_label, string)
    match = staticmethod(match)

#
# SECTION  9
#


class Io_Unit(StringBase):  # R901
    """
    <io-unit> = <file-unit-number>
                | *
                | <internal-file-variable>
    """
    subclass_names = ['File_Unit_Number', 'Internal_File_Variable']

    def match(string):
        return StringBase.match('*', string)
    match = staticmethod(match)


class File_Unit_Number(Base):  # R902
    """
    <file-unit-number> = <scalar-int-expr>
    """
    subclass_names = ['Scalar_Int_Expr']


class Internal_File_Variable(Base):  # R903
    """
    <internal-file-variable> = <char-variable>
    C901: <char-variable> shall not be an array section with a
        vector subscript.
    """
    subclass_names = ['Char_Variable']


class Open_Stmt(StmtBase, CALLBase):  # R904
    """
    <open-stmt> = OPEN ( <connect-spec-list> )
    """
    subclass_names = []
    use_names = ['Connect_Spec_List']

    @staticmethod
    def match(string):
        # The Connect_Spec_List class is generated automatically
        # by code at the end of this module
        return CALLBase.match('OPEN', Connect_Spec_List, string,
                              require_rhs=True)


class Connect_Spec(KeywordValueBase):
    """
    R905
    <connect-spec> = [ UNIT = ] <file-unit-number>
                     | ACCESS = <scalar-default-char-expr>
                     | ACTION = <scalar-default-char-expr>
                     | ASYNCHRONOUS = <scalar-default-char-expr>
                     | BLANK = <scalar-default-char-expr>
                     | DECIMAL = <scalar-default-char-expr>
                     | DELIM = <scalar-default-char-expr>
                     | ENCODING = <scalar-default-char-expr>
                     | ERR = <label>
                     | FILE = <file-name-expr>
                     | FORM = <scalar-default-char-expr>
                     | IOMSG = <iomsg-variable>
                     | IOSTAT = <scalar-int-variable>
                     | PAD = <scalar-default-char-expr>
                     | POSITION = <scalar-default-char-expr>
                     | RECL = <scalar-int-expr>
                     | ROUND = <scalar-default-char-expr>
                     | SIGN = <scalar-default-char-expr>
                     | STATUS = <scalar-default-char-expr>
    """
    subclass_names = []
    use_names = ['File_Unit_Number', 'Scalar_Default_Char_Expr', 'Label',
                 'File_Name_Expr', 'Iomsg_Variable',
                 'Scalar_Int_Expr', 'Scalar_Int_Variable']

    @staticmethod
    def match(string):
        '''
        :param str string: Fortran code to check for a match
        :return: 2-tuple containing the keyword and value or None if the
                 supplied string is not a match
        :rtype: 2-tuple containing keyword (e.g. "UNIT") and associated value
        '''
        if "=" not in string:
            # The only argument which need not be named is the unit number
            return 'UNIT', File_Unit_Number(string)
        # We have a keyword-value pair. Check whether it is valid...
        for (keyword, value) in [
                (['ACCESS', 'ACTION', 'ASYNCHRONOUS', 'BLANK', 'DECIMAL',
                  'DELIM', 'ENCODING', 'FORM', 'PAD', 'POSITION', 'ROUND',
                  'SIGN', 'STATUS'], Scalar_Default_Char_Expr),
                ('ERR', Label),
                ('FILE', File_Name_Expr),
                ('IOSTAT', Scalar_Int_Variable),
                ('IOMSG', Iomsg_Variable),
                ('RECL', Scalar_Int_Expr),
                ('UNIT', File_Unit_Number)]:
            try:
                obj = KeywordValueBase.match(keyword, value, string,
                                             upper_lhs=True)
            except NoMatchError:
                obj = None
            if obj is not None:
                return obj
        return None


class File_Name_Expr(Base):  # R906
    """
    <file-name-expr> = <scalar-default-char-expr>
    """
    subclass_names = ['Scalar_Default_Char_Expr']


class Iomsg_Variable(Base):  # R907
    """
    <iomsg-variable> = <scalar-default-char-variable>
    """
    subclass_names = ['Scalar_Default_Char_Variable']


class Close_Stmt(StmtBase, CALLBase):  # R908
    """
    <close-stmt> = CLOSE ( <close-spec-list> )
    """
    subclass_names = []
    use_names = ['Close_Spec_List']

    def match(string):
        return CALLBase.match('CLOSE', Close_Spec_List, string,
                              require_rhs=True)
    match = staticmethod(match)


class Close_Spec(KeywordValueBase):  # R909
    """
    <close-spec> = [ UNIT = ] <file-unit-number>
                   | IOSTAT = <scalar-int-variable>
                   | IOMSG = <iomsg-variable>
                   | ERR = <label>
                   | STATUS = <scalar-default-char-expr>
    """
    subclass_names = []
    use_names = ['File_Unit_Number', 'Scalar_Default_Char_Expr',
                 'Label', 'Iomsg_Variable',
                 'Scalar_Int_Variable']

    def match(string):
        for (k, v) in [
                ('ERR', Label),
                ('IOSTAT', Scalar_Int_Variable),
                ('IOMSG', Iomsg_Variable),
                ('STATUS', Scalar_Default_Char_Expr),
                ('UNIT', File_Unit_Number), ]:
            try:
                obj = KeywordValueBase.match(k, v, string, upper_lhs=True)
            except NoMatchError:
                obj = None
            if obj is not None:
                return obj
        return 'UNIT', File_Unit_Number(string)
    match = staticmethod(match)


class Read_Stmt(StmtBase):  # R910
    """
:F03R:`910`::
    <read-stmt> = READ ( <io-control-spec-list> ) [ <input-item-list> ]
                    | READ <format> [ , <input-item-list> ]

Attributes
----------
items : (Io_Control_Spec_List, Format, Input_Item_List)
    """
    subclass_names = []
    use_names = ['Io_Control_Spec_List', 'Input_Item_List', 'Format']

    @staticmethod
    def match(string):
        if string[:4].upper() != 'READ':
            return
        line = string[4:].lstrip()
        if line.startswith('('):
            line, repmap = string_replace_map(line)
            idx = line.find(')')
            if idx == -1:
                return
            trimline = line[1:idx].strip()
            if not trimline:
                return
            if idx == len(line) - 1:
                return Io_Control_Spec_List(repmap(trimline)), None, None
            return Io_Control_Spec_List(repmap(trimline)), None, \
                Input_Item_List(repmap(line[idx+1:].lstrip()))
        if not line:
            return
        char = line[0].upper()
        # No parentheses therefore first argument must be a format
        # specifier (either a string or a line/label number
        if 'A' <= char <= 'Z' or char == '_':
            return
        line, repmap = string_replace_map(line.lstrip())
        # There must be a comma betwee the format specifier and the following
        # list of values/variables
        idx = line.find(',')
        if idx == -1:
            return None
        trimline = repmap(line[idx+1:].lstrip())
        if not trimline:
            return
        return (None, Format(repmap(line[:idx].rstrip())),
                Output_Item_List(trimline))

    def tostr(self):
        if self.items[0] is not None:
            assert self.items[1] is None, repr(self.items)
            if self.items[2] is None:
                return 'READ(%s)' % (self.items[0])
            return 'READ(%s) %s' % (self.items[0], self.items[2])
        assert self.items[1] is not None, repr(self.items)
        if self.items[2] is None:
            return 'READ %s' % (self.items[1])
        return 'READ %s, %s' % (self.items[1], self.items[2])


class Write_Stmt(StmtBase):  # pylint: disable=invalid-name
    '''
    :F03R:`911`::

    Fortran 2003 rule R911
    that specifies syntax of a "WRITE" statement.

    <write-stmt> = WRITE ( <io-control-spec-list> ) [ <output-item-list> ]
    '''
    subclass_names = []
    use_names = ['Io_Control_Spec_List', 'Output_Item_List']

    @staticmethod
    def match(string):
        '''
        :param str string: Fortran code to check for a match
        :return: 2-tuple containing strings and instances of the classes
                 describing "WRITE" statement (mandatory IO control
                 specification list and optional output item list.
        :rtype: 2-tuple of objects (1 mandatory and 1 optional)
        '''
        if string[:5].upper() != 'WRITE':
            return
        line = string[5:].lstrip()
        # Look for mandatory IO control specification list and
        # return without a match if it is not found
        if not line.startswith('('):
            return
        line, repmap = string_replace_map(line)
        i = line.find(')')
        if i == -1:
            return
        tmp = line[1:i].strip()
        if not tmp:
            return
        tmp = repmap(tmp)
        if i == len(line)-1:
            return Io_Control_Spec_List(tmp), None
        # Return optional output item list as well
        return Io_Control_Spec_List(tmp), \
            Output_Item_List(repmap(line[i+1:].lstrip()))

    def tostr(self):
        '''
        :return: parsed representation of a "WRITE" statement
        :rtype: str
        '''
        if self.items[1] is None:
            return 'WRITE(%s)' % (self.items[0])
        return 'WRITE(%s) %s' % tuple(self.items)


class Print_Stmt(StmtBase):  # R912
    """
:F03R:`912`::
    <print-stmt> = PRINT <format> [ , <output-item-list> ]

Parameters
----------
items : (Format, Output_Item_List)
    """
    subclass_names = []
    use_names = ['Format', 'Output_Item_List']

    def match(string):
        if string[:5].upper() != 'PRINT':
            return
        line = string[5:]
        if not line:
            return
        c = line[0].upper()
        if 'A' <= c <= 'Z' or c == '_' or '0' <= c <= '9':
            return
        line, repmap = string_replace_map(line.lstrip())
        i = line.find(',')
        if i == -1:
            return Format(repmap(line)), None
        tmp = repmap(line[i+1:].lstrip())
        if not tmp:
            return
        return Format(repmap(line[:i].rstrip())), Output_Item_List(tmp)
    match = staticmethod(match)

    def tostr(self):
        if self.items[1] is None:
            return 'PRINT %s' % (self.items[0])
        return 'PRINT %s, %s' % tuple(self.items)


class Io_Control_Spec_List(SequenceBase):  # R913-list
    """
    <io-control-spec-list> is a list taking into account C910, C917, C918
    """
    subclass_names = []
    use_names = ['Io_Control_Spec']

    @staticmethod
    def match(string):
        line, repmap = string_replace_map(string)
        splitted = line.split(',')
        lst = []
        unit_is_positional = False
        for idx in range(len(splitted)):
            spec = splitted[idx].strip()
            spec = repmap(spec)
            if idx == 0 and "=" not in spec:
                # Must be a unit number. However, we do not prepend "UNIT="
                # to it in case the following Io_Control_Spec is positional
                # (and therefore either a Format or Namelist spec).
                lst.append(Io_Control_Spec(spec))
                unit_is_positional = True
            elif idx == 1 and "=" not in spec:
                if not unit_is_positional:
                    # Cannot have a positional argument following a
                    # named argument
                    return
                # Without knowing the type of the variable named in spec
                # we have no way of knowing whether this is a format or
                # a namelist specifier. However, if it is a character
                # constant or "*" then it must be a Format spec and we can
                # prepend "FMT=" to it.
                spec = spec.lstrip().rstrip()
                if Char_Literal_Constant.match(spec) or \
                   StringBase.match("*", spec):
                    spec = "FMT={0}".format(spec)
                lst.append(Io_Control_Spec(spec))
            else:
                lst.append(Io_Control_Spec(spec))
        return ',', tuple(lst)


class Io_Control_Spec(KeywordValueBase):  # R913
    """
    <io-control-spec> = [ UNIT = ] <io-unit>
                        | [ FMT = ] <format>
                        | [ NML = ] <namelist-group-name>
                        | ADVANCE = <scalar-default-char-expr>
                        | ASYNCHRONOUS = <scalar-char-initialization-expr>
                        | BLANK = <scalar-default-char-expr>
                        | DECIMAL = <scalar-default-char-expr>
                        | DELIM = <scalar-default-char-expr>
                        | END = <label>
                        | EOR = <label>
                        | ERR = <label>
                        | ID = <scalar-int-variable>
                        | IOMSG = <iomsg-variable>
                        | IOSTAT = <scalar-int-variable>
                        | PAD = <scalar-default-char-expr>
                        | POS = <scalar-int-expr>
                        | REC = <scalar-int-expr>
                        | ROUND = <scalar-default-char-expr>
                        | SIGN = <scalar-default-char-expr>
                        | SIZE = <scalar-int-variable>
    """
    subclass_names = []
    use_names = ['Io_Unit', 'Format', 'Namelist_Group_Name',
                 'Scalar_Default_Char_Expr',
                 'Scalar_Char_Initialization_Expr', 'Label',
                 'Scalar_Int_Variable',
                 'Iomsg_Variable', 'Scalar_Int_Expr']

    @staticmethod
    def match(string):
        for (k, v) in [('UNIT', Io_Unit),
                       ('FMT', Format),
                       ('NML', Namelist_Group_Name)]:
            obj = KeywordValueBase.match(k, v, string,
                                         require_lhs=False,
                                         upper_lhs=True)
            if obj:
                return obj

        for (k, v) in [(['ADVANCE', 'BLANK', 'DECIMAL', 'DELIM', 'PAD',
                         'ROUND', 'SIGN'], Scalar_Default_Char_Expr),
                       ('ASYNCHRONOUS', Scalar_Char_Initialization_Expr),
                       (['END', 'EOR', 'ERR'], Label),
                       (['ID', 'IOSTAT', 'SIZE'], Scalar_Int_Variable),
                       ('IOMSG', Iomsg_Variable),
                       (['POS', 'REC'], Scalar_Int_Expr)]:
            obj = KeywordValueBase.match(k, v, string, upper_lhs=True)
            if obj:
                return obj
        return


class Format(StringBase):  # R914
    """
    <format> = <default-char-expr>
               | <label>
               | *
    """
    subclass_names = ['Label', 'Default_Char_Expr']

    @staticmethod
    def match(string):
        return StringBase.match('*', string)


class Input_Item(Base):  # R915
    """
    <input-item> = <variable>
                   | <io-implied-do>
    """
    subclass_names = ['Variable', 'Io_Implied_Do']


class Output_Item(Base):  # R916
    """
    <output-item> = <expr>
                    | <io-implied-do>
    """
    subclass_names = ['Expr', 'Io_Implied_Do']


class Io_Implied_Do(Base):  # R917
    """
    <io-implied-do> = ( <io-implied-do-object-list> , <io-implied-do-control> )
    """
    subclass_names = []
    use_names = ['Io_Implied_Do_Object_List', 'Io_Implied_Do_Control']

    @staticmethod
    def match(string):
        if len(string) <= 9 or string[0] != '(' or string[-1] != ')':
            return
        line, repmap = string_replace_map(string[1:-1].strip())
        i = line.rfind('=')
        if i == -1:
            return
        j = line[:i].rfind(',')
        if j == -1:
            return
        return Io_Implied_Do_Object_List(
            repmap(line[:j].rstrip())), \
            Io_Implied_Do_Control(repmap(line[j+1:].lstrip()))

    def tostr(self):
        return '(%s, %s)' % (self.items)


class Io_Implied_Do_Object(Base):  # R918
    """
    <io-implied-do-object> = <input-item>
                             | <output-item>
    """
    subclass_names = ['Input_Item', 'Output_Item']


class Io_Implied_Do_Control(Base):  # R919
    """
    <io-implied-do-control> = <do-variable> = <scalar-int-expr> ,
        <scalar-int-expr> [ , <scalar-int-expr> ]
    """
    subclass_names = []
    use_names = ['Do_Variable', 'Scalar_Int_Expr']

    @staticmethod
    def match(string):
        line, repmap = string_replace_map(string)
        if '=' not in line:
            return
        v, exprs = line.split('=', 1)
        v = Do_Variable(repmap(v.rstrip()))
        exprs = exprs.lstrip().split(',')
        if len(exprs) not in [2, 3]:
            return
        exprs = tuple([Scalar_Int_Expr(repmap(e.strip())) for e in exprs])
        if len(exprs) == 2:
            return (v,) + exprs + (None,)
        return (v,) + exprs

    def tostr(self):
        if self.items[3] is not None:
            return '%s = %s, %s, %s' % (self.items)
        return '%s = %s, %s' % (self.items[:-1])


class Dtv_Type_Spec(CALLBase):  # R920
    """
    <dtv-type-spec> = TYPE ( <derived-type-spec> )
                      | CLASS ( <derived-type-spec> )
    """
    subclass_names = []
    use_names = ['Derived_Type_Spec']

    @staticmethod
    def match(string):
        return CALLBase.match(['TYPE', 'CLASS'], Derived_Type_Spec,
                              string, require_rhs=True)


class Wait_Stmt(StmtBase, CALLBase):  # R921
    """
    <wait-stmt> = WAIT ( <wait-spec-list> )
    """
    subclass_names = []
    use_names = ['Wait_Spec_List']

    @staticmethod
    def match(string):
        return CALLBase.match('WAIT', Wait_Spec_List, string, require_rhs=True)


class Wait_Spec(KeywordValueBase):  # R922
    """
    <wait-spec> = [ UNIT = ] <file-unit-number>
                  | END = <label>
                  | EOR = <label>
                  | ERR = <label>
                  | ID = <scalar-int-expr>
                  | IOMSG = <iomsg-variable>
                  | IOSTAT = <scalar-int-variable>
    """
    subclass_names = []
    use_names = ['File_Unit_Number', 'Label', 'Scalar_Int_Expr',
                 'Iomsg_Variable', 'Scalar_Int_Variable']

    @staticmethod
    def match(string):
        for (k, v) in [
                (['END', 'EOR', 'ERR'], Label),
                ('IOSTAT', Scalar_Int_Variable),
                ('IOMSG', Iomsg_Variable),
                ('ID', Scalar_Int_Expr),
                ('UNIT', File_Unit_Number), ]:
            try:
                obj = KeywordValueBase.match(k, v, string, upper_lhs=True)
            except NoMatchError:
                obj = None
            if obj is not None:
                return obj
        return 'UNIT', File_Unit_Number(string)


class Backspace_Stmt(StmtBase):  # R923
    """
:F03R:`923`::
    <backspace-stmt> = BACKSPACE <file-unit-number>
                       | BACKSPACE ( <position-spec-list> )

Attributes
----------
items : (File_Unit_Number, Position_Spec_List)
    """
    subclass_names = []
    use_names = ['File_Unit_Number', 'Position_Spec_List']

    @staticmethod
    def match(string):
        if string[:9].upper() != 'BACKSPACE':
            return
        line = string[9:].lstrip()
        if line.startswith('('):
            if not line.endswith(')'):
                return
            return None, Position_Spec_List(line[1:-1].strip())
        return File_Unit_Number(line), None

    def tostr(self):
        if self.items[0] is not None:
            assert self.items[1] is None, repr(self.items)
            return 'BACKSPACE %s' % (self.items[0])
        return 'BACKSPACE(%s)' % (self.items[1])


class Endfile_Stmt(StmtBase):  # R924
    """
:F03R:`924`::
    <endfile-stmt> = ENDFILE <file-unit-number>
                     | ENDFILE ( <position-spec-list> )

Attributes
----------
items : (File_Unit_Number, Position_Spec_List)
    """
    subclass_names = []
    use_names = ['File_Unit_Number', 'Position_Spec_List']

    @staticmethod
    def match(string):
        if string[:7].upper() != 'ENDFILE':
            return
        line = string[7:].lstrip()
        if line.startswith('('):
            if not line.endswith(')'):
                return
            return None, Position_Spec_List(line[1:-1].strip())
        return File_Unit_Number(line), None

    def tostr(self):
        if self.items[0] is not None:
            assert self.items[1] is None, repr(self.items)
            return 'ENDFILE %s' % (self.items[0])
        return 'ENDFILE(%s)' % (self.items[1])


class Rewind_Stmt(StmtBase):  # R925
    """
:F03R:`925`::
    <rewind-stmt> = REWIND <file-unit-number>
                    | REWIND ( <position-spec-list> )

Attributes
----------
items : (File_Unit_Number, Position_Spec_List)
    """
    subclass_names = []
    use_names = ['File_Unit_Number', 'Position_Spec_List']

    @staticmethod
    def match(string):
        if string[:6].upper() != 'REWIND':
            return
        line = string[6:].lstrip()
        if line.startswith('('):
            if not line.endswith(')'):
                return
            return None, Position_Spec_List(line[1:-1].strip())
        return File_Unit_Number(line), None

    def tostr(self):
        if self.items[0] is not None:
            assert self.items[1] is None, repr(self.items)
            return 'REWIND %s' % (self.items[0])
        return 'REWIND(%s)' % (self.items[1])


class Position_Spec(KeywordValueBase):  # R926
    """
    <position-spec> = [ UNIT = ] <file-unit-number>
                      | IOMSG = <iomsg-variable>
                      | IOSTAT = <scalar-int-variable>
                      | ERR = <label>
    """
    subclass_names = []
    use_names = ['File_Unit_Number', 'Iomsg_Variable',
                 'Scalar_Int_Variable', 'Label']

    def match(string):
        for (k, v) in [
                ('ERR', Label),
                ('IOSTAT', Scalar_Int_Variable),
                ('IOMSG', Iomsg_Variable),
                ('UNIT', File_Unit_Number), ]:
            try:
                obj = KeywordValueBase.match(k, v, string, upper_lhs=True)
            except NoMatchError:
                obj = None
            if obj is not None:
                return obj
        return 'UNIT', File_Unit_Number(string)
    match = staticmethod(match)


class Flush_Stmt(StmtBase):  # R927
    """
:F03R:`927`::
    <flush-stmt> = FLUSH <file-unit-number>
                    | FLUSH ( <position-spec-list> )
Attributes
----------
items : (File_Unit_Number, Position_Spec_List)
    """
    subclass_names = []
    use_names = ['File_Unit_Number', 'Position_Spec_List']

    @staticmethod
    def match(string):
        if string[:5].upper() != 'FLUSH':
            return
        line = string[5:].lstrip()
        if line.startswith('('):
            if not line.endswith(')'):
                return
            return None, Position_Spec_List(line[1:-1].strip())
        return File_Unit_Number(line), None

    def tostr(self):
        if self.items[0] is not None:
            assert self.items[1] is None, repr(self.items)
            return 'FLUSH %s' % (self.items[0])
        return 'FLUSH(%s)' % (self.items[1])


class Flush_Spec(KeywordValueBase):  # R928
    """
:F03R:`928`::
    <flush-spec> = [ UNIT = ] <file-unit-number>
                   | IOMSG = <iomsg-variable>
                   | IOSTAT = <scalar-int-variable>
                   | ERR = <label>
Attributes
----------
items : ({'UNIT', 'IOMSG', 'IOSTAT', 'ERR'}, {File_Unit_Number,
          Iomsg_Variable, Scalar_Int_Variable, Label})
    """
    subclass_names = []
    use_names = ['File_Unit_Number', 'Iomsg_Variable',
                 'Scalar_Int_Variable', 'Label']

    def match(string):
        for (k, v) in [
                ('ERR', Label),
                ('IOSTAT', Scalar_Int_Variable),
                ('IOMSG', Iomsg_Variable),
                ('UNIT', File_Unit_Number), ]:
            try:
                obj = KeywordValueBase.match(k, v, string, upper_lhs=True)
            except NoMatchError:
                obj = None
            if obj is not None:
                return obj
        return 'UNIT', File_Unit_Number(string)
    match = staticmethod(match)


class Inquire_Stmt(StmtBase):  # R929
    """
:F03R:`929`::
    <inquire-stmt> = INQUIRE ( <inquire-spec-list> )
                     | INQUIRE ( IOLENGTH = <scalar-int-variable> )
                       <output-item-list>
Attributes
----------
items : (Inquire_Spec_List, Scalar_Int_Variable, Output_Item_List)
    """
    subclass_names = []
    use_names = ['Inquire_Spec_List', 'Scalar_Int_Variable',
                 'Output_Item_List']

    @staticmethod
    def match(string):
        if string[:7].upper() != 'INQUIRE':
            return
        line = string[7:].lstrip()
        if not line.startswith('('):
            return
        if line.endswith(')'):
            return Inquire_Spec_List(line[1:-1].strip()), None, None
        line, repmap = string_replace_map(line)
        i = line.find(')')
        if i == -1:
            return
        tmp = repmap(line[1:i])
        if tmp[:8].upper() != 'IOLENGTH':
            return
        tmp = tmp[8:].lstrip()
        if not tmp.startswith('='):
            return
        tmp = tmp[1:].lstrip()
        return None, Scalar_Int_Variable(tmp), \
            Output_Item_List(repmap(line[i+1:].lstrip()))

    def tostr(self):
        if self.items[0] is None:
            assert None not in self.items[1:], repr(self.items)
            return 'INQUIRE(IOLENGTH=%s) %s' % (self.items[1:])
        return 'INQUIRE(%s)' % (self.items[0])


class Inquire_Spec(KeywordValueBase):  # R930
    """
    :F03R:`930`::
    <inquire-spec> = [ UNIT = ] <file-unit-number>
                     | FILE = <file-name-expr>
                     | ACCESS = <scalar-default-char-variable>
                     | ACTION = <scalar-default-char-variable>
                     | ASYNCHRONOUS = <scalar-default-char-variable>
                     | BLANK = <scalar-default-char-variable>
                     | DECIMAL = <scalar-default-char-variable>
                     | DELIM = <scalar-default-char-variable>
                     | DIRECT = <scalar-default-char-variable>
                     | ENCODING = <scalar-default-char-variable>
                     | ERR = <label>
                     | EXIST = <scalar-default-logical-variable>
                     | FORM = <scalar-default-char-variable>
                     | FORMATTED = <scalar-default-char-variable>
                     | ID = <scalar-int-expr>
                     | IOMSG = <iomsg-variable>
                     | IOSTAT = <scalar-int-variable>
                     | NAME = <scalar-default-char-variable>
                     | NAMED = <scalar-default-logical-variable>
                     | NEXTREC = <scalar-int-variable>
                     | NUMBER = <scalar-int-variable>
                     | OPENED = <scalar-default-logical-variable>
                     | PAD = <scalar-default-char-variable>
                     | PENDING = <scalar-default-logical-variable>
                     | POS = <scalar-int-variable>
                     | POSITION = <scalar-default-char-variable>
                     | READ = <scalar-default-char-variable>
                     | READWRITE = <scalar-default-char-variable>
                     | RECL = <scalar-int-variable>
                     | ROUND = <scalar-default-char-variable>
                     | SEQUENTIAL = <scalar-default-char-variable>
                     | SIGN = <scalar-default-char-variable>
                     | SIZE = <scalar-int-variable>
                     | STREAM = <scalar-default-char-variable>
                     | UNFORMATTED = <scalar-default-char-variable>
                     | WRITE = <scalar-default-char-variable>

    Attributes
    ----------
    items : (str, instance)
    """
    subclass_names = []
    use_names = ['File_Unit_Number', 'File_Name_Expr',
                 'Scalar_Default_Char_Variable',
                 'Scalar_Default_Logical_Variable', 'Scalar_Int_Variable',
                 'Scalar_Int_Expr', 'Label', 'Iomsg_Variable']

    @staticmethod
    def match(string):
        '''
        :param str string: The string to check for conformance with an
                           Inquire_Spec
        :return: 2-tuple of name (e.g. "UNIT") and value or None if
                 string is not a valid Inquire_Spec
        :rtype: 2-tuple where first object represents the name and the
                second the value.
        '''
        if "=" not in string:
            # The only argument which need not be named is the unit number
            return 'UNIT', File_Unit_Number(string)
        # We have a keyword-value pair. Check whether it is valid...
        for (keyword, value) in [
                (['ACCESS', 'ACTION', 'ASYNCHRONOUS', 'BLANK', 'DECIMAL',
                  'DELIM', 'DIRECT', 'ENCODING', 'FORM', 'NAME', 'PAD',
                  'POSITION', 'READ', 'READWRITE', 'ROUND', 'SEQUENTIAL',
                  'SIGN', 'STREAM', 'UNFORMATTED', 'WRITE'],
                 Scalar_Default_Char_Variable),
                ('ERR', Label),
                (['EXIST', 'NAMED', 'PENDING', 'OPENED'],
                 Scalar_Default_Logical_Variable),
                ('ID', Scalar_Int_Expr),
                (['IOSTAT', 'NEXTREC', 'NUMBER', 'POS', 'RECL', 'SIZE'],
                 Scalar_Int_Variable),
                ('IOMSG', Iomsg_Variable),
                ('FILE', File_Name_Expr),
                ('UNIT', File_Unit_Number)]:
            try:
                obj = KeywordValueBase.match(keyword, value, string,
                                             upper_lhs=True)
            except NoMatchError:
                obj = None
            if obj is not None:
                return obj
        return None

#
# SECTION 10
#


class Format_Stmt(StmtBase, WORDClsBase):  # R1001
    """
    <format-stmt> = FORMAT <format-specification>
    """
    subclass_names = []
    use_names = ['Format_Specification']

    @staticmethod
    def match(string):
        return WORDClsBase.match('FORMAT', Format_Specification,
                                 string, require_cls=True)


class Format_Item_List(SequenceBase):  # pylint: disable=invalid-name
    '''This class replaces the one generated by fparser. This class is
    required as support for hollerith strings makes matching more
    complicated.

    '''
    use_names = []
    subclass_names = ['Format_Item']

    @staticmethod
    def match(string):
        '''Implements the matching for a list of format items.

        Supporting Hollerith strings makes it very difficult to
        correctly split the input string into items a-priori. The
        reason for this can be seen in the following example:

        `2H,x,e2.2` is `2H,x` and `e2.2` but when split with commas
        incorrectly gives `2H`, `x` and `e2.2`.

        Further, hollerith strings could also confuse any code that
        tried to determine whether code was inside quotes or not. For
        example:

        `2H"x,2H"x` does not mean that `x,2H` is part of a string.

        The solution chosen is to match one item at a time, first
        checking for a valid Hollerith string and then checking for
        any other valid input.

        :param str string: the string to match as a Format List.
        :return: None if there is no match or a tuple of size 2 \
        containing a string with a comma followed by a tuple \
        containing a list which itself contains the matched \
        format items.
        :rtype: (`str`, \
        ([:py:class:`fparser.two.Fortran2003.Format_Item`s])) or `NoneType`

        '''
        if not string:
            return None
        current_string = string.strip()
        if not current_string:
            return None
        item_list = []
        while current_string:
            # Does the current item match the start of a
            # hollerith string?
            my_pattern = Hollerith_Item.match_pattern
            match = re.search(my_pattern, current_string)
            if match:
                # The current item matches with a hollerith string.
                match_str = match.group(0)
                hol_length_str = match_str[:-1]
                hol_length = int(hol_length_str)
                num_chars = len(match_str) + hol_length
                if len(current_string) < num_chars:
                    # The string is not long enough.
                    return None
                item_list.append(Format_Item(current_string[:num_chars]))
                current_string = current_string[num_chars:].lstrip()
                if current_string:
                    # Remove the next comma and any white space.
                    if current_string[0] != ',':
                        # There is no comma so we have a format error.
                        return None
                    current_string = current_string[1:].lstrip()
            else:
                # Current item does not match with a hollerith string
                # so we are safe to split using a ',' as separator
                # after applying string_replace_map.
                line, repmap = string_replace_map(current_string)
                splitted = line.split(',', 1)
                item_list.append(Format_Item(repmap(splitted[0].strip())))
                current_string = ""
                if len(splitted) == 2:
                    current_string = repmap(splitted[1]).strip()
        if len(item_list) <= 1:
            # a list must contain at least 2 items (see SequenceBase)
            return None
        return ',', tuple(item_list)


class Format_Specification(BracketBase):  # pylint: disable=invalid-name
    '''
    Fortran 2003 rule R1002

    format-specification = ( [ format-item-list ] )

    C1002 is implemented in a separate class Format_Item_C1002

    C1002 (R1002) The comma used to separate format-items in a
    format-item-list may be omitted

    (1) Between a P edit descriptor and an immediately following F, E,
    EN, ES, D, or G edit descriptor, possibly preceded by a repeat
    specifier,

    (2) Before a slash edit descriptor when the optional repeat
    specification is not present,

    (3) After a slash edit descriptor, or

    (4) Before or after a colon edit descriptor.

    '''
    subclass_names = []
    use_names = ['Format_Item_List']

    @staticmethod
    def match(string):
        '''Implements the matching for a format specification.

        :param str string: The string to check for conformance with a \
                           format specification.
        :return: `None` if there is no match, otherwise a tuple of \
        size three, the first entry being a string containing a left \
        bracket and the third being a string containing a right \
        bracket. The second entry is either a Format_Item or a \
        Format_Item_List.
        :rtype: `NoneType` or ( `str`, \
        :py:class:`fparser.two.Fortran2003.Format_Item` or \
        :py:class:`fparser.two.Fortran2003.Format_Item_List`, `str` )

        '''
        return BracketBase.match('()', Format_Item_List, string,
                                 require_cls=False)


def skip_digits(string):
    '''Skips over any potential digits (including spaces) to the next
    non-digit character and return its index. If no such character is
    found or if the first character in the string is not a digit then
    specify that the skip has failed.

    :param str string: The string to search
    :returns: a 2-tuple with the first entry indicating if a valid \
    character has been found and the second entry indicating the index \
    of this character in the 'string' argument.
    :rtype: (bool, int)

    '''
    found = False
    index = 0
    for index, char in enumerate(string):
        if not (char.isdigit() or char == ' '):
            if index > 0:
                found = True
            break
    return found, index


class Format_Item_C1002(Base):  # pylint: disable=invalid-name
    '''
    Fortran 2003 constraint C1002

    format-item-c1002 is kP [,] (F|D)w.d | (E|EN|ES|G)w.d[Ee]
                      or [r]/ [,] format-item
                      or : [,] format-item
                      or format-item [,] / [[,] format-item]
                      or format-item [,] : [[,] format-item]

    C1002 (R1002) The comma used to separate format-items in a
    format-item-list may be omitted

    (1) Between a P edit descriptor and an immediately following F, E,
    EN, ES, D, or G edit descriptor, possibly preceded by a repeat
    specifier,

    (2) Before a slash edit descriptor when the optional repeat
    specification is not present (10.7.2),

    (3) After a slash edit descriptor, or

    (4) Before or after a colon edit descriptor.

    '''
    subclass_names = []
    use_names = ['K', 'W', 'D', 'E', 'Format_Item', 'R']

    @staticmethod
    def match(string):
        '''Implements the matching for the C1002 Format Item constraint. The
        constraints specify certain combinations of format items that
        do not need a comma to separate them. Rather than sorting this
        out when parsing the list, it was decided to treat these
        separately and match them in this class. As a result the
        generated class hierarchy is a little more complicated.

        :param str string: The string to check for conformance with a \
                           C1002 format item constraint.
        :return: `None` if there is no match, otherwise a tuple of \
        size 2 containing a mixture of Control_Edit_Descriptor and \
        Format_Item classes depending on what has been matched.

        :rtype: `NoneType` or ( \
        :py:class:`fparser.two.Control_Edit_Desc`, \
        :py:class:`fparser.two.Format_Item` ) or \
        (:py:class:`fparser.two.Format_Item`, \
        :py:class:`fparser.two.Control_Edit_Desc`) or \
        (:py:class:`fparser.two.Format_Item`, \
        :py:class:`fparser.two.Format_Item`)

        '''
        if not string:
            return None
        strip_string = string.strip()
        if len(strip_string) <= 1:
            return None
        if strip_string[0] in ':/':
            # No comma is required after slash edit descriptor (3) or
            # after a colon edit descriptor (4)
            return Control_Edit_Desc(strip_string[0]), \
                Format_Item(strip_string[1:].lstrip())
        if strip_string[-1] in ':/':
            # No comma is required before a slash edit descriptor,
            # when the optional repeat specification is not present
            # (2), or before a colon edit descriptor (4). Note, if an
            # optional repeat specification is present it will be
            # treated as if it is part of the previous item.
            return Format_Item(strip_string[:-1].rstrip()), \
                Control_Edit_Desc(strip_string[-1])
        # We may have a P edit descriptor (which requires a number
        # before the 'P') (1) or a slash edit descriptor with a repeat
        # specifier (3) so look for the repeat specifier.
        found, index = skip_digits(strip_string)
        if found:
            # We found a possible repeat specifier (which may contain
            # white space after the first digit)
            result = strip_string[index].upper()
            if result == '/':
                # We found a possible slash edit descriptor with a
                # repeat specifier (3).
                return Control_Edit_Desc(strip_string[:index+1]), \
                    Format_Item(strip_string[index+1:].lstrip())
            if result == 'P':
                # We found a possible P edit descriptor (1).
                # Rule C1002 only allows a comma to be ommited between
                # a P edit descriptor and a following F, E, EN, ES, D,
                # or G edit descriptor with an optional repeat
                # specifier. In fparser2 this translates to a
                # Format_Item instance containing a Data_Edit_Desc, or
                # Data_Edit_Desc_C1002 instance as its second item
                # with the data edit descriptor instance's first item
                # specifying the type of edit descriptor.
                lhs = Control_Edit_Desc(strip_string[:index+1])
                rhs = Format_Item(strip_string[index+1:].lstrip())
                if not isinstance(rhs, Format_Item):
                    # Matched with a subclass of Format_item or no match.
                    return None
                descriptor_object = rhs.items[1]
                if not isinstance(descriptor_object, (Data_Edit_Desc,
                                                      Data_Edit_Desc_C1002)):
                    return None
                edit_descriptor = descriptor_object.items[0]
                if edit_descriptor.upper() not in ['F', 'E', 'EN', 'ES',
                                                   'D', 'G']:
                    return None
                return lhs, rhs

        # Replace any content inside strings etc. so we dont split the
        # line in the wrong place.
        line, repmap = string_replace_map(strip_string)

        # Slash and colon edit descriptors may have no comma's both
        # before and after them (2,3,4) e.g. ('a' / 'b'). To match this
        # situation we split the line with the first potential descriptor found
        # in the string and try to match the lhs and rhs separately
        # (adding the edit descriptor to the RHS).
        for option in '/:':
            if option in line:
                left, right = line.split(option, 1)
                return Format_Item(repmap(left.rstrip())), \
                    Format_Item(option+repmap(right.lstrip()))

    def tostr(self):
        '''
        :return: Parsed representation of two format items
        :rtype: str

        :raises InternalError: if the length of the internal items \
        list is not 2.
        :raises InternalError: if the first entry of the internal \
        items list has no content.
        :raises InternalError: if the second entry of the internal \
        items list has no content.

        '''
        if len(self.items) != 2:
            raise InternalError(
                "Class Format_Item_C1002 method tostr(): internal items list "
                "should be length 2 but found '{0}'".format(len(self.items)))
        if not self.items[0]:
            raise InternalError(
                "Class Format_Item_C1002 method tostr() items entry 0 should "
                "contain a format items object but it is empty or None")
        if not self.items[1]:
            raise InternalError(
                "Class Format_Item_C1002 method tostr() items entry 1 should "
                "contain a format items object but it is empty or None")
        return "{0}, {1}".format(self.items[0], self.items[1])


class Hollerith_Item(Base):  # pylint: disable=invalid-name
    '''Hollerith strings take the form `nHx`, where `n` is an integer and
    `x` is a sequence of characters of length `n`.

    Note, the Hollerith format was deprecated in Fortran77 and removed in
    Fortran95. However, Fortran compilers still support it. See, for example
    https://gcc.gnu.org/onlinedocs/gcc-4.8.2/gfortran/
    Hollerith-constants-support.html

    '''
    subclass_names = []
    use_names = []
    match_pattern = '^[1-9][0-9 ]*[hH]'

    @staticmethod
    def match(string):
        '''Implements the matching for a Hollerith string.

        :param str string: The string to check for conformance with a \
                           Hollerith string
        :return: String containing the contents of the Hollerith \
        string.
        :rtype: str

        '''
        from fparser.two.utils import EXTENSIONS
        if 'hollerith' not in EXTENSIONS:
            return None
        if not string:
            return None
        # Only strip space to the left as space to the right could be
        # part of the hollerith string.
        strip_string = string.lstrip()
        match = re.search(Hollerith_Item.match_pattern, strip_string)
        if not match:
            return None
        # Current item matches with a hollerith string.
        match_str = match.group(0)
        hol_length_str = match_str[:-1].replace(' ', '')
        hol_length = int(hol_length_str)
        num_chars = len(match_str) + hol_length
        if len(strip_string) < num_chars:
            # The string is too short
            return None
        if len(strip_string) > num_chars:
            # The string is too long
            if strip_string[num_chars:].strip():
                # The extra is not just white space
                return None
        return strip_string[len(match_str):num_chars],

    def tostr(self):
        '''
        :return: Parsed representation of a Hollerith String.
        :rtype: str

        :raises InternalError: if the length of the internal items \
        list is not 1.
        :raises InternalError: if the first entry of the internal \
        items list has no content.

        '''
        if len(self.items) != 1:
            raise InternalError(
                "Class Hollerith_Item method tostr(): internal items list "
                "should be of length 1 but found '{0}'".
                format(len(self.items)))
        if not self.items[0]:
            raise InternalError(
                "Class Hollerith_Item method tostr() items entry 0 should be "
                "a valid Hollerith string but it is empty or None")
        return "{0}H{1}".format(len(self.items[0]), self.items[0])


class Format_Item(Base):  # pylint: disable=invalid-name
    '''
    Fortran 2003 rule R1003
    format-item is [ r ] data-edit-desc
                or control-edit-desc
                or char-string-edit-desc
                or [ r ] ( format-item-list )
                or format-item-c1002
                or hollerith-item

    '''
    subclass_names = ['Hollerith_Item', 'Control_Edit_Desc',
                      'Char_String_Edit_Desc', 'Format_Item_C1002']
    use_names = ['R', 'Format_Item_List', 'Data_Edit_Desc']

    @staticmethod
    def match(string):
        '''Implements the matching of a Format Item. This method matches '[ r
        ] data-edit-desc' and '[ r ] ( format-item-list )'. The
        remaining options are matched via subclasses specified in the
        subclass_names variable.

        :param str string: A string or the Fortran reader containing the \
                    line of code that we are trying to match.
        :return: `None` if there is no match or a `tuple` of size 2 \
        containing an instance of the R class followed by an \
        instance of either the Format_Item_List or the Data_Edit_Desc \
        class.
        :rtype: `None` or ( :py:class:`fparser.two.Fortran2003.R`, \
        :py:class:`fparser.two.Fortran2003.Format_Item_List` or \
        :py:class:`fparser.two.Fortran2003.Data_Edit_Desc`)

        '''
        if not string:
            return None
        strip_string = string.strip()
        if not strip_string:
            return None
        index = 0
        # Look for an optional repeat specifier (the 'r' in this rule)
        found, index = skip_digits(strip_string)
        rpart = None
        my_string = strip_string
        if found:
            # We found a repeat specifier (with content after it) so
            # create an R class using the value
            rpart = R(strip_string[:index])
            my_string = strip_string[index:].lstrip()
        # We deal with format-item-list and data-edit-desc in this
        # match method. Other matches are performed by the subclasses.
        if my_string[0] == '(' and my_string[-1] == ')':
            # This could be a format-item-list
            rest = Format_Item_List(my_string[1:-1].strip())
        else:
            # This is not a format-item-list so see if it is a
            # data-edit-descriptor
            rest = Data_Edit_Desc(my_string)
        return rpart, rest

    def tostr(self):
        '''
        :return: Parsed representation of a Format Item.
        :rtype: str

        :raises InternalError: if the length of the internal items \
        list is not 2.
        :raises InternalError: if the first entry of the internal \
        items list has no content.

        '''
        if len(self.items) != 2:
            raise InternalError(
                "Class Format_Item method tostr(): internal items list "
                "should be of length 2 but found '{0}'".
                format(len(self.items)))
        if not self.items[1]:
            raise InternalError(
                "Class Format_Item method tostr(): items list second entry "
                "should be a valid descriptor but it is empty or None")
        rpart = self.items[0]
        rest = self.items[1]

        rpart_str = rpart if rpart else ""
        if isinstance(rest, (Data_Edit_Desc, Data_Edit_Desc_C1002)):
            return "{0}{1}".format(rpart_str, rest)
        return "{0}({1})".format(rpart_str, rest)


class R(Base):  # R1004
    """
::
    <r> = <int-literal-constant>

Notes
-----
C1003, C1004: <r> shall be positive and without kind parameter specified.
    """
    subclass_names = ['Digit_String']


class Data_Edit_Desc_C1002(Base):
    '''This class helps implement the matching for the first part of the
    Fortran 2003 Constraint C1002 which constrains rule R1002. In
    particular it matches with the subset of edit descriptors that can
    follow a P edit descriptor without needing a comma, see below:

    C1002 (applied to R1002) The comma used to separate format-items
    in a format-item-list may be omitted

    (1) Between a P edit descriptor and an immediately following F, E,
    EN, ES, D, or G edit descriptor, possibly preceded by a
    repeat specifier.

    [Remaining constraint clauses ommitted as they are not relevant
    here.]

    data-edit-desc is F w . d
                   or E w . d [ E e ]
                   or EN w . d [ E e ]
                   or ES w . d [ E e]
                   or G w . d [ E e ]
                   or D w . d

    '''
    subclass_names = []
    use_names = ['W', 'D', 'E']

    @staticmethod
    def match(string):
        '''Check whether the input matches the rule.

        param str string: contains the Fortran that we are trying to \
        match.
        :return: `None` if there is no match, otherwise a `tuple` of \
        size 4, the first entry containing a string with one of ['F', \
        'E', 'EN', 'ES', 'G', 'D'], the second entry containing a W \
        class instance, the third entry containing D class instance \
        and the fourth entry containing either None or an E class \
        instance.
        :rtype: `NoneType`, (`str`, :py:class:`fparser.two.W`, \
        :py:class:`fparser.two.D`, `NoneType`) or, (`str`, \
        :py:class:`fparser.two.W`, :py:class:`fparser.two.D`, \
        :py:class:`fparser.two.E`)

        '''
        if not string:
            return None
        strip_string = string.strip()
        if not strip_string:
            return None
        char = strip_string[0].upper()
        if char in ['F', 'D']:
            # match w . d
            my_str = strip_string[1:].lstrip().upper()
            if '.' in my_str:
                left, right = my_str.split('.', 1)
                left = left.rstrip()
                right = right.lstrip()
                return char, W(left), D(right), None
            return None
        if char in ['E', 'G']:
            # match w . d [ E e ]
            # Format descriptor could also be 'ES' or 'EN'
            my_str = strip_string[1:].lstrip().upper()
            char2 = my_str[0]
            if char == 'E' and char2 in ['S', 'N']:
                my_str = my_str[1:].lstrip()
            else:
                char2 = ""
            if "." not in my_str:
                return None
            left, right = my_str.split('.', 1)
            left = left.rstrip()
            right = right.lstrip()
            # Can optionally specify the number of digits for the
            # exponent
            if right.count('E') >= 1:
                middle, right = right.split('E', 1)
                middle = middle.rstrip()
                right = right.lstrip()
                return char+char2, W(left), D(middle), E(right)
            return char+char2, W(left), D(right), None
        # Invalid char
        return None

    def tostr(self):
        '''
        :return: parsed representation of a Data Edit Descriptor \
        conforming to constraint C1002.
        :rtype: str

        :raises InternalError: if the length of the internal items \
        list is not 4.
        :raises InternalError: if the first, second or third entry of \
        the internal items list has no content.
        :raises InternalError: if the value of the first entry is \
        unsupported.
        :raises InternalError: if the value of the first entry is 'F' \
        or 'D' and the fourth entry has content.
        :raises InternalError: if the value of the first entry is 'E', \
        'EN', 'ES' or 'G' and the fourth entry is empty or None.

        '''
        if not len(self.items) == 4:
            raise InternalError(
                "Class Data_Edit_Desc_C1002 method tostr() has '{0}' items, "
                "but expecting 4.".format(len(self.items)))
        if not self.items[0]:
            raise InternalError(
                "items[0] in Class Data_Edit_Desc_C1002 method tostr() "
                "should be a descriptor name but is empty or None")
        if not self.items[1]:
            raise InternalError(
                "items[1] in Class Data_Edit_Desc_C1002 method tostr() "
                "should be the w value but is empty or None")
        if not self.items[2]:
            raise InternalError(
                "items[2] in Class Data_Edit_Desc_C1002 method tostr() "
                "should be the m value but is empty or None")
        descriptor_name = self.items[0]
        if descriptor_name in ['F', 'D']:
            if self.items[3]:
                raise InternalError(
                    "items[3] in Class Data_Edit_Desc_C1002 method tostr() "
                    "has an exponent value '{0}' but this is not allowed for "
                    "'F' and 'D' descriptors and should therefore be "
                    "None".format(self.items[3]))
            return "{0}{1}.{2}".format(descriptor_name, self.items[1],
                                       self.items[2])
        elif descriptor_name in ['E', 'EN', 'ES', 'G']:
            if self.items[3] is None:
                return "{0}{1}.{2}".format(descriptor_name, self.items[1],
                                           self.items[2])
            return "{0}{1}.{2}E{3}".format(descriptor_name, self.items[1],
                                           self.items[2], self.items[3])
        raise InternalError(
            "Unexpected descriptor name '{0}' in Class Data_Edit_Desc_C1002 "
            "method tostr()".format(descriptor_name))


class Data_Edit_Desc(Base):  # R1005
    """
::
    <data-edit-desc> =   I <w> [ . <m> ]
                       | B <w> [ . <m> ]
                       | O <w> [ . <m> ]
                       | Z <w> [ . <m> ]
                       | L <w>
                       | A [ <w> ]
                       | DT [ <char-literal-constant> ] [ ( <v-list> ) ]
                       | <data-edit-desc-c1002>
    """
    subclass_names = ['Data_Edit_Desc_C1002']
    use_names = ['W', 'M', 'Char_Literal_Constant', 'V_List']

    @staticmethod
    def match(string):
        c = string[0].upper()
        if c in ['I', 'B', 'O', 'Z']:
            line = string[1:].lstrip()
            if '.' in line:
                i1, i2 = line.split('.', 1)
                i1 = i1.rstrip()
                i2 = i2.lstrip()
                return c, W(i1), M(i2), None, Int_Literal_Constant
            return c, W(line), None, None
        if c == 'L':
            line = string[1:].lstrip()
            if not line:
                return
            return c, W(line), None, None
        if c == 'A':
            line = string[1:].lstrip()
            if not line:
                return c, None, None, None
            return c, W(line), None, None
        c = string[:2].upper()
        if len(c) != 2:
            return
        if c == 'DT':
            line = string[2:].lstrip()
            if not line:
                return c, None, None, None
            lst = None
            if line.endswith(')'):
                i = line.rfind('(')
                if i == -1:
                    return
                tmp = line[i+1:-1].strip()
                if not tmp:
                    return
                lst = V_List(tmp)
                line = line[:i].rstrip()
            if not line:
                return c, None, lst, None
            return c, Char_Literal_Constant(line), lst, None
        return

    def tostr(self):
        c = self.items[0]
        if c in ['I', 'B', 'O', 'Z', 'A', 'L']:
            if self.items[2] is None:
                if self.items[1] is None:
                    return c
                return '%s%s' % (c, self.items[1])
            return '%s%s.%s' % (c, self.items[1], self.items[2])
        if c == 'DT':
            if self.items[1] is None:
                if self.items[2] is None:
                    return c
                else:
                    return '%s(%s)' % (c, self.items[2])
            else:
                if self.items[2] is None:
                    return '%s%s' % (c, self.items[1])
                else:
                    return '%s%s(%s)' % (c, self.items[1], self.items[2])
        raise NotImplementedError(repr(c))


class W(Base):  # R1006
    """
::
    <w> = <int-literal-constant> == <digit-string>

Notes
-----
C1006, C1007: <w> is zero or postive and without kind parameters.
    """
    subclass_names = ['Digit_String']


class M(Base):  # R1007
    """
::
    <m> = <int-literal-constant>

Notes
-----
C1007: <w> is without kind parameters.
    """
    subclass_names = ['Int_Literal_Constant']


class D(Base):  # R1008
    """
::
    <d> = <int-literal-constant>

Notes
-----
C1007: <d> is without kind parameters.
    """
    subclass_names = ['Int_Literal_Constant']


class E(Base):  # R1009
    """
::
    <e> = <int-literal-constant>

Notes
-----
C1005, C1007: <e> is postive and without kind parameters.
    """
    subclass_names = ['Digit_String']


class V(Base):  # R1010
    """
::
    <v> = <signed-int-literal-constant>

Notes
-----
C1007: <w> is without kind parameters.
    """
    subclass_names = ['Signed_Int_Literal_Constant']


class Control_Edit_Desc(Base):  # pylint: disable=invalid-name
    '''
    Fortran 2003 rule R1011

    control-edit-desc is position-edit-desc
                      or [ r ] /
                      or :
                      or sign-edit-desc
                      or k P
                      or blank-interp-edit-desc
                      or round-edit-desc
                      or decimal-edit-desc
                      or $

    '$' is used to suppress the carriage return on output.  Note that
    this is an extension to the Fortran standard.

    '''
    subclass_names = ['Position_Edit_Desc', 'Sign_Edit_Desc',
                      'Blank_Interp_Edit_Desc', 'Round_Edit_Desc',
                      'Decimal_Edit_Desc']
    use_names = ['R', 'K']

    @staticmethod
    def match(string):
        '''Check whether the input matches the rule.

        param str string: contains the Fortran that we are trying to \
        match.
        :return: `None` if there is no match, otherwise a `tuple` of \
        size 2 containing, None and a string with one of '/', ':', or \
        '$', an R class and a string containing '/' or a K class and a \
        string containing 'P'.
        :rtype: `NoneType`, (`NoneType`, `str`), \
        (:py:class:`fparser.two.Fortran2003.R`, `str`), or \
        (:py:class:`fparser.two.Fortran2003.K`, `str`)

        '''
        if not string:
            return None
        strip_string = string.strip()
        if not strip_string:
            return None
        if len(strip_string) == 1 and strip_string in '/:$':
            from fparser.two.utils import EXTENSIONS
            if strip_string == '$' and 'dollar-descriptor' not in EXTENSIONS:
                return None
            return None, strip_string
        if strip_string[-1] == '/':
            return R(strip_string[:-1].rstrip()), '/'
        if strip_string[-1].upper() == 'P':
            return K(strip_string[:-1].rstrip()), 'P'
        return None

    def tostr(self):
        '''
        :return: parsed representation of a Control Edit Descriptor
        :rtype: str
        :raises InternalError: if the length of the internal items \
        list is not 2.
        :raises InternalError: if the second entry of the internal \
        items list has no content.

        '''
        if len(self.items) != 2:
            raise InternalError(
                "Class Control_Edit_Desc method tostr() has '{0}' items, "
                "but expecting 2.".format(len(self.items)))
        if not self.items[1]:
            raise InternalError(
                "items[1] in Class Control_Edit_Desc method tostr() should "
                "be an edit descriptor name but is empty or None")
        if self.items[0] is not None:
            return "{0}{1}".format(self.items[0], self.items[1])
        return "{0}".format(self.items[1])


class K(Base):  # R1012
    """
::
    <k> = <signed-int-literal-constant>

Notes
-----
C1009: <k> is without kind parameters.
    """
    subclass_names = ['Signed_Int_Literal_Constant']


class Position_Edit_Desc(Base):  # R1013
    '''
    Fortran 2003 rule R1013

    position-edit-desc is T n
                       or TL n
                       or TR n
                       or n X

    where n is a positive integer.

    If the extensions list includes the string 'x-format' then 'X'
    without a preceeding integer is also matched. This is a common
    extension in Fortran compilers.

    '''
    subclass_names = []
    use_names = ['N']

    @staticmethod
    def match(string):
        '''Check whether the input matches the rule.

        param str string: contains the Fortran that we are trying to \
        match.
        :return: `None` if there is no match, otherwise a `tuple` of \
        size 2 either containing a `string` which is one of "T", "TL" \
        or "TR", followed by an `N` class, or containing an `N` class, \
        or `None`, followed by an "X".
        :rtype: `NoneType`, (`str`, \
        :py:class:`fparser.two.Fortran2003.N`), \
        (:py:class:`fparser.two.Fortran2003.N`, `str`) or (`NoneType`, \
        `str`)

        '''
        if not string:
            return None
        strip_string_upper = string.strip().upper()
        if not strip_string_upper:
            # empty input string
            return None
        if strip_string_upper[0] == 'T':
            if not len(strip_string_upper) > 1:
                # string is not long enough to be valid
                return None
            if strip_string_upper[1] in 'LR':
                # We match TL* or TR* where * is stored in variable
                # rest
                start = strip_string_upper[:2]
                rest = strip_string_upper[2:].lstrip()
            else:
                # We match T* where * is stored in variable rest
                start = strip_string_upper[0]
                rest = strip_string_upper[1:].lstrip()
            # Note, if class N does not match it raises an exception
            number_obj = N(rest)
            return start, number_obj
        if strip_string_upper[-1] == 'X':
            # We match *X
            from fparser.two.utils import EXTENSIONS
            if "x-format" in EXTENSIONS and len(strip_string_upper) == 1:
                # The match just contains 'X' which is not valid
                # fortran 2003 but is an accepted extension
                return None, "X"
            # Note, if class N does not match it raises an
            # exception
            number_obj = N(strip_string_upper[:-1].rstrip())
            return number_obj, 'X'
        else:
            return None

    def tostr(self):
        '''
        :return: parsed representation of a Position Edit Descriptor
        :rtype: str
        :raises InternalError: if the length of the internal items \
        list is not 2.
        :raises InternalError: if the second entry of the internal \
        items list has no content.

        '''
        if not len(self.items) == 2:
            raise InternalError(
                "Class Position_Edit_Desc method tostr() has '{0}' items, "
                "but expecting 2.".format(len(self.items)))
        if not self.items[1]:
            raise InternalError(
                "items[1] in Class Position_Edit_Desc method tostr() is "
                "empty or None")
        if self.items[0]:
            return "{0}{1}".format(self.items[0], self.items[1])
        # This output is only required for the "x-format" extension.
        return "{0}".format(self.items[1])


class N(Base):  # R1014
    """
::
    <n> = <int-literal-constant> == <digit-string>

C1010, C1011: <n> is positive and without kind parameter.
    """
    subclass_names = ['Digit_String']


class Sign_Edit_Desc(STRINGBase):  # R1015
    """
    <sign-edit-desc> = SS
                       | SP
                       | S
    """
    subclass_names = []

    def match(string):
        return STRINGBase.match(['SS', 'SP', 'S'], string)
    match = staticmethod(match)


class Blank_Interp_Edit_Desc(STRINGBase):  # R1016
    """
    <blank-interp-edit-desc> = BN
                               | BZ
    """
    subclass_names = []

    def match(string):
        return STRINGBase.match(['BN', 'BZ', ], string)
    match = staticmethod(match)


class Round_Edit_Desc(STRINGBase):  # R1017
    """
    <round-edit-desc> = RU
                        | RD
                        | RZ
                        | RN
                        | RC
                        | RP

    """
    subclass_names = []

    def match(string):
        return STRINGBase.match(['RU', 'RD', 'RZ', 'RN', 'RC', 'RP'],
                                string)
    match = staticmethod(match)


class Decimal_Edit_Desc(STRINGBase):  # R1018
    """
    <decimal-edit-desc> = DC
                          | DP
    """
    subclass_names = []

    def match(string):
        return STRINGBase.match(['DC', 'DP'], string)
    match = staticmethod(match)


class Char_String_Edit_Desc(Base):  # R1019
    """
    <char-string-edit-desc> = <char-literal-constant>
    """
    subclass_names = ['Char_Literal_Constant']

#
# SECTION 11
#


class Main_Program(BlockBase):  # R1101 [C1101, C1102, C1103]
    '''Fortran 2003 rule R1101

    This class does not cater for the case where there is no
    program-stmt. The separate Main_Program0() class matches this
    situation. See Class Program() method match() for how this is
    implemented.

    main-program is program-stmt
                    [ specification-part ]
                    [ execution-part ]
                    [ internal-subprogram-part ]
                    end-program-stmt

    C1101 In a main-program, the execution-part shall not contain a
    RETURN statement or an ENTRY statement. This is currently not
    checked, see issue #140.

    C1102 The program-name may be included in the end-program-stmt
    only if the optional program-stmt is used and, if included, shall
    be identical to the program-name specified in the program-stmt.

    C1103 An automatic object shall not appear in the
    specification-part (R204) of a main program. This is currently not
    checked, see issue #140.

    '''
    subclass_names = []
    use_names = ['Program_Stmt', 'Specification_Part', 'Execution_Part',
                 'Internal_Subprogram_Part', 'End_Program_Stmt']

    @staticmethod
    def match(reader):
        '''Implements the matching of a main program which has a Program
        statement. See class Main_Program0 for matching without a
        Program Statement. Matching uses `BlockBase` as it conforms to
        the start/end with optional content pattern. `match_names` is
        set to `True` so that different names e.g. `program x` and
        `end program y` will not match.

        :param reader: the Fortran reader containing the line(s) of \
                       code that we are trying to match
        :type reader: :py:class:`fparser.common.readfortran.FortranReaderBase`

        :returns: `None` if there is not match or, if there is a match, \
                  a `tuple` containing a single `list`, with minimum \
                  size 2 and maximum size 5, which contains instances \
                  of the classes that have matched. The first entry in \
                  the list will be a `Program_Stmt` and the last entry \
                  in the list will be an `End_Program_Stmt`. In-between \
                  these two instances will be an optional \
                  `Specification_Part` followed by an optional \
                  `Execution_Part` followed by an optional \
                  `Internal_Subprogram_Part`.
        :rtype: `NoneType` or \
                ([:py:class:`fparser.two.Fortran2003.Program_Stmt`, \
                optional \
                :py:class:`fparser.two.Fortran2003.Specification_Part`, \
                optional \
                :py:class:`fparser.two.Fortran2003.Execution_Part`, \
                optional \
                :py:class:`fparser.two.Fortran2003.Internal_Subprogram_Part`, \
                :py:class:`fparser.two.Fortran2003.End_Program_Stmt`])

        '''
        return BlockBase.match(
            Program_Stmt, [Specification_Part, Execution_Part,
                           Internal_Subprogram_Part], End_Program_Stmt,
            reader, match_names=True, strict_order=True)


class Main_Program0(BlockBase):
    """<main-program> =
                         [ <specification-part> ]
                         [ <execution-part> ]
                         [ <internal-subprogram-part> ]
                         <end-program-stmt>

    C1102 The program-name may be included in the end-program-stmt
    only if the optional program-stmt is used and, if included, shall
    be identical to the program-name specified in the
    program-stmt.

    In this class an end program name is not allowed due to C1102.

    """
    subclass_names = []
    use_names = ['Program_Stmt', 'Specification_Part',
                 'Execution_Part', 'Internal_Subprogram_Part',
                 'End_Program_Stmt']

    @staticmethod
    def match(reader):
        return BlockBase.match(None,
                               [Specification_Part, Execution_Part,
                                Internal_Subprogram_Part],
                               End_Program_Stmt, reader)


class Program_Stmt(StmtBase, WORDClsBase):  # R1102
    '''
    Fortran 2003 rule R1102
    program-stmt is PROGRAM program-name

    '''
    subclass_names = []
    use_names = ['Program_Name']

    @staticmethod
    def match(string):
        '''Implements the matching for a Program Statement. Makes use of
        `WORDClsBase`, as the required match is a string followed by a
        class. The class is made compulsory for the match as the
        PROGRAM keyword is not valid without a program name.

        :param str string: Fortran code to check for a match
        :returns: `None` if there is no match or, if there is a match, \
                  a tuple of size 2 with the first entry being the \
                  string 'PROGRAM' and the second entry being a `Name` \
                  class containing the name of the program.
        :rtype: `NoneType` or ( `str`, \
                :py:class:`fparser.two.Fortran2003.Name` )

        '''
        return WORDClsBase.match('PROGRAM', Program_Name, string,
                                 require_cls=True)

    def get_name(self):
        '''Provides the program name as an instance of the `Name` class.

        :returns: the program name as a `Name` class
        :rtype: `Name`

        '''
        return self.items[1]

    def get_start_name(self):
        '''Provides the program name as a string. This is used for matching
        with the equivalent `end program` name if there is one.

        :returns: the program name as a string
        :rtype: str

        '''
        return self.get_name().string


class End_Program_Stmt(EndStmtBase):  # R1103
    """
    <end-program-stmt> = END [ PROGRAM [ <program-name> ] ]
    """
    subclass_names = []
    use_names = ['Program_Name']

    @staticmethod
    def match(string):
        return EndStmtBase.match('PROGRAM', Program_Name, string)


class Module(BlockBase):  # R1104
    """
    <module> = <module-stmt>
                   [ <specification-part> ]
                   [ <module-subprogram-part> ]
                   <end-module-stmt>
    """
    subclass_names = []
    use_names = ['Module_Stmt', 'Specification_Part',
                 'Module_Subprogram_Part', 'End_Module_Stmt']

    @staticmethod
    def match(reader):
        return BlockBase.match(Module_Stmt,
                               [Specification_Part, Module_Subprogram_Part],
                               End_Module_Stmt, reader)


class Module_Stmt(StmtBase, WORDClsBase):  # R1105
    """
    <module-stmt> = MODULE <module-name>
    """
    subclass_names = []
    use_names = ['Module_Name']

    @staticmethod
    def match(string):
        return WORDClsBase.match('MODULE', Module_Name, string,
                                 require_cls=True)

    def get_name(self):
        return self.items[1]


class End_Module_Stmt(EndStmtBase):  # R1106
    """
    <end-module-stmt> = END [ MODULE [ <module-name> ] ]
    """
    subclass_names = []
    use_names = ['Module_Name']

    @staticmethod
    def match(string):
        return EndStmtBase.match('MODULE', Module_Name, string)


class Module_Subprogram_Part(BlockBase):  # R1107
    """
    <module-subprogram-part> = <contains-stmt>
                                   <module-subprogram>
                                   [ <module-subprogram> ]...
    """
    subclass_names = []
    use_names = ['Contains_Stmt', 'Module_Subprogram']

    @staticmethod
    def match(reader):
        return BlockBase.match(Contains_Stmt, [Module_Subprogram],
                               None, reader)


class Module_Subprogram(Base):  # R1108
    """
    <module-subprogram> = <function-subprogram>
                          | <subroutine-subprogram>
    """
    subclass_names = ['Function_Subprogram', 'Subroutine_Subprogram']


class Use_Stmt(StmtBase):  # pylint: disable=invalid-name
    '''
    Fortran 2003 rule R1109

    use-stmt is USE [ [ , module-nature ] :: ] module-name [ , rename-list ]
             or USE [ [ , module-nature ] :: ] module-name ,
                 ONLY : [ only-list ]

    '''
    subclass_names = []
    use_names = ['Module_Nature', 'Module_Name', 'Rename_List', 'Only_List']

    @staticmethod
    def match(string):
        '''
        :param str string: Fortran code to check for a match
        :return: 5-tuple containing strings and instances of the classes
                 describing a module (optional module nature, optional
                 double colon delimiter, mandatory module name, optional
                 "ONLY" specification and optional "Rename" or "Only" list)
        :rtype: 5-tuple of objects (module name and 4 optional)
        '''
        line = string.strip()
        # Incorrect 'USE' statement or line too short
        if line[:3].upper() != 'USE':
            return
        line = line[3:]
        # Empty string after 'USE'
        if not line:
            return
        # No separation between 'USE' statement and its specifiers
        if line[0].isalnum():
            return
        line = line.lstrip()
        i = line.find('::')
        nature = None
        dcolon = None
        if i != -1:
            # The nature of the module ("intrinsic" or
            # "non-intrinsic") is specified
            dcolon = '::'
            if line.startswith(','):
                line_nat = line[1:i].strip()
                # Missing Module_Nature between ',' and '::'
                if not line_nat:
                    return
                nature = Module_Nature(line_nat)
            line = line[i+2:].lstrip()
            # No Module_Name after 'USE, Module_Nature ::'
            if not line:
                return
        else:
            # Check for missing '::' after Module_Nature
            items = re.findall(r"[\w']+", line)
            for item in items:
                try:
                    nature = Module_Nature(item)
                except NoMatchError:
                    pass
            # Missing '::' after Module_Nature
            if nature is not None:
                return

        position = line.find(',')
        if position == -1:
            return nature, dcolon, Module_Name(line), '', None
        name = line[:position].rstrip()
        # Missing Module_Name before Only_List
        if not name:
            return
        name = Module_Name(name)
        line = line[position+1:].lstrip()
        # Missing 'ONLY' specification after 'USE Module_Name,'
        if not line:
            return
        if line[:4].upper() == 'ONLY':
            line = line[4:].lstrip()
            if not line:
                # Expected ':' but there is nothing after the 'ONLY'
                # specification
                return
            if line[0] != ':':
                # Expected ':' but there is a different character
                # after the 'ONLY' specification
                return
            line = line[1:].lstrip()
            if not line:
                # Missing Only_List after 'USE Module_Name, ONLY:'
                return nature, dcolon, name, ', ONLY:', None
            return nature, dcolon, name, ', ONLY:', Only_List(line)
        return nature, dcolon, name, ',', Rename_List(line)

    def tostr(self):
        '''
        :return: parsed representation of "USE" statement
        :rtype: string
        :raises InternalError: if items array is not the expected size
        :raises InternalError: if items array[2] is not a string or is an \
                               empty string
        :raises InternalError: if items array[3] is 'None' as it should be \
                               a string
        '''
        if len(self.items) != 5:
            raise InternalError(
                "Use_Stmt.tostr(). 'Items' should be of size 5 but found "
                "'{0}'.".format(len(self.items)))
        if not self.items[2]:
            raise InternalError("Use_Stmt.tostr(). 'Items' entry 2 should "
                                "be a module name but it is empty")
        if self.items[3] is None:
            raise InternalError("Use_Stmt.tostr(). 'Items' entry 3 should "
                                "be a string but found 'None'")
        usestmt = 'USE'
        # Add optional Module_Nature ("INTRINSIC" or "NON_INTRINSIC")
        # followed by a double colon to "USE" statement
        if self.items[0] and self.items[1]:
            usestmt += ", {0} {1}".format(self.items[0], self.items[1])
        # Add optional double colon after "USE" statement without
        # Module_Nature (valid Fortran)
        elif not self.items[0] and self.items[1]:
            usestmt += " {0}".format(self.items[1])
        # Add Module_Name and optional "ONLY" specifier if present
        usestmt += " {0}{1}".format(self.items[2], self.items[3])
        # Add optional Only_List or Rename_List if present
        if self.items[4] is not None:
            usestmt += " {0}".format(self.items[4])
        return usestmt


class Module_Nature(STRINGBase):  # pylint: disable=invalid-name
    """
    R1110

    <module-nature> = INTRINSIC
                      | NON_INTRINSIC
    """
    subclass_names = []

    @staticmethod
    def match(string):
        '''
        :param str string: Fortran code to check for a match
        :return: keyword describing module nature ("INTRINSIC" or
                 "NON_INTRINSIC") or nothing if no match is found
        :rtype: string
        '''
        return STRINGBase.match(['INTRINSIC', 'NON_INTRINSIC'], string)


class Rename(Base):  # R1111
    """
    <rename> = <local-name> => <use-name>
               | OPERATOR(<local-defined-operator>) =>
                 OPERATOR(<use-defined-operator>)
    """
    subclass_names = []
    use_names = ['Local_Name', 'Use_Name', 'Local_Defined_Operator',
                 'Use_Defined_Operator']

    def match(string):
        s = string.split('=>', 1)
        if len(s) != 2:
            return
        lhs, rhs = s[0].rstrip(), s[1].lstrip()
        if not lhs or not rhs:
            return
        if lhs[:8].upper() == 'OPERATOR' and rhs[:8].upper() == 'OPERATOR':
            tmp = lhs[8:].lstrip()
            r = rhs[8:].lstrip()
            if tmp and r and tmp[0] + tmp[-1] == '()':
                if r[0]+r[-1] != '()':
                    return
                tmp = tmp[1:-1].strip()
                r = r[1:-1].strip()
                if not tmp or not r:
                    return
                return 'OPERATOR', Local_Defined_Operator(tmp), \
                    Use_Defined_Operator(r)
        return None, Local_Name(lhs), Use_Name(rhs)
    match = staticmethod(match)

    def tostr(self):
        if not self.items[0]:
            return '%s => %s' % self.items[1:]
        return '%s(%s) => %s(%s)' % (self.items[0], self.items[1],
                                     self.items[0], self.items[2])


class Only(Base):  # R1112
    """
    <only> = <generic-spec>
             | <only-use-name>
             | <rename>
    """
    subclass_names = ['Generic_Spec', 'Only_Use_Name', 'Rename']


class Only_Use_Name(Base):  # R1113
    """
    <only-use-name> = <name>
    """
    subclass_names = ['Name']


class Local_Defined_Operator(Base):  # R1114
    """
    <local-defined-operator> = <defined-unary-op>
                               | <defined-binary-op>
    """
    subclass_names = ['Defined_Unary_Op', 'Defined_Binary_Op']


class Use_Defined_Operator(Base):  # R1115
    """
    <use-defined-operator> = <defined-unary-op>
                             | <defined-binary-op>
    """
    subclass_names = ['Defined_Unary_Op', 'Defined_Binary_Op']


class Block_Data(BlockBase):  # R1116
    """
::
    <block-data> = <block-data-stmt>
                       [ <specification-part> ]
                       <end-block-data-stmt>
    """
    subclass_names = []
    use_names = ['Block_Data_Stmt', 'Specification_Part',
                 'End_Block_Data_Stmt']

    @staticmethod
    def match(reader):
        return BlockBase.match(
            Block_Data_Stmt, [Specification_Part],
            End_Block_Data_Stmt, reader)


class Block_Data_Stmt(StmtBase):  # R1117
    """
::
    <block-data-stmt> = BLOCK DATA [ <block-data-name> ]
    """
    subclass_names = []
    use_names = ['Block_Data_Name']

    @staticmethod
    def match(string):
        if string[:5].upper() != 'BLOCK':
            return
        line = string[5:].lstrip()
        if line[:4].upper() != 'DATA':
            return
        line = line[4:].lstrip()
        if not line:
            return None,
        return Block_Data_Name(line),

    def tostr(self):
        if self.items[0] is None:
            return 'BLOCK DATA'
        return 'BLOCK DATA %s' % self.items

    def get_name(self):
        return self.items[0]


class End_Block_Data_Stmt(EndStmtBase):  # R1118
    """
::
    <end-block-data-stmt> = END [ BLOCK DATA [ <block-data-name> ] ]
    """
    subclass_names = []
    use_names = ['Block_Data_Name']

    @staticmethod
    def match(string):
        return EndStmtBase.match('BLOCK DATA', Block_Data_Name, string)


#
# SECTION 12
#


class Interface_Block(BlockBase):  # R1201
    """
::
    <interface-block> = <interface-stmt>
                            [ <interface-specification> ]...
                            <end-interface-stmt>
    """
    subclass_names = []
    use_names = ['Interface_Stmt', 'Interface_Specification',
                 'End_Interface_Stmt']

    @staticmethod
    def match(reader):
        return BlockBase.match(
            Interface_Stmt, [Interface_Specification],
            End_Interface_Stmt, reader)


class Interface_Specification(Base):  # R1202
    """
    <interface-specification> = <interface-body>
                                | <procedure-stmt>
    """
    subclass_names = ['Interface_Body', 'Procedure_Stmt']


class Interface_Stmt(StmtBase):  # R1203
    """
::
    <interface-stmt> = INTERFACE [ <generic-spec> ]
                       | ABSTRACT INTERFACE

Attributes
----------
items : ({Generic_Spec, 'ABSTRACT'},)
    """
    subclass_names = []
    use_names = ['Generic_Spec']

    @staticmethod
    def match(string):
        if string[:9].upper() == 'INTERFACE':
            line = string[9:].strip()
            if not line:
                return None,
            return Generic_Spec(line),
        if string[:8].upper() == 'ABSTRACT':
            line = string[8:].strip()
            if line.upper() == 'INTERFACE':
                return 'ABSTRACT',

    def tostr(self):
        if self.items[0] == 'ABSTRACT':
            return 'ABSTRACT INTERFACE'
        if self.items[0] is None:
            return 'INTERFACE'
        return 'INTERFACE %s' % (self.items[0])


class End_Interface_Stmt(EndStmtBase):  # R1204
    """
::
    <end-interface-stmt> = END INTERFACE [ <generic-spec> ]

Attributes
----------
items : (Generic_Spec, )
    """
    subclass_names = []
    use_names = ['Generic_Spec']

    def match(string):
        return EndStmtBase.match(
            'INTERFACE', Generic_Spec, string, require_stmt_type=True)
    match = staticmethod(match)


class Function_Body(BlockBase):
    """
::
    <function-body> = <function-stmt>
                        [ <specification-part> ]
                      <end-function-stmt>
    """
    subclass_names = []
    use_names = ['Function_Stmt', 'Specification_Part', 'End_Function_Stmt']

    @staticmethod
    def match(reader):
        return BlockBase.match(
            Function_Stmt, [Specification_Part],
            End_Function_Stmt, reader)


class Subroutine_Body(BlockBase):
    """
::
    <subroutine-body> = <subroutine-stmt>
                        [ <specification-part> ]
                      <end-subroutine-stmt>
    """
    subclass_names = []
    use_names = ['Subroutine_Stmt', 'Specification_Part',
                 'End_Subroutine_Stmt']

    @staticmethod
    def match(reader):
        return BlockBase.match(
            Subroutine_Stmt, [Specification_Part],
            End_Subroutine_Stmt, reader)


class Interface_Body(Base):  # R1205
    """
::
    <interface-body> = <function-body> | <subroutine-body>

See also
--------
Function_Body, Subroutine_Body
    """
    subclass_names = ['Function_Body', 'Subroutine_Body']
    use_names = []


class Procedure_Stmt(StmtBase):  # R1206
    """
::
    <procedure-stmt> = [ MODULE ] PROCEDURE <procedure-name-list>

Attributes
----------
items : (Procedure_Name_List, )
    """
    subclass_names = []
    use_names = ['Procedure_Name_List']

    @staticmethod
    def match(string):
        if string[:6].upper() == 'MODULE':
            line = string[6:].lstrip()
        else:
            line = string
        if line[:9].upper() != 'PROCEDURE':
            return
        line = line[9:].lstrip()
        return Procedure_Name_List(line),

    def tostr(self):
        return 'MODULE PROCEDURE %s' % (self.items[0])


class Generic_Spec(Base):  # R1207
    """
::
    <generic-spec> = <generic-name>
                     | OPERATOR ( <defined-operator> )
                     | ASSIGNMENT ( = )
                     | <dtio-generic-spec>
Attributes
----------
items : ({'OPERATOR', 'ASSIGNMENT'}, {Defined_Operator, '='})
    """
    subclass_names = ['Generic_Name', 'Dtio_Generic_Spec']
    use_names = ['Defined_Operator']

    @staticmethod
    def match(string):
        if string[:8].upper() == 'OPERATOR':
            line = string[8:].lstrip()
            if not line or line[0] != '(' or line[-1] != ')':
                return
            return 'OPERATOR', Defined_Operator(line[1:-1].strip())
        if string[:10].upper() == 'ASSIGNMENT':
            line = string[10:].lstrip()
            if not line or line[0] != '(' or line[-1] != ')':
                return
            if line[1:-1].strip() == '=':
                return 'ASSIGNMENT', '='

    def tostr(self):
        return '%s(%s)' % (self.items)


class Dtio_Generic_Spec(Base):  # R1208
    """
::
    <dtio-generic-spec> = READ ( FORMATTED )
                          | READ ( UNFORMATTED )
                          | WRITE ( FORMATTED )
                          | WRITE ( UNFORMATTED )
Attributes
----------
items : (str, )
    """
    subclass_names = []

    @staticmethod
    def match(string):
        for rw in ['READ', 'WRITE']:
            if string[:len(rw)].upper() == rw:
                line = string[len(rw):].lstrip()
                if not line:
                    return
                if line[0] != '(' or line[-1] != ')':
                    return
                line = line[1:-1].strip().upper()
                if line in ['FORMATTED', 'UNFORMATTED']:
                    return '%s(%s)' % (rw, line),

    def tostr(self):
        return '%s' % (self.items[0])


class Import_Stmt(StmtBase, WORDClsBase):  # pylint: disable=invalid-name
    '''
    Fortran 2003 rule R1209
    import-stmt is IMPORT [[ :: ] import-name-list ]

    C1210 (R1209) The IMPORT statement is allowed only in an
    interface-body. Note, this constraint is not currently enforced.

    C1211 (R1209) Each import-name shall be the name of an entity in
    the host scoping unit. This constraint is not currently enforced
    and can not be generally enforced as the name may come from a use
    statement without an only clause.

    '''
    subclass_names = []
    use_names = ['Import_Name_List']
    tostr = WORDClsBase.tostr_a

    @staticmethod
    def match(string):
        '''
        Implements the matching for the import-stmt rule.

        Makes use of the WORDClsBase base class.

        :param str string: the string to match.

        :returns: None if there is no match, otherwise a tuple of size \
            2 containing the string `IMPORT` as the first entry and \
            an object of type `Import_Name_List` if names are \
            specified in the string or `None` if not.

        :rtype: None, or (str, \
            :py:class:`fparser.two.Fortran2003.Import_Name_List`) or \
            (str, None)

        '''
        return WORDClsBase.match(
            'IMPORT', Import_Name_List, string, colons=True,
            require_cls=False)


class External_Stmt(StmtBase, WORDClsBase):  # R1210
    """
    <external-stmt> = EXTERNAL [ :: ] <external-name-list>
    """
    subclass_names = []
    use_names = ['External_Name_List']

    def match(string):
        return WORDClsBase.match(
            'EXTERNAL', External_Name_List, string,
            colons=True, require_cls=True)
    match = staticmethod(match)
    tostr = WORDClsBase.tostr_a


class Procedure_Declaration_Stmt(StmtBase):  # R1211
    """
::
    <procedure-declaration-stmt> = PROCEDURE ( [ <proc-interface> ] )
        [ [ , <proc-attr-spec> ]... :: ] <proc-decl-list>

Attributes
----------
items : (Proc_Interface, Proc_Attr_Spec_List, Proc_Decl_List)
    """
    subclass_names = []
    use_names = ['Proc_Interface', 'Proc_Attr_Spec_List', 'Proc_Decl_List']

    @staticmethod
    def match(string):
        if string[:9].upper() != 'PROCEDURE':
            return
        line = string[9:].lstrip()
        if not line.startswith('('):
            return
        line, repmap = string_replace_map(line)
        i = line.find(')')
        if i == -1:
            return
        tmp = line[1:i].strip()
        proc_interface = Proc_Interface(repmap(tmp)) if tmp else None
        line = line[i+1:].lstrip()
        i = line.find('::')
        proc_attr_spec_list = None
        if i != -1:
            tmp = line[:i].rstrip()
            if tmp and tmp[0] == ',':
                proc_attr_spec_list = Proc_Attr_Spec_List(
                    repmap(tmp[1:].lstrip()))
            line = line[i+2:].lstrip()
        return proc_interface, proc_attr_spec_list, \
            Proc_Decl_List(repmap(line))

    def tostr(self):
        r = 'PROCEDURE'
        if self.items[0] is not None:
            r += '(%s)' % (self.items[0])
        else:
            r += '()'
        if self.items[1] is not None:
            r += ', %s ::' % (self.items[1])
        return '%s %s' % (r, self.items[2])


class Proc_Interface(Base):  # R1212
    """
    <proc-interface> = <interface-name>
                       | <declaration-type-spec>
    """
    subclass_names = ['Interface_Name', 'Declaration_Type_Spec']


class Proc_Attr_Spec(Base):  # R1213
    """
    <proc-attr-spec> = <access-spec>
                       | <proc-language-binding-spec>
                       | INTENT ( <intent-spec> )
                       | OPTIONAL
                       | POINTER
                       | PROTECTED
                       | SAVE

Attributes
----------
items : ({'INTENT', 'OPTIONAL', 'POINTER', 'PROTECTED', 'SAVE'}, Intent_Spec)
    """
    subclass_names = ['Access_Spec', 'Proc_Language_Binding_Spec']
    use_names = ['Intent_Spec']

    @staticmethod
    def match(string):
        '''
        Matches procedure arguments.

        :param str string: Candidate string.
        :return: Discovered arguments.
        :rtype: tuple, str or None
        '''
        if string[:6].upper() == 'INTENT':
            line = string[6:].lstrip()
            if not line:
                return
            if line[0] != '(' or line[-1] != ')':
                return
            return 'INTENT', Intent_Spec(line[1:-1].strip())
        if len(string) == 8 and string.upper() == 'OPTIONAL':
            return 'OPTIONAL', None
        if len(string) == 7 and string.upper() == 'POINTER':
            return 'POINTER', None
        if len(string) == 9 and string.upper() == 'PROTECTED':
            return 'PROTECTED', None
        if len(string) == 4 and string.upper() == 'SAVE':
            return 'SAVE', None

    def tostr(self):
        if self.items[1] is None:
            return '%s' % (self.items[0])
        return '%s(%s)' % (self.items)


class Proc_Decl(BinaryOpBase):  # R1214
    """
::
    <proc-decl> = <procedure-entity-name> [ => <null-init> ]

Attributes
----------
items : (Procedure_Entity_Name, Null_Init)
    """
    subclass_names = ['Procedure_Entity_Name']
    use_names = ['Null_Init']

    def match(string):
        return BinaryOpBase.match(Procedure_Entity_Name, '=>',
                                  Null_Init, string)
    match = staticmethod(match)


class Interface_Name(Base):  # R1215
    """
    <interface-name> = <name>
    """
    subclass_names = ['Name']


class Intrinsic_Stmt(StmtBase, WORDClsBase):  # R1216
    """
    <intrinsic-stmt> = INTRINSIC [ :: ] <intrinsic-procedure-name-list>
    """
    subclass_names = []
    use_names = ['Intrinsic_Procedure_Name_List']

    def match(string):
        return WORDClsBase.match(
            'INTRINSIC', Intrinsic_Procedure_Name_List,
            string, colons=True, require_cls=True)
    match = staticmethod(match)
    tostr = WORDClsBase.tostr_a


class Function_Reference(CallBase):  # R1217
    """
    <function-reference> = <procedure-designator>
        ( [ <actual-arg-spec-list> ] )
    """
    subclass_names = []
    use_names = ['Procedure_Designator', 'Actual_Arg_Spec_List']

    def match(string):
        return CallBase.match(
            Procedure_Designator, Actual_Arg_Spec_List, string)
    match = staticmethod(match)


class Intrinsic_Name(STRINGBase):  # No explicit rule
    '''Represents the name of a Fortran intrinsic function.

    All generic intrinsic names are specified as keys in the
    `generic_function_names` dictionary, with their values indicating
    the minimum and maximum number of arguments allowed for this
    intrinsic function. A `-1` indicates an unlimited number of
    arguments. The names are split into the categories specified in
    the Fortran2003 specification document.

    All specific intrinsic names (which have a different name to their
    generic counterpart) are specified as keys in the
    `specific_function_names` dictionary, with their values indicating
    which generic function they are associated with.

    '''

    numeric_names = {
        "ABS": {"min": 1, "max": 1}, "AIMAG": {"min": 1, "max": 1},
        "AINT": {"min": 1, "max": 2}, "ANINT": {"min": 1, "max": 2},
        "CEILING": {"min": 1, "max": 2}, "CMPLX": {"min": 1, "max": 3},
        "CONJG": {"min": 1, "max": 1}, "DBLE": {"min": 1, "max": 1},
        "DIM": {"min": 2, "max": 2}, "DPROD": {"min": 2, "max": 2},
        "FLOOR": {"min": 1, "max": 2}, "INT": {"min": 1, "max": 2},
        "MAX": {"min": 2, "max": None}, "MIN": {"min": 2, "max": None},
        "MOD": {"min": 2, "max": 2}, "MODULO": {"min": 2, "max": 2},
        "NINT": {"min": 1, "max": 2}, "REAL": {"min": 1, "max": 2},
        "SIGN": {"min": 2, "max": 2}}

    mathematical_names = {
        "ACOS": {"min": 1, "max": 1}, "ASIN": {"min": 1, "max": 1},
        "ATAN": {"min": 1, "max": 1}, "ATAN2": {"min": 2, "max": 2},
        "COS": {"min": 1, "max": 1}, "COSH": {"min": 1, "max": 1},
        "EXP": {"min": 1, "max": 1}, "LOG": {"min": 1, "max": 1},
        "LOG10": {"min": 1, "max": 1}, "SIN": {"min": 1, "max": 1},
        "SINH": {"min": 1, "max": 1}, "SQRT": {"min": 1, "max": 1},
        "TAN": {"min": 1, "max": 1}, "TANH": {"min": 1, "max": 1}}

    # Removed max and min from this dictionary as they already appear
    # in numeric_function_names.
    character_names = {
        "ACHAR": {"min": 1, "max": 2}, "ADJUSTL": {"min": 1, "max": 1},
        "ADJUSTR": {"min": 1, "max": 1}, "CHAR": {"min": 1, "max": 2},
        "IACHAR": {"min": 1, "max": 2}, "ICHAR": {"min": 1, "max": 2},
        "INDEX": {"min": 2, "max": 4}, "LEN_TRIM": {"min": 1, "max": 2},
        "LGE": {"min": 2, "max": 2}, "LGT": {"min": 2, "max": 2},
        "LLE": {"min": 2, "max": 2}, "LLT": {"min": 2, "max": 2},
        "REPEAT": {"min": 2, "max": 2}, "SCAN": {"min": 2, "max": 4},
        "TRIM": {"min": 1, "max": 1}, "VERIFY": {"min": 2, "max": 4}}

    kind_names = {
        "KIND": {"min": 1, "max": 1},
        "SELECTED_CHAR_KIND": {"min": 1, "max": 1},
        "SELECTED_INT_KIND": {"min": 1, "max": 1},
        "SELECTED_REAL_KIND": {"min": 1, "max": 2}}

    miscellaneous_type_conversion_names = {
        "LOGICAL": {"min": 1, "max": 2},
        "TRANSFER": {"min": 2, "max": 3}}

    numeric_inquiry_names = {
        "DIGITS": {"min": 1, "max": 1},
        "EPSILON": {"min": 1, "max": 1},
        "HUGE": {"min": 1, "max": 1},
        "MAXEXPONENT": {"min": 1, "max": 1},
        "MINEXPONENT": {"min": 1, "max": 1},
        "PRECISION": {"min": 1, "max": 1},
        "RADIX": {"min": 1, "max": 1},
        "RANGE": {"min": 1, "max": 1},
        "TINY": {"min": 1, "max": 1}}

    array_inquiry_names = {
        "LBOUND": {"min": 1, "max": 3},
        "SHAPE": {"min": 1, "max": 2},
        "SIZE": {"min": 1, "max": 3},
        "UBOUND": {"min": 1, "max": 3}}

    other_inquiry_names = {
        "ALLOCATED": {"min": 1, "max": 1},
        "ASSOCIATED": {"min": 1, "max": 2},
        "BIT_SIZE": {"min": 1, "max": 1},
        "EXTENDS_TYPE_OF": {"min": 2, "max": 2},
        "LEN": {"min": 1, "max": 2},
        "NEW_LINE": {"min": 1, "max": 1},
        "PRESENT": {"min": 1, "max": 1},
        "SAME_TYPE_AS": {"min": 2, "max": 2}}

    bit_manipulation_names = {
        "BTEST": {"min": 2, "max": 2},
        "IAND": {"min": 2, "max": 2},
        "IBCLR": {"min": 2, "max": 2},
        "IBITS": {"min": 2, "max": 2},
        "IBSET": {"min": 2, "max": 2},
        "IEOR": {"min": 2, "max": 2},
        "IOR": {"min": 2, "max": 2},
        "ISHFT": {"min": 2, "max": 2},
        "ISHFTC": {"min": 2, "max": 3},
        "MVBITS": {"min": 5, "max": 5},
        "NOT": {"min": 1, "max": 1}}

    floating_point_manipulation_names = {
        "EXPONENT": {"min": 1, "max": 1},
        "FRACTION": {"min": 1, "max": 1},
        "NEAREST": {"min": 2, "max": 2},
        "RRSPACING": {"min": 1, "max": 1},
        "SCALE": {"min": 2, "max": 2},
        "SET_EXPONENT": {"min": 2, "max": 2},
        "SPACING": {"min": 1, "max": 1}}

    vector_and_matrix_multiply_names = {
        "DOT_PRODUCT": {"min": 2, "max": 2},
        "MATMUL": {"min": 2, "max": 2}}

    array_reduction_names = {
        "ALL": {"min": 1, "max": 2},
        "ANY": {"min": 1, "max": 2},
        "COUNT": {"min": 1, "max": 3},
        "MAXVAL": {"min": 1, "max": 3},
        "MINVAL": {"min": 1, "max": 3},
        "PRODUCT": {"min": 1, "max": 3},
        "SUM": {"min": 1, "max": 3}}

    array_construction_names = {
        "CSHIFT": {"min": 2, "max": 3},
        "EOSHIFT": {"min": 2, "max": 4},
        "MERGE": {"min": 3, "max": 3},
        "PACK": {"min": 2, "max": 3},
        "RESHAPE": {"min": 2, "max": 4},
        "SPREAD": {"min": 3, "max": 3},
        "TRANSPOSE": {"min": 1, "max": 1},
        "UNPACK": {"min": 3, "max": 3}}

    array_location_names = {
        "MAXLOC": {"min": 1, "max": 4},
        "MINLOC": {"min": 1, "max": 4}}

    null_names = {
        "NULL": {"min": 0, "max": 1}}

    allocation_transfer_names = {
        "MOVE_ALLOC": {"min": 2, "max": 2}}

    random_number_names = {
        "RANDOM_NUMBER": {"min": 1, "max": 1},
        "RANDOM_SEED": {"min": 0, "max": 3}}

    system_environment_names = {
        "COMMAND_ARGUMENT_COUNT": {"min": 0, "max": 0},
        "CPU_TIME": {"min": 1, "max": 1},
        "DATE_AND_TIME": {"min": 0, "max": 4},
        "GET_COMMAND": {"min": 0, "max": 3},
        "GET_COMMAND_ARGUMENT": {"min": 1, "max": 4},
        "GET_ENVIRONMENT_VARIABLE": {"min": 1, "max": 5},
        "IS_IOSTAT_END": {"min": 1, "max": 1},
        "IS_IOSTAT_EOR": {"min": 1, "max": 1},
        "SYSTEM_CLOCK": {"min": 0, "max": 3}}

    # A map from specific function names to their generic equivalent.
    specific_function_names = {
        "ALOG": "LOG", "ALOG10": "LOG10", "AMAX0": "MAX", "AMAX1": "MAX",
        "AMIN0": "MIN", "AMIN1": "MIN", "AMOD": "MOD", "CABS": "ABS",
        "CCOS": "COS", "CEXP": "EXP", "CLOG": "LOG", "CSIN": "SIN",
        "CSQRT": "SQRT", "DABS": "ABS", "DACOS": "ACOS", "DASIN": "ASIN",
        "DATAN": "ATAN", "DATAN2": "ATAN2", "DCOS": "COS", "DCOSH": "COSH",
        "DDIM": "DIM", "DEXP": "EXP", "DINT": "AINT", "DLOG": "LOG",
        "DLOG10": "LOG10", "DMAX1": "MAX", "DMIN1": "MIN", "DMOD": "MOD",
        "DNINT": "ANINT", "DSIGN": "SIGN", "DSIN": "SIN", "DSINH": "SINH",
        "DSQRT": "SQRT", "DTAN": "TAN", "DTANH": "TANH", "FLOAT": "REAL",
        "IABS": "ABS", "IDIM": "DIM", "IDINT": "INT", "IDNINT": "NINT",
        "IFIX": "INT", "ISIGN": "SIGN", "MAX0": "MAX", "MAX1": "MAX",
        "MIN0": "MIN", "MIN1": "MIN", "SNGL": "REAL"}

    generic_function_names = {}
    generic_function_names.update(numeric_names)
    generic_function_names.update(mathematical_names)
    generic_function_names.update(character_names)
    generic_function_names.update(kind_names)
    generic_function_names.update(miscellaneous_type_conversion_names)
    generic_function_names.update(numeric_inquiry_names)
    generic_function_names.update(array_inquiry_names)
    generic_function_names.update(other_inquiry_names)
    generic_function_names.update(bit_manipulation_names)
    generic_function_names.update(floating_point_manipulation_names)
    generic_function_names.update(vector_and_matrix_multiply_names)
    generic_function_names.update(array_reduction_names)
    generic_function_names.update(array_construction_names)
    generic_function_names.update(array_location_names)
    generic_function_names.update(null_names)
    generic_function_names.update(allocation_transfer_names)
    generic_function_names.update(random_number_names)
    generic_function_names.update(system_environment_names)

    # A list of all function names
    function_names = (list(generic_function_names.keys()) +
                      list(specific_function_names.keys()))

    subclass_names = []

    @staticmethod
    def match(string):
        '''Attempt to match the input `string` with the intrinsic function
        names defined in `generic_function_names` or
        `specific_function_names`. If there is a match the resultant
        string will be converted to upper case.

        :param str string: The pattern to be matched.

        :returns: A tuple containing the matched string (converted to \
        upper case) if there is a match or None if there is not.
        :rtype: (str,) or NoneType

        '''
        return STRINGBase.match(Intrinsic_Name.function_names, string)


class Intrinsic_Function_Reference(CallBase):  # No explicit rule
    '''Represents Fortran intrinsics.

    function-reference is intrinsic-name ( [ actual-arg-spec-list ] )

    '''
    subclass_names = []
    use_names = ['Intrinsic_Name', 'Actual_Arg_Spec_List']

    @staticmethod
    def match(string):
        '''Match the string as an intrinsic function. Also check that the
        number of arguments provided matches the number expected by
        the intrinsic.

        :param str string: the string to match with the pattern rule.

        :return: a tuple of size 2 containing the name of the \
        intrinsic and its arguments if there is a match, or None if \
        there is not.
        :rtype: (:py:class:`fparser.two.Fortran2003.Intrinsic_Name`, \
        :py:class:`fparser.two.Fortran2003.Actual_Arg_Spec_List`) or \
        NoneType

        :raises InternalSyntaxError: If the number of arguments \
        provided does not match the number of arguments expected by \
        the intrinsic.

        '''
        result = CallBase.match(
            Intrinsic_Name, Actual_Arg_Spec_List, string)
        if result:
            # There is a match so check the number of args provided
            # matches the number of args expected by the intrinsic.
            function_name = str(result[0])
            function_args = result[1]
            # This if/else will not be needed once issue #170 has been
            # addressed.
            if isinstance(function_args, Actual_Arg_Spec_List):
                nargs = len(function_args.items)
            elif function_args is None:
                nargs = 0
            else:
                nargs = 1

            if function_name in Intrinsic_Name.specific_function_names.keys():
                # If this is a specific function then use its generic
                # name to test min and max number of arguments.
                test_name = Intrinsic_Name.specific_function_names[
                    function_name]
            else:
                test_name = function_name

            min_nargs = Intrinsic_Name.generic_function_names[test_name]["min"]
            max_nargs = Intrinsic_Name.generic_function_names[test_name]["max"]

            if max_nargs is None:
                if nargs < min_nargs:
                    # None indicates an unlimited number of arguments
                    raise InternalSyntaxError(
                        "Intrinsic '{0}' expects at least {1} args but found "
                        "{2}.".format(function_name, min_nargs, nargs))
                # The number of arguments is valid. Return here as
                # further tests will fail due to max_args being
                # None.
                return result
            if min_nargs == max_nargs and nargs != min_nargs:
                raise InternalSyntaxError(
                    "Intrinsic '{0}' expects {1} arg(s) but found {2}."
                    "".format(function_name, min_nargs, nargs))
            if min_nargs < max_nargs and (nargs < min_nargs or
                                          nargs > max_nargs):
                raise InternalSyntaxError(
                    "Intrinsic '{0}' expects between {1} and {2} args but "
                    "found {3}.".format(function_name, min_nargs, max_nargs,
                                        nargs))
        return result


class Call_Stmt(StmtBase):  # R1218
    """
    <call-stmt> = CALL <procedure-designator>
                  [ ( [ <actual-arg-spec-list> ] ) ]

Attributes
----------
items : (Procedure_Designator, Actual_Arg_Spec_List)
    """
    subclass_names = []
    use_names = ['Procedure_Designator', 'Actual_Arg_Spec_List']

    def match(string):
        if string[:4].upper() != 'CALL':
            return
        line, repmap = string_replace_map(string[4:].lstrip())
        if line.endswith(')'):
            i = line.rfind('(')
            if i == -1:
                return
            args = repmap(line[i+1:-1].strip())
            if args:
                return Procedure_Designator(repmap(line[:i].rstrip())), \
                       Actual_Arg_Spec_List(args)
            return Procedure_Designator(repmap(line[:i].rstrip())), None
        return Procedure_Designator(string[4:].lstrip()), None
    match = staticmethod(match)

    def tostr(self):
        if self.items[1] is None:
            return 'CALL %s' % (self.items[0])
        return 'CALL %s(%s)' % self.items


class Procedure_Designator(BinaryOpBase):  # R1219
    """
    <procedure-designator> = <procedure-name>
                             | <proc-component-ref>
                             | <data-ref> % <binding-name>
    """
    subclass_names = ['Procedure_Name', 'Proc_Component_Ref']
    use_names = ['Data_Ref', 'Binding_Name']

    def match(string):
        return BinaryOpBase.match(Data_Ref, pattern.percent_op.named(),
                                  Binding_Name, string)
    match = staticmethod(match)


class Actual_Arg_Spec(KeywordValueBase):  # R1220
    """
    <actual-arg-spec> = [ <keyword> = ] <actual-arg>
    """
    subclass_names = ['Actual_Arg']
    use_names = ['Keyword']

    @staticmethod
    def match(string):
        return KeywordValueBase.match(Keyword, Actual_Arg, string)


class Actual_Arg(Base):  # R1221
    """
    <actual-arg> = <expr>
                 | <variable>
                 | <procedure-name>
                 | <proc-component-ref>
                 | <alt-return-spec>
    """
    subclass_names = ['Expr',
                      'Procedure_Name',
                      'Proc_Component_Ref',
                      'Alt_Return_Spec',
                      'Variable']


class Alt_Return_Spec(Base):  # R1222
    """
    <alt-return-spec> = * <label>
    """
    subclass_names = []
    use_names = ['Label']

    def match(string):
        if not string.startswith('*'):
            return
        line = string[1:].lstrip()
        if not line:
            return
        return Label(line),
    match = staticmethod(match)

    def tostr(self):
        return '*%s' % (self.items[0])


class Function_Subprogram(BlockBase):  # R1223
    """
    <function-subprogram> = <function-stmt>
                               [ <specification-part> ]
                               [ <execution-part> ]
                               [ <internal-subprogram-part> ]
                            <end-function-stmt>
    """
    subclass_names = []
    use_names = ['Function_Stmt', 'Specification_Part', 'Execution_Part',
                 'Internal_Subprogram_Part', 'End_Function_Stmt']

    @staticmethod
    def match(reader):
        return BlockBase.match(Function_Stmt,
                               [Specification_Part,
                                Execution_Part,
                                Internal_Subprogram_Part],
                               End_Function_Stmt,
                               reader)


class Function_Stmt(StmtBase):  # R1224
    """
    <function-stmt> = [ <prefix> ] FUNCTION <function-name>
                      ( [ <dummy-arg-name-list> ] ) [ <suffix> ]

    C1242 (R1227) A prefix shall not specify ELEMENTAL if
    proc-language-binding-spec appears in the function-stmt or
    subroutine-stmt. The spec associates this constraint with R1227
    but it needs to be checked here.

    """
    subclass_names = []
    use_names = ['Prefix', 'Function_Name', 'Dummy_Arg_Name_List', 'Suffix']

    @staticmethod
    def match(string):
        line, repmap = string_replace_map(string)
        m = pattern.function.search(line)
        if m is None:
            return
        prefix = line[:m.start()].rstrip() or None
        if prefix is not None:
            prefix = Prefix(repmap(prefix))
        line = line[m.end():].lstrip()
        m = pattern.name.match(line)
        if m is None:
            return
        name = Function_Name(m.group())
        line = line[m.end():].lstrip()
        if not line.startswith('('):
            return
        i = line.find(')')
        if i == -1:
            return
        dummy_args = line[1:i].strip() or None
        if dummy_args is not None:
            dummy_args = Dummy_Arg_List(repmap(dummy_args))
        line = line[i+1:].lstrip()
        suffix = None
        if line:
            suffix = Suffix(repmap(line))
        if suffix:
            # A suffix may or may not contain a binding spec.
            binding_spec = walk(suffix, Language_Binding_Spec)
            # Check that we conform to C1242.
            if not c1242_valid(prefix, binding_spec):
                return None
        return prefix, name, dummy_args, suffix

    def tostr(self):
        prefix, name, dummy_args, suffix = self.items
        if prefix is not None:
            s = '%s FUNCTION %s' % (prefix, name)
        else:
            s = 'FUNCTION %s' % (name)
        if dummy_args is not None:
            s += '(%s)' % (dummy_args)
        else:
            s += '()'
        if suffix is not None:
            s += ' %s' % (suffix)
        return s


class Proc_Language_Binding_Spec(Base):  # 1225
    """
    <proc-language-binding-spec> = <language-binding-spec>
    """
    subclass_names = ['Language_Binding_Spec']


class Dummy_Arg_Name(Base):  # R1226
    """
    <dummy-arg-name> = <name>
    """
    subclass_names = ['Name']


class Prefix(SequenceBase):
    '''Fortran2003 rule R1227

    prefix is prefix-spec [ prefix-spec ] ...

    C1240 (R1227) A prefix shall contain at most one of each
    prefix-spec. Checked below.

    C1241 (R1227) A prefix shall not specify both ELEMENTAL and
    RECURSIVE. Checked below.

    C1242 (R1227) A prefix shall not specify ELEMENTAL if
    proc-language-binding-spec appears in the function-stmt or
    subroutine-stmt. This constraint can not be checked here, it is
    checked in R1224 and R1232.

    '''
    subclass_names = []

    @staticmethod
    def match(string):
        '''Match a space separated list of Prefix_Spec objects. Objects may be
        separated by 1 or more spaces.

        :returns: A tuple of size 2 containing the separator and a \
        tuple containing one or more Prefix_Spec objects if there is a \
        match and None if not.

        :rtype: (str, (:class:py:`fparser.two.Fortran2003.Prefix_Spec`,)) \
        or NoneType

        '''
        start_match_list = []
        end_match_list = []
        decl_spec_list = []
        keyword_list = []
        split = string.split()
        # Match prefix-spec (apart from declaration-type-spec) from
        # the left end of the string. These can be tokenised with a
        # simple split as they are guaranteed to not contain any
        # whitespace (as they are keywords).
        while split and split[0].upper() in Prefix_Spec.keywords:
            start_match_list.append(Prefix_Spec(split[0]))
            keyword_list.append(split[0].upper())
            split = split[1:]
        # Match prefix-spec (apart from declaration-type-spec) from
        # the right end of the string.
        while split and split[-1].upper() in Prefix_Spec.keywords:
            end_match_list.insert(0, Prefix_Spec(split[-1]))
            keyword_list.append(split[-1].upper())
            split = split[:-1]
        # What is remaining must be a declaration-type-spec (or is
        # empty) as only one of each prefix-spec is allowed in a
        # prefix (C1240). This may contain internal white space so
        # join the remaining parts together.
        remaining = " ".join(split)
        if remaining:
            decl_spec_list = [Declaration_Type_Spec(remaining)]
        if len(set(keyword_list)) != len(keyword_list):
            # C1240 A prefix shall contain at most one of each
            # prefix-spec. No need to check declaration-type-spec as
            # that is limited to at most one by design.
            return None
        if "ELEMENTAL" in keyword_list and "RECURSIVE" in keyword_list:
            # C1241 A prefix shall not specify both ELEMENTAL and RECURSIVE.
            return None
        result_list = start_match_list + decl_spec_list + end_match_list
        if result_list:
            return " ", tuple(result_list)
        # A prefix must contain at least one prefix-spec.
        return None


class Prefix_Spec(STRINGBase):  # R1228
    """
    <prefix-spec> = <declaration-type-spec>
                    | ELEMENTAL
                    | IMPURE
                    | MODULE
                    | PURE
                    | RECURSIVE
    """
    subclass_names = ['Declaration_Type_Spec']
    # issue #221. IMPURE and MODULE are Fortran2008.
    keywords = ['ELEMENTAL', 'IMPURE', 'MODULE', 'PURE', 'RECURSIVE']

    def match(string):
        '''
        Matches procedure prefixes.

        :param str string: Candidate string.
        :return: Discovered prefix.
        :rtype: str
        '''
        return STRINGBase.match(Prefix_Spec.keywords, string)
    match = staticmethod(match)


class Suffix(Base):  # R1229
    """
    <suffix> = <proc-language-binding-spec> [ RESULT ( <result-name> ) ]
               | RESULT ( <result-name> ) [ <proc-language-binding-spec> ]
    """
    subclass_names = ['Proc_Language_Binding_Spec']
    use_names = ['Result_Name']

    def match(string):
        if string[:6].upper() == 'RESULT':
            line = string[6:].lstrip()
            if not line.startswith('('):
                return
            i = line.find(')')
            if i == -1:
                return
            name = line[1:i].strip()
            if not name:
                return
            line = line[i+1:].lstrip()
            if line:
                return Result_Name(name), Proc_Language_Binding_Spec(line)
            return Result_Name(name), None
        if not string.endswith(')'):
            return
        i = string.rfind('(')
        if i == -1:
            return
        name = string[i+1:-1].strip()
        if not name:
            return
        line = string[:i].rstrip()
        if line[-6:].upper() != 'RESULT':
            return
        line = line[:-6].rstrip()
        if not line:
            return
        return Result_Name(name), Proc_Language_Binding_Spec(line)
    match = staticmethod(match)

    def tostr(self):
        if self.items[1] is None:
            return 'RESULT(%s)' % (self.items[0])
        return 'RESULT(%s) %s' % self.items


class End_Function_Stmt(EndStmtBase):  # R1230
    """
    <end-function-stmt> = END [ FUNCTION [ <function-name> ] ]
    """
    subclass_names = []
    use_names = ['Function_Name']

    def match(string):
        return EndStmtBase.match('FUNCTION', Function_Name, string)
    match = staticmethod(match)


class Subroutine_Subprogram(BlockBase):  # R1231
    """
    <subroutine-subprogram> = <subroutine-stmt>
                                 [ <specification-part> ]
                                 [ <execution-part> ]
                                 [ <internal-subprogram-part> ]
                              <end-subroutine-stmt>
    """
    subclass_names = []
    use_names = ['Subroutine_Stmt', 'Specification_Part', 'Execution_Part',
                 'Internal_Subprogram_Part', 'End_Subroutine_Stmt']

    def match(reader):
        return BlockBase.match(Subroutine_Stmt,
                               [Specification_Part,
                                Execution_Part,
                                Internal_Subprogram_Part],
                               End_Subroutine_Stmt,
                               reader)
    match = staticmethod(match)


def c1242_valid(prefix, binding_spec):
    '''If prefix and binding-spec exist then check whether they conform to
    constraint C1242 : "A prefix shall not specify ELEMENTAL if
    proc-language-binding-spec appears in the function-stmt or
    subroutine-stmt."

    :param prefix: matching prefix instance if one exists.
    :type: :py:class:`fparser.two.Fortran2003.Prefix` or `NoneType`
    :param binding_spec: matching binding specification instance if \
        one exists.
    :type binding_spec: \
        :py:class:`fparser.two.Fortran2003.Language_Binding_Spec` or
        `NoneType`
    :returns: False if prefix and binding-spec break constraint C1242, \
        otherwise True.
    :rtype: bool

    '''
    if binding_spec and prefix:
        # Prefix(es) may or may not be of type ELEMENTAL
        elemental = any("ELEMENTAL" in str(child)
                        for child in walk(prefix.items, Prefix_Spec))
        if elemental:
            # Constraint C1242. A prefix shall not specify ELEMENTAL if
            # proc-language-binding-spec appears in the function-stmt or
            # subroutine-stmt.
            return False
    return True


class Subroutine_Stmt(StmtBase):  # R1232
    """<subroutine-stmt>
    = [ <prefix> ] SUBROUTINE <subroutine-name>
      [ ( [ <dummy-arg-list> ] ) [ <proc-language-binding-spec> ] ]

    C1242 (R1227) A prefix shall not specify ELEMENTAL if
    proc-language-binding-spec appears in the function-stmt or
    subroutine-stmt. The spec associates this constraint with R1227
    but it needs to be checked here.

    """
    subclass_names = []
    use_names = ['Prefix', 'Subroutine_Name', 'Dummy_Arg_List',
                 'Proc_Language_Binding_Spec']

    def match(string):
        line, repmap = string_replace_map(string)
        m = pattern.subroutine.search(line)
        if m is None:
            return
        prefix = line[:m.start()].rstrip() or None
        if prefix is not None:
            prefix = Prefix(repmap(prefix))
        line = line[m.end():].lstrip()
        m = pattern.name.match(line)
        if m is None:
            return
        name = Subroutine_Name(m.group())
        line = line[m.end():].lstrip()
        dummy_args = None
        if line.startswith('('):
            i = line.find(')')
            if i == -1:
                return
            dummy_args = line[1:i].strip() or None
            if dummy_args is not None:
                dummy_args = Dummy_Arg_List(repmap(dummy_args))
            line = line[i+1:].lstrip()
        binding_spec = None
        if line:
            binding_spec = Proc_Language_Binding_Spec(repmap(line))
        if not c1242_valid(prefix, binding_spec):
            return None
        return prefix, name, dummy_args, binding_spec
    match = staticmethod(match)

    def get_name(self): return self.items[1]

    def tostr(self):
        if self.items[0] is not None:
            s = '%s SUBROUTINE %s' % (self.items[0], self.items[1])
        else:
            s = 'SUBROUTINE %s' % (self.items[1])
        if self.items[2] is not None:
            s += '(%s)' % (self.items[2])
        if self.items[3] is not None:
            s += ' %s' % (self.items[3])
        return s


class Dummy_Arg(StringBase):  # R1233
    """
    <dummy-arg> = <dummy-arg-name>
                  | *
    """
    subclass_names = ['Dummy_Arg_Name']

    @staticmethod
    def match(string): return StringBase.match('*', string)


class End_Subroutine_Stmt(EndStmtBase):  # R1234
    """
    <end-subroutine-stmt> = END [ SUBROUTINE [ <subroutine-name> ] ]
    """
    subclass_names = []
    use_names = ['Subroutine_Name']

    @staticmethod
    def match(string):
        return EndStmtBase.match('SUBROUTINE', Subroutine_Name, string)


class Entry_Stmt(StmtBase):  # R1235
    """
::
    <entry-stmt> = ENTRY <entry-name> [ ( [ <dummy-arg-list> ] ) [ <suffix> ] ]

Attributes
----------
items : (Entry_Name, Dummy_Arg_List, Suffix)
    """
    subclass_names = []
    use_names = ['Entry_Name', 'Dummy_Arg_List', 'Suffix']

    @staticmethod
    def match(string):
        if string[:5].upper() != 'ENTRY':
            return
        line = string[5:].lstrip()
        i = line.find('(')
        if i == -1:
            return Entry_Name(line), None, None
        name = Entry_Name(line[:i].rstrip())
        line, repmap = string_replace_map(line[i:])
        i = line.find(')')
        if i == -1:
            return
        args = line[1:i].strip()
        args = Dummy_Arg_List(repmap(args)) if args else None
        line = line[i+1:].lstrip()
        if line:
            return name, args, Suffix(repmap(line))
        return name, args, None

    def tostr(self):
        name, args, suffix = self.items
        if suffix is None:
            if args is None:
                return 'ENTRY %s()' % (name)
            return 'ENTRY %s(%s)' % (name, args)
        elif args is None:
            return 'ENTRY %s() %s' % (name, suffix)
        return 'ENTRY %s(%s) %s' % (name, args, suffix)


class Return_Stmt(StmtBase):  # R1236
    """
    <return-stmt> = RETURN [ <scalar-int-expr> ]
    """
    subclass_names = []
    use_names = ['Scalar_Int_Expr']

    def match(string):
        start = string[:6].upper()
        if start != 'RETURN':
            return
        if len(string) == 6:
            return None,
        return Scalar_Int_Expr(string[6:].lstrip()),
    match = staticmethod(match)

    def tostr(self):
        if self.items[0] is None:
            return 'RETURN'
        return 'RETURN %s' % self.items


class Contains_Stmt(StmtBase, STRINGBase):  # R1237
    """
    <contains-stmt> = CONTAINS
    """
    subclass_names = []

    def match(string):
        return STRINGBase.match('CONTAINS', string)

    match = staticmethod(match)


class Stmt_Function_Stmt(StmtBase):  # R1238
    """
    <stmt-function-stmt>
    = <function-name> ( [ <dummy-arg-name-list> ] ) = Scalar_Expr
    """
    subclass_names = []
    use_names = ['Function_Name', 'Dummy_Arg_Name_List', 'Scalar_Expr']

    def match(string):
        i = string.find('=')
        if i == -1:
            return
        expr = string[i+1:].lstrip()
        if not expr:
            return
        line = string[:i].rstrip()
        if not line or not line.endswith(')'):
            return
        i = line.find('(')
        if i == -1:
            return
        name = line[:i].rstrip()
        if not name:
            return
        args = line[i+1:-1].strip()
        if args:
            return Function_Name(name),       \
                   Dummy_Arg_Name_List(args), \
                   Scalar_Expr(expr)
        return Function_Name(name), None, Scalar_Expr(expr)

    match = staticmethod(match)

    def tostr(self):
        if self.items[1] is None:
            return '%s () = %s' % (self.items[0], self.items[2])
        return '%s (%s) = %s' % self.items

#
# GENERATE Scalar_, _List, _Name CLASSES
#


ClassType = type(Base)
_names = dir()
for clsname in _names:
    my_cls = eval(clsname)
    if not (isinstance(my_cls, ClassType) and issubclass(my_cls, Base) and
            not my_cls.__name__.endswith('Base')):
        continue

    names = getattr(my_cls, 'subclass_names', []) + \
        getattr(my_cls, 'use_names', [])
    for n in names:
        if n in _names:
            continue
        if n.endswith('_List'):
            _names.append(n)
            n = n[:-5]
            # Generate 'list' class
            exec('''\
class %s_List(SequenceBase):
    subclass_names = [\'%s\']
    use_names = []
    def match(string): return SequenceBase.match(r\',\', %s, string)
    match = staticmethod(match)
''' % (n, n, n))
        elif n.endswith('_Name'):
            _names.append(n)
            n = n[:-5]
            exec('''\
class %s_Name(Base):
    subclass_names = [\'Name\']
''' % (n))
        elif n.startswith('Scalar_'):
            _names.append(n)
            n = n[7:]
            exec('''\
class Scalar_%s(Base):
    subclass_names = [\'%s\']
''' % (n, n))

# EOF
