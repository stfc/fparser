# Modified work Copyright (c) 2017-2020 Science and Technology
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

'''Base classes and exception handling for Fortran parser

'''
# Original author: Pearu Peterson <pearu@cens.ioc.ee>
# First version created: Oct 2006

import re
import logging
import six
from fparser.common.splitline import string_replace_map
from fparser.two import pattern_tools as pattern
from fparser.common.readfortran import FortranReaderBase


# A list of supported extensions to the standard(s)

# An X edit descriptor in a format statement specifies the position
# (forward from the current position) at which the next character will
# be transmitted to or from a record. In standard Fortran2003 the X
# edit descriptor must be preceeded by an integer which specifies how
# far forward from the current position. The 'x-format' extension
# allows the X edit descriptor to be specified without a preceeding
# integer.
EXTENSIONS = ["x-format"]

# Cray pointers are a well known extension to the Fortran
# standard. See http://pubs.cray.com/content/S-3901/8.6/
# cray-fortran-reference-manual-s-3901-86/types or
# https://gcc.gnu.org/onlinedocs/gfortran/Cray-pointers.html for
# example. If 'cray-pointer' is specified in EXTENSIONS then this
# extension is allowed in fparser.
EXTENSIONS += ["cray-pointer"]

# A Hollerith constant is a way of specifying a string as a sequence
# of characters preceded by the string length and separated by an 'H'
# e.g. 5Hhello. See
# https://gcc.gnu.org/onlinedocs/gfortran/Hollerith-constants-support.html,
# for example for more details. fparser currently supports Hollerith
# constants specified in format statements when 'hollerith' is specified
# in the EXTENSIONS list.
EXTENSIONS += ["hollerith"]

# Many compilers support the use of '$' in a fortran write statement
# to indicate that the carriage return should be suppressed. This is
# an extension to the Fortran standard and is supported by fparser if
# 'dollar-descriptor' is specified in the EXTENSIONS list.
EXTENSIONS += ["dollar-descriptor"]


def py2_encode_list_items(mylist):
    '''
    If we are running under Python2 then ensure that all strings in the
    supplied list are encoded as bytes. If we are running under Python3
    then all strings are unicode and this routine does nothing.

    :param list mylist: List of strings to modify.

    '''
    if six.PY2:
        # If we're in Python2 then we have to take care as comments
        # and character literals may be UTF while other elements are not.
        for idx, item in enumerate(mylist[:]):
            if isinstance(item, six.text_type):
                # This item is UTF so encode it as bytes
                mylist[idx] = item.encode('utf-8')


class FparserException(Exception):
    '''Base class exception for fparser. This allows an external tool to
    capture all exceptions if required.

    :param str info: a string giving contextual error information.

    '''
    def __init__(self, info):
        Exception.__init__(self, info)


class NoMatchError(FparserException):
    '''An exception indicating that a particular rule implemented by a
    class does not match the provided string. It does not necessary
    mean there is an error as another rule may match. This exception
    is used internally so should never be visible externally.

    '''


class FortranSyntaxError(FparserException):
    '''An exception indicating that fparser believes the provided code to
    be invalid Fortran. Also returns information about the location of
    the error if that information is available.

    :param reader: input string or reader where the error took \
    place. This is used to provide line number and line content \
    information.
    :type reader: str or :py:class:`FortranReaderBase`
    :param str info: a string giving contextual error information.

    '''
    def __init__(self, reader, info):
        output = "at unknown location "
        if isinstance(reader, FortranReaderBase):
            output = "at line {0}\n>>>{1}\n".format(
                reader.linecount,
                reader.source_lines[reader.linecount-1])
        if info:
            output += "{0}".format(info)
        FparserException.__init__(self, output)


class InternalError(FparserException):
    '''An exception indicating that an unexpected error has occured in the
    parser.

    :param str info: a string giving contextual error information.

    '''
    def __init__(self, info):
        new_info = ("'{0}'. Please report this to the "
                    "authors.".format(info))
        FparserException.__init__(self, new_info)


class InternalSyntaxError(FparserException):
    '''An exception indicating that a syntax error has been found by the
    parser. This is used instead of `FortranSyntaxError` when the
    reader object is not available.

    '''


def show_result(func):
    return func

    def new_func(cls, string, **kws):
        r = func(cls, string, **kws)
        if r is not None and isinstance(r, StmtBase):
            print('%s(%r) -> %r' % (cls.__name__, string, str(r)))
        return r
    return new_func


#
# BASE CLASSES
#


class ComparableMixin(object):
    """ Mixin class to provide rich comparison operators.

    This mixin provides a set of rich comparison operators. Each class using
    this mixin has to provide a _cmpkey() method that returns a key of objects
    that can be compared.

    See also http://python3porting.com/preparing.html#richcomparisons
    """
    # pylint: disable=too-few-public-methods

    def _compare(self, other, method):
        """ Call the method, if other is able to be used within it.

        :param object other: The other object to compare with
        :type other: object
        :param method: The method to call to compare self and other.
        :type method: LambdaType
        :return: NotImplemented, when the comparison for the given type
                 combination can't be performed.
        :rtype: :py:type:`NotImplementedType`
        """
        try:
            # This routine's purpose is to access the protected method
            # _cmpkey() from client classes, therefore: pylint:
            # disable=protected-access
            return method(self._cmpkey(), other._cmpkey())
        except (AttributeError, TypeError):
            # _cmpkey not implemented, or return different type,
            # so I can't compare with "other".
            # According to the Python Language Reference Manual
            # (http://www.network-theory.co.uk/docs/pylang/Coercionrules.html)
            # return NotImplemented
            return NotImplemented

    def __lt__(self, other):
        return self._compare(other, lambda s, o: s < o)

    def __le__(self, other):
        return self._compare(other, lambda s, o: s <= o)

    def __eq__(self, other):
        return self._compare(other, lambda s, o: s == o)

    def __ge__(self, other):
        return self._compare(other, lambda s, o: s >= o)

    def __gt__(self, other):
        return self._compare(other, lambda s, o: s > o)

    def __ne__(self, other):
        return self._compare(other, lambda s, o: s != o)


