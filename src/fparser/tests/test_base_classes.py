# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2017 Science and Technology Facilities Council
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
Test battery associated with fparser.base_classes package.
'''
import logging
import fparser.tests.logging_utils

import fparser.base_classes
import fparser.parsefortran
import fparser.readfortran


def test_statement(monkeypatch):
    '''
    Tests the Statement class.

    Only exercises the logging functionality at the moment.
    '''
    reader = fparser.readfortran.FortranStringReader("dummy = 1")
    parser = fparser.parsefortran.FortranParser(reader)

    logger = logging.getLogger('fparser')
    log = fparser.tests.logging_utils.CaptureLoggingHandler()
    logger.addHandler(log)

    monkeypatch.setattr(fparser.base_classes.Statement,
                        'process_item', lambda x: None, raising=False)
    unit_under_test = fparser.base_classes.Statement(parser, None)

    unit_under_test.error('Scary biscuits')
    assert(log.messages == {'critical': [],
                            'debug':    [],
                            'error':    ['Scary biscuits'],
                            'info':     [],
                            'warning':  []})
