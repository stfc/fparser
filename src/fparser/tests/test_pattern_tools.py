##############################################################################
# Copyright (c) 2017-2018 Science and Technology Facilities Council
#
# All rights reserved.
#
# Modifications made as part of the fparser project are distributed
# under the following license:
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
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
##############################################################################
# Modified M.Hambley, UK Met Office
##############################################################################
'''
Test battery associated with fparser.two.pattern_tools package.
'''

import fparser.two.pattern_tools


def test_name_pattern():
    '''
    Tests inherited from implementation source.
    '''
    assert fparser.two.pattern_tools.name.match('a1_a')
    assert abs(fparser.two.pattern_tools.name).match('a1_a')
    assert not abs(fparser.two.pattern_tools.name).match('a1_a[]')


def test_kind_param_pattern():
    '''
    Tests inherited from implementation source.
    '''
    match = abs(fparser.two.pattern_tools.kind_param)
    assert match.match('23')
    assert match.match('SHORT')


def test_signed_digit_pattern():
    '''
    Tests inherited from implementation source.
    '''
    match = abs(fparser.two.pattern_tools.signed_digit_string)
    assert match.match('23')
    assert match.match('+ 23')
    assert match.match('- 23')
    assert match.match('-23')
    assert not match.match('+n')


def test_thing():
    '''
    Tests inherited from implementation source.
    '''
    match = ~fparser.two.pattern_tools.sign.named() \
        + fparser.two.pattern_tools.digit_string.named('number')
    result = match.match('23')
    assert result.groupdict() == {'number': '23', 'sign': None}
    result = match.match('- 23')
    assert result.groupdict() == {'number': '23', 'sign': '-'}


def test_char_literal_const_pattern():
    '''
    Tests inherited from implementation source.
    '''
    match = abs(fparser.two.pattern_tools.char_literal_constant)
    assert match.match('"adadfa"')
    assert match.match('"adadfa""adad"')
    assert match.match('HEY_"adadfa"')
    assert match.match('HEY _ "ad\tadfa"')
    assert not match.match('adadfa')


def test_multi_op_pattern():
    '''
    Tests inherited from implementation source.
    '''
    match = fparser.two.pattern_tools.mult_op.named()
    assert match.rsplit('a *  b')
    assert match.lsplit('a * c* b') == ('a', '*', 'c* b')
    assert match.rsplit('a * c* b') == ('a * c', '*', 'b')
    assert match.lsplit('a * b ** c') == ('a', '*', 'b ** c')
    assert match.rsplit('a * b ** c') == ('a', '*', 'b ** c')
    assert match.lsplit('a * b ** c * d') == ('a', '*', 'b ** c * d')
    assert match.rsplit('a * b ** c * d') == ('a * b ** c', '*', 'd')


def test_power_op_pattern():
    '''
    Tests inherited from implementation source.
    '''
    match = fparser.two.pattern_tools.power_op.named()
    assert match.rsplit('a **  b')
    assert match.lsplit('a * b ** c') == ('a * b', '**', 'c')
    assert match.rsplit('a * b ** c') == ('a * b', '**', 'c')
    assert match.lsplit('a ** b ** c') == ('a', '**', 'b ** c')
    assert match.rsplit('a ** b ** c') == ('a ** b', '**', 'c')