class Base(ComparableMixin):
    ''' Base class for Fortran 2003 syntax rules.

    All Base classes have the following attributes:
      self.string - original argument to construct a class instance, its type \
                    is either str or FortranReaderBase.
      self.item   - Line instance (holds label) or None.

    :param type cls: the class of object to create.
    :param string: (source of) Fortran string to parse.
    :type string: `str` or \
                  :py:class:`fparser.common.readfortran.FortranReaderBase`
    :param parent_cls: the parent class of this object.
    :type parent_cls: `type`

    '''
    # This dict of subclasses is populated dynamically by code at the end
    # of this module. That code uses the entries in the
    # 'subclass_names' list belonging to each class defined in this module.
    subclasses = {}

    def __init__(self, string, parent_cls=None):
        # pylint:disable=unused-argument
        self.parent = None

    @show_result
    def __new__(cls, string, parent_cls=None):

        def _set_parent(parent_node, items):
            ''' Recursively set the parent of all of the elements
            in the list that are a sub-class of Base. (Recursive because
            sometimes the list of elements itself contains a list or tuple.)

            :param parent_node: the parent of the nodes listed in `items`.
            :type parent_node: sub-class of :py:class:`fparser.two.utils.Base`
            :param items: list or tuple of nodes for which to set the parent.
            :type items: list or tuple of :py:class:`fparser.two.utils.Base` \
                         or `str` or `list` or `tuple` or NoneType.
            '''
            for item in items:
                if item:
                    if isinstance(item, Base):
                        # We can only set the parent of `Base` objects.
                        # Anything else (e.g. str) is passed over.
                        item.parent = parent_node
                    elif isinstance(item, (list, tuple)):
                        _set_parent(parent_node, item)
        # ------------------------------------------------------------------

        from fparser.common import readfortran
        if parent_cls is None:
            parent_cls = [cls]
        elif cls not in parent_cls:
            parent_cls.append(cls)

        # Get the class' match method if it has one
        match = cls.__dict__.get('match')

        if isinstance(string, FortranReaderBase) and \
           match and not issubclass(cls, BlockBase):
            reader = string
            item = reader.get_item()
            if item is None:
                return None
            if isinstance(item, readfortran.Comment):
                # We got a comment but we weren't after a comment (we handle
                # those in Comment.__new__)
                obj = None
            else:
                try:
                    obj = item.parse_line(cls, parent_cls)
                except NoMatchError:
                    obj = None
            if obj is None:
                # No match so give the item back to the reader
                reader.put_item(item)
                return None
            obj.item = item
            return obj

        result = None
        if match:
            # IMPORTANT: if string is FortranReaderBase then cls must
            # restore readers content when no match is found.
            try:
                result = cls.match(string)
            except NoMatchError as msg:
                if str(msg) == '%s: %r' % (cls.__name__, string):
                    # avoid recursion 1.
                    raise

        if isinstance(result, tuple):
            obj = object.__new__(cls)
            obj.string = string
            obj.item = None
            # Set-up parent information for the results of the match
            _set_parent(obj, result)
            if hasattr(cls, 'init'):
                obj.init(*result)
            return obj
        elif isinstance(result, Base):
            return result
        elif result is None:
            # Loop over the possible sub-classes of this class and
            # check for matches
            for subcls in Base.subclasses.get(cls.__name__, []):
                if subcls in parent_cls:  # avoid recursion 2.
                    continue
                try:
                    obj = subcls(string, parent_cls=parent_cls)
                except NoMatchError as msg:
                    obj = None
                if obj is not None:
                    return obj
        else:
            raise AssertionError(repr(result))
        # If we get to here then we've failed to match the current line
        if isinstance(string, FortranReaderBase):
            content = False
            for index in range(string.linecount):
                # Check all lines up to this one for content. We
                # should be able to only check the current line but
                # but as the line number returned is not always
                # correct (due to coding errors) we cannot assume the
                # line pointed to is the line where the error actually
                # happened.
                if string.source_lines[index].strip():
                    content = True
                    break
            if not content:
                # There are no lines in the input or all lines up to
                # this one are empty or contain only white space. This
                # is typically accepted by fortran compilers so we
                # follow their lead and do not raise an exception.
                return
            line = string.source_lines[string.linecount-1]
            errmsg = u"at line {0}\n>>>{1}\n".format(
                string.linecount, line)
        else:
            errmsg = u"{0}: '{1}'".format(cls.__name__, string)
        raise NoMatchError(errmsg)

    def get_root(self):
        '''
        Gets the node at the root of the parse tree to which this node belongs.

        :returns: the node at the root of the parse tree.
        :rtype: :py:class:`fparser.two.utils.Base`

        '''
        current = self
        while current.parent:
            current = current.parent
        return current

    @property
    def children(self):
        '''Return an iterable containing the immediate children of this node in
        the parse tree.

        If this node represents an expression then its children are
        contained in a tuple which is immutable. Therefore, the
        manipulation of the children of such a node must be done by
        replacing the `items` property of the node directly rather than via the
        objects returned by this method.

        :returns: the immediate children of this node.
        :rtype: list or tuple containing zero or more of \
                :py:class:`fparser.two.utils.Base` or NoneType or str

        '''
        child_list = getattr(self, 'content', None)
        if child_list is None:
            child_list = getattr(self, 'items', [])
        return child_list

    def init(self, *items):
        '''
        Store the supplied list of nodes in the `items` list of this node.

        :param items: the children of this node.
        :type items: tuple of :py:class:`fparser.two.utils.Base`

        '''
        self.items = items

    def torepr(self):
        return '%s(%s)' % (self.__class__.__name__, ', '.join(map(repr,
                                                                  self.items)))

    def __str__(self):
        return self.tostr()

    def __repr__(self):
        return self.torepr()

    def _cmpkey(self):
        """ Provides a key of objects to be used for comparing.
        """
        return self.items

    def tofortran(self, tab='', isfix=None):
        '''
        Produce the Fortran representation of this Comment.

        :param str tab: characters to pre-pend to output.
        :param bool isfix: whether or not this is fixed-format code.

        :returns: Fortran representation of this comment.
        :rtype: str
        '''
        this_str = six.text_type(self)
        if this_str.strip():
            return tab + this_str
        else:
            # If this_str is empty (i.e this Comment is a blank line) then
            # don't prepend any spaces to it
            return this_str

    def restore_reader(self, reader):
        reader.put_item(self.item)


