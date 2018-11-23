# -*- coding: utf-8 -*-
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
Test battery associated with fparser.common.readfortran package.
'''
from __future__ import print_function
from __future__ import unicode_literals

import os.path
import tempfile
import pytest
from fparser.common.readfortran import FortranFileReader, FortranStringReader
import fparser.common.sourceinfo
import fparser.common.tests.logging_utils


def test_empty_line_err():
    ''' Check that we raise the expected error if we try and create
    an empty Line '''
    from fparser.common.readfortran import Line, FortranReaderError
    with pytest.raises(FortranReaderError) as err:
        _ = Line("   ", 1, "", "a_name", None)
    assert "Got empty line: \'   \'" in str(err)


def test_111fortranreaderbase(log, monkeypatch):
    '''
    Tests the FortranReaderBase class.

    Currently only tests logging functionality.
    '''
    class FailFile(object):
        '''
        A "file-like" object which returns a line of Fortran source followed
        by raising a StopIteration exception.
        '''
        _stuff = ['x=1']

        def next(self):
            '''
            Used by Python 2.7.
            '''
            return self.__next__()

        def __next__(self):
            '''
            Used by Python 3.
            '''
            return self._stuff.pop()

    monkeypatch.setattr('fparser.common.readfortran.FortranReaderBase.id',
                        lambda x: 'foo', raising=False)
    mode = fparser.common.sourceinfo.FortranFormat(True, False)
    unit_under_test = fparser.common.readfortran.FortranReaderBase(FailFile(),
                                                                   mode,
                                                                   True)
    assert str(unit_under_test.next()) == "line #1'x=1'"
    with pytest.raises(StopIteration):
        unit_under_test.next()

    assert log.messages['info'] == []
    assert log.messages['warning'] == []
    assert log.messages['error'] == []
    result = log.messages['critical'][0].split('\n')[1]
    assert result == '    1:x=1 <== while processing line'
    assert log.messages['critical'][1] == 'STOPPED READING'
    expected = 'Traceback\n'
    assert log.messages['debug'][0][:len(expected)] == expected


def test_base_next_bad_include(log):
    '''
    Tests that FortranReaderBase.next() causes a message to be logged when an
    included file does not exist.
    '''
    code = "include 'nonexistant.f90'\nx=1"
    unit_under_test = fparser.common.readfortran.FortranStringReader(code)
    line = unit_under_test.next()
    assert str(line) == 'line #2\'x=1\''
    assert log.messages['debug'] == []
    assert log.messages['error'] == []
    assert log.messages['info'] == []
    assert log.messages['critical'] == []
    expected = "    1:include 'nonexistant.f90' " \
               + "<== 'nonexistant.f90' not found in '.'. " \
               + "INLCUDE line treated as comment line."
    result = log.messages['warning'][0].split('\n')[1]
    assert result == expected


def test_base_next_good_include(log):
    '''
    Tests that FortranReaderBase.next() causes a message to be logged when a
    file is included.
    '''
    code = "include 'modfile.f95'\nx=2"
    include_directories = [os.path.dirname(__file__)]
    unit_under_test = fparser.common.readfortran \
        .FortranStringReader(code, include_dirs=include_directories,
                             ignore_comments=False)
    line = unit_under_test.next()
    assert str(line)[:19] == "Comment('! Modified"  # First line of inclusion
    assert log.messages['debug'] == []
    assert log.messages['error'] == []
    assert log.messages['warning'] == []
    assert log.messages['critical'] == []
    expected = "    1:include 'modfile.f95' " \
               + "<== including file '{path}/modfile.f95'"
    result = log.messages['info'][0].split('\n')[1]
    assert result == expected.format(path=include_directories[0])


def test_fortranreaderbase_info(log):
    '''
    Tests that FortranReaderBase.info() causes a message to be logged.
    '''
    unit_under_test = fparser.common.readfortran.FortranStringReader('x=3')
    thing = unit_under_test.get_source_item()
    unit_under_test.info('Mighty Whirlitzer', thing)
    assert log.messages['debug'] == []
    assert log.messages['error'] == []
    assert log.messages['warning'] == []
    assert log.messages['critical'] == []
    expected = '    1:x=3 <== Mighty Whirlitzer'
    result = log.messages['info'][0].split('\n')[1]
    assert result == expected


def test_fortranreaderbase_error(log):
    '''
    Tests that FortranReaderBase.error() causes a message to be logged.
    '''
    unit_under_test = fparser.common.readfortran.FortranStringReader('x=2')
    thing = unit_under_test.get_source_item()
    with pytest.raises(SystemExit):
        unit_under_test.error('Thundering Chalmer', thing)
    assert log.messages['debug'] == []
    assert log.messages['info'] == []
    assert log.messages['warning'] == []
    assert log.messages['critical'] == []
    expected = '    1:x=2 <== Thundering Chalmer'
    result = log.messages['error'][0].split('\n')[1]
    assert result == expected


def test_fortranreaderbase_warning(log):
    '''
    Tests that FortranReaderBase.warning() causes a message to be logged.
    '''
    unit_under_test = fparser.common.readfortran.FortranStringReader('x=1')
    thing = unit_under_test.get_source_item()
    unit_under_test.warning('Flatulent Hermit', thing)
    assert log.messages['debug'] == []
    assert log.messages['info'] == []
    assert log.messages['error'] == []
    assert log.messages['critical'] == []
    expected = '    1:x=1 <== Flatulent Hermit'
    result = log.messages['warning'][0].split('\n')[1]
    assert result == expected


def test_base_handle_multilines(log):
    '''
    Tests that FortranReaderBase.get_source_item() logs the correct messages
    when there are quote discrepancies.
    '''
    code = 'character(8) :: test = \'foo"""bar'
    log.reset()
    unit_under_test = fparser.common.readfortran.FortranStringReader(code)
    mode = fparser.common.sourceinfo.FortranFormat(True, True)
    unit_under_test.set_format(mode)  # Force strict free format
    unit_under_test.get_source_item()
    assert log.messages['debug'] == []
    assert log.messages['info'] == []
    assert log.messages['error'] == []
    assert log.messages['critical'] == []
    expected = 'multiline prefix contains odd number of "\'" characters'
    result = log.messages['warning'][0].split('<==')[1].lstrip()
    assert result == expected

    code = 'goo """boo\n doo""" soo \'foo'
    log.reset()
    unit_under_test = fparser.common.readfortran.FortranStringReader(code)
    mode = fparser.common.sourceinfo.FortranFormat(True, True)
    unit_under_test.set_format(mode)  # Force strict free format
    unit_under_test.get_source_item()
    assert log.messages['debug'] == []
    assert log.messages['info'] == []
    assert log.messages['error'] == []
    assert log.messages['critical'] == []
    expected = 'following character continuation: "\'", expected None.'
    result = log.messages['warning'][0].split('<==')[1].lstrip()
    assert result == expected


def test_base_fixed_nonlabel(log):
    '''
    Tests that FortranReaderBase.get_source_item() logs the correct messages
    when there is an unexpected character in the initial 6 columns.
    '''
    # Checks that a bad character in the first column causes an event to be
    # logged.
    code = 'w    integer :: i'
    log.reset()
    unit_under_test = fparser.common.readfortran.FortranStringReader(code)
    mode = fparser.common.sourceinfo.FortranFormat(False, True)
    unit_under_test.set_format(mode)  # Force fixed format
    unit_under_test.get_source_item()
    assert log.messages['debug'] == []
    assert log.messages['info'] == []
    assert log.messages['error'] == []
    assert log.messages['critical'] == []
    result = log.messages['warning'][0].split('<==')[1].lstrip()
    expected = "non-space/digit char 'w' found in column 1 of fixed " \
               + "Fortran code, interpreting line as comment line"
    assert result == expected

    # Checks a bad character in columns 2-6
    for i in range(1, 5):
        code = ' '*i + 'w' + ' '*(5-i) + 'integer :: i'
        log.reset()
        unit_under_test = fparser.common.readfortran.FortranStringReader(code)
        mode = fparser.common.sourceinfo.FortranFormat(False, True)
        unit_under_test.set_format(mode)  # Force strict fixed format
        unit_under_test.get_source_item()
        assert log.messages['debug'] == []
        assert log.messages['info'] == []
        assert log.messages['error'] == []
        assert log.messages['critical'] == []
        result = log.messages['warning'][0].split('<==')[1].lstrip()
        expected = "non-space/digit char 'w' found in column {col} " \
                   + "of fixed Fortran code"
        assert result == expected.format(col=i+1)

    # Checks for a bad character, not in the first column, with "sloppy" mode
    # engaged.
    code = ' w   integer :: i'
    log.reset()
    unit_under_test = fparser.common.readfortran.FortranStringReader(code)
    mode = fparser.common.sourceinfo.FortranFormat(False, False)
    unit_under_test.set_format(mode)  # Force sloppy fixed format
    unit_under_test.get_source_item()
    assert log.messages['debug'] == []
    assert log.messages['info'] == []
    assert log.messages['error'] == []
    assert log.messages['critical'] == []
    expected = "non-space/digit char 'w' found in column 2 " \
               + "of fixed Fortran code, switching to free format mode"
    result = log.messages['warning'][0].split('<==')[1].lstrip()
    assert result == expected


def test_base_fixed_continuation(log):
    '''
    Tests that FortranReaderBase.get_source_item() logs the correct messages
    when there are quote mismatches across a continuation in fixed format.
    '''
    code = '     character(4) :: cheese = "a & !\n     & b'
    log.reset()
    unit_under_test = fparser.common.readfortran.FortranStringReader(code)
    mode = fparser.common.sourceinfo.FortranFormat(False, False)
    unit_under_test.set_format(mode)  # Force sloppy fixed format
    unit_under_test.get_source_item()
    assert log.messages['debug'] == []
    assert log.messages['info'] == []
    assert log.messages['error'] == []
    assert log.messages['critical'] == []
    expected = 'following character continuation: \'"\', expected None.'
    result = log.messages['warning'][0].split('<==')[1].lstrip()
    assert result == expected

    code = '     x=1 &\n     +1 &\n     -2'
    log.reset()
    unit_under_test = fparser.common.readfortran.FortranStringReader(code)
    mode = fparser.common.sourceinfo.FortranFormat(False, False)
    unit_under_test.set_format(mode)  # Force sloppy fixed format
    unit_under_test.get_source_item()
    assert log.messages['debug'] == []
    assert log.messages['info'] == []
    assert log.messages['error'] == []
    assert log.messages['critical'] == []
    expected = 'free format line continuation character `&\' detected ' \
               + 'in fix format code\n    2:     +1 &\n    3:     -2'
    result = log.messages['warning'][0].split('<==')[1].lstrip()
    assert result == expected


def test_base_free_continuation(log):
    '''
    Tests that FortranReaderBase.get_source_item() logs the correct messages
    when there are quote mismatches across a continuation in free format.
    '''
    code = 'character(4) :: "boo & que'
    log.reset()
    unit_under_test = fparser.common.readfortran.FortranStringReader(code)
    mode = fparser.common.sourceinfo.FortranFormat(True, False)
    unit_under_test.set_format(mode)  # Force sloppy free format
    unit_under_test.get_source_item()
    assert log.messages['debug'] == []
    assert log.messages['info'] == []
    assert log.messages['warning'] == []
    assert log.messages['critical'] == []
    expected = 'following character continuation: \'"\', expected None.'
    result = log.messages['error'][0].split('<==')[1].lstrip()
    assert result == expected


##############################################################################

FULL_FREE_SOURCE = '''
program test

  implicit none

  character, paramater :: nature = 'free format'

