# Modified work Copyright (c) 2018 Science and Technology
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

'''The file implements the Fortran2008 rules as defined in
    https://j3-fortran.org/doc/year/10/10-007r1.pdf

'''
# pylint: disable=invalid-name
# pylint: disable=arguments-differ
# pylint: disable=undefined-variable
# pylint: disable=eval-used
# pylint: disable=exec-used
# pylint: disable=unused-import
from fparser.two.Fortran2003 import Program_Unit as Program_Unit_2003
from fparser.two.Fortran2003 import EndStmtBase, BlockBase, SequenceBase, \
    Base, Specification_Part, Module_Subprogram_Part, Implicit_Part, \
    Implicit_Part_Stmt, Declaration_Construct, Use_Stmt, Import_Stmt


class Program_Unit(Program_Unit_2003):  # R202
    '''
    Fortran 2008 rule R202
    program-unit is main-program
                    or external-subprogram
                    or module
                    or submodule
                    or block-data

    '''

    # Fortran2008 adds the concept of submodules to a program-unit. We
    # therefore extend the Fortran2003 specification
    subclass_names = Program_Unit_2003.subclass_names[:]
    subclass_names.append("Submodule")


class Specification_Part_C1112(Specification_Part):  # C1112
    '''Fortran 2008 constraint C1112
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

    '''
    use_names = ['Use_Stmt', 'Import_Stmt', 'Implicit_Part_C1112',
                 'Declaration_Construct_C1112']

    @staticmethod
    def match(reader):
        '''Check whether the input matches the rule

        param reader: the fortran file reader containing the line(s)
                      of code that we are trying to match
        :type reader: :py:class:`fparser.common.readfortran.FortranFileReader`
                      or
                      :py:class:`fparser.common.readfortran.FortranStringReader`
        :return: `tuple` containing a single `list` which contains
                 instance of the classes that have matched if there is
                 a match or `None` if there is no match

        '''
        return BlockBase.match(None, [Use_Stmt, Import_Stmt,
                                      Implicit_Part_C1112,
                                      Declaration_Construct_C1112],
                               None, reader)


class Implicit_Part_C1112(Implicit_Part):  # C1112
    '''Fortran 2008 constraint C1112
    C1112 A submodule specification-part shall not contain a
    format-stmt, entry-stmt, or stmt-function-stmt.

    This class specialises 'Implicit_Part' so that the specialised
    'Implicit_Part_Stmt_C1112' is called rather than the original
    'Implicit_Part_Stmt'

    '''
    use_names = ['Implicit_Part_Stmt_C1112', 'Implicit_Stmt']

    @staticmethod
    def match(reader):
        '''Check whether the input matches the rule

        param reader: the fortran file reader containing the line(s)
                      of code that we are trying to match
        :type reader: :py:class:`fparser.common.readfortran.FortranFileReader`
                      or
                      :py:class:`fparser.common.readfortran.FortranStringReader`
        :return: `tuple` containing a single `list` which contains
                 instance of the classes that have matched if there is
                 a match or `None` if there is no match

        '''
        return BlockBase.match(None, [Implicit_Part_Stmt_C1112], None, reader)


class Implicit_Part_Stmt_C1112(Implicit_Part_Stmt):  # C1112
    '''Fortran 2008 constraint C1112
    C1112 A submodule specification-part shall not contain a
    format-stmt, entry-stmt, or stmt-function-stmt.

    This class specialises 'Implicit_Part_Stmt' to remove
    'Format_Stmt' and 'Entry_Stmt'

    '''
    subclass_names = Implicit_Part_Stmt.subclass_names[:]
    subclass_names.remove('Format_Stmt')
    subclass_names.remove('Entry_Stmt')


class Declaration_Construct_C1112(Declaration_Construct):  # C1112
    '''Fortran 2008 constraint C1112
    C1112 A submodule specification-part shall not contain a
    format-stmt, entry-stmt, or stmt-function-stmt.

    This class specialises 'Declaration_Construct' to remove
    'Format_Stmt', 'Entry_Stmt' and 'Stmt_Function_Stmt'

    '''
    subclass_names = Declaration_Construct.subclass_names[:]
    subclass_names.remove('Format_Stmt')
    subclass_names.remove('Entry_Stmt')
    subclass_names.remove('Stmt_Function_Stmt')