class BlockBase(Base):
    """
::
    <block-base> = [ <startcls> ]
                     [ <subcls> ]...
                     ...
                     [ <subcls> ]...
                     [ <endcls> ]

content : tuple
    """
    @staticmethod
    def match(startcls, subclasses, endcls, reader,
              match_labels=False,
              match_names=False,
              match_name_classes=(),
              enable_do_label_construct_hook=False,
              enable_if_construct_hook=False,
              enable_where_construct_hook=False,
              enable_select_type_construct_hook=False,
              enable_case_construct_hook=False,
              strict_order=False):
        '''
        Checks whether the content in reader matches the given
        type of block statement (e.g. DO..END DO, IF...END IF etc.)

        :param type startcls: The class marking the beginning of the block
        :param list subclasses: List of classes that can be children of
                                the block
        :param type endcls: The class marking the end of the block
        :param reader: Content to check for match
        :type reader: str or instance of :py:class:`FortranReaderBase`
        :param bool match_labels: TBD
        :param bool match_names: TBD
        :param tuple match_name_classes: TBD
        :param bool enable_do_label_construct_hook: TBD
        :param bool enable_if_construct_hook: TBD
        :param bool enable_where_construct_hook: TBD
        :param bool enable_select_type_construct_hook: TBD
        :param bool enable_case_construct_hook: TBD
        :param bool strict_order: Whether to enforce the order of the
                                  given subclasses.

        :return: instance of startcls or None if no match is found
        :rtype: startcls
        '''
        from fparser.two.Fortran2003 import Comment, Include_Stmt, \
            add_comments_includes
        assert isinstance(reader, FortranReaderBase), repr(reader)
        content = []

        if startcls is not None:
            # Deal with any preceding comments and/or includes
            add_comments_includes(content, reader)
            # Now attempt to match the start of the block
            try:
                obj = startcls(reader)
            except NoMatchError:
                obj = None
            if obj is None:
                # Ultimately we failed to find a match for the
                # start of the block so put back any comments that
                # we processed along the way
                for obj in reversed(content):
                    obj.restore_reader(reader)
                return
            # Store the index of the start of this block proper (i.e.
            # excluding any comments)
            start_idx = len(content)
            content.append(obj)

            if enable_do_label_construct_hook:
                start_label = obj.get_start_label()
            if match_names:
                start_name = obj.get_start_name()

        # Comments and Include statements are always valid sub-classes
        classes = subclasses + [Comment, Include_Stmt]
        if endcls is not None:
            classes += [endcls]
            endcls_all = tuple([endcls]+endcls.subclasses[endcls.__name__])

        # Start trying to match the various subclasses, starting from
        # the beginning of the list (where else?)
        i = 0
        had_match = False
        found_end = False
        while i < len(classes):
            if enable_do_label_construct_hook:
                try:
                    obj = startcls(reader)
                except NoMatchError:
                    obj = None
                if obj is not None:
                    if start_label == obj.get_start_label():
                        content.append(obj)
                        continue
                    else:
                        obj.restore_reader(reader)
            # Attempt to match the i'th subclass
            cls = classes[i]
            try:
                obj = cls(reader)
            except NoMatchError:
                obj = None
            if obj is None:
                # No match for this class, continue checking the list
                # starting from the i+1'th...
                i += 1
                continue

            # We got a match for this class
            had_match = True
            content.append(obj)

            if match_names and isinstance(obj, match_name_classes):
                end_name = obj.get_end_name()
                if end_name and not start_name:
                    raise FortranSyntaxError(
                        reader, "Name '{0}' has no corresponding starting "
                        "name".format(end_name))
                if end_name and start_name and \
                   end_name.lower() != start_name.lower():
                    raise FortranSyntaxError(
                        reader, "Expecting name '{0}'".format(start_name))

            if endcls is not None and isinstance(obj, endcls_all):
                if match_labels:
                    start_label, end_label = content[start_idx].\
                                             get_start_label(),\
                                             content[-1].get_end_label()
                    if start_label != end_label:
                        continue
                if match_names:
                    start_name, end_name = content[start_idx].\
                                           get_start_name(), \
                                           content[-1].get_end_name()
                    if end_name and not start_name:
                        raise FortranSyntaxError(
                            reader, "Name '{0}' has no corresponding starting "
                            "name".format(end_name))
                    elif start_name and end_name and (start_name.lower() !=
                                                      end_name.lower()):
                        raise FortranSyntaxError(
                            reader, "Expecting name '{0}'".format(start_name))
                # We've found the enclosing end statement so break out
                found_end = True
                break
            if not strict_order:
                # Return to start of classes list now that we've matched.
                i = 0
            if enable_if_construct_hook:
                from fparser.two.Fortran2003 import Else_If_Stmt, Else_Stmt, \
                    End_If_Stmt
                if isinstance(obj, Else_If_Stmt):
                    # Got an else-if so go back to start of possible
                    # classes to match
                    i = 0
                if isinstance(obj, (Else_Stmt, End_If_Stmt)):
                    # Found end-if
                    enable_if_construct_hook = False
            if enable_where_construct_hook:
                from fparser.two.Fortran2003 import Masked_Elsewhere_Stmt, \
                    Elsewhere_Stmt, End_Where_Stmt
                if isinstance(obj, Masked_Elsewhere_Stmt):
                    i = 0
                if isinstance(obj, (Elsewhere_Stmt, End_Where_Stmt)):
                    enable_where_construct_hook = False
            if enable_select_type_construct_hook:
                from fparser.two.Fortran2003 import Type_Guard_Stmt, \
                    End_Select_Type_Stmt
                if isinstance(obj, Type_Guard_Stmt):
                    i = 1
                if isinstance(obj, End_Select_Type_Stmt):
                    enable_select_type_construct_hook = False
            if enable_case_construct_hook:
                from fparser.two.Fortran2003 import Case_Stmt, \
                    End_Select_Stmt
                if isinstance(obj, Case_Stmt):
                    i = 1
                if isinstance(obj, End_Select_Stmt):
                    enable_case_construct_hook = False
            continue

        if not had_match or endcls and not found_end:
            # We did not get a match from any of the subclasses or
            # failed to find the endcls
            if endcls is not None:
                for obj in reversed(content):
                    obj.restore_reader(reader)
                return

        if not content:
            return
        if startcls is not None and endcls is not None:
            # check names of start and end statements:
            start_stmt = content[start_idx]
            end_stmt = content[-1]
            if isinstance(end_stmt, endcls_all) and \
               hasattr(end_stmt, 'get_name') and \
               hasattr(start_stmt, 'get_name'):
                if end_stmt.get_name() is not None:
                    if start_stmt.get_name().string.lower() != \
                       end_stmt.get_name().string.lower():
                        end_stmt.item.reader.error(
                            'expected <%s-name> is %s but got %s. Ignoring.'
                            % (end_stmt.get_type().lower(),
                               start_stmt.get_name(), end_stmt.get_name()))
        return (content,)

    def init(self, content):
        '''
        Initialise the `content` attribute with the list of child nodes.

        :param content: list of nodes that are children of this one.
        :type content: list of :py:class:`fparser.two.utils.Base` or NoneType

        '''
        self.content = content

    def _cmpkey(self):
        """ Provides a key of objects to be used for comparing.
        """
        return self.content

    def tostr(self):
        return self.tofortran()

    def torepr(self):
        return '%s(%s)' % (self.__class__.__name__, ', '.
                           join(map(repr, self.content)))

    def tofortran(self, tab='', isfix=None):
        '''
        Create a string containing the Fortran representation of this class

        :param str tab: indent to prefix to code.
        :param bool isfix: whether or not to generate fixed-format code.

        :return: Fortran representation of this class.
        :rtype: str
        '''
        mylist = []
        start = self.content[0]
        end = self.content[-1]
        extra_tab = ''
        if isinstance(end, EndStmtBase):
            extra_tab = '  '
        if start is not None:
            mylist.append(start.tofortran(tab=tab, isfix=isfix))
        for item in self.content[1:-1]:
            mylist.append(item.tofortran(tab=tab+extra_tab, isfix=isfix))
        if len(self.content) > 1:
            mylist.append(end.tofortran(tab=tab, isfix=isfix))
        # Ensure all strings in list are encoded consistently
        py2_encode_list_items(mylist)
        return '\n'.join(mylist)

    def restore_reader(self, reader):
        for obj in reversed(self.content):
            obj.restore_reader(reader)


