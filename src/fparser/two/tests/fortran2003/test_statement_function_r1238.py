# Copyright (c) 2018 Science and Technology Facilities Council

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

'''Test Fortran 2003 rule R1238 : Tests support for statement functions.

'''


import pytest
from fparser.two.utils import InternalError
from fparser.api import get_reader
from fparser.two.Fortran2003 import Stmt_Function_Stmt, Program

def test_statement_function_simple(f2003_create):
    """
    Test that a simple statement function can be parsed.
    """
    code = """
    MYFUNC(ARG1) = MAX(0.0, ARG1)
    """
    reader = get_reader(code)
    ast = Stmt_Function_Stmt(reader)
    assert "MYFUNC (ARG1) = MAX(0.0, ARG1)" in str(ast)


def test_statement_function_multiline(f2003_create):
    """
    Test that a multiline statement function can be parsed.
    """
    code = """
    MYFUNC(X, Y, Z) = &
      & MAX(X, MIN(Y, Z))
    """
    reader = get_reader(code)
    ast = Stmt_Function_Stmt(reader)
    assert "MYFUNC (X, Y, Z) = MAX(X, MIN(Y, Z))" in str(ast)


def test_statement_function_subroutine(f2003_create):
    """
    Test that we can parse a statement function in the declaration
    section of a subroutine.
    """
    code = """
    subroutine test()
      integer :: x, y
      integer :: mymax
      mymax(x, y) = MAX(x, y)
    end subroutine
    """
    reader = get_reader(code)
    ast = Program(reader)

    # Ensure we have a Stmt_Function_Stmt type!
    ast_spec = ast.content[0].content[1]
    assert type(ast_spec.content[2]) is Stmt_Function_Stmt
    assert """SUBROUTINE test
  INTEGER :: x, y
  INTEGER :: mymax
  mymax (x, y) = MAX(x, y)
END SUBROUTINE""" in str(ast)
