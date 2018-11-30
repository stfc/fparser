#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Modified work Copyright (c) 2017-2018 Science and Technology
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

"""Provides Fortran reader classes.

Overview
========

Provides FortranReader classes for reading Fortran codes from files and
strings. FortranReader handles comments and line continuations of both
fix and free format Fortran codes.

Examples
========

::

    >> from fparser.common.readfortran import FortranFileReader
    >>> import os
    >>> reader = FortranFileReader(os.path.expanduser('~/src/blas/daxpy.f'))
    >>> print reader.next()
    line #1 'subroutine daxpy(n,da,dx,incx,dy,incy)'
    >>> print `reader.next()`
    Comment('c     constant times a vector plus a vector.\\n
    c     uses unrolled loops for increments equal to one.\\n
    c     jack dongarra, linpack, 3/11/78.\\n
    c     modified 12/3/93, array(1) declarations changed to array(*)',(3, 6))
    >>> print `reader.next()`
    Line('double precision dx(*),dy(*),da',(8, 8),'')
    >>> print `reader.next()`
    Line('integer i,incx,incy,ix,iy,m,mp1,n',(9, 9),'')

Note that the ``.next()`` method may return `Line`, `SyntaxErrorLine`,
`Comment`, `MultiLine`, or `SyntaxErrorMultiLine` instance.
Let us continue with the above example session to illustrate the `Line`
methods and attributes::

    >>> item = reader.next()
    >>> item
        Line('if (da .eq. 0.0d0) return',(12, 12),'')
    >>> item.line
        'if (da .eq. 0.0d0) return'
    >>> item.strline
        'if (F2PY_EXPR_TUPLE_5) return'
    >>> item.strlinemap
        {'F2PY_EXPR_TUPLE_5': 'da .eq. 0.0d0'}
    >>> item.span
        (12, 12)
    >>> item.get_line()
        'if (F2PY_EXPR_TUPLE_5) return'

To read a Fortran code from a string, use `FortranStringReader` class::

    >>> from fparser.common.sourceinfo import FortranFormat
    >>> from fparser.common.readfortran import FortranStringReader
    >>> code = '''
    ...       subroutine foo(a)
    ...         integer a
    ...         print*,\"a=\",a
    ...       end
    ... '''
    >>> reader = FortranStringReader(code)
    >>> reader.set_format(FortranFormat(False, True))
    >>> reader.next()
        Line('subroutine foo(a)',(2, 2),'')
    >>> reader.next()
        Line('integer a',(3, 3),'')
    >>> reader.next()
        Line('print*,\"a=\",a',(4, 4),'')

"""
# Author: Pearu Peterson <pearu@cens.ioc.ee>
# Created: May 2006

from __future__ import print_function

import re
import os
import sys
import logging
import traceback

import six

import fparser.common.sourceinfo
from fparser.common.splitline import String, string_replace_map, splitquote

__all__ = ['FortranFileReader',
           'FortranStringReader',
           'FortranReaderError',
           'Line',
           'SyntaxErrorLine',
           'Comment',
           'MultiLine',
           'SyntaxErrorMultiLine']

_SPACEDIGITS = ' 0123456789'
_CF2PY_RE = re.compile(r'(?P<indent>\s*)!f2py(?P<rest>.*)', re.I)
_LABEL_RE = re.compile(r'\s*(?P<label>\d+)\s*(\b|(?=&)|\Z)', re.I)
_CONSTRUCT_NAME_RE = re.compile(r'\s*(?P<name>\w+)\s*:\s*(\b|(?=&)|\Z)', re.I)
_IS_INCLUDE_LINE = re.compile(r'\s*include\s*("[^"]+"'
                              + r'|\'[^\']+\')\s*\Z', re.I).match


def _is_fix_cont(line):
    return line and len(line) > 5 and line[5] != ' ' and line[:5] == 5 * ' '


def _is_fix_comment(line, isstrict):
    """
    Check whether line is a comment line in fixed format Fortran source.

    :param str line: Line of code to check
    :param bool isstrict: Whether we are strictly enforcing fixed/free fmt

    References
    ----------
    :f2008:`3.3.3`
    """
    if line:
        if line[0] in '*cC!':
            return True
        if not isstrict:
            i = line.find('!')
            if i != -1:
                start = line[:i].lstrip()
                if not start:
                    if i == 5:
                        # line continuation
                        return False
                    return True
                else:
                    # inline comment or ! is used in character context
                    # inline comments are handled elsewhere
                    pass
    elif line == '':
        return True
    return False


_HOLLERITH_START_SEARCH = re.compile(r'(?P<pre>\A|,\s*)'
                                     + r'(?P<num>\d+)h', re.I).search
_IS_CALL_STMT = re.compile(r'call\b', re.I).match


class FortranReaderError(Exception):
    '''
    Thrown when there is an error reading the Fortran source file.
    '''
    pass