class SequenceBase(Base):
    '''
    Match one or more fparser2 rules separated by a defined separator.

    sequence-base is obj [sep obj ] ...

    '''
    @staticmethod
    def match(separator, subcls, string):
        '''Match one or more 'subcls' fparser2 rules in the string 'string'
        separated by 'separator'.

        :param str separator: the separator used to split the supplied \
        string.
        :param subcls: an fparser2 object representing the rule that \
        should be matched.
        :type subcls: subclass of :py:class:`fparser.two.utils.Base`
        :param str string: the input string to match.

        :returns: a tuple containing 1) the separator and 2) the \
        matched objects in a tuple, or None if there is no match.
        :rtype: (str, (Subclass of \
        :py:class:`fparser.two.utils.Base`)) or NoneType

        :raises InternalError: if the separator or string arguments \
        are not the expected type.
        :raises InternalError: if the separator is white space.

        '''
        if not isinstance(separator, (str, six.text_type)):
            raise InternalError(
                "SequenceBase class match method argument separator expected "
                "to be a string but found '{0}'.".format(type(string)))
        if not isinstance(string, (str, six.text_type)):
            raise InternalError(
                "SequenceBase class match method argument string expected to "
                "be a string but found '{0}'.".format(type(string)))

        if separator == ' ':
            raise InternalError(
                "SequenceBase class match method argument separator cannot "
                "be white space.")
        line, repmap = string_replace_map(string)
        splitted = line.split(separator)
        if not splitted:
            # There should be at least one entry.
            return None
        lst = [subcls(repmap(entry.strip())) for entry in splitted]
        return separator, tuple(lst)

    def init(self, separator, items):
        '''Store the result of the match method if the match is successful.

        :param str separator: the separator used to split the supplied string.
        :param items: a tuple containing the matched objects.
        :type items: tuple(Subclass of :py:class:`fparser.two.utils.Base`)

        '''
        self.separator = separator
        self.items = items

    def tostr(self):
        '''
        :returns: The Fortran representation of this object as a string.
        :rtype: str

        '''
        sep = self.separator
        if sep == ',':
            sep = sep + ' '
        elif sep == ' ':
            pass
        else:
            sep = ' ' + sep + ' '
        return sep.join(map(str, self.items))

    def torepr(self):
        '''
        :returns: The Python representation of this object as a string.
        :rtype: str

        '''
        return "{0}('{1}', {2})".format(self.__class__.__name__,
                                        self.separator, self.items)

    # The mixin class is likely to be removed so _cmpkey would not be
    # needed. It is not used at the moment. It is only commented out
    # at this point, rather than removed, in case it turns out that
    # the mixin class is useful.
    # def _cmpkey(self):
    #     """ Provides a key of objects to be used for comparing.
    #     """
    #     return (self.separator, self.items)


