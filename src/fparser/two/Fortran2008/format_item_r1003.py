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
Module containing Fortran 2008 Format_Item rule R1003
"""

from typing import Optional, Tuple, Union

from fparser.two.Fortran2003 import (
    Digit_String,
    Format_Item as Format_Item_2003,
    Format_Item_List,
)
from fparser.two.utils import NoMatchError


class Format_Item(Format_Item_2003):  # R1003
    """Fortran 2008 rule R1003

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

    # Inherit the parent's subclass_names so that Control_Edit_Desc,
    # Hollerith_Item, etc. remain registered when the F2008 parser
    # replaces F2003 Format_Item in the class hierarchy.
    # Include "Format_Item" itself so that this F2008 class is
    # registered in Base.subclasses["Format_Item"] and can be
    # discovered when F2003 code (e.g. Format_Item_List.match)
    # directly references the F2003 Format_Item class.
    subclass_names = Format_Item_2003.subclass_names[:] + ["Format_Item"]
    use_names = Format_Item_2003.use_names[:]

    @staticmethod
    def match(
        string: str,
    ) -> Optional[
        Tuple[Union[str, Digit_String], Union[Format_Item_2003, Format_Item_List]]
    ]:
        """Attempts to match the supplied text with this rule.

        Calls the Fortran 2003 match first. If that fails, checks
        for the Fortran 2008 unlimited format repeat: ``*(format-item-list)``.

        :param string: Fortran code to check for a match.

        :returns: None if there is no match, a tuple of size 2
            containing a repeat specifier (``"*"`` or a Repeat instance)
            and the matched descriptor or format-item-list.

        """
        if not string:
            return None
        # Fortran 2003 matches all but unlimited repeat, so try it first.
        # The F2003 match raises NoMatchError rather than returning None
        # when it cannot parse the string (e.g. Data_Edit_Desc fails).
        try:
            result = Format_Item_2003.match(string)
        except NoMatchError:
            result = None
        if result:
            return result
        # Try to match unlimited format repeat: *(format-item-list)
        strip_string = string.strip()
        if not strip_string:
            return None
        if strip_string[0] == "*" and len(strip_string) > 1:
            my_string = strip_string[1:].lstrip()
            if my_string[0] == "(" and my_string[-1] == ")":
                return ("*", Format_Item_List(my_string[1:-1].lstrip()))
        return None