class Line(object):
    """ Holds a Fortran source line.

    Attributes
    ----------
    line : str
      code line
    span : 2-tuple
      starting and ending line numbers
    label : {int, None}
      Specify statement label
    name : {str, None}
      Specify construct name.
    reader : FortranReaderBase
    strline : {None, str}
    is_f2py_directive : bool
      the line contains f2py directive
    """

    f2py_strmap_findall = re.compile(r'(_F2PY_STRING_CONSTANT_\d+_'
                                     + r'|F2PY_EXPR_TUPLE_\d+)').findall

    def __init__(self, line, linenospan, label, name, reader):
        self.line = line.strip()
        if not self.line:
            raise FortranReaderError("Got empty line: '{0}'. linenospan={1}, "
                                     "label='{2}'".format(line,
                                                          linenospan, label))
        self.span = linenospan
        assert label is None or isinstance(label, int), repr(label)
        assert name is None or isinstance(name, str) and name != '', repr(name)
        self.label = label
        self.name = name
        self.reader = reader
        self.strline = None
        self.is_f2py_directive = linenospan[0] in reader.f2py_comment_lines
        self.parse_cache = {}

    def has_map(self):
        '''
        Returns true when a substitution map has been registered.
        '''
        return hasattr(self, 'strlinemap') and self.strlinemap

    def apply_map(self, line):
        '''
        Substitutes magic strings in a line with values specified in a map.
        '''
        if not hasattr(self, 'strlinemap') or not self.strlinemap:
            return line
        findall = self.f2py_strmap_findall
        str_map = self.strlinemap
        keys = findall(line)
        for k in keys:
            line = line.replace(k, str_map[k])
        return line

    def copy(self, line=None, apply_map=False):
        '''
        Creates a Line object from a string.

        If no line argument is specified a copy is made of this Line.

        If a substitution map is provided it is used while making the copy.
        '''
        if line is None:
            line = self.line
        if apply_map:
            line = self.apply_map(line)
        return Line(line, self.span, self.label, self.name, self.reader)

    def clone(self, line):
        '''
        This Line has its contents overwitten by the passed string. The
        incoming string has substitution applied.
        '''
        self.line = self.apply_map(line)
        self.strline = None
        return

    def __repr__(self):
        return self.__class__.__name__+'(%r,%s,%r,%r,<reader>)' \
               % (self.line, self.span, self.label, self.name)

    def __str__(self):
        s = 'line #%s' % (self.span[0])
        if self.label is not None:
            s += ' %s ' % (self.label)
        if self.name is not None:
            s += '%s: ' % (self.name)
        return s + repr(self.line)

    def isempty(self, ignore_comments=False):
        return not (self.line
                    or self.label is not None
                    or self.name is not None)

    def get_line(self, apply_map=False):
        if apply_map:
            return self.apply_map(self.get_line(apply_map=False))
        if self.strline is not None:
            return self.strline
        line = self.line

        if self.reader.format.is_f77:
            # Handle Hollerith constants by replacing them
            # with char-literal-constants.
            # H constants may appear only in DATA statements and
            # in the argument list of CALL statement.
            # Hollerith constants were removed from the Fortran 77 standard.
            # The following handling is not perfect but works for simple
            # usage cases.
            # todo: Handle hollerith constants in DATA statement
            if _IS_CALL_STMT(line):
                l2 = self.line[4:].lstrip()
                i = l2.find('(')
                if i != -1 and l2[-1] == ')':
                    substrings = ['call '+l2[:i+1]]
                    start_search = _HOLLERITH_START_SEARCH
                    l2 = l2[i+1:-1].strip()
                    m = start_search(l2)
                    while m:
                        substrings.append(l2[:m.start()])
                        substrings.append(m.group('pre'))
                        num = int(m.group('num'))
                        substrings.append("'"+l2[m.end():m.end()+num]+"'")
                        l2 = l2[m.end()+num:]
                        m = start_search(l2)
                    substrings.append(l2)
                    substrings.append(')')
                    line = ''.join(substrings)

        line, str_map = string_replace_map(line,
                                           lower=not self.reader.format.is_pyf)
        self.strline = line
        self.strlinemap = str_map
        return line

    def parse_line(self, cls, parent_cls):
        if cls not in self.parse_cache:
            self.parse_cache[cls] = None
            obj = cls(self.line, parent_cls=parent_cls)
            self.parse_cache[cls] = obj
        else:
            obj = self.parse_cache[cls]
        return obj

    def parse_block(self, reader, cls, parent_cls):
        key = cls, tuple(parent_cls)
        if key not in self.parse_cache:
            obj = cls(reader, parent_cls=parent_cls)
            self.parse_cache[key] = obj
        else:
            obj = self.parse_cache[key]
        return obj


class SyntaxErrorLine(Line, FortranReaderError):
    '''
    Indicates a syntax error while processing a line.
    '''
    def __init__(self, line, linenospan, label, name, reader, message):
        Line.__init__(self, line, linenospan, label, name, reader)
        FortranReaderError.__init__(self, message)


class Comment(object):
    """ Holds Fortran comment.

    Attributes
    ----------
    comment : str
      comment multiline string
    span : 2-tuple
      starting and ending line numbers
    reader : FortranReaderBase
    """
    def __init__(self, comment, linenospan, reader):
        self.comment = comment
        self.span = linenospan
        self.reader = reader

    def __repr__(self):
        return self.__class__.__name__+'(%r,%s)' \
               % (self.comment, self.span)

    def isempty(self, ignore_comments=False):
        '''
        Whether or not this comment is in fact empty (or we are ignoring
        it). Provided for compatibility with Line.isempty()

        :param bool ignore_comments: whether we ignore comments
        :return: True if we are ignoring comments, False otherwise
        :rtype: bool
        '''
        return ignore_comments


