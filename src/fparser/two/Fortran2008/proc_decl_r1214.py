# -----------------------------------------------------------------------------
# BSD 3-Clause License
#
# Copyright (c) 2026, Science and Technology Facilities Council.
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

"""
Module containing Fortran 2008 Proc_Decl rule R1214
"""

from typing import Optional, Tuple, Union

from fparser.two.Fortran2003 import (
    Name,
    Null_Init,
    Procedure_Entity_Name,
    Proc_Decl as Proc_Decl_2003,
)
from fparser.two.utils import BinaryOpBase, NoMatchError


class Proc_Decl(Proc_Decl_2003):  # R1214
    """Fortran 2008 rule R1214

    proc-decl is procedure-entity-name [ => proc-pointer-init ]

    where (R1216) proc-pointer-init is either null-init or
    initial-proc-target, and (R1217) initial-proc-target is a
    procedure-name. The Fortran 2003 form of R1214 only accepts
    null-init on the right-hand side of ``=>``; this subclass
    extends it to also accept an initial-proc-target so that
    declarations such as::

        procedure(cb), pointer, nopass :: eval => dummy

    parse under ``std='f2008'``.

    """

    # Inherit the parent's subclass_names and include "Proc_Decl" itself
    # so that this F2008 class is registered in Base.subclasses["Proc_Decl"]
    # and discovered when F2003 code (e.g. Proc_Decl_List.match) references
    # the F2003 Proc_Decl class directly.
    subclass_names = Proc_Decl_2003.subclass_names[:] + ["Proc_Decl"]
    use_names = Proc_Decl_2003.use_names[:] + ["Name"]

    @staticmethod
    def match(
        string: str,
    ) -> Optional[Tuple[Procedure_Entity_Name, str, Union[Null_Init, Name]]]:
        """Attempts to match the supplied text with this rule.

        Calls the Fortran 2003 match first (which handles the
        null-init branch); if that fails, tries the Fortran 2008
        initial-proc-target branch where the right-hand side of
        ``=>`` is a procedure-name.

        :param string: Fortran code to check for a match.

        :returns: None if there is no match, otherwise a 3-tuple
            of (procedure-entity-name, ``"=>"``, proc-pointer-init).

        """
        if not string:
            return None
        try:
            result = Proc_Decl_2003.match(string)
        except NoMatchError:
            result = None
        if result:
            return result
        # Fortran 2008 initial-proc-target (R1217): the RHS of "=>"
        # is a procedure-name. Match it as a bare Name, consistent
        # with how fparser treats other name-bearing rules.
        try:
            return BinaryOpBase.match(Procedure_Entity_Name, "=>", Name, string)
        except NoMatchError:
            return None
