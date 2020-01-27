# Copyright (c) 2017-2019 Science and Technology Facilities Council

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

"""
Test the various utility functions

"""
import io
import os

import pytest
import six

from fparser.common.utils import split_comma, ParseError, make_clean_tmpfile
from fparser.utils import InternalError


def test_split_comma():
    ''' Test the split_comma() function '''
    items = split_comma("hello, goodbye")
    print(items)
    assert items[0] == "hello"
    assert items[1] == "goodbye"
    # With trailing and leading white space
    items = split_comma("  hello, goodbye   ")
    print(items)
    assert items[0] == "hello"
    assert items[1] == "goodbye"
    items = split_comma("  ")
    assert not items


def test_split_comma_exceptions():
    ''' Test that we raise the expected exceptions if we don't supply
    the brackets in the right form '''
    with pytest.raises(ParseError) as excinfo:
        _ = split_comma("one, two", brackets="()")
    assert "brackets must be a tuple" in str(excinfo.value)
    with pytest.raises(ParseError) as excinfo:
        _ = split_comma("one, two", brackets=("()", ))
    assert "brackets tuple must contain just two items" in str(excinfo.value)
    with pytest.raises(ParseError) as excinfo:
        _ = split_comma("one, two", brackets=("(", "(", "("))
    assert "brackets tuple must contain just two items" in str(excinfo.value)


def test_split_bracketed_list():
    ''' Test the splitting of a list bracketed with parentheses '''
    items = split_comma("(well(1), this(is), it)", brackets=("(", ")"))
    print(items)
    assert items[0] == "well(1)"
    assert items[1] == "this(is)"
    # With superfluous white space
    items = split_comma("  (  well(1), this(is), it  )  ",
                        brackets=("(", ")"))
    print(items)
    assert items[0] == "well(1)"
    assert items[1] == "this(is)"
    assert items[2] == "it"
    # Square brackets
    items = split_comma("[well(1), this(is), it]", brackets=("[", "]"))
    print(items)
    assert items[0] == "well(1)"
    assert items[1] == "this(is)"
    assert items[2] == "it"
    # Mis-matched brackets
    items = split_comma("[well(1), this(is), it)", brackets=("[", "]"))
    assert not items


def test_extract_bracketed_list():
    ''' Test the extraction and parsing of a list within parentheses within
    a larger string '''
    from fparser.common.utils import extract_bracketed_list_items
    items = extract_bracketed_list_items("hello (this, is, a) test")
    assert items[0] == "this"
    assert items[1] == "is"
    assert items[2] == "a"


def test_extract_bracketed_list_err():
    ''' Test that we get the expected errors if the string passed into
    extract_bracketed_list_items() does not have the correct format '''
    from fparser.common.utils import extract_bracketed_list_items
    with pytest.raises(ParseError) as excinfo:
        _ = extract_bracketed_list_items("hello (this, is, wrong(")
    assert "more than one opening/closing parenthesis found" in \
        str(excinfo.value)
    with pytest.raises(ParseError) as excinfo:
        _ = extract_bracketed_list_items("hello )this, is, wrong)")
    assert "more than one opening/closing parenthesis found" in \
        str(excinfo.value)
    with pytest.raises(ParseError) as excinfo:
        _ = extract_bracketed_list_items("hello (this, is, wrong) (too)")
    assert "more than one opening/closing parenthesis found" in \
        str(excinfo.value)
    with pytest.raises(ParseError) as excinfo:
        _ = extract_bracketed_list_items("hello )this, is, wrong( too")
    assert "failed to find expression within parentheses in" in \
        str(excinfo.value)

# utility for the make_clean_tmpfile tests


def create_tmp_file(string, tmpdir, filename="tmp_in.f90"):
    '''Utility function used by make_clean_tmpfile tests. Creates a
    temporary file and adds the content of a text string to it.

    :param str string: string containing content to be placed in a \
    file.
    :param tmpdir: pytest temporary directory structure.
    :type tmpdir: :py:class:'py._path.local.LocalPath'
    :param str filename: the name of the temporary file

    :returns: the filepath of the created file
    :rtype: str

    '''
    filepath = os.path.join(str(tmpdir), filename)
    # Create the input_file
    tmp_file = io.open(filepath, "w", encoding='UTF-8')
    if six.PY2:
        string = unicode(string)
    tmp_file.write(string)
    return tmp_file.name

# tests for the make_clean_tmpfile function


def test_mct_works(tmpdir):
    '''Test that if there are no errors in the input file then we get an
    exact copy of the input file in the temporary file.'''
    content = (
        "program valid\n"
        "end program valid\n")
    input_filepath = create_tmp_file(content, tmpdir)
    output_filepath = make_clean_tmpfile(input_filepath)
    with open(output_filepath, "r") as cfile:
        output = cfile.read()
    assert output == content


def test_mct_invalid_filename_arg():
    '''Test that the expected exception occurs if an invalid input file
    is provided.

    '''
    with pytest.raises(IOError) as excinfo:
        _ = make_clean_tmpfile("nonexistantfile")
    assert "No such file or directory" in str(excinfo.value)


def test_mct_invalid_skip_arg(tmpdir):
    '''Test that the expected exception occurs if an invalid
    skip_bad_input argument is provided.

    '''
    input_filepath = create_tmp_file("", tmpdir)
    with pytest.raises(InternalError) as excinfo:
        _ = make_clean_tmpfile(input_filepath, skip_bad_input="INVALID")
    assert ("skip_bad_input argument should be False or True but "
            "found 'INVALID'.") in str(excinfo.value)


def test_mct_invalid_encode_arg(tmpdir):
    '''Test that an appropriate exception is raised if the encode argument
    is invalid.

    '''
    input_filepath = create_tmp_file("", tmpdir)
    with pytest.raises(InternalError) as excinfo:
        _ = make_clean_tmpfile(input_filepath, encoding="invalid")
    assert "unknown encoding: invalid'." in str(excinfo.value)


def test_mct_parse_error(tmpdir):
    '''Test that an appropriate exception is raised if there is an invalid
    character in the input file and skip_bad_argument is set to
    False.

    '''
    invalid_content = u"\xca"
    input_filepath = create_tmp_file(invalid_content, tmpdir)
    with pytest.raises(ParseError) as excinfo:
        _ = make_clean_tmpfile(input_filepath, skip_bad_input=False,
                               encoding="ascii")
    assert ("Bad character in input file. Error returned was 'ascii' "
            "codec can't decode byte ") in str(excinfo.value)
    # Can't check the actual value as some versions of Python3 return
    # a different value to the one above.
    assert "in position 0: ordinal not in range(128)." in str(excinfo.value)


def test_mct_skip_error(tmpdir, caplog):
    '''Test that invalid characters are skipped in an input file by
    default and that logging messages are created.

    '''
    content = "HELLO"
    invalid_content = u"\xca".join(content)
    input_filepath = create_tmp_file(invalid_content, tmpdir)
    output_filepath = make_clean_tmpfile(input_filepath, encoding="ascii")
    with open(output_filepath, "r") as cfile:
        output = cfile.read()
    assert output == content
    for record in caplog.records:
        assert record.levelname != 'CRITICAL'
    assert ("Skipped bad character in input file. Error returned was 'ascii' "
            "codec can't decode byte ") in caplog.text
    # Can't check the actual value as some versions of Python3 return
    # a different value to the one above.
    assert "in position 1: ordinal not in range(128)." in caplog.text


def test_mct_utf8():
    '''Test that utf8 content can be read and written correctly in
    make_clean_tmpfile.

    '''
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "utf.f90")
    _ = make_clean_tmpfile(filepath)
