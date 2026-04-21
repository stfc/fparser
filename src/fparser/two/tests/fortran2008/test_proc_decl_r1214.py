# Copyright (c) 2026 Science and Technology Facilities Council

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

"""Test Fortran 2008 rule R1214

proc-decl is procedure-entity-name [ => proc-pointer-init ]

where (R1216) proc-pointer-init is either null-init or
initial-proc-target, and (R1217) initial-proc-target is a
procedure-name.

Extends the Fortran 2003 rule R1214, which only accepted
null-init on the right-hand side of ``=>``.

"""

import pytest

from fparser.common.readfortran import FortranStringReader
from fparser.two.Fortran2008 import Proc_Decl
from fparser.two.parser import ParserFactory
from fparser.two.utils import NoMatchError, walk


def test_proc_decl_bare_name():
    """A bare procedure-entity-name matches via the inherited
    subclass_names branch (no `=>` present)."""
    obj = Proc_Decl("my_proc")
    assert str(obj) == "my_proc"


def test_proc_decl_null_init():
    """The F2003 null-init branch still matches (regression guard)."""
    obj = Proc_Decl("p => null()")
    assert isinstance(obj, Proc_Decl)
    assert str(obj).lower() == "p => null()"


@pytest.mark.parametrize(
    "text,expected",
    [
        ("p => dummy", "p => dummy"),
        ("eval => compute_result", "eval => compute_result"),
        ("cb => foo_impl", "cb => foo_impl"),
    ],
)
def test_proc_decl_initial_proc_target(text, expected):
    """The F2008 initial-proc-target branch matches a plain
    procedure-name on the RHS of ``=>``."""
    obj = Proc_Decl(text)
    assert isinstance(obj, Proc_Decl)
    assert str(obj) == expected


@pytest.mark.parametrize("text", ["=> dummy", "p =>", "p => 1", "p => 'x'"])
def test_proc_decl_invalid(text):
    """Malformed proc-decls raise NoMatchError."""
    with pytest.raises(NoMatchError):
        _ = Proc_Decl(text)


def test_proc_pointer_component_f2008():
    """End-to-end: a derived-type component with a procedure pointer
    initialised to a module procedure parses under std='f2008'."""
    f2008 = ParserFactory().create(std="f2008")
    reader = FortranStringReader(
        "module m\n"
        "  abstract interface\n"
        "    subroutine cb()\n"
        "    end subroutine cb\n"
        "  end interface\n"
        "  type :: t\n"
        "    procedure(cb), pointer, nopass :: eval => dummy\n"
        "  end type t\n"
        "contains\n"
        "  subroutine dummy()\n"
        "  end subroutine dummy\n"
        "end module m\n"
    )
    tree = f2008(reader)
    assert tree is not None
    proc_decls = walk(tree, Proc_Decl)
    assert any("eval => dummy" in str(pd) for pd in proc_decls)


def test_proc_pointer_component_null_init_f2008():
    """Regression guard: the null-init form still parses end-to-end
    under std='f2008'. The null-init branch is still handled by the
    inherited F2003 match, so the resulting node may be an instance
    of the F2003 Proc_Decl (the F2008 subclass's parent)."""
    from fparser.two.Fortran2003 import Proc_Decl as Proc_Decl_2003

    f2008 = ParserFactory().create(std="f2008")
    reader = FortranStringReader(
        "module m\n"
        "  abstract interface\n"
        "    subroutine cb()\n"
        "    end subroutine cb\n"
        "  end interface\n"
        "  type :: t\n"
        "    procedure(cb), pointer, nopass :: eval => null()\n"
        "  end type t\n"
        "end module m\n"
    )
    tree = f2008(reader)
    assert tree is not None
    proc_decls = walk(tree, Proc_Decl_2003)
    assert any(
        "eval => " in str(pd) and "null()" in str(pd).lower() for pd in proc_decls
    )


def test_proc_pointer_component_initial_proc_target_f2003_fails():
    """An initial-proc-target on the RHS of ``=>`` is *only* valid in
    F2008; under std='f2003' the same source must fail to parse
    because the F2003 grammar only allows null-init."""
    from fparser.two.utils import FortranSyntaxError

    f2003 = ParserFactory().create(std="f2003")
    reader = FortranStringReader(
        "module m\n"
        "  abstract interface\n"
        "    subroutine cb()\n"
        "    end subroutine cb\n"
        "  end interface\n"
        "  type :: t\n"
        "    procedure(cb), pointer, nopass :: eval => dummy\n"
        "  end type t\n"
        "contains\n"
        "  subroutine dummy()\n"
        "  end subroutine dummy\n"
        "end module m\n"
    )
    with pytest.raises(FortranSyntaxError):
        _ = f2003(reader)