class UnaryOpBase(Base):
    """
::
    <unary-op-base> = <unary-op> <rhs>
    """
    def tostr(self):
        return '%s %s' % tuple(self.items)

    def match(op_pattern, rhs_cls, string, exclude_op_pattern=None):
        m = op_pattern.match(string)
        if not m:
            return
        rhs = string[m.end():].lstrip()
        if not rhs:
            return
        op = string[:m.end()].rstrip().upper()
        if exclude_op_pattern is not None:
            if exclude_op_pattern.match(op):
                return
        return op, rhs_cls(rhs)
    match = staticmethod(match)


class BinaryOpBase(Base):
    """
::
    <binary-op-base> = <lhs> <op> <rhs>
    <op> is searched from right by default.
    """
    def match(lhs_cls, op_pattern, rhs_cls, string, right=True,
              exclude_op_pattern=None, is_add=False):
        line, repmap = string_replace_map(string)
        if isinstance(op_pattern, str):
            if right:
                t = line.rsplit(op_pattern, 1)
            else:
                t = line.split(op_pattern, 1)
            if len(t) != 2:
                return
            lhs, rhs = t[0].rstrip(), t[1].lstrip()
            op = op_pattern
        else:
            if right:
                t = op_pattern.rsplit(line, is_add=is_add)
            else:
                t = op_pattern.lsplit(line)
            if t is None or len(t) != 3:
                return
            lhs, op, rhs = t
            lhs = lhs.rstrip()
            rhs = rhs.lstrip()
            op = op.upper()
        if not lhs:
            return
        if not rhs:
            return
        if exclude_op_pattern is not None:
            if exclude_op_pattern.match(op):
                return

        lhs_obj = lhs_cls(repmap(lhs))
        rhs_obj = rhs_cls(repmap(rhs))
        return lhs_obj, op.replace(' ', ''), rhs_obj
    match = staticmethod(match)

    def tostr(self):
        return '%s %s %s' % tuple(self.items)


class SeparatorBase(Base):
    """
::
    <separator-base> = [ <lhs> ] : [ <rhs> ]
    """
    def match(lhs_cls, rhs_cls, string, require_lhs=False, require_rhs=False):
        line, repmap = string_replace_map(string)
        if ':' not in line:
            return
        lhs, rhs = line.split(':', 1)
        lhs = lhs.rstrip()
        rhs = rhs.lstrip()
        lhs_obj, rhs_obj = None, None
        if lhs:
            if lhs_cls is None:
                return
            lhs_obj = lhs_cls(repmap(lhs))
        elif require_lhs:
            return
        if rhs:
            if rhs_cls is None:
                return
            rhs_obj = rhs_cls(repmap(rhs))
        elif require_rhs:
            return
        return lhs_obj, rhs_obj
    match = staticmethod(match)

    def tostr(self):
        s = ''
        if self.items[0] is not None:
            s += '%s :' % (self.items[0])
        else:
            s += ':'
        if self.items[1] is not None:
            s += ' %s' % (self.items[1])
        return s


class KeywordValueBase(Base):
    """
::
    <keyword-value-base> = [ <lhs> = ] <rhs>
    """
    @staticmethod
    def match(lhs_cls, rhs_cls, string, require_lhs=True, upper_lhs=False):
        '''
        :param lhs_cls: list, tuple or single value of classes to attempt to
                        match LHS against (in order), or string containing
                        keyword to match
        :type lhs_cls: names of classes deriving from `:py:class:Base` or str
        :param rhs_cls: name of class to match RHS against
        :type rhs_cls: name of a class deriving from `:py:class:Base`
        :param str string: text to be matched
        :param bool require_lhs: whether the expression to be matched must
                                 contain a LHS that is assigned to
        :param bool upper_lhs: whether or not to convert the LHS of the
                               matched expression to upper case
        :return: instances of the classes representing quantities on the LHS
                 and RHS (LHS is optional) or nothing if no match is found
        :rtype: 2-tuple of objects or nothing
        '''
        if require_lhs and '=' not in string:
            return
        if isinstance(lhs_cls, (list, tuple)):
            for s in lhs_cls:
                obj = KeywordValueBase.match(s, rhs_cls, string,
                                             require_lhs=require_lhs,
                                             upper_lhs=upper_lhs)
                if obj:
                    return obj
            return obj
        # We can't just blindly check whether 'string' contains an '='
        # character as it could itself hold a string constant containing
        # an '=', e.g. FMT='("Hello = False")'
        from fparser.two.Fortran2003 import Char_Literal_Constant
        if not Char_Literal_Constant.match(string) and "=" in string:
            lhs, rhs = string.split('=', 1)
            lhs = lhs.rstrip()
        else:
            lhs = None
            rhs = string.rstrip()
        rhs = rhs.lstrip()
        if not rhs:
            return
        if not lhs:
            if require_lhs:
                return
            return None, rhs_cls(rhs)
        if isinstance(lhs_cls, str):
            if upper_lhs:
                lhs = lhs.upper()
            if lhs_cls != lhs:
                return
            return lhs, rhs_cls(rhs)
        return lhs_cls(lhs), rhs_cls(rhs)

    def tostr(self):
        if self.items[0] is None:
            return str(self.items[1])
        return '%s = %s' % tuple(self.items)


