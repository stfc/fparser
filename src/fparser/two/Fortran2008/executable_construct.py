# Copyright (c) 2018-2023 Science and Technology Facilities Council.

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
"""The file implements the Fortran2008 executable-construct rule R213
    as defined in https://j3-fortran.org/doc/year/10/10-007r1.pdf

"""
from fparser.two.Fortran2003 import Executable_Construct as \
    Executable_Construct_2003


class Executable_Construct(Executable_Construct_2003):  # R213
    # pylint: disable=invalid-name
    """
    Fortran 2008 rule R213.

    .. code-block:: fortran

        executable-construct is action-stmt
                             or associate-construct
                             or block-construct
                             or case-construct
                             or critical-construct
                             or do-construct
                             or forall-construct
                             or if-construct
                             or select-type-construct
                             or where-construct

    Associated constraints are:

    "C201 (R208) An execution-part shall not contain an end-function-stmt,
          end-mp-subprogram-stmt, end-program-stmt, or end-subroutine-stmt."

    """

    subclass_names = [
        "Action_Stmt",
        "Associate_Construct",
        "Block_Construct",
        "Case_Construct",
        "Critical_Construct",
        "Do_Construct",
        "Forall_Construct",
        "If_Construct",
        "Select_Type_Construct",
        "Where_Construct",
    ]
