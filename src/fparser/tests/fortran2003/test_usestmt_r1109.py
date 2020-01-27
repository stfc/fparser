# Copyright (c) 2018-2019 Science and Technology Facilities Council

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

'''Test Fortran 2003 rule R1109 : This file tests the support for the
Use statement.

'''

import pytest
from fparser.api import get_reader
from fparser.two.Fortran2003 import Use_Stmt
from fparser.two.utils import NoMatchError, InternalError

# match() use ...


# match() 'use x'. Use both string and reader input here, but from
# here on we will just use string input as that is what is passed to
# the match() method
def test_use(f2003_create):
    '''Check that a basic use is parsed correctly. Input separately as a
    string and as a reader object

    '''
    def check_use(reader):
        '''Internal helper function to avoid code replication.'''
        ast = Use_Stmt(reader)
        assert "USE my_model" in str(ast)
        assert repr(ast) == "Use_Stmt(None, None, Name('my_model'), '', None)"

    line = "use my_model"
    check_use(line)
    reader = get_reader(line)
    check_use(reader)


# match() 'use :: x'
def test_use_colons(f2003_create):
    '''Check that a basic use with '::' is parsed correctly.'''
    line = "use :: my_model"
    ast = Use_Stmt(line)
    assert "USE :: my_model" in str(ast)
    assert repr(ast) == "Use_Stmt(None, '::', Name('my_model'), '', None)"


# match() 'use, nature :: x'
def test_use_nature(f2003_create):
    '''Check that a use with a 'nature' specification is parsed correctly.'''
    line = "use, intrinsic :: my_model"
    ast = Use_Stmt(line)
    assert "USE, INTRINSIC :: my_model" in str(ast)
    assert repr(ast) == (
        "Use_Stmt(Module_Nature('INTRINSIC'), '::', Name('my_model'), "
        "'', None)")


# match() 'use x, rename'
def test_use_rename(f2003_create):
    '''Check that a use with a nename clause is parsed correctly.'''
    line = "use my_module, name=>new_name"
    ast = Use_Stmt(line)
    assert "USE my_module, name => new_name" in str(ast)
    assert repr(ast) == (
        "Use_Stmt(None, None, Name('my_module'), ',', Rename_List(',', "
        "(Rename(None, Name('name'), Name('new_name')),)))")


# match() 'use x, only: y'
def test_use_only(f2003_create):
    '''Check that a use statement is parsed correctly when there is an
    only clause.

    '''
    line = "use my_model, only: name"
    ast = Use_Stmt(line)
    assert "USE my_model, ONLY: name" in str(ast)
    assert repr(ast) == (
        "Use_Stmt(None, None, Name('my_model'), ', ONLY:', Only_List(',', "
        "(Name('name'),)))")


# match() 'use x, only:'
def test_use_only_empty(f2003_create):
    '''Check that a use statement is parsed correctly when there is an
    only clause without any content.

    '''
    line = "use my_model, only:"
    ast = Use_Stmt(line)
    assert "USE my_model, ONLY:" in str(ast)
    assert repr(ast) == (
        "Use_Stmt(None, None, Name('my_model'), ', ONLY:', None)")


# match() '  use  ,  nature  ::  x  ,  name=>new_name'
def test_use_spaces_1(f2003_create):
    '''Check that a use statement with spaces works correctly with
    renaming.

    '''
    line = "  Use  ,  intrinsic  ::  my_model  ,  name=>new_name  "
    ast = Use_Stmt(line)
    assert "USE, INTRINSIC :: my_model, name => new_name" in str(ast)
    assert repr(ast) == (
        "Use_Stmt(Module_Nature('INTRINSIC'), '::', Name('my_model'), ',', "
        "Rename_List(',', (Rename(None, Name('name'), Name('new_name')),)))")


# match() '  use  ,  nature  ::  x  ,  only  :  name'
def test_use_spaces_2(f2003_create):
    '''Check that a use statement with spaces works correctly with an only
    clause.

    '''
    line = "  use  ,  intrinsic  ::  my_model  ,  only  :  name  "
    ast = Use_Stmt(line)
    assert "USE, INTRINSIC :: my_model, ONLY: name" in str(ast)
    assert (repr(ast) ==
            "Use_Stmt(Module_Nature('INTRINSIC'), '::', Name('my_model'), ', "
            "ONLY:', Only_List(',', (Name('name'),)))")


# match() mixed case
def test_use_mixed_case(f2003_create):
    '''Check that a use statement with mixed case keywords ('use' and
    'only') works as expected.

    '''
    line = "UsE my_model, OnLy: name"
    ast = Use_Stmt(line)
    assert "USE my_model, ONLY: name" in str(ast)
    assert (repr(ast) ==
            "Use_Stmt(None, None, Name('my_model'), ', ONLY:', Only_List(',', "
            "(Name('name'),)))")

# match() Syntax errors


def test_syntaxerror(f2003_create):
    '''Test that NoMatchError is raised for various syntax errors.'''
    for line in ["us", "ust", "use", "usemy_model", "use, ", "use, ::",
                 "use, intrinsic", "use, intrinsic::",
                 "use, intrinsic my_module", "use,", "use my_model,",
                 "use my_model, only", "use my_model, only ;",
                 "use my_model, only name"]:
        with pytest.raises(NoMatchError) as excinfo:
            _ = Use_Stmt(line)
        assert "Use_Stmt: '{0}'".format(line) in str(excinfo.value)

# match() Internal errors


def test_use_internal_error1(f2003_create):
    '''Check that an internal error is raised if the length of the Items
    list is not 5 as the str() method assumes that it is.

    '''
    line = "use my_model"
    ast = Use_Stmt(line)
    ast.items = (None, None, None, None)
    with pytest.raises(InternalError) as excinfo:
        str(ast)
    assert "should be of size 5 but found '4'" in str(excinfo.value)


def test_use_internal_error2(f2003_create):
    '''Check that an internal error is raised if the module name (entry 2
    of Items) is empty or None as the str() method assumes that it is
    a string with content.

    '''
    line = "use my_model"
    ast = Use_Stmt(line)
    for content in [None, ""]:
        ast.items = (None, None, content, None, None)
        with pytest.raises(InternalError) as excinfo:
            str(ast)
        assert ("entry 2 should be a module name but it is "
                "empty") in str(excinfo.value)


def test_use_internal_error3(f2003_create):
    '''Check that an internal error is raised if entry 3 of Items is
    'None' as the str() method assumes it is a (potentially empty)
    string.

    '''
    line = "use my_model"
    ast = Use_Stmt(line)
    ast.items = (None, None, "my_module", None, None)
    with pytest.raises(InternalError) as excinfo:
        str(ast)
    assert "entry 3 should be a string but found 'None'" in str(excinfo.value)
