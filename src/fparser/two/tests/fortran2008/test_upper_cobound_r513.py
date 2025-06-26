# Copyright (c) 2020 Science and Technology Facilities Council

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

"""Test Fortran 2008 rule R513

upper-cobound is specification-expr

"""

import pytest
from fparser.two.Fortran2008 import Upper_Cobound
from fparser.two import Fortran2003


@pytest.mark.usefixtures("f2008_create")
@pytest.mark.parametrize(
    "attr, _type",
    [
        ("aaa", Fortran2003.Name),
        ("aAa", Fortran2003.Name),
        ("1", Fortran2003.Int_Literal_Constant),
        ("5  + 7", Fortran2003.Level_2_Expr),
        ("3-9", Fortran2003.Level_2_Expr),
    ],
)
def test_upper_cobound(attr, _type):
    """Test that upper_cobound is parsed correctly."""
    obj = Upper_Cobound(attr)
    assert isinstance(obj, _type), repr(obj)
    ref = attr.replace(" ", "").replace("+", " + ").replace("-", " - ")
    assert str(obj) == ref


@pytest.mark.usefixtures("f2008_create")
@pytest.mark.parametrize("attr", ["", "*"])
def test_invalid_upper_cobound(attr):
    """Test that invalid upper_cobound raise exception."""
    with pytest.raises(Fortran2003.NoMatchError):
        _ = Upper_Cobound(attr)
