# -----------------------------------------------------------------------------
# BSD 3-Clause License
#
# Copyright (c) 2023, Science and Technology Facilities Council.
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
    Module containing Fortran2008 Critical_Stmt rule R811
"""
from fparser.two.utils import StmtBase, WORDClsBase


class Critical_Stmt(StmtBase, WORDClsBase):
    """
    Fortran 2008 Rule R811.

    critical-stmt is [ critical-construct-name : ] CRITICAL

    """

    subclass_names = []
    use_names = ["Critical_Construct_Name"]

    @staticmethod
    def match(string):
        """
        Attempts to match the supplied string as a CRITICAL statement.

        :param str string: the string to attempt to match.

        :returns: 2-tuple containing the matched word "CRITICAL" and None or \
                  None if no match.
        :rtype: Tuple[str, NoneType] or NoneType

        """
        return WORDClsBase.match("CRITICAL", None, string)

    def get_start_name(self):
        """
        :returns: the name associated with the start of this CRITICAL region (if any)
        :rtype: str | NoneType
        """
        return self.item.name

    def tostr(self):
        """
        :returns: the string representation of this node.
        :rtype: str
        """
        return "CRITICAL"