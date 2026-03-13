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

"""Test Fortran 2008 rule R1003

format-item is [ r ] data-edit-desc
            or control-edit-desc
            or char-string-edit-desc
            or [ r ] ( format-item-list )
            or format-item-c1002
            or hollerith-item
            or * ( format-item-list )

Extends the Fortran 2003 rule R1003 with the additional unlimited
format repeat specifier ``*`` before a parenthesised format-item-list.

"""

from fparser.two.Fortran2008 import Format_Item
from fparser.two.parser import ParserFactory
from fparser.common.readfortran import FortranStringReader


def test_unlimited_repeat_basic():
    """Test basic unlimited format repeat: *(I5)."""
    obj = Format_Item("*(I5)")
    assert isinstance(obj, Format_Item)
    assert str(obj) == "*(I5)"


def test_unlimited_repeat_multiple_items():
    """Test unlimited format repeat with multiple items: *(1X,A12)."""
    obj = Format_Item("*(1X,A12)")
    assert isinstance(obj, Format_Item)
    assert str(obj) == "*(1X, A12)"


def test_unlimited_repeat_pe_descriptor():
    """Test unlimited format repeat with PE descriptor: *(1X,1PE12.5)."""
    obj = Format_Item("*(1X,1PE12.5)")
    assert isinstance(obj, Format_Item)
    assert str(obj) == "*(1X, 1P, E12.5)"


def test_f2003_match():
    """Test that F2003 format items still match via the F2008 class."""
    obj = Format_Item("3(I5)")
    assert isinstance(obj, Format_Item)
    assert str(obj) == "3(I5)"


def test_format_stmt_unlimited_repeat():
    """Test unlimited format repeat in a full FORMAT statement."""
    f2008 = ParserFactory().create(std="f2008")

    reader = FortranStringReader("subroutine t()\n  1 format(*(I5))\nend subroutine")
    tree = f2008(reader)
    assert tree is not None


def test_format_stmt_mixed_items():
    """Test FORMAT with regular items followed by unlimited repeat."""
    f2008 = ParserFactory().create(std="f2008")

    reader = FortranStringReader(
        "subroutine t()\n  1 format('!',A12,*(1X,A12))\nend subroutine"
    )
    tree = f2008(reader)
    assert tree is not None


def test_format_stmt_pe_descriptor():
    """Test FORMAT with unlimited repeat and PE edit descriptor."""
    f2008 = ParserFactory().create(std="f2008")

    reader = FortranStringReader(
        "subroutine t()\n  2 format(*(1X,1PE12.5))\nend subroutine"
    )
    tree = f2008(reader)
    assert tree is not None
