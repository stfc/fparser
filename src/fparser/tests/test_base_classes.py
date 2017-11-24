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

import logging
import StringIO

import fparser.base_classes
import fparser.readfortran

class ReaderHarness(fparser.readfortran.FortranReaderBase):
    def __init__( self ):
      pseudoFile = StringIO.StringIO( 'First line of code' )
      super(ReaderHarness, self).__init__( pseudoFile, True, True )

      self.id = 'readerharness'

class StatementHarness(fparser.base_classes.Statement):
  def __init__( self ):
      reader = ReaderHarness()
      reader.get_next_line() # Charge the internal buffers.
      line = fparser.readfortran.Line( 'Some line of code', (1,1),
                                       None, None, reader )
      super(StatementHarness, self).__init__( None, line )

  def process_item( self ):
    pass

class CaptureLoggingHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        super(CaptureLoggingHandler, self).__init__(*args, **kwargs)
        self.reset()

    def emit(self, record):
        self.messages[record.levelname.lower()].append(record.getMessage())

    def reset(self):
        self.messages = {'debug': [],
                         'info': [],
                         'warning': [],
                         'error': [],
                         'critical': []}

def test_statement():
    logger = logging.getLogger( 'fparser' )
    log = CaptureLoggingHandler()
    logger.addHandler( log )

    unit_under_test = StatementHarness()

    unit_under_test.error( 'Scary biscuits' )
    expected = "While processing 'readerharness' (mode='pyf')..\n    1:First line of code <== Scary biscuits"
    assert( log.messages['error'][0] == expected )
    assert( log.messages == {'debug': [],
                             'info': [],
                             'warning': [],
                             'error': [expected],
                             'critical': []} )

