#!/usr/bin/env python

# Modified work Copyright (c) 2017-2022 Science and Technology
# Facilities Council.
# Modified work Copyright (c) 2017 by J. Henrichs, Bureau of Meteorology
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

"""
Defines LineSplitter and helper functions.

Original Author: Pearu Peterson <pearu@cens.ioc.ee>
First version created: May 2006

"""


import re
from typing import List, Tuple, Optional, Union


class String(str):
    """Class used to represent a *quoted* string."""


class ParenString(str):
    """Class representing a parenthesis string."""


__all__ = ["String", "string_replace_map", "splitquote", "splitparen"]

_f2py_str_findall = re.compile(r"_F2PY_STRING_CONSTANT_\d+_").findall
_is_name = re.compile(r"\w*\Z", re.I).match
_is_simple_str = re.compile(r"\w*\Z", re.I).match
_f2py_findall = re.compile(
    r"(_F2PY_STRING_CONSTANT_\d+_|F2PY_REAL_CONSTANT_\d+_|" r"F2PY_EXPR_TUPLE_\d+)"
).findall
# A valid exponential constant must begin with a digit or a '.' (and be
# preceeded by a non-'word' character or the start of the string).
# We have to exclude '.' from the match for a non-word character as
# otherwise, in a string such as ".5d0", it would be matched by the
# non-capturing group. Since the first group is non-capturing (?:),
# the matched literal is in group 1.
# R417 for real-literal-constant does not permit whitespace.
exponential_constant = re.compile(
    r"(?:[^\w.]|^)((\d+[.]\d*|\d*[.]\d+|\d+)[edED][+-]?\d+(_\w+)?)"
)


class StringReplaceDict(dict):
    """
    Dictionary object that is callable for applying map returned
    by string_replace_map() function.
    """

    def __call__(self, line):
        for key in _f2py_findall(line):
            if key in self:
                # We only replace the occurrence of `key` corresponding to
                # the current result of the findall. This prevents the
                # 'replace' also affecting subsequent matches that may
                # have key as a substring (e.g. 'F2PY_EXPR_TUPLE_10'
                # contains 'F2PY_EXPR_TUPLE_1').
                line = line.replace(key, self[key], 1)
        return line


def memoize(function):
    """Simple memoization decorator.

    :param function: The function to memoize.
    :type function: Callable

    TODO # 472 Python 3.9 comes with a thread-safe and more efficient cache as
    it can be bounded and we are interested in lines that have temporal
    locality. It's the: @functools.lru_cache(maxsize=8)

    """
    memo = {}

    def wrapper(*args, **kwargs):
        key = args
        if kwargs:
            for item in kwargs.items():
                key += item
        result = memo.get(key, None)
        if result is not None:
            return result
        result = function(*args, **kwargs)
        memo[key] = result
        return result

    return wrapper


@memoize
def string_replace_map(line, lower=False):
    """
    #. Replaces string constants with symbol `'_F2PY_STRING_CONSTANT_<index>_'`
    #. Replaces (`expression`) with symbol `(F2PY_EXPR_TUPLE_<index>)`
    #. Replaces real numerical constants containing an exponent with symbol
       `F2PY_REAL_CONSTANT_<index>_`

    :param str line: the line of text in which to perform substitutions.
    :param bool lower: whether or not the call to splitquote() should return
        items as lowercase (default is to leave the case unchanged).

    :returns: a new line and the replacement map.
    :rtype: Tuple[str, :py:class:`fparser.common.splitline.StringReplaceDict`]

    """

    str_idx = 0
    const_idx = 0
    parens_idx = 0

    items = []
    string_map = StringReplaceDict()
    rev_string_map = {}
    for item in splitquote(line, lower=lower)[0]:
        if isinstance(item, String) and not _is_simple_str(item[1:-1]):
            key = rev_string_map.get(item)
            if key is None:
                str_idx += 1
                key = "_F2PY_STRING_CONSTANT_{0}_".format(str_idx)
                trimmed = item[1:-1]
                string_map[key] = trimmed
                rev_string_map[trimmed] = key
            items.append(item[0] + key + item[-1])
        else:
            items.append(item)
    newline = "".join(items)

    const_keys = []
    for item in exponential_constant.finditer(newline):
        # Get the first captured group as that corresponds to the literal
        # *without* any preceding non-word character.
        found = item.group(1)

        key = rev_string_map.get(found)
        if key is None:
            const_idx += 1
            key = "F2PY_REAL_CONSTANT_{0}_".format(const_idx)
            string_map[key] = found
            rev_string_map[found] = key
            const_keys.append(key)
        newline = newline.replace(found, key)

    items = []
    expr_keys = []
    for item in splitparen(newline):
        if isinstance(item, ParenString) and not _is_name(item[1:-1].strip()):
            key = rev_string_map.get(item)
            if key is None:
                parens_idx += 1
                key = "F2PY_EXPR_TUPLE_{0}".format(parens_idx)
                trimmed = item[1:-1].strip()
                string_map[key] = trimmed
                rev_string_map[trimmed] = key
                expr_keys.append(key)
            items.append(item[0] + key + item[-1])
        else:
            items.append(item)

    # Ensure that any entries in the map do not themselves contain
    # substitutions
    found_keys = set()
    for key in expr_keys + const_keys:
        entry = string_map[key]
        # Find any keys within this map entry
        included_keys = _f2py_findall(entry)
        if included_keys:
            found_keys = found_keys.union(included_keys)
            for inc_key in included_keys:
                entry = entry.replace(inc_key, string_map[inc_key], 1)
            string_map[key] = entry

    return "".join(items), string_map