class BracketBase(Base):
    '''
    bracket-base is left-bracket something right-bracket.

    This class is able to cope with nested brackets as long as they
    are correctly nested. Brackets in strings are ignored.

    The 'something' can be specified as being optional.

    '''
    @staticmethod
    def match(brackets, cls, string, require_cls=True):
        '''A generic match method for all types of bracketed
        expressions.

        :param str brackets: the format of the left and right brackets \
        provided as a string, for example '()'
        :param cls: the class to match the content within the brackets \
        :type cls: subclass of :py:class:`fparser.two.utils.Base`
        :param str string: the content to match
        :param bool require_cls: whether the class and associated \
        content is mandatory (True) or optional (False). The default \
        is True.
        :return: None if there is no match, otherwise a tuple with the \
        first and third entries being strings containing the left and \
        right brackets respectively and the second entry being either \
        None or an instance of the class provided as the second \
        argument (cls).
        :rtype: 'NoneType', ( `str`, `NoneType`, `str`) or ( `str`, \
        `cls`, `str` )

        '''
        if not cls and require_cls:
            return None
        if not string:
            return None
        string_strip = string.strip()
        if not brackets:
            return None
        brackets_nospc = brackets.replace(' ', '')
        if not brackets_nospc:
            return None
        if len(brackets_nospc) % 2 == 1:
            # LHS and RHS bracketing must be the same size
            return None
        bracket_len = len(brackets_nospc)//2
        left = brackets_nospc[:bracket_len]
        right = brackets_nospc[-bracket_len:]
        if len(string_strip) < bracket_len*2:
            return None
        if not (string_strip.startswith(left) and
                string_strip.endswith(right)):
            return None
        # Check whether or not there's anything between the open
        # and close brackets
        line = string_strip[bracket_len:-bracket_len].strip()
        if (not line and cls and require_cls) or (line and not cls):
            return None
        if not line and (not cls or not require_cls):
            return left, None, right
        return left, cls(line), right

    def tostr(self):
        '''
        :raises InternalError: if the internal items list variable is \
        not the expected size.
        :raises InternalError: if the first element of the internal \
        items list is None or is an empty string.
        '''

        if len(self.items) != 3:
            raise InternalError(
                "Class BracketBase method tostr() has '{0}' items, "
                "but expecting 3.".format(len(self.items)))
        if not self.items[0]:
            raise InternalError(
                "Class BracketBase method tostr(). 'Items' entry 0 "
                "should be a string containing the left hand bracket "
                "but it is empty or None")
        if not self.items[2]:
            raise InternalError(
                "Class BracketBase method tostr(). 'Items' entry 2 "
                "should be a string containing the right hand bracket "
                "but it is empty or None")
        if self.items[1] is None:
            return "{0}{1}".format(self.items[0], self.items[2])
        return "{0}{1}{2}".format(self.items[0], self.items[1], self.items[2])


class NumberBase(Base):
    """
::
    <number-base> = <number> [ _ <kind-param> ]
    """

    def match(number_pattern, string):
        m = number_pattern.match(string.replace(' ', ''))
        if m is None:
            return
        d = m.groupdict()
        return d['value'].upper(), d.get('kind_param')
    match = staticmethod(match)

    def tostr(self):
        if self.items[1] is None:
            return str(self.items[0])
        return '%s_%s' % tuple(self.items)

    def _cmpkey(self):
        """ Provides a key of objects to be used for comparing.
        """
        return self.items[0]


class CallBase(Base):
    """
::
    <call-base> = <lhs> ( [ <rhs> ] )
    """
    def match(lhs_cls, rhs_cls, string, upper_lhs=False, require_rhs=False):
        if not string.endswith(')'):
            return
        line, repmap = string_replace_map(string)
        i = line.rfind('(')
        if i == -1:
            return
        lhs = line[:i].rstrip()
        if not lhs:
            return
        j = line.rfind(')')
        rhs = line[i+1: j].strip()
        if line[j+1:].lstrip():
            return
        lhs = repmap(lhs)
        if upper_lhs:
            lhs = lhs.upper()
        rhs = repmap(rhs)
        if isinstance(lhs_cls, str):
            if lhs_cls != lhs:
                return
        else:
            lhs = lhs_cls(lhs)
        if rhs:
            if isinstance(rhs_cls, str):
                if rhs_cls != rhs:
                    return
            else:
                rhs = rhs_cls(rhs)
            return lhs, rhs
        elif require_rhs:
            return
        return lhs, None
    match = staticmethod(match)

    def tostr(self):
        if self.items[1] is None:
            return '%s()' % (self.items[0])
        return '%s(%s)' % (self.items[0], self.items[1])


class CALLBase(CallBase):
    """
::
    <CALL-base> = <LHS> ( [ <rhs> ] )
    """
    def match(lhs_cls, rhs_cls, string, require_rhs=False):
        return CallBase.match(lhs_cls, rhs_cls, string,
                              upper_lhs=True, require_rhs=require_rhs)
    match = staticmethod(match)


class StringBase(Base):
    """
::
    <string-base> = <xyz>

Attributes
----------
string
    """
    def match(pattern, string):
        if isinstance(pattern, (list, tuple)):
            for p in pattern:
                obj = StringBase.match(p, string)
                if obj is not None:
                    return obj
            return
        if isinstance(pattern, str):
            if len(pattern) == len(string) and pattern == string:
                return string,
            return
        if pattern.match(string):
            return string,
        return
    match = staticmethod(match)

    def init(self, string):
        self.string = string
        return

    def tostr(self):
        return str(self.string)

    def torepr(self):
        return '%s(%r)' % (self.__class__.__name__, self.string)

    def _cmpkey(self):
        """ Provides a key of objects to be used for comparing.
        """
        return self.string


