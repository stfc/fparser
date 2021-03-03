# Copyright (c) 2021 Science and Technology Facilities Council
# All rights reserved.
#
# Modifications made as part of the fparser project are distributed
# under the following license:
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
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

''' Module containing tests for the symbol-table functionality
 of fparser2. '''

import pytest
from fparser.two import Fortran2003
from fparser.two.utils import walk
from fparser.two.symbol_table import SymbolTable, SYMBOL_TABLES
from fparser.api import get_reader


def test_basic_table():
    ''' Check the basic functionality of a symbol table. '''
    table = SymbolTable("BAsic")
    # Name of table is not case sensitive
    assert table.name == "basic"
    assert table.parent is None
    assert table.children == []
    with pytest.raises(KeyError) as err:
        table.lookup("missing")
    assert "Failed to find symbol named 'missing'" in str(err.value)
    # Add a symbol and check that its naming is not case sensitive
    table.new_symbol("Var", "integer")
    sym = table.lookup("var")
    assert sym.name == "var"
    assert sym.primitive_type == "integer"
    assert table.lookup("VAR") is sym


def test_str_method():
    ''' Test the str property of the SymbolTable class. '''
    table = SymbolTable("basic")
    assert "Symbol Table 'basic'\nSymbols:\nUsed modules:\n" in str(table)
    table.new_symbol("var", "integer")
    assert "Symbol Table 'basic'\nSymbols:\nvar\nUsed modules:\n" in str(table)
    table.new_module("some_mod")
    assert ("Symbol Table 'basic'\nSymbols:\nvar\nUsed modules:\nsome_mod\n"
            in str(table))


def test_parent_child():
    ''' Test the parent/child-related properties. '''
    table = SymbolTable("BASIC")
    with pytest.raises(TypeError) as err:
        table.add_child("wrong")
    assert "Expected a SymbolTable instance but got 'str'" in str(err.value)
    inner_table = SymbolTable("func1", parent=table)
    table.add_child(inner_table)
    assert table.children == [inner_table]
    assert inner_table.parent is table


def test_module_use(f2003_parser):
    ''' Check that a USE of a module is captured in the symbol table. '''
    _ = f2003_parser(get_reader('''\
PROGRAM a_prog
  use some_mod
END PROGRAM a_prog
    '''))
    tables = SYMBOL_TABLES
    table = tables.lookup("a_prog")
    assert isinstance(table, SymbolTable)
    assert table.parent is None
    assert "some_mod" in table._modules


def test_module_use_with_only(f2003_parser):
    ''' Check that USE statements with an ONLY: clause are correctly captured
    in the symbol table. '''
    _ = f2003_parser(get_reader('''\
PROGRAM a_prog
  use some_mod, only:
  use mod2, only: this_one, that_one
END PROGRAM a_prog
    '''))
    tables = SYMBOL_TABLES
    table = tables.lookup("a_prog")
    assert isinstance(table, SymbolTable)
    assert table.parent is None
    assert "some_mod" in table._modules
    assert table._modules["some_mod"] is None
    assert "mod2" in table._modules
    assert sorted(table._modules["mod2"]) == ["that_one", "this_one"]


def test_module_definition(f2003_parser):
    ''' Check that a SymbolTable is created for a module and populated with
    the symbols it defines. '''
    _ = f2003_parser(get_reader('''\
module my_mod
  use some_mod
  real :: a
end module my_mod
    '''))
    tables = SYMBOL_TABLES
    assert list(tables._symbol_tables.keys()) == ["my_mod"]
    table = tables.lookup("my_mod")
    assert isinstance(table, SymbolTable)
    assert "some_mod" in table._modules
    assert "a" in table._symbols
    sym = table.lookup("a")
    assert sym.name == "a"
    assert sym.primitive_type == "REAL"


def test_routine_in_module(f2003_parser):
    ''' Check that we get two, nested symbol tables when a module contains
    a subroutine. '''
    _ = f2003_parser(get_reader('''\
module my_mod
  use some_mod
  real :: a
contains
  subroutine my_sub()
  end subroutine my_sub
end module my_mod
    '''))
    tables = SYMBOL_TABLES
    assert list(tables._symbol_tables.keys()) == ["my_mod"]
    table = tables.lookup("my_mod")
    assert len(table.children) == 1
    assert table.children[0].name == "my_sub"
    assert table.children[0].parent is table
    # Check that the search for a symbol moves up to the parent scope
    sym = table.children[0].lookup("a")
    assert sym.name == "a"
    assert sym.primitive_type == "REAL"


def test_routine_in_prog(f2003_parser):
    ''' Check that we get two, nested symbol tables when a program contains
    a subroutine. '''
    _ = f2003_parser(get_reader('''\
program my_prog
  use some_mod
  real :: a
contains
  subroutine my_sub()
    real :: b
  end subroutine my_sub
end program my_prog
    '''))
    tables = SYMBOL_TABLES
    assert list(tables._symbol_tables.keys()) == ["my_prog"]
    table = SYMBOL_TABLES.lookup("my_prog")
    assert len(table.children) == 1
    assert table.children[0].name == "my_sub"
    assert table.children[0]._symbols["b"].name == "b"
    assert table.children[0].parent is table


def test_shadowed_intrinsic(f2003_parser):
    ''' Check that a locally-defined symbol that shadows (overwrites) a
    Fortran intrinsic is correctly identified. '''
    tree = f2003_parser(get_reader('''\
module my_mod
  use some_mod
  real :: dot_product(2,2)
contains
  subroutine my_sub()
    real :: result
    result = dot_product(1,1)
  end subroutine my_sub
end module my_mod
    '''))
    tables = SYMBOL_TABLES
    # We should not have an intrinsic-function reference in the parse tree
    assert not walk(tree, Fortran2003.Intrinsic_Function_Reference)
    table = tables.lookup("my_mod")
    sym = table.children[0].lookup("dot_product")
    assert sym.primitive_type == "REAL"