def _next_quote(line: str, quote_char: Optional[str] = None, start: int = 0) -> int:
    """
    Find the location of the first quotation char from the specified start position
    (defaults to the beginning of the string).

    In Fortran, quotation marks within quoted strings are escaped through
    repetition, i.e. '""' means '"' and "''" means "'". If the `quote_char` argument
    is supplied then this is taken to mean that we are searching within a quoted
    string and therefore any repeated quotation marks are interpreted as escaped
    quotation marks.

    :param line: the line of text to search.
    :param quote_char: the specific quotation character to search for. If it is not
        specified then both ' and " are searched for.
    :param start: the position in the line from which to search.

    :returns: the index of the quotation char in the supplied string or -1 if
              none is found.
    """
    line_len = len(line)
    i = start
    if quote_char:
        target_quote_chars = [quote_char]
    else:
        target_quote_chars = ["'", '"']

    while i < line_len:
        if line[i] in target_quote_chars:

            if quote_char and i < line_len - 1 and line[i + 1] == line[i]:
                # We're inside a quoted string so this is an escaped quotation
                # character ('' or "").
                i += 2
                continue
            return i
        i += 1
    return -1


def splitquote(
    line: str, stopchar: Optional[str] = None, lower: bool = False
) -> Tuple[List[Union[String, str]], Optional[str]]:
    """
    Splits the supplied line of text into parts consisting of regions that
    are not contained within quotes and those that are.

    Allows for the processing of a line that follows on from a previous one
    where a quoted string was begun but not closed by supporting the
    current closing quotation character to be specified.

    :param str line: the line to split.
    :param stopchar: the quote character that will terminate an
                     existing quoted string or None otherwise.
    :param lower: whether or not to convert the non-quoted parts of the line
                  to lowercase.

    :returns: tuple containing a list of the parts of the line split into
              those parts that are not quoted strings and those parts that are
              (as instances of String) as well as the quote character
              corresponding with any quoted string that has not been closed
              before the end of the line.

    """

    def _lower(text: str):
        """
        :returns: the supplied text lower-cased if the 'lower' argument to
                  the parent routine is True.
        """
        if lower:
            return text.lower()
        return text

    segments = []
    i = 0
    pos = 0
    n = len(line)
    if stopchar:
        # We start inside an existing quoted region.
        end = _next_quote(line, quote_char=stopchar)
        if end != -1:
            # Has to be 'end+1' to include quotation char.
            segments.append(String(line[pos : end + 1]))
            pos = end + 1
        else:
            # Didn't find a closing quotation char.
            return [String(line)], stopchar

    while pos < n:
        start = _next_quote(line, start=pos)
        if start == -1:
            # No opening quotation char found
            segments.append(_lower(line[pos:]))
            return segments, None
        if start != pos:
            segments.append(_lower(line[pos:start]))
        end = _next_quote(line, quote_char=line[start], start=start + 1)
        if end == -1:
            # Didn't find a closing quotation char.
            segments.append(String(line[start:]))
            return segments, line[start]
        segments.append(String(line[start : end + 1]))
        pos = end + 1

    return segments, None


def splitparen(line, paren_open="([", paren_close=")]"):
    """
    Splits a line into top-level parenthesis and not-parenthesised
    parts. E.g.: "a( (1+2)*3) = b(x)" becomes:
    ["a", "( (1+2)*3)", " = b", "(x)"]
    :param str line: the string to split.
    :param str paren_open: The characters that define an open parentheses.
    :param str paren_close: The characters that define a closing parentheses.
    :return: List of parenthesised and not-parenthesised parts
    :rtype: list of str
    The paren_open and paren_close strings must be matched in order:
    paren_open[x] is closed by paren_close[x].
    """

    assert len(paren_open) == len(paren_close)

    items = []  # Result list
    num_backslashes = 0  # Counts consecutive "\" characters
    # Empty if outside quotes, or set to the starting (and therefore
    # also the ending) quote character while reading text inside quotes.
    inside_quotes_char = ""
    start = 0  # Index of start of current part.
    stack = []  # Stack keeping track of required closing brackets

    for idx, char in enumerate(line):
        if char == "\\":
            num_backslashes = (num_backslashes + 1) % 2
            continue

        # We had an odd number of \, so the next character is neither
        # a real quote or parenthesis character, and can just be added.
        if num_backslashes == 1:
            num_backslashes = 0
            continue

        # If we are reading a quote, keep on reading till closing
        # quote is reached
        if inside_quotes_char != "":
            # Reset inside_quotes_char if we find the closing quote
            if char == inside_quotes_char:
                inside_quotes_char = ""
            continue

        if char == "'" or char == '"':
            inside_quotes_char = char
            continue

        pos = paren_open.find(char)
        if pos > -1:
            if len(stack) == 0:
                # New part starts:
                items.append(line[start:idx])
                start = idx
            stack.append(paren_close[pos])
            continue

        # Found closing bracket
        if len(stack) > 0 and char == stack[-1]:
            stack.pop()
            if len(stack) == 0:
                # Found last closing bracket
                items.append(ParenString(line[start : idx + 1]))
                start = idx + 1

    # Add any leftover characters as a separate item
    if start != len(line):
        items.append(line[start:])
    return items