end program test
'''

FULL_FREE_EXPECTED = ['program test',
                      '  implicit none',
                      "  character, paramater :: nature = 'free format'",
                      'end program test']


##############################################################################

def test_filename_reader():
    '''
    Tests that a Fortran source file can be read given its filename.
    '''
    handle, filename = tempfile.mkstemp(suffix='.f90', text=True)
    os.close(handle)
    try:
        with open(filename, mode='w') as source_file:
            print(FULL_FREE_SOURCE, file=source_file)

        unit_under_test = FortranFileReader(filename)
        expected = fparser.common.sourceinfo.FortranFormat(True, False)
        assert unit_under_test.format == expected
        for expected in FULL_FREE_EXPECTED:
            found = unit_under_test.get_single_line(ignore_empty=True)
            assert found == expected
    except Exception:
        os.unlink(filename)
        raise


##############################################################################

def test_file_reader():
    '''
    Tests that a Fortran source file can be read given a file object of it.
    '''
    handle, filename = tempfile.mkstemp(suffix='.f90', text=True)
    os.close(handle)
    try:
        with open(filename, mode='w') as source_file:
            print(FULL_FREE_SOURCE, file=source_file)

        with open(filename, mode='r') as source_file:
            unit_under_test = FortranFileReader(source_file)

            expected = fparser.common.sourceinfo.FortranFormat(True, False)
            assert unit_under_test.format == expected
            for expected in FULL_FREE_EXPECTED:
                assert unit_under_test.get_single_line(ignore_empty=True) \
                       == expected
    except Exception:
        os.unlink(filename)
        raise


##############################################################################

def test_bad_file_reader():
    '''
    Tests that the file reader can spot when it is given something to read
    which is neither file nor filename.
    '''
    with pytest.raises(ValueError) as ex:
        unit_under_test = FortranFileReader(42)
    expected = 'FortranFileReader is used with a filename or file-like object.'
    assert expected in str(ex)


##############################################################################

def test_string_reader():
    '''
    Tests that Fortran source can be read from a string.
    '''
    unit_under_test = FortranStringReader(FULL_FREE_SOURCE)
    expected = fparser.common.sourceinfo.FortranFormat(True, False)
    assert unit_under_test.format == expected
    for expected in FULL_FREE_EXPECTED:
        assert unit_under_test.get_single_line(ignore_empty=True) == expected


##############################################################################

def test_inherited_f77():
    '''
    A grab bag of functional tests inherited from readfortran.py.
    '''
    string_f77 = """c -*- f77 -*-
c12346 comment
      subroutine foo
      call foo
     'bar
a    'g
      abc=2
cf2py call me ! hey
      call you ! hi
      end
     '"""
    expected = ["Comment('c -*- f77 -*-',(1, 1))",
                "Comment('c12346 comment',(2, 2))",
                "line #3'subroutine foo'",
                "line #4'call foobar'",
                'Comment("a    \'g",(6, 6))',
                "line #7'abc=2'",
                "line #9'call you ! hi'",
                "line #10'end'"]

    # Reading from buffer
    reader = fparser.common.readfortran.FortranStringReader(
        string_f77, ignore_comments=False)
    assert reader.format.mode == 'f77', repr(reader.format.mode)
    stack = expected[:]
    for item in reader:
        assert str(item) == stack.pop(0)

    # Reading from file
    handle, filename = tempfile.mkstemp(suffix='.f', text=True)
    os.close(handle)
    with open(filename, 'w') as fortran_file:
        print(string_f77, file=fortran_file)

    reader = fparser.common.readfortran.FortranFileReader(
        filename, ignore_comments=False)
    stack = expected[:]
    for item in reader:
        assert str(item) == stack.pop(0)


def test_pyf():
    '''
    Tests inherited from implementation.
    '''
    string_pyf = """! -*- pyf -*-
python module foo
  interface
  beginml '''1st line
  2nd line
  end line'''endml='tere!fake comment'!should be a comment
  a = 2
  'charc\"onstant' ''' single line mline '''a='hi!fake comment'!should be a comment
  a=\\\\\\\\\\'''not a multiline'''
  !blah='''never ending multiline
  b=3! hey, fake line continuation:&
  c=4& !line cont
  &45
  thisis_label_2 : c = 3
   xxif_isotropic_2 :     if ( string_upper_compare ( o%opt_aniso, 'ISOTROPIC' ) ) then
   g=3
   endif
  end interface
  if ( pc_get_lun() .ne. 6) &

    write ( pc_get_lun(), '( &
    & /, a, /, " p=", i4, " stopping c_flag=", a, &
    & /, " print unit=", i8)') &
    trim(title), pcpsx_i_pel(), trim(c_flag), pc_get_lun()
