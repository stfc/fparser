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

import logging
import logging_utils

import fparser.base_classes
import fparser.parsefortran
import fparser.readfortran

class SourceFile(object):
  def __init__( self ):
    self._read = False

  def next( self ):
    if self._read:
      raise StopIteration
    else:
      self._read = True
      return "The only line"

class PretendReader(fparser.readfortran.FortranReaderBase):
  def __init__( self ):
    super(PretendReader, self).__init__( SourceFile(), True, True )
    self.id = 'pretend source file'

class StatementHarness(fparser.base_classes.Statement):
  def __init__( self ):
    parser = fparser.parsefortran.FortranParser( PretendReader() )
    super(StatementHarness, self).__init__( parser, None )

  def process_item( self ):
    pass

def test_statement():
    logger = logging.getLogger( 'fparser' )
    log = logging_utils.CaptureLoggingHandler()
    logger.addHandler( log )

    unit_under_test = StatementHarness()

    unit_under_test.error( 'Scary biscuits' )
    expected = "Scary biscuits"
    assert( log.messages == {'critical': [],
                             'debug':    [],
                             'error':    ['Scary biscuits'],
                             'info':     [],
                             'warning':  []} )
