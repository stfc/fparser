..  Copyright (c) 2017-2019 Science and Technology Facilities Council.

    All rights reserved.

    Modifications made as part of the fparser project are distributed
    under the following license:

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are
    met:

    1. Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in the
    documentation and/or other materials provided with the distribution.

    3. Neither the name of the copyright holder nor the names of its
    contributors may be used to endorse or promote products derived from
    this software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
    A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
    HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
    SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
    LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
    DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
    THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

.. _Introduction:

Introduction
============

The fparser package is a Python implementation of a Fortran
66/77/90/95/2003/2008 language parser. The code is available on the
Python Package Index (https://pypi.python.org/pypi/fparser) or from
github (https://github.com/stfc/fparser).  The fparser project
currently includes two different implementations; the first,
"fparser1", supports Fortran 66/77/90 (plus some extensions --- see
:ref:`fparser`) but only parses down to the level of individual lines
of code, i.e. not the content of the Fortran expressions
themselves. The second implementation, "fparser2", additionally has
support for Fortran 2003 and some Fortran 2008 (see :ref:`fparser2`)
and is able to fully parse Fortran code.

The use of fparser2 is strongly recommended as support for fparser1
has now ceased and it will be removed in a future version of the
fparser project.

The Fortran language syntax rules for Fortran2003 are implemented in
`Fortran2003.py`_, with the rules being taken from the following
ISO/IEC 1539 document:
https://wg5-fortran.org/N1601-N1650/N1601.pdf

.. _Fortran2003.py:  https://github.com/stfc/fparser/blob/master/src/fparser/two/Fortran2003.py

The additional Fortran language syntax rules for Fortran2008 are
implemented in `Fortran2008.py`_, with the rules being taken from the
following document:
https://j3-fortran.org/doc/year/10/10-007r1.pdf

.. _Fortran2008.py:  https://github.com/stfc/fparser/blob/master/src/fparser/two/Fortran2008.py

This code was originally developed by Pearu Peterson as part of the
f2py project (https://github.com/pearu/f2py). The fparser package is
used in the PSyclone (https://github.com/stfc/PSyclone) and Habakkuk
(https://github.com/arporter/habakkuk) tools. If you make use of
fparser and want your project added to this list, please let the
developers know.

For a full list of the contributors please see the `CHANGELOG.md`
file in the root directory.