end python module foo
! end of file
"""
    expected = ["Comment('! -*- pyf -*-',(1, 1))",
                "line #2'python module foo'",
                "line #3'interface'",
                "MultiLine('  beginml ',"
                + "['1st line', '  2nd line', '  end line'],"
                + "\"endml='tere!fake comment'\",(4, 6))",
                "Comment('!should be a comment',(6, 6))",
                "line #7'a = 2'",
                "MultiLine('  \\'charc\"onstant\\' ',"
                + "[' single line mline '],"
                + "\"a='hi!fake comment'\",(8, 8))",
                "Comment('!should be a comment',(8, 8))",
                'line #9"a=\\\\\\\\\\\\\\\\\\\\\'\'\'not a multiline\'\'\'"',
                'Comment("!blah=\'\'\'never ending multiline",(10, 10))',
                "line #11'b=3'",
                "Comment('! hey, fake line continuation:&',(11, 11))",
                "line #12'c=445'",
                "Comment('!line cont',(12, 12))",
                "line #14thisis_label_2: 'c = 3'",
                'line #15xxif_isotropic_2: '
                + '"if ( string_upper_compare ( o%opt_aniso,'
                + ' \'ISOTROPIC\' ) ) then"',
                "line #16'g=3'",
                "line #17'endif'",
                "line #18'end interface'",
                'line #19\'if ( pc_get_lun() .ne. 6)'
                + '     write ( pc_get_lun(), \\\'(  /, a, /, " p=", i4,'
                + ' " stopping c_flag=", a,  /, " print unit=", i8)\\\')'
                + '     trim(title), pcpsx_i_pel(), trim(c_flag),'
                + ' pc_get_lun()\'',
                "line #25'end python module foo'",
                "Comment('! end of file',(26, 26))"]

    reader = fparser.common.readfortran.FortranStringReader(
        string_pyf, ignore_comments=False)
    assert reader.format.mode == 'pyf', repr(reader.format.mode)
    for item in reader:
        assert str(item) == expected.pop(0)


def test_fix90():
    '''
    Tests inherited from implementation.
    '''
    string_fix90 = """c -*- fix -*-
      subroutine foo