class MultiLine(object):
    """ Holds PYF file multiline.

    PYF file multiline is represented as follows::
      prefix+'''+lines+'''+suffix.

    Attributes
    ----------
    prefix : str
    block : list
      list of lines
    suffix : str
    span : 2-tuple
      starting and ending line numbers
    reader : FortranReaderBase
    """
    def __init__(self, prefix, block, suffix, linenospan, reader):
        self.prefix = prefix
        self.block = block
        self.suffix = suffix
        self.span = linenospan
        self.reader = reader

    def __repr__(self):
        string = '{cls}({prefix!r},{block},{suffix!r},{span})'
        return string.format(cls=self.__class__.__name__,
                             prefix=self.prefix,
                             block=self.block,
                             suffix=self.suffix,
                             span=self.span)

    def isempty(self, ignore_comments=False):
        '''
        Returns true if there is no significant text in this multi-line
        string.
        '''
        return not (self.prefix or self.block or self.suffix)


class SyntaxErrorMultiLine(MultiLine, FortranReaderError):
    '''
    Indicates a syntax error while processing Python multi-line strings.
    '''
    def __init__(self, prefix, block, suffix, linenospan, reader, message):
        MultiLine.__init__(self, prefix, block, suffix, linenospan, reader)
        FortranReaderError.__init__(self, message)


##############################################################################

