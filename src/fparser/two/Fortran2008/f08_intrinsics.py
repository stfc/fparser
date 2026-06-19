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
Module containing Fortran2008 Intrinsics.
"""

from fparser.two.Fortran2003 import Intrinsic_Name

class Fortran2008_Intrinsic_Names(Intrinsic_Name):
    """
    Represents the name of a Fortran 2008 intrinsic function.

    All generic intrinsic names are specified as keys in the
    `generic_function_names` dictionary, with their values indicating
    the minimum and maximum number of arguments allowed for this
    intrinsic function. A `-1` indicates an unlimited number of
    arguments. The names are split into the categories specified in
    the Fortran2003 specification document.

    All specific intrinsic names (which have a different name to their
    generic counterpart) are specified as keys in the
    `specific_function_names` dictionary, with their values indicating
    which generic function they are associated with
    """

    f08_math_intrinsics = {
        "ERF": {"min": 1, "max": 1},
        "GAMMA": {"min": 1, "max": 1},
    }
    
    f08_bitshift_intrinsics = {
            "SHIFTL": {"min": 2, "max": 2},
            "SHIFTR": {"min": 2, "max": 2},
            "SHIFTA": {"min": 2, "max": 2},
    }

    generic_function_names = {}
    generic_function_names.update(f08_math_intrinsics)
    generic_function_names.update(f08_bitshift_intrinsics)

    specific_function_names = {}

    # A list of all function names
    function_names = list(generic_function_names.keys()) + list(
        specific_function_names.keys()
    )

    @staticmethod
    def match(string):
        """Attempt to match the input `string` with the intrinsic function
        names defined in `generic_function_names` or
        `specific_function_names`. If there is a match the resultant
        string will be converted to upper case.

        :param str string: The pattern to be matched.

        :returns: A tuple containing the matched string (converted to \
        upper case) if there is a match or None if there is not.
        :rtype: (str,) or NoneType

        """
        from fparser.two.utils import STRINGBase
        return STRINGBase.match(Fortran2008_Intrinsic_Names.function_names,
                                string)