class Submodule(BlockBase):  # R1116 [C1112,C1114]
    '''Fortran 2008 rule R1116
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

    '''

    subclass_names = []
    use_names = ['Submodule_Stmt', 'Specification_Part_C1112',
                 'Module_Subprogram_Part', 'End_Submodule_Stmt']

    @staticmethod
    def match(reader):
        '''Check whether the input matches the rule

        param reader: the fortran file reader containing the line(s)
                      of code that we are trying to match
        :type reader: :py:class:`fparser.common.readfortran.FortranFileReader`
                      or
                      :py:class:`fparser.common.readfortran.FortranStringReader`
        :return: `tuple` containing a single `list` which contains
                 instance of the classes that have matched if there is
                 a match or `None` if there is no match

        '''

        result = BlockBase.match(
            Submodule_Stmt,
            [Specification_Part_C1112, Module_Subprogram_Part],
            End_Submodule_Stmt, reader)
        return result


class Submodule_Stmt(Base):  # R1117
    '''
    Fortran 2008 rule R1117
    submodule-stmt is SUBMODULE ( parent-identifier ) submodule-name

    '''
    subclass_names = []
    use_names = ['Submodule_Name', 'Parent_Identifier']

    @staticmethod
    def match(fstring):
        '''Check whether the input matches the rule

        param string fstring : contains the Fortran that we are trying
        to match

        :return: instances of the Classes that have matched if there
        is a match or `None` if there is no match

        '''
        # First look for "SUBMODULE"
        name = "SUBMODULE"
        if fstring[:len(name)].upper() != name:
            # the string does not start with SUBMODULE so does not
            # match
            return None
        # "SUBMODULE is found so strip it out and split the remaining
        # line by parenthesis
        from fparser.common.splitline import splitparen
        splitline = splitparen(fstring[len(name):].lstrip())
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
        '''return the fortran representation of this object'''
        # return self.string  # this returns the original code
        return "SUBMODULE ({0}) {1}".format(self.items[0], self.items[1])

    def get_name(self):  # C1114
        '''Fortran 2008 constraint C1114
        return the submodule name. This is used by the base class to check
        whether the submodule name matches the name used for the end
        submodule statement if one is provided.

        :return: the name of the submodule stored in a Name class
        :return type: :py:class:`fparser.two.Fortran2003.Name`
        '''
        return self.items[1]


class End_Submodule_Stmt(EndStmtBase):  # R1119
    '''
    Fortran 2008 rule R1119
    end-submodule-stmt is END [ SUBMODULE [ submodule-name ] ]

    '''
    subclass_names = []
    use_names = ['Submodule_Name']

    @staticmethod
    def match(fstring):
        '''Check whether the input matches the rule

        param string fstring : contains the Fortran that we are trying
        to match

        :return: instances of the Classes that have matched if there
        is a match or `None` if there is no match

        '''
        return EndStmtBase.match('SUBMODULE', Submodule_Name, fstring)

    def get_name(self):  # C1114
        '''Fortran 2008 constraint C1114 return the submodule name as
        specified by the end submodule statement or `None` if one is
        not specified. This is used by the base class to check whether
        this name matches the submodule name.

        :return: the name of the submodule stored in a Name class
        :return type: :py:class:`fparser.two.Fortran2003.Name` or `None`

        '''
        return self.items[1]


class Parent_Identifier(Base):  # R1118 (C1113)
    '''Fortran 2008 rule R1118
    parent-identifier is ancestor-module-name [ : parent-submodule-name ]

    C1113 The ancestor-module-name shall be the name of a nonintrinsic
    module; the parent-submodule name shall be the name of a
    descendant of that module.
    This constraint can not be tested by fparser in general as the
    module or submodule may be in a different file. We therefore do
    not check this constraint in fparser.

    '''

    use_names = ['Ancestor_Module_Name', 'Parent_SubModule_Name']

    @staticmethod
    def match(fstring):
        '''Check whether the input matches the rule

        param string fstring : contains the Fortran that we are trying
        to match

        :return: instances of the Classes that have matched if there
        is a match or `None` if there is no match

        '''
        split_string = fstring.split(":")
        len_split_string = len(split_string)
        lhs_name = split_string[0].lstrip().rstrip()
        if len_split_string == 1:
            return Ancestor_Module_Name(lhs_name), None
        elif len_split_string == 2:
            rhs_name = split_string[1].lstrip().rstrip()
            return Ancestor_Module_Name(lhs_name), \
                Parent_SubModule_Name(rhs_name)
        # we expect at most one ':' in our input so the match fails
        return None

    def tostr(self):
        '''return the fortran representation of this object'''
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
    if not (isinstance(cls, ClassType) and issubclass(cls, Base) and
            not cls.__name__.endswith('Base')):
        continue

    names = getattr(cls, 'subclass_names', []) + getattr(cls, 'use_names', [])
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
# Currently there are no examples using scalar_* as a class name.
#         elif n.startswith('Scalar_'):
#             _names.append(n)
#             n = n[7:]
#             exec('''\
# class Scalar_%s(Base):
#     subclass_names = [\'%s\']
# ''' % (n, n))