class STRINGBase(StringBase):
    '''STRINGBase matches an upper case version of the input string with
    another a pattern (typically taken from pattern_tools.py) and
    returns the string in upper case if there is a match.

    '''

    @staticmethod
    def match(my_pattern, string):
        '''Matches an input string with a specified pattern. Casts the string
        to upper case before performing a match and, if there is a
        match, returns the string in upper case.

        The pattern can be a regular expression, a string, a list or a
        tuple. If the input pattern is a regular expression or a
        string, a direct equivalence is performed. If the input pattern is a
        list or a tuple, then all of the contents of the list
        or tuple are searched for a match (by recursing). The list or tuple may
        contain regular expressions, strings, lists or tuples. This
        functionality can be used to recurse down a tree of lists and
        or tuples until regular expressions or strings are found (at
        the leaves of the tree) on which to match. The patterns used
        to match in fparser can be found in patterns_tools.py. These
        make use of the pattern class, whose match method behaves like
        a regular expression. For example:

        from fparser.two import pattern_tools
        pattern = pattern_tools.intrinsic_type_name
        result = STRINGBase.match(pattern, "logical")

        :param pattern: the pattern to match
        :type pattern: `list`, `tuple`, `str` or an `re` expression
        :param str string: the string to match with the pattern
        :return: None if there is no match, or a tuple containing the \
        matched string in upper case.
        :rtype: `NoneType` or ( `str` )

        '''
        if string is None:
            return None
        if not isinstance(string, (str, six.text_type)):
            raise InternalError(
                "Supplied string should be of type str or {0}, but found "
                "{1}".format(six.text_type, type(string)))
        if isinstance(my_pattern, (list, tuple)):
            for child in my_pattern:
                result = STRINGBase.match(child, string)
                if result:
                    return result
            return None
        string_upper = string.upper()
        if isinstance(my_pattern, str):
            if len(my_pattern) == len(string) and my_pattern == string_upper:
                return string_upper,
            return None
        try:
            if my_pattern.match(string_upper):
                return string_upper,
        except AttributeError:
            raise InternalError(
                "Supplied pattern should be a list, tuple, str or regular "
                "expression but found {0}".format(type(my_pattern)))
        return None


class StmtBase(Base):
    """
::
    [ [ <label> ] [ <construct-name> : ] ] <stmt>

Attributes
----------
item : readfortran.Line
    """
    def tofortran(self, tab='', isfix=None):
        label = None
        name = None
        if self.item is not None:
            label = self.item.label
            name = self.item.name
        if isfix:
            c = ' '
        else:
            c = ''
        if label:
            t = c + str(label)
            if isfix:
                while len(t) < 6:
                    t += ' '
            else:
                tab = tab[len(t):] or ' '
        else:
            # BUG allow for fixed format here
            t = ''
        if name:
            return t + tab + name+':' + str(self)
        return t + tab + str(self)

    def get_end_label(self):
        return self.item.label


class EndStmtBase(StmtBase):
    """
::
    <end-stmt-base> = END [ <stmt> [ <stmt-name>] ]
    """
    @staticmethod
    def match(stmt_type, stmt_name, string, require_stmt_type=False):
        start = string[:3].upper()
        if start != 'END':
            return
        line = string[3:].lstrip()
        start = line[:len(stmt_type)].upper()
        if start:
            if start.replace(' ', '') != stmt_type.replace(' ', ''):
                return
            line = line[len(stmt_type):].lstrip()
        else:
            if require_stmt_type:
                return
            return None, None
        if line:
            if stmt_name is None:
                return
            return stmt_type, stmt_name(line)
        return stmt_type, None

    def init(self, stmt_type, stmt_name):
        '''
        Initialise this EndStmtBase object.

        :param str stmt_type: the type of statement, e.g. 'PROGRAM'.
        :param stmt_name: the name associated with the statement or None.
        :type stmt_name: :py:class:`fparser.two.Fortran2003.Name`

        '''
        self.items = [stmt_type, stmt_name]

    def get_name(self):
        return self.items[1]

    def get_type(self):
        return self.items[0]

    def tostr(self):
        if self.items[1] is not None:
            return 'END %s %s' % tuple(self.items)
        if self.items[0] is not None:
            return 'END %s' % (self.items[0])
        return 'END'

    def torepr(self):
        return '%s(%r, %r)' % (
            self.__class__.__name__, self.get_type(), self.get_name())

    def get_end_name(self):
        name = self.items[1]
        if name is not None:
            return name.string


def isalnum(c):
    return c.isalnum() or c == '_'