cComment
 1234 a = 3 !inline comment
      b = 3
!
     !4!line cont. with comment symbol
     &5
      a = 3!f2py.14 ! pi!
!   KDMO
      write (obj%print_lun, *) ' KDMO : '
      write (obj%print_lun, *) '  COORD = ',coord, '  BIN_WID = ',             &
       obj%bin_wid,'  VEL_DMO = ', obj%vel_dmo
      end subroutine foo
      subroutine

     & foo
      end
"""
    expected = ["Comment('c -*- fix -*-',(1, 1))",
                "line #2'subroutine foo'",
                "Comment('cComment',(3, 3))",
                "line #4 1234 'a = 3'",
                "Comment('!inline comment',(4, 4))",
                "line #5'b = 345'",
                "Comment('!',(6, 6))",
                "Comment('!line cont. with comment symbol',(7, 7))",
                "line #9'a = 3.14'",
                "Comment('! pi!',(9, 9))",
                "Comment('!   KDMO',(10, 10))",
                'line #11"write (obj%print_lun, *) \' KDMO : \'"',
                'line #12"write (obj%print_lun, *) \'  COORD = \',coord,'
                + ' \'  BIN_WID = \',             &"',
                'line #13"obj%bin_wid,\'  VEL_DMO = \', obj%vel_dmo"',
                "line #14'end subroutine foo'",
                "line #15'subroutine foo'",
                "Comment('',(16, 16))",
                "line #18'end'"]
    reader = fparser.common.readfortran.FortranStringReader(
        string_fix90, ignore_comments=False)
    assert reader.format.mode == 'fix', repr(reader.format.mode)
    for item in reader:
        assert str(item) == expected.pop(0)
