# Copyright (c) 2019 Science and Technology Facilities Council

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

''' File containing unit tests for the BlockBase baseclass in utils.py '''

import textwrap
from fparser.two.utils import BlockBase
from fparser.common.graph_tools import LineAnnotator


# TODO #179: full testing of this class. We currently only test the
# comment and include support.

def test_include(f2003_create):
    '''Test the BlockBase match method supports include statements and
    comments before the class that indicates the start of the block
    (the start class).

    '''
    # Use the Main Program rule R1101 as an example
    from fparser.two.Fortran2003 import Program_Stmt, Specification_Part, \
        Execution_Part, Internal_Subprogram_Part, End_Program_Stmt
    from fparser.api import get_reader
    startcls = Program_Stmt
    subclasses = [Specification_Part, Execution_Part,
                  Internal_Subprogram_Part]
    endcls = End_Program_Stmt

    expected = textwrap.dedent("""
      ! t: Include_Stmt
      INCLUDE '1'
      ! t: Comment
      ! comment1
      ! t: Program_Stmt
      PROGRAM test
          ! t: Include_Stmt
          INCLUDE '2'
          ! t: Comment
          ! comment2
        ! t: Type_Declaration_Stmt
        INTEGER :: i
          ! t: Include_Stmt
          INCLUDE '3'
          ! t: Comment
          ! comment3
        ! t: Assignment_Stmt
        i = 1
        ! t: Include_Stmt
        INCLUDE '4'
        ! t: Comment
        ! comment4
        ! t: Contains_Stmt
        CONTAINS
        ! t: Include_Stmt
        INCLUDE '5'
        ! t: Comment
        ! comment5
      ! t: End_Program_Stmt
      END PROGRAM test
    """).strip()

    # The source is every-other line (i.e. with no "type" comments)
    source = '\n'.join(expected.split('\n')[1::2]) + """
      ! I should be ignored (as I am after END PROGRAM)
      include 'so should I'
    """.strip()

    reader = get_reader(source, ignore_comments=False)
    result = BlockBase.match(startcls, subclasses, endcls, reader)

    assert expected == LineAnnotator(result).content
