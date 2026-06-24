# -----------------------------------------------------------------------------
# BSD 3-Clause License
#
# Copyright (c) 2023-2024, Science and Technology Facilities Council.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# -----------------------------------------------------------------------------

"""Test the Fortran 2008 intrinsic support."""

from fparser.common.readfortran import FortranStringReader
from fparser.two.Fortran2003 import Part_Ref
from fparser.two.Fortran2008 import Intrinsic_Name
from fparser.two.utils import walk


def test_f2008_intrinsic(f2008_parser):
    """Test Fortran2008 intrinsic is created with the f2008 parser."""

    reader = FortranStringReader("""subroutine test
        integer :: i

        i = erf(i)
        end subroutine test
        """)
    tree = f2008_parser(reader)
    intrinsic = walk(tree, Intrinsic_Name)
    print(tree.__repr__)
    assert len(intrinsic) == 1
    assert str(intrinsic[0]) == "ERF"


def test_f2008_intrinsic_f2003_parse(f2003_parser):
    """Test Fortran2008 intrinsic is not created with the f2003 parser."""
    reader = FortranStringReader("""subroutine test
        integer :: i

        i = erf(i)
        end subroutine test
        """)
    tree = f2003_parser(reader)
    intrinsic = walk(tree, Intrinsic_Name)
    assert len(intrinsic) == 0
    partref = walk(tree, Part_Ref)
    assert len(partref) == 1
    assert str(partref[0]) == "erf(i)"