class FortranReaderBase(object):
    """
    Base class for reading Fortran sources.

    A Fortran source must be a file-like object (have a ``.next()``
    method) and it may hold Fortran 77 code, fixed format Fortran
    code, free format Fortran code, or PYF signatures (with extended
    free format Fortran syntax).

    :param source: A file-like object with .next() method used to
                   retrive a line.
    :type source: either :py:class:`six.StringIO` or a file handle
    :param mode: A FortranFormat object as returned by
                 `sourceinfo.get_source_info()`
    :type mode: :py:class:`fparser.common.sourceinfo.Format`
    :param bool isstrict: Whether we are strictly enforcing fixed format
    :param bool ignore_comments: Whether or not to discard comments

    The Fortran source is iterated by `get_single_line`,
    `get_next_line`, `put_single_line` methods.

    """

    def __init__(self, source, mode, ignore_comments):
        self.source = source
        self._format = mode

        self.linecount = 0   # the current number of consumed lines
        self.isclosed = False
        # This value for ignore_comments can be overridden by using the
        # ignore_comments optional argument to e.g. get_single_line()
        self._ignore_comments = ignore_comments

        self.filo_line = []  # used for un-consuming lines.
        self.fifo_item = []
        self.source_lines = []  # source lines cache

        self.f2py_comment_lines = []  # line numbers of f2py directives

        self.reader = None
        self.include_dirs = ['.']

        self.source_only = None

        self.exit_on_error = True
        self.restore_cache = []

        return

    ##########################################################################

    def __repr__(self):
        return '%s(%r, %r, %r)' % (self.__class__.__name__,
                                   self.source,
                                   self._format.is_free,
                                   self._format.is_strict)

    def find_module_source_file(self, mod_name):
        '''
        Scans registered dependees for a named module.
        '''
        from .utils import get_module_file, module_in_file
        if self.source_only:
            for sf in self.source_only:
                if module_in_file(mod_name, sf):
                    return sf
        else:
            fn = None
            for d in self.include_dirs:
                fn = get_module_file(mod_name, d)
                if fn is not None:
                    return fn

    def set_format(self, mode):
        '''
        Set Fortran code mode (fixed/free format etc).

        :param mode: Object describing the desired mode for the reader
        :type mode: :py:class:`fparser.common.sourceinfo.FortranFormat`
        '''
        self._format = mode

    @property
    def format(self):
        '''
        :returns: the currently applicable format.
        :rtype: :py:class:`fparser.sourceinfo.FortranFormat`
        '''
        return self._format

    @property
    def name(self):
        '''
        :returns: the name of this reader.
        :rtype: str
        '''
        return '{source} mode={mode}'.format(source=self.source,
                                             mode=self._format.mode)

    def close_source(self):
        """ Called when self.source.next() raises StopIteration.
        """
        pass

    # For handling raw source lines:

    def put_single_line(self, line):
        """ Put single line to FILO line buffer.

        ``linecount`` will be decremented, that is, the line was
        returned by ``get_single_line`` call then it will be
        un-consumed.

        See also
        --------
        get_single_line, get_next_line
        """
        self.filo_line.append(line)
        self.linecount -= 1
        return

    def get_single_line(self, ignore_empty=False, ignore_comments=None):
        """ Return line from FILO line buffer or from source.

        First try getting the line from FILO line buffer.

        If FILO line buffer is empty then get the next line from
        source. Tabs in source line are expanded, ending blank and new
        line characters will be removed.  The source line will be
        added to ``source_lines`` list. If source line is empty then
        recursively get next non-empty line.

        In both situations ``linecount`` will be incremented, that is,
        the line will be consumed.

        :param bool ignore_empty: If True then ignore empty lines.
        :param bool ignore_comments: If True then ignore comments (overrides
                                     self._ignore_comments)

        See also
        --------
        put_single_line, get_next_line
        """
        if ignore_comments is None:
            ignore_comments = self._ignore_comments

        try:
            line = self.filo_line.pop()
            self.linecount += 1
            return line
        except IndexError:
            pass
        if self.isclosed:
            return None
        try:
            line = next(self.source)
        except StopIteration:
            self.isclosed = True
            self.close_source()
            return None
        self.linecount += 1
        # expand tabs, replace special symbols, get rid of nl characters
        line = line.expandtabs().replace('\xa0', ' ').rstrip()
        self.source_lines.append(line)

        if ignore_comments and (self.format.is_fixed or self.format.is_f77):
            # Check for a fixed-format comment. If the current line *is*
            # a comment and we are ignoring them, then recursively call this
            # routine again to get the next source line.
            if _is_fix_comment(line, isstrict=self.format.is_strict):
                return self.get_single_line(ignore_empty, ignore_comments)

        if ignore_empty and not line:
            return self.get_single_line(ignore_empty, ignore_comments)

        return line

    def get_next_line(self, ignore_empty=False, ignore_comments=None):
        """ Return next non-empty line from FILO line buffer or from source.

        The line will be put to FILO line buffer. So, this method can
        be used for looking forward lines without consuming them.

        See also
        --------
        get_single_line, put_single_line
        """
        if ignore_comments is None:
            ignore_comments = self._ignore_comments

        line = self.get_single_line(ignore_empty, ignore_comments)
        if line is None:
            return
        self.put_single_line(line)
        return line

    # Parser methods:
    def get_item(self, ignore_comments=None):
        """ Return next item.
        """
        if ignore_comments is None:
            ignore_comments = self._ignore_comments

        try:
            item = self.next(ignore_comments=ignore_comments)
        except StopIteration:
            return
        return item

    def put_item(self, item):
        """ Insert item to FIFO item buffer.
        """
        self.fifo_item.insert(0, item)
        return

    # Iterator methods:

    def __iter__(self):
        """ Make FortranReader an iterator.
        """
        return self

    def __next__(self):
        return self.next()

    def next(self, ignore_comments=None):
        """ Return the next Fortran code item.

        Include statements are realized.

        Parameters
        ----------
        ignore_comments : bool
          When True then act as if Fortran code does not contain
          any comments or blank lines.

        See also
        --------
        _next, get_source_item
        """
        if ignore_comments is None:
            ignore_comments = self._ignore_comments
        try:
            if self.reader is not None:
                # inside INCLUDE statement
                try:
                    return next(self.reader)
                except StopIteration:
                    self.reader = None
            item = self._next(ignore_comments)
            if isinstance(item, Line) and _IS_INCLUDE_LINE(item.line):
                # catch INCLUDE statement and create a new FortranReader
                # to enter to included file.
                reader = item.reader
                filename = item.line.strip()[7:].lstrip()[1:-1]
                include_dirs = self.include_dirs[:]
                path = filename
                for incl_dir in include_dirs:
                    path = os.path.join(incl_dir, filename)
                    if os.path.exists(path):
                        break
                if not os.path.isfile(path):  # include file does not exist
                    dirs = os.pathsep.join(include_dirs)
                    # According to Fortran standard, INCLUDE line is
                    # not a Fortran statement.
                    message = '{!r} not found in {!r}. ' \
                              + 'INLCUDE line treated as comment line.'
                    reader.warning(message.format(filename, dirs), item)
                    # Create a comment from the include statement
                    # TODO fix bugs so that we don't need this and/or
                    # support 'include' in fparser2 AST.
                    cmt = Comment("!UNTREATED " + item.line, item.span,
                                  item.reader)
                    return cmt
                    #item = self.next(ignore_comments)
                    #return item
                reader.info('including file %r' % (path), item)
                self.reader = FortranFileReader(
                    path,
                    include_dirs=include_dirs,
                    ignore_comments=ignore_comments)
                return self.reader.next(ignore_comments=ignore_comments)
            return item
        except StopIteration:
            raise
        # TODO can we specify one or more specific exception types
        # rather than catching *every* exception.
        except Exception as err:
            message = self.format_message('FATAL ERROR',
                                          'while processing line',
                                          self.linecount, self.linecount)
            logging.getLogger(__name__).critical(message)
            message = 'Traceback\n' + ''.join(traceback.format_stack())
            logging.getLogger(__name__).debug(message)
            logging.getLogger(__name__).debug(str(err))
            logging.getLogger(__name__).critical('STOPPED READING')
            raise StopIteration

    def _next(self, ignore_comments=None):
        """
        Return the next item from FIFO item buffer or construct
        one from source line.

        Resolves ``;`` statement terminations.

        :param bool ignore_comments: Whether or not to ignore comments
                                     (overrides self._ignore_comments)

        See also
        --------
        next, get_source_item
        """
        if ignore_comments is None:
            ignore_comments = self._ignore_comments
        fifo_item_pop = self.fifo_item.pop
        while 1:
            try:
                # first empty the FIFO item buffer:
                item = fifo_item_pop(0)
            except IndexError:
                # construct a new item from source
                item = self.get_source_item()
                if item is None:
                    raise StopIteration
            if not (item.isempty(ignore_comments)):
                break
            # else ignore empty lines and comments by getting next line

        if not isinstance(item, Comment):
            # resolve `;` statement terminations
            if not self._format.is_pyf and isinstance(item, Line) \
                   and not item.is_f2py_directive \
                   and ';' in item.get_line():
                # ;-separator not recognized in pyf-mode
                items = []
                for line in item.get_line().split(';'):
                    line = line.strip()
                    if line:
                        items.append(item.copy(line, apply_map=True))
                items.reverse()
                for newitem in items:
                    self.fifo_item.insert(0, newitem)
                return fifo_item_pop(0)
        return item

    # Interface to returned items:

    def line_item(self,
                  line,
                  startlineno,
                  endlineno,
                  label,
                  name,
                  errmessage=None):
        """ Construct Line item.
        """
        if errmessage is None:
            return Line(line, (startlineno, endlineno), label, name, self)
        return SyntaxErrorLine(line, (startlineno, endlineno),
                               label, name, self, errmessage)

    def multiline_item(self, prefix, lines, suffix,
                       startlineno, endlineno, errmessage=None):
        """ Construct MultiLine item.
        """
        if errmessage is None:
            return MultiLine(prefix,
                             lines,
                             suffix,
                             (startlineno, endlineno),
                             self)
        return SyntaxErrorMultiLine(prefix,
                                    lines,
                                    suffix,
                                    (startlineno, endlineno),
                                    self,
                                    errmessage)

    def comment_item(self, comment, startlineno, endlineno):
        """ Construct Comment item.
        """
        return Comment(comment, (startlineno, endlineno), self)

    # For handling messages:

    def format_message(self, kind, message, startlineno, endlineno,
                       startcolno=0, endcolno=-1):
        '''
        Prepares a string for logging.
        '''
        back_index = {'warning': 2,
                      'error': 3,
                      'info': 0}.get(kind.lower(), 3)
        r = ['While processing %r (mode=%r)..' % (self.id,
                                                  self._format.mode)]
        for i in range(max(1, startlineno - back_index), startlineno):
            r.append('%5d:%s' % (i, self.source_lines[i - 1]))
        for i in range(startlineno, min(endlineno+back_index,
                                        len(self.source_lines))+1):
            if i == 0 and not self.source_lines:
                break
            linenostr = '%5d:' % (i)
            if i == endlineno:
                sourceline = self.source_lines[i-1]
                l0 = linenostr+sourceline[:startcolno]
                if endcolno == -1:
                    l1 = sourceline[startcolno:]
                    l2 = ''
                else:
                    l1 = sourceline[startcolno:endcolno]
                    l2 = sourceline[endcolno:]
                r.append('%s%s%s <== %s' % (l0, l1, l2, message))
            else:
                r.append(linenostr + self.source_lines[i-1])
        return '\n'.join(r)

    def format_error_message(self, message, startlineno, endlineno,
                             startcolno=0, endcolno=-1):
        '''Create a string with an error message.'''
        return self.format_message('ERROR', message, startlineno,
                                   endlineno, startcolno, endcolno)

    def format_warning_message(self, message, startlineno, endlineno,
                               startcolno=0, endcolno=-1):
        '''Create a string with a warning message. '''
        return self.format_message('WARNING', message, startlineno,
                                   endlineno, startcolno, endcolno)

    def info(self, message, item=None):
        '''
        Logs an information message.
        '''
        if item is None:
            m = self.format_message('INFORMATION',
                                    message,
                                    len(self.source_lines)-2,
                                    len(self.source_lines))
        else:
            m = self.format_message('INFORMATION',
                                    message,
                                    item.span[0], item.span[1])
        logging.getLogger(__name__).info(m)
        return

    def error(self, message, item=None):
        '''
        Logs an error message.
        '''
        if item is None:
            m = self.format_error_message(message, len(self.source_lines)-2,
                                          len(self.source_lines))
        else:
            m = self.format_error_message(message, item.span[0], item.span[1])
        logging.getLogger(__name__).error(m)
        if self.exit_on_error:
            sys.exit(1)
        return

    def warning(self, message, item=None):
        '''
        Logs a warning message.
        '''
        if item is None:
            m = self.format_warning_message(message,
                                            len(self.source_lines) - 2,
                                            len(self.source_lines))
        else:
            m = self.format_warning_message(message,
                                            item.span[0],
                                            item.span[1])
        logging.getLogger(__name__).warning(m)
        return

    # Auxiliary methods for processing raw source lines:

    def handle_cf2py_start(self, line):
        """ Apply f2py directives to line.

        F2py directives are specified in the beginning of the line.

        f2py directives can be used only in Fortran codes.  They are
        ignored when used inside PYF files.

        Parameters
        ----------
        line : str

        Returns
        -------
        line : str
        """
        if not line or self._format.is_pyf:
            return line
        if self._format.is_fixed:
            if line[0] in '*cC!#':
                if line[1:5].lower() == 'f2py':
                    line = 5*' ' + line[5:]
                    self.f2py_comment_lines.append(self.linecount)
            if self._format.is_f77:
                return line
        m = _CF2PY_RE.match(line)
        if m:
            newline = m.group('indent')+5*' '+m.group('rest')
            self.f2py_comment_lines.append(self.linecount)
            assert len(newline) == len(line), repr((newline, line))
            return newline
        return line

    def handle_inline_comment(self, line, lineno, quotechar=None):
        """
        Any in-line comment is extracted from the line. If
        keep_inline_comments==True then the extracted comments are put back
        into the fifo sequence where they will subsequently be processed as
        a comment line.

        :param str line: line of code from which to remove in-line comment
        :param int lineno: line-no. in orig. file
        :param quotechar: String to use as character-string delimiter
        :type quotechar: {None, str}

        :return: line_with_no_comments, quotechar, had_comment
        :rtype: 3-tuple of str, str, bool
        """
        had_comment = False
        if quotechar is None and '!' not in line and \
           '"' not in line and "'" not in line:
            # There's no comment on this line
            return line, quotechar, had_comment

        idx = line.find('!')
        put_item = self.fifo_item.append
        if quotechar is None and idx != -1:
            # first try a quick method:
            newline = line[:idx]
            if '"' not in newline and '\'' not in newline:
                if self.format.is_f77 or not line[idx:].startswith('!f2py'):
                    put_item(self.comment_item(line[idx:], lineno, lineno))
                    return newline, quotechar, True

        # We must allow for quotes...
        items, newquotechar = splitquote(line, quotechar)
        noncomment_items = []
        noncomment_items_append = noncomment_items.append
        n = len(items)
        commentline = None
        for k in range(n):
            item = items[k]
            if isinstance(item, String) or '!' not in item:
                noncomment_items_append(item)
                continue
            j = item.find('!')
            noncomment_items_append(item[:j])
            items[k] = item[j:]
            commentline = ''.join(items[k:])
            break
        if commentline is not None:
            if commentline.startswith('!f2py'):
                # go to next iteration:
                newline = ''.join(noncomment_items) + commentline[5:]
                self.f2py_comment_lines.append(lineno)
                return self.handle_inline_comment(newline, lineno, quotechar)
            put_item(self.comment_item(commentline, lineno, lineno))
            had_comment = True
        return ''.join(noncomment_items), newquotechar, had_comment

    def handle_multilines(self, line, startlineno, mlstr):
        '''
        Examines line for Python triple quote strings (f2py feature).

        :param str line: line of Fortran source text
        :param int startlineno: the number of the line on which this
                                 multi-line string began.
        :param list mlstr: list of delimiters for a multi-line string
                           (e.g. '"""')
        '''
        i = line.find(mlstr)
        if i != -1:
            prefix = line[:i]
            # skip fake multiline starts
            p, k = prefix, 0
            while p.endswith('\\'):
                p, k = p[:-1], k + 1
            if k % 2:
                return
        if i != -1 and '!' not in prefix:
            # Note character constants like 'abc"""123',
            # so multiline prefix should better not contain `'' or `"' not `!'.
            for quote in '"\'':
                if prefix.count(quote) % 2:
                    message = 'multiline prefix contains odd number of' \
                              + ' {!r} characters'.format(quote)
                    message = self.format_warning_message(message,
                                                          startlineno,
                                                          startlineno,
                                                          0,
                                                          len(prefix))
                    logging.getLogger(__name__).warning(message)

            suffix = None
            multilines = []
            line = line[i+3:]
            while line is not None:
                j = line.find(mlstr)
                if j != -1 and '!' not in line[:j]:
                    multilines.append(line[:j])
                    suffix = line[j+3:]
                    break
                multilines.append(line)
                line = self.get_single_line()
            if line is None:
                message = 'multiline block never ends'
                message = self.format_error_message(message,
                                                    startlineno,
                                                    startlineno,
                                                    i)
                return self.multiline_item(prefix,
                                           multilines,
                                           suffix,
                                           startlineno,
                                           self.linecount,
                                           message)
            suffix, qc, had_comment \
                = self.handle_inline_comment(suffix, self.linecount)
            # no line continuation allowed in multiline suffix
            if qc is not None:
                message = 'following character continuation: {!r},' \
                          + ' expected None.'
                message = self.format_message('ASSERTION FAILURE(pyf)',
                                              message.format(qc),
                                              startlineno,
                                              self.linecount)
                logging.getLogger(__name__).warning(message)
            # XXX: should we do line.replace('\\'+mlstr[0],mlstr[0])
            #      for line in multilines?
            return self.multiline_item(prefix,
                                       multilines,
                                       suffix,
                                       startlineno,
                                       self.linecount)

    # The main method of interpreting raw source lines within
    # the following contexts: f77, fixed, free, pyf.

    def get_source_item(self):
        """ Return next source item.

        A source item is ..
        - a fortran line
        - a list of continued fortran lines
        - a multiline - lines inside triple-qoutes, only when in ispyf mode
        - a comment line
        """
        get_single_line = self.get_single_line
        line = get_single_line()
        if line is None:
            return
        startlineno = self.linecount
        line = self.handle_cf2py_start(line)
        is_f2py_directive = startlineno in self.f2py_comment_lines
        isstrict = self._format.is_strict
        have_comment = False
        label = None
        name = None

        if self._format.is_pyf:
            # handle multilines
            for mlstr in ['"""', "'''"]:
                r = self.handle_multilines(line, startlineno, mlstr)
                if r:
                    return r
        if self._format.is_fixed:
            if _is_fix_comment(line, isstrict):
                # comment line:
                return self.comment_item(line, startlineno, startlineno)

            for i in range(min(5, len(line))):
                # check that fixed format line starts according to Fortran
                # standard
                if line[i] not in _SPACEDIGITS:
                    message = 'non-space/digit char %r found in column %i'\
                              ' of fixed Fortran code' % (line[i], i + 1)
                    if i == 0:
                        message += ', interpreting line as comment line'
                    if self._format.is_fix:
                        if i != 0:
                            message += ', switching to free format mode'
                        message = self.format_warning_message(message,
                                                              startlineno,
                                                              self.linecount)
                        logging.getLogger(__name__).warning(message)
                        if i == 0:
                            # non standard comment line:
                            return self.comment_item(line,
                                                     startlineno,
                                                     startlineno)
                        mode = fparser.common.sourceinfo.FortranFormat(True,
                                                                       False)
                        self.set_format(mode)
                    else:
                        message = self.format_warning_message(message,
                                                              startlineno,
                                                              self.linecount)
                        logging.getLogger(__name__).warning(message)
                        if i == 0:
                            # non standard comment line:
                            return self.comment_item(line,
                                                     startlineno,
                                                     startlineno)
                        # return line item with error message
                        # TODO: handle cases with line[6:]==''
                        message = self.format_error_message(message,
                                                            startlineno,
                                                            self.linecount)
                        return self.line_item(line[6:],
                                              startlineno,
                                              self.linecount,
                                              label,
                                              name,
                                              message)
            if self._format.is_fixed:  # Check for switched to free format
                # check for label
                s = line[:5].strip().lower()
                if s:
                    label = int(s)
                if not self._format.is_f77:
                    m = _CONSTRUCT_NAME_RE.match(line[6:])
                    if m:
                        name = m.group('name')
                        line = line[:6] + line[6:][m.end():].lstrip()
                if not line[6:].strip():
                    # check for a blank line
                    if name is not None:
                        self.error('No construct following construct-name.')
                    elif label is not None:
                        self.warning('Label must follow nonblank character'
                                     + ' (F2008:3.2.5_2)')
                    return self.comment_item('', startlineno, self.linecount)
                # line is not a comment and the start of the line is valid

        if self._format.is_f77 and not is_f2py_directive:
            # Fortran 77 is easy..
            lines = [line[6:72]]
            # get_next_line does not actually consume lines - they are put
            # into the FILO buffer as well as being returned. This means
            # that we can ignore comments for the purposes of dealing
            # with the continued line and then handle them as though they
            # follow on after the single line constructed from the multiple
            # continued lines.
            while _is_fix_cont(self.get_next_line(ignore_empty=True,
                                                  ignore_comments=True)):
                # handle fix format line continuations for F77 code
                line = get_single_line()
                lines.append(line[6:72])
            return self.line_item(''.join(lines), startlineno,
                                  self.linecount, label, name)

        handle_inline_comment = self.handle_inline_comment

        endlineno = self.linecount
        if self._format.is_fix and not is_f2py_directive:
            # handle inline comment
            newline, qc, had_comment = handle_inline_comment(line[6:],
                                                             startlineno)
            have_comment |= had_comment
            lines = [newline]
            next_line = self.get_next_line()

            while _is_fix_cont(next_line) or _is_fix_comment(next_line,
                                                             isstrict):
                # handle fix format line continuations for F90 or
                # newer code.  Mixing fix format and free format line
                # continuations is not allowed nor detected, just
                # eject warnings.
                line2 = get_single_line()  # consume next_line as line2
                if _is_fix_comment(line2, isstrict):
                    # handle fix format comments inside line continuations
                    # after the line construction
                    citem = self.comment_item(line2,
                                              self.linecount,
                                              self.linecount)
                    self.fifo_item.append(citem)
                else:
                    # line continuation
                    newline, qc, had_comment \
                        = self.handle_inline_comment(line2[6:],
                                                     self.linecount,
                                                     qc)
                    have_comment |= had_comment
                    lines.append(newline)
                    endlineno = self.linecount
                next_line = self.get_next_line()
            # no character continuation should follows now
            if qc is not None:
                message = 'following character continuation: ' \
                          + '{!r}, expected None.'
                message = self.format_message('ASSERTION FAILURE(fix)',
                                              message.format(qc),
                                              startlineno,
                                              self.linecount)
                logging.getLogger(__name__).warning(message)
            if len(lines) > 1:
                for i in range(len(lines)):
                    line = lines[i]
                    if line.rstrip().endswith('&'):
                        message = 'free format line continuation character ' \
                                  + "`&' detected in fix format code"
                        location = line.rfind('&') + 5
                        message = self.format_warning_message(message,
                                                              startlineno + i,
                                                              startlineno + i,
                                                              location)
                        logging.getLogger(__name__).warning(message)
            return self.line_item(''.join(lines),
                                  startlineno,
                                  endlineno,
                                  label,
                                  name)

        # line is free format or fixed format with f2py directive (that
        # will be interpretted as free format line).

        start_index = 0
        if self._format.is_fix:
            start_index = 6
        lines = []
        lines_append = lines.append
        put_item = self.fifo_item.append
        qc = None
        while line is not None:
            if start_index:  # fix format code
                line, qc, had_comment \
                    = handle_inline_comment(line[start_index:],
                                            self.linecount, qc)
                have_comment |= had_comment
                is_f2py_directive = self.linecount in self.f2py_comment_lines
            else:
                # free format
                line_lstrip = line.lstrip()
                if lines:
                    if line_lstrip.startswith('!'):
                        # check for comment line within line continuation
                        put_item(self.comment_item(line_lstrip,
                                                   self.linecount,
                                                   self.linecount))
                        have_comment = True
                        line = get_single_line()
                        continue
                    elif line_lstrip == "":
                        # skip blank lines within a line continuation
                        line = get_single_line()
                        continue
                else:
                    # first line, check for a label
                    m = _LABEL_RE.match(line)
                    if m:
                        assert not label, repr(label)
                        label = int(m.group('label'))
                        line = line[m.end():]
                    # check for a construct name
                    m = _CONSTRUCT_NAME_RE.match(line)
                    if m:
                        name = m.group('name')
                        line = line[m.end():].lstrip()
                line, qc, had_comment = handle_inline_comment(line,
                                                              self.linecount,
                                                              qc)
                have_comment |= had_comment
                is_f2py_directive = self.linecount in self.f2py_comment_lines

            i = line.rfind('&')
            if i != -1:
                line_i1_rstrip = line[i+1:].rstrip()
            if not lines:
                # first line
                if i == -1 or line_i1_rstrip:
                    lines_append(line)
                    break
                endlineno = self.linecount
                lines_append(line[:i])
                line = get_single_line()
                continue
            if i == -1 or line_i1_rstrip:
                # no line continuation follows
                i = len(line)
            k = -1
            if i != -1:
                # handle the beggining of continued line
                k = line[:i].find('&')
                if k != 1 and line[:k].lstrip():
                    k = -1
            endlineno = self.linecount
            lines_append(line[k+1:i])
            if i == len(line):
                break
            line = get_single_line()

        if qc is not None:
            message = 'following character continuation: {!r}, ' \
                      + 'expected None.'
            message = self.format_message('ASSERTION FAILURE(free)',
                                          message.format(qc),
                                          startlineno,
                                          endlineno)
            logging.getLogger(__name__).error(message)
        line_content = ''.join(lines).strip()
        if line_content:
            return self.line_item(line_content,
                                  startlineno,
                                  endlineno,
                                  label,
                                  name)
        if label is not None:
            message = 'Label must follow nonblank character (F2008:3.2.5_2)'
            self.warning(message)
        if name is not None:
            self.error('No construct following construct-name.')
        if have_comment:
            return next(self)
        return self.comment_item('', startlineno, endlineno)


