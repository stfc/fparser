#!/usr/bin/env python
# Modified work Copyright (c) 2017-2019 Science and Technology
# Facilities Council
# Original work Copyright (c) 1999-2008 Pearu Peterson

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

# The original software (in the f2py project) was distributed under
# the following license:

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

#   a. Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#   b. Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#   c. Neither the name of the F2PY project nor the names of its
#      contributors may be used to endorse or promote products derived from
#      this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.

''' Example script to parse a Fortran program using fparser '''
from __future__ import print_function
from fparser.scripts.script_options import set_fparser_options

try:
    from iocbio.optparse_gui import OptionParser
except ImportError:
    from optparse import OptionParser


def runner(_, options, args):
    ''' Function to read, parse and output fortran source code '''
    from fparser.two.parser import ParserFactory
    from fparser.two.Fortran2003 import FortranSyntaxError, InternalError
    from fparser.common.readfortran import FortranFileReader
    if not args:
        print ("Error: No fortran files specified")
        raise SystemExit(1)
    for filename in args:
        try:
            reader = FortranFileReader(filename)
        except IOError as error:
            print (error)
            return
        if options.mode != 'auto':
            reader.format.from_mode(options.mode)
        try:
            f2003_parser = ParserFactory().create()
            program = f2003_parser(reader)
        except FortranSyntaxError as msg:
            print ("Syntax error: {0}".format(str(msg)))
            try:
                # protect the access to fifo_item[-1] in case the fifo
                # buffer is empty
                print('parsing %r failed at %s' % (filename, reader.fifo_item[-1]))
                print('started at %s' % (reader.fifo_item[0]))
            except IndexError:
                pass
            raise SystemExit(1)
        except InternalError as msg:
            print ("Internal error in fparser: {0}".format(str(msg)))
            raise SystemExit(1)

        if options.task == 'repr':
            print (repr(program))
        elif options.task == 'show':
            print (program)
        elif options.task == 'none':
            pass
        else:
            print ("Internal error in fparser2.py: task command line option "
                   "'{0}' is not supported.".format(options.task))
            raise SystemExit(1)


def main():
    ''' Check arguments before parsing code '''
    parser = OptionParser()
    set_fparser_options(parser)
    options, args = parser.parse_args()
    runner(parser, options, args)
    return


if __name__ == "__main__":
    main()  # pragma: no cover