class WORDClsBase(Base):
    '''Base class to support situations where there is a keyword which is
    optionally followed by further text, potentially separated by
    '::'.

    For example 'program fred', or 'import :: a,b'

    WORD-cls is WORD [ [ :: ] cls ]

    '''
    @staticmethod
    def match(keyword, cls, string, colons=False, require_cls=False):
        '''Checks whether the content in string matches the expected
        WORDClsBase format with 'keyword' providing the keyword, 'cls'
        providing the following text, 'colons' specifying whether an
        optional '::' is allowed as a separator between the keyword
        and cls and 'require_cls' specifying whether cls must have
        content or not.

        Note, if the optional '::' is allowed and exists in the string
        then 1) cls must also have content i.e. it implies
        `require_cls=True` and 2) white space is not required between
        the keyword and the '::' and the '::' and cls.

        The simplest form of keyword pattern is a string. However this
        method can also match more complex patterns as specified by
        the Pattern class in pattern_tools.py. As patterns can be
        built from combinations of other patterns (again see
        pattern_tool.py) this method also supports a hierarchy of
        lists and/or tuples of patterns.

        :param keyword: the pattern of the WORD to match. This can be \
            a Pattern, string, list or tuple, with a list or tuple \
            containing one or more Pattern, string, list or tuple.
        :type keyword: :py:class:`fparser.two.pattern_tools.Pattern`, \
            str, tuple of str/Pattern/tuple/list or list of \
            str/Pattern/tuple/list
        :param cls: the class to match.
        :type cls: a subclass of :py:class:`fparser.two.utils.Base`
        :param str string: Text that we are trying to match.
        :param bool colons: whether '::' is allowed as an optional \
            separator between between WORD and cls.
        :param bool require_cls: whether content for cls is required \
            or not.

        :returns: None if there is no match or, if there is a match, a \
            2-tuple containing a string matching the 'WORD' and an \
            instance of 'cls' (or None if an instance of cls is not \
            required and not provided).
        :rtype: (str, cls or NoneType) or NoneType

        '''
        if isinstance(keyword, (tuple, list)):
            for child in keyword:
                try:
                    obj = WORDClsBase.match(child, cls, string,
                                            colons=colons,
                                            require_cls=require_cls)
                except NoMatchError:
                    obj = None
                if obj is not None:
                    return obj
            return None

        if isinstance(keyword, str):
            line = string.lstrip()
            if line[:len(keyword)].upper() != keyword.upper():
                return None
            line = line[len(keyword):]
            pattern_value = keyword
        else:
            my_match = keyword.match(string)
            if my_match is None:
                return None
            line = string[len(my_match.group()):]
            pattern_value = keyword.value

        if not line:
            if require_cls:
                # no text found but it is required
                return None
            return pattern_value, None
        if isalnum(line[0]):
            return None
        line = line.lstrip()
        has_colons = False
        if colons and line.startswith('::'):
            has_colons = True
            line = line[2:].lstrip()
        if not line:
            if has_colons or require_cls:
                # colons without following content is not allowed.
                return None
            return pattern_value, None
        if cls is None:
            return None
        return pattern_value, cls(line)

    def tostr(self):
        '''Convert the class into Fortran.

        :return: String representation of this class without any \
                 optional '::'.
        :rtype: str

        '''
        if self.items[1] is None:
            return str(self.items[0])
        s = str(self.items[1])
        if s and s[0] in '(*':
            return '%s%s' % (self.items[0], s)
        return '%s %s' % (self.items[0], s)

    def tostr_a(self):
        '''Convert the class into Fortran, adding in "::".

        :return: String representation of this class including an \
                 optional '::'.
        :rtype: str

        '''
        if self.items[1] is None:
            return str(self.items[0])
        return '%s :: %s' % (self.items[0], self.items[1])


class Type_Declaration_StmtBase(StmtBase):
    """<type-declaration-stmt> = <declaration-type-spec> [ [ ,
    <attr-spec> ]... :: ] <entity-decl-list>

    """
    subclass_names = []
    use_names = None  # derived class must define this list

    @staticmethod
    def match(decl_type_spec_cls, attr_spec_list_cls,
              entity_decl_list_cls, string):
        line, repmap = string_replace_map(string)
        i = line.find('::')
        if i != -1:
            j = line[:i].find(',')
            if j != -1:
                i = j
        else:
            if line[:6].upper() == 'DOUBLE':
                m = re.search(r'\s[a-z_]', line[6:].lstrip(), re.I)
                if m is None:
                    return
                i = m.start() + len(line)-len(line[6:].lstrip())
            else:
                m = re.search(r'\s[a-z_]', line, re.I)
                if m is None:
                    return
                i = m.start()
        type_spec = decl_type_spec_cls(repmap(line[:i].rstrip()))
        if type_spec is None:
            return
        line = line[i:].lstrip()
        if line.startswith(','):
            i = line.find('::')
            if i == -1:
                return
            attr_specs = attr_spec_list_cls(repmap(line[1:i].strip()))
            if attr_specs is None:
                return
            line = line[i:]
        else:
            attr_specs = None
        if line.startswith('::'):
            line = line[2:].lstrip()
        entity_decls = entity_decl_list_cls(repmap(line))
        if entity_decls is None:
            return
        return type_spec, attr_specs, entity_decls

    def tostr(self):
        if self.items[1] is None:
            return '%s :: %s' % (self.items[0], self.items[2])
        else:
            return '%s, %s :: %s' % self.items


def walk(node_list, types=None, indent=0, debug=False):
    '''
    Walk down the parse tree produced by fparser2.  Returns a list of all
    nodes with the specified type(s).

    :param node_list: node or list of nodes from which to walk.
    :type node_list: (list of) :py:class:fparser.two.utils.Base
    :param types: type or tuple of types of Node to return. (Default is to \
                  return all nodes.)
    :type types: type or tuple of types
    :param int indent: extent to which to indent debug output.
    :param bool debug: whether or not to write textual representation of AST \
                       to stdout.
    :returns: a list of nodes
    :rtype: `list` of :py:class:`fparser.two.utils.Base`
    '''
    local_list = []

    if not isinstance(node_list, (list, tuple)):
        node_list = [node_list]

    for child in node_list:
        if debug:
            if isinstance(child, str):
                print(indent*"  " + "child type = ", type(child), repr(child))
            else:
                print(indent*"  " + "child type = ", type(child))
        if types is None or isinstance(child, types):
            local_list.append(child)
        # Recurse down
        if isinstance(child, Base):
            local_list += walk(child.children, types, indent+1, debug)

    return local_list


def get_child(node, node_type):
    '''
    Searches for the first, immediate child of the supplied node that is of
    the specified type.

    :param node: the node whose children will be searched.
    :type node: :py:class:`fparser.two.utils.Base`
    :param type node_type: the class of child node to search for.

    :returns: the first child node of type node_type that is encountered \
              or None.
    :rtype: :py:class:`fparser.two.utils.Base`

    '''
    for child in node.children:
        if isinstance(child, node_type):
            return child
    return None
