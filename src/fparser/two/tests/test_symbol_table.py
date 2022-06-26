# -----------------------------------------------------------------------------
# Copyright (c) 2021-2022 Science and Technology Facilities Council.
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
# -----------------------------------------------------------------------------

""" Module containing tests for the symbol-table functionality
 of fparser2. """

import pytest
from fparser.two.symbol_table import SymbolTable, SYMBOL_TABLES, SymbolTableError
from fparser.api import get_reader


def test_basic_table():
    """Check the basic functionality of a symbol table."""
    table = SymbolTable("BAsic")
    # Name of table is not case sensitive
    assert table.name == "basic"
    assert table.parent is None
    assert table.children == []
    # Consistency checking is disabled by default
    assert table._checking_enabled is False
    with pytest.raises(KeyError) as err:
        table.lookup("missing")
    assert "Failed to find symbol named 'missing'" in str(err.value)
    # Add a symbol and check that its naming is not case sensitive
    table.add_data_symbol("Var", "integer")
    sym = table.lookup("var")
    assert sym.name == "var"
    assert table.lookup("VAR") is sym
    # Check that we can enable consistency checking
    table2 = SymbolTable("table2", checking_enabled=True)
    assert table2._checking_enabled is True


def test_add_data_symbol():
    """Test that the add_data_symbol() method behaves as expected when
    validation is enabled."""
    table = SymbolTable("basic", checking_enabled=True)
    table.add_data_symbol("var", "integer")
    sym = table.lookup("var")
    assert sym.primitive_type == "integer"
    with pytest.raises(SymbolTableError) as err:
        table.add_data_symbol("var", "real")
    assert (
        "Symbol table already contains a symbol for a variable with name "
        "'var'" in str(err.value)
    )
    with pytest.raises(TypeError) as err:
        table.add_data_symbol(table, "real")
    assert "name of the symbol must be a str but got 'SymbolTable'" in str(err.value)
    with pytest.raises(TypeError) as err:
        table.add_data_symbol("var2", table)
    assert (
        "primitive type of the symbol must be specified as a str but got "
        "'SymbolTable'" in str(err.value)
    )
    # Check a clash with a USE statement - both the module name and the
    # name of imported variables
    table.add_use_symbols("mod1", ["var3"])
    with pytest.raises(SymbolTableError) as err:
        table.add_data_symbol("mod1", "real")
    assert "table already contains a use of a module with name 'mod1'" in str(err.value)
    with pytest.raises(SymbolTableError) as err:
        table.add_data_symbol("var3", "real")
    assert (
        "table already contains a use of a symbol named 'var3' from "
        "module 'mod1'" in str(err.value)
    )


def test_add_data_symbols_no_checks():
    """Check that we can disable the checks in the
    add_data_symbol() method."""
    table = SymbolTable("basic", checking_enabled=False)
    table.add_data_symbol("var", "integer")
    table.add_data_symbol("var", "real")
    sym = table.lookup("var")
    assert sym.primitive_type == "real"
    table.add_use_symbols("mod1", ["var3"])
    table.add_data_symbol("mod1", "real")
    table.add_use_symbols("mod2", ["var3"])
    table.add_data_symbol("var3", "real")
    assert table.lookup("var3").primitive_type == "real"


def test_add_use_symbols():
    """Test that the add_use_symbols() method behaves as expected."""
    table = SymbolTable("basic")
    # A use without an 'only' clause
    table.add_use_symbols("mod1")
    assert table._modules["mod1"] is None
    # Fortran permits other use statements for the same module
    table.add_use_symbols("mod1", ["var"])
    # Since we already have a wildcard import and don't yet capture any
    # additional, specific imports (TODO #294) the list of associated symbols
    # should still be None.
    assert table._modules["mod1"] is None
    table.add_use_symbols("mod2", ["iVar"])
    assert table._modules["mod2"] == ["ivar"]
    table.add_use_symbols("mod2", ["jvar"])
    assert table._modules["mod2"] == ["ivar", "jvar"]


def test_add_use_symbols_errors():
    """Test the various checks on the supplied parameters to
    add_use_symbols()."""
    table = SymbolTable("basic")
    with pytest.raises(TypeError) as err:
        table.add_use_symbols(table)
    assert "name of the module must be a str but got 'SymbolTable'" in str(err.value)
    with pytest.raises(TypeError) as err:
        table.add_use_symbols("mod3", only_list="hello")
    assert "If present, the only_list must be a list but got 'str'" in str(err.value)
    with pytest.raises(TypeError) as err:
        table.add_use_symbols("mod3", only_list=["hello", table])
    assert (
        "If present, the only_list must be a list of str but got: ['str', "
        "'SymbolTable']" in str(err.value)
    )