class FortranFileReader(FortranReaderBase):
    '''
    Constructs a FortranFileReader object from a file.

    :param file_candidate: A filename or file-like object.
    :param list include_dirs: Directories in which to look for inclusions.
    :param list source_only: Fortran source files to search for modules
                             required by "use" statements.
    :param bool ignore_comments: Whether or not to ignore comments

    For example:

    >>> from fparser.common.readfortran import FortranFileReader
    >>> import os
    >>> reader = FortranFileReader(\'myfile.f90\')

    '''
    def __init__(self, file_candidate, include_dirs=None, source_only=None,
                 ignore_comments=True):
        if isinstance(file_candidate, six.string_types):
            self.id = file_candidate
            self.file = open(file_candidate, 'r')
            self._close_on_destruction = True
        elif hasattr(file_candidate,
                     'read') and hasattr(file_candidate,
                                         'name'):  # Is likely a file
            self.id = file_candidate.name
            self.file = file_candidate
            self._close_on_destruction = False
        else:  # Probably not something we can deal with
            message = 'FortranFileReader is used with a filename'
            message += ' or file-like object.'
            raise ValueError(message)
        mode = fparser.common.sourceinfo.get_source_info(file_candidate)

        FortranReaderBase.__init__(self, self.file, mode, ignore_comments)

        if include_dirs is None:
            self.include_dirs.insert(0, os.path.dirname(self.id))
        else:
            self.include_dirs = include_dirs[:]
        if source_only is not None:
            self.source_only = source_only[:]
        return

    def __del__(self):
        if self._close_on_destruction:
            self.file.close()

    def close_source(self):
        self.file.close()


class FortranStringReader(FortranReaderBase):
    '''
    Reads Fortran source code as a string.

    :param str string: string to read
    :param list include_dirs: List of dirs to search for include files
    :param list source_only: Fortran source files to search for modules
                             required by "use" statements.
    :param bool ignore_comments: Whether or not to ignore comments

    For example:

    >>> from fparser.common.readfortran import FortranStringReader
    >>> code = \'\'\'
             subroutine foo(a)
                integer a
                print*,\"a=\",a
              end
        \'\'\'
    >>> reader = FortranStringReader(code) 

    '''
    def __init__(self, string, include_dirs=None, source_only=None,
                 ignore_comments=True):
        self.id = 'string-' + str(id(string))
        source = six.StringIO(string)
        mode = fparser.common.sourceinfo.get_source_info_str(string)
        FortranReaderBase.__init__(self, source, mode,
                                   ignore_comments)
        if include_dirs is not None:
            self.include_dirs = include_dirs[:]
        if source_only is not None:
            self.source_only = source_only[:]
        return
