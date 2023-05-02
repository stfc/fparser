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

"""
xxx
"""
import inspect
import sys

from fparser.two.Fortran2003 import Base, SequenceBase

from fparser.two.Fortran2008.executable_construct import Executable_Construct
from fparser.two.Fortran2008.executable_construct_c201 import (
    Executable_Construct_C201)
from fparser.two.Fortran2008.program_unit import Program_Unit

from fparser.two.Fortran2008_orig import (
    Action_Stmt, Action_Stmt_C201, Action_Stmt_C816, Action_Stmt_C828,
    Data_Component_Def_Stmt, Component_Attr_Spec, Type_Declaration_Stmt,
    Codimension_Attr_Spec, Coarray_Bracket_Spec, Attr_Spec, Coarray_Spec,
    Deferred_Coshape_Spec, Explicit_Coshape_Spec, Coshape_Spec,
    Lower_Cobound, Upper_Cobound, Do_Term_Action_Stmt, Alloc_Opt,
    Allocate_Stmt, If_Stmt, Error_Stop_Stmt, Specification_Part_C1112,
    Implicit_Part_C1112, Implicit_Part_Stmt_C1112,
    Declaration_Construct_C1112, Submodule, Submodule_Stmt,
    End_Submodule_Stmt, Parent_Identifier, Open_Stmt, Connect_Spec,
    Block_Construct, Block_Stmt, End_Block_Stmt, Critical_Construct,
    Critical_Stmt, End_Critical_Stmt, Procedure_Stmt)


#
# GENERATE Scalar_, _List, _Name CLASSES
#


ClassType = type(Base)
_names = dir()
for clsname in _names:
    new_cls = eval(clsname)
    if not (
        isinstance(new_cls, ClassType)
        and issubclass(new_cls, Base)
        and not new_cls.__name__.endswith("Base")
    ):
        continue

    names = getattr(new_cls, "subclass_names", []) + getattr(new_cls, "use_names", [])
    for n in names:
        if n in _names:
            continue
        if n.endswith("_List"):
            _names.append(n)
            n = n[:-5]
            # Generate 'list' class
            exec(
                f"""\
class {n}_List(SequenceBase):
    subclass_names = [\'{n}\']
    use_names = []
    @staticmethod
    def match(string): return SequenceBase.match(r\',\', {n}, string)
"""
            )
        elif n.endswith("_Name"):
            _names.append(n)
            n = n[:-5]
            exec(
                f"""\
class {n}_Name(Base):
    subclass_names = [\'Name\']
"""
            )
        elif n.startswith("Scalar_"):
            print(f"scalar {n}")
            _names.append(n)
            n = n[7:]
            exec(
                f"""\
class Scalar_{n}(Base):
    subclass_names = [\'{n}\']
"""
            )


# Inspect the contents of this module and list all of the classes in __all__
# for automatic documentation generation with AutoDoc.

classes = inspect.getmembers(
    sys.modules[__name__],
    lambda member: inspect.isclass(member) and member.__module__ == __name__,
)

__all__ = [name[0] for name in classes]