def test_str_method():
    """Test the str property of the SymbolTable class."""
    table = SymbolTable("basic")
    assert "Symbol Table 'basic'\nSymbols:\nUsed modules:\n" in str(table)
    table.add_data_symbol("var", "integer")
    assert "Symbol Table 'basic'\nSymbols:\nvar\nUsed modules:\n" in str(table)
    table.add_use_symbols("some_mod")
    assert "Symbol Table 'basic'\nSymbols:\nvar\nUsed modules:\nsome_mod\n" in str(
        table
    )


def test_del_child():
    """Checks for the del_child method."""
    table = SymbolTable("BASIC")
    inner_table = SymbolTable("func1", parent=table)
    table.add_child(inner_table)
    with pytest.raises(KeyError) as err:
        table.del_child("missing")
    assert "Symbol table 'basic' does not contain a table named 'missing'" in str(
        err.value
    )
    table.del_child("func1")
    assert table.children == []


def test_parent_child():
    """Test the parent/child-related properties."""
    table = SymbolTable("BASIC")
    with pytest.raises(TypeError) as err:
        table.add_child("wrong")
    assert "Expected a SymbolTable instance but got 'str'" in str(err.value)
    inner_table = SymbolTable("func1", parent=table)
    table.add_child(inner_table)
    assert table.children == [inner_table]
    assert inner_table.parent is table
    with pytest.raises(TypeError) as err:
        inner_table.parent = "wrong"
    assert (
        "Unless it is None, the parent of a SymbolTable must also be a "
        "SymbolTable but got 'str'" in str(err.value)
    )


def test_root_property():
    """Test the `root` property of the SymbolTable."""
    table = SymbolTable("BASIC")
    inner_table = SymbolTable("func1", parent=table)
    table.add_child(inner_table)
    inner_inner_table = SymbolTable("func2", parent=inner_table)
    assert inner_inner_table.root is table
    assert inner_table.root is table
    assert table.root is table


def test_module_use(f2003_parser):
    """Check that a USE of a module is captured in the symbol table."""
    _ = f2003_parser(
        get_reader(
            """\
PROGRAM a_prog
  use some_mod
END PROGRAM a_prog
    """
        )
    )
    tables = SYMBOL_TABLES
    table = tables.lookup("a_prog")
    assert isinstance(table, SymbolTable)
    assert table.parent is None
    assert "some_mod" in table._modules


def test_module_use_with_only(f2003_parser):
    """Check that USE statements with an ONLY: clause are correctly captured
    in the symbol table."""
    _ = f2003_parser(
        get_reader(
            """\
PROGRAM a_prog
  use some_mod, only:
  use mod2, only: this_one, that_one
END PROGRAM a_prog
    """
        )
    )
    tables = SYMBOL_TABLES
    table = tables.lookup("a_prog")
    assert isinstance(table, SymbolTable)
    assert table.parent is None
    assert "some_mod" in table._modules
    assert table._modules["some_mod"] is None
    assert "mod2" in table._modules
    assert sorted(table._modules["mod2"]) == ["that_one", "this_one"]


def test_module_definition(f2003_parser):
    """Check that a SymbolTable is created for a module and populated with
    the symbols it defines."""
    _ = f2003_parser(
        get_reader(
            """\
module my_mod
  use some_mod
  real :: a
end module my_mod
    """
        )
    )
    tables = SYMBOL_TABLES
    assert list(tables._symbol_tables.keys()) == ["my_mod"]
    table = tables.lookup("my_mod")
    assert isinstance(table, SymbolTable)
    assert "some_mod" in table._modules
    assert "a" in table._data_symbols
    sym = table.lookup("a")
    assert sym.name == "a"
    assert sym.primitive_type == "real"


def test_routine_in_module(f2003_parser):
    """Check that we get two, nested symbol tables when a module contains
    a subroutine."""
    _ = f2003_parser(
        get_reader(
            """\
module my_mod
  use some_mod
  real :: a
contains
  subroutine my_sub()
  end subroutine my_sub
end module my_mod
    """
        )
    )
    tables = SYMBOL_TABLES
    assert list(tables._symbol_tables.keys()) == ["my_mod"]
    table = tables.lookup("my_mod")
    assert len(table.children) == 1
    assert table.children[0].name == "my_sub"
    assert table.children[0].parent is table
    # Check that the search for a symbol moves up to the parent scope
    sym = table.children[0].lookup("a")
    assert sym.name == "a"
    assert sym.primitive_type == "real"


def test_routine_in_prog(f2003_parser):
    """Check that we get two, nested symbol tables when a program contains
    a subroutine."""
    _ = f2003_parser(
        get_reader(
            """\
program my_prog
  use some_mod
  real :: a
contains
  subroutine my_sub()
    real :: b
  end subroutine my_sub
end program my_prog
    """
        )
    )
    tables = SYMBOL_TABLES
    assert list(tables._symbol_tables.keys()) == ["my_prog"]
    table = SYMBOL_TABLES.lookup("my_prog")
    assert len(table.children) == 1
    assert table.children[0].name == "my_sub"
    assert table.children[0]._data_symbols["b"].name == "b"
    assert table.children[0].parent is table
