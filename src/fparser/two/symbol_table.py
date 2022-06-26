# -----------------------------------------------------------------------------
# BSD 3-Clause License
#
# Copyright (c) 2021-2022, Science and Technology Facilities Council.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# -----------------------------------------------------------------------------

"""
The fparser2 symbol-table module. Defines various classes as well as
the single, global SYMBOL_TABLES instance. The latter is a container
for all of the top-level scoping units encountered during parsing.

"""
from collections import namedtuple


class SymbolTableError(Exception):
    """Base class exception for symbol-table related errors."""


class SymbolTables:
    """
    Class encapsulating functionality for the global symbol-tables object.
    This is a container for all symbol tables constructed while parsing
    code. All names are converted to lower case (since Fortran is not
    case sensitive).

    """

    def __init__(self):
        self._symbol_tables = {}
        # Those classes that correspond to a new scoping unit
        self._scoping_unit_classes = []
        # The symbol table of the current scope
        self._current_scope = None
        # Whether or not we enable consistency checks in the symbol tables
        # that are created.
        self._enable_checks = False

    def __str__(self):
        result = "SymbolTables: {0} tables\n" "========================\n".format(
            len(self._symbol_tables)
        )
        return result + "\n".join(sorted(self._symbol_tables.keys()))

    def enable_checks(self, value):
        """
        Sets whether or not to enable consistency checks in every symbol
        table that is created during a parse.

        :param bool value: whether or not checks are enabled.

        """
        self._enable_checks = value

    def clear(self):
        """
        Deletes any stored SymbolTables but retains the stored list of
        classes that define scoping units.

        """
        self._symbol_tables = {}
        self._current_scope = None

    def add(self, name):
        """
        Add a new symbol table with the supplied name. The name will be
        converted to lower case if necessary.

        :param str name: the name for the new table.

        :returns: the new symbol table.
        :rtype: :py:class:`fparser.two.symbol_table.SymbolTable`

        :raises SymbolTableError: if there is already an entry with the \
                                  supplied name.
        """
        lower_name = name.lower()
        if lower_name in self._symbol_tables:
            raise SymbolTableError(
                "The table of top-level (un-nested) symbol tables already "
                "contains an entry for '{0}'".format(lower_name)
            )
        table = SymbolTable(lower_name, checking_enabled=self._enable_checks)
        self._symbol_tables[lower_name] = table
        return table

    def lookup(self, name):
        """
        Find the named symbol table and return it.

        :param str name: the name of the required symbol table (not case \
                         sensitive).

        :returns: the named symbol table.
        :rtype: :py:class:`fparser.two.symbol_table.SymbolTable`

        """
        return self._symbol_tables[name.lower()]

    @property
    def scoping_unit_classes(self):
        """
        :returns: the fparser2 classes that are taken to mark the start of \
                  a new scoping region.
        :rtype: list of types

        """
        return self._scoping_unit_classes

    @scoping_unit_classes.setter
    def scoping_unit_classes(self, value):
        """
        Set the list of fparser2 classes that are taken to mark the start of \
        a new scoping region.

        :param value: the list of fparser2 classes.
        :type value: list of types

        :raises TypeError: if the supplied value is not a list of types.

        """
        if not isinstance(value, list):
            raise TypeError(
                "Supplied value must be a list but got '{0}'".format(
                    type(value).__name__
                )
            )
        if not all(isinstance(item, type) for item in value):
            raise TypeError(
                "Supplied list must contain only classes but " "got: {0}".format(value)
            )
        self._scoping_unit_classes = value

    @property
    def current_scope(self):
        """
        :returns: the symbol table for the current scoping unit or None.
        :rtype: :py:class:`fparser.two.symbol_table.SymbolTable` or NoneType
        """
        return self._current_scope

    def enter_scope(self, name):
        """
        Called when the parser enters a new scoping region (i.e. when it
        encounters one of the classes listed in `_scoping_unit_classes`).
        Sets the 'current scope' to be the symbol table with the supplied name.
        If we are not currently within a tree of scoping regions then a
        new entry is created in the internal dict of symbol tables. If there
        is an existing tree then a new table is created and added to the
        bottom.

        :param str name: name of the scoping region.

        """
        lname = name.lower()

        if not self._current_scope:
            # We're not already inside a nested scope.
            try:
                table = self.lookup(lname)
            except KeyError:
                # Create a new, top-level symbol table with the supplied name.
                table = self.add(lname)
        else:
            # We are already inside a scoping region so create a new table
            # and setup its parent/child connections.
            table = SymbolTable(
                lname, parent=self._current_scope, checking_enabled=self._enable_checks
            )
            self._current_scope.add_child(table)

        # Finally, make this new table the current scope
        self._current_scope = table

    def exit_scope(self):
        """
        Marks the end of the processing of the current scoping unit. Since
        we are exiting the current scoping region, the new 'current scoping
        region' will be its parent.

        :raises SymbolTableError: if there is no current scope from which to \
                                  exit.
        """
        if not self._current_scope:
            raise SymbolTableError(
                "exit_scope() called but no current scope " "exists."
            )
        self._current_scope = self._current_scope.parent

    def remove(self, name):
        """
        Removes the named symbol table and any descendants it may have.
        When searching for the named table, the current scope takes priority
        followed by the list of top-level symbol tables.

        :param str name: the name of the symbol table to remove (not case \
                         sensitive).
        :raises SymbolTableError: if the named symbol table is not in the \
            current scope or in the list of top-level symbol tables.

        """
        lname = name.lower()
        if self._current_scope:
            try:
                self._current_scope.del_child(lname)
                # We succeeded in removing it from the current scope so we
                # are done.
                return
            except KeyError:
                pass

        if lname not in self._symbol_tables:
            msg = "Failed to find a table named '{0}' in ".format(name)
            if self._current_scope:
                msg += "either the current scope (which contains {0}) or ".format(
                    [child.name for child in self._current_scope.children]
                )
            msg += "the list of top-level symbol tables ({0}).".format(
                list(self._symbol_tables.keys())
            )
            raise SymbolTableError(msg)

        # Check that we're not currently somewhere inside the scope of the
        # named table.
        top_table = self._symbol_tables[lname]
        if self._current_scope:
            if self._current_scope.root is top_table:
                raise SymbolTableError(
                    "Cannot remove top-level symbol table '{0}' because the "
                    "current scope '{1}' has it as an ancestor.".format(
                        name, self._current_scope.name
                    )
                )

        del self._symbol_tables[lname]


class SymbolTable:
    """
    Class implementing a single symbol table.

    Since this functionality is not yet fully mature, checks that new symbols
    don't clash with existing symbols are disabled by default.
    Once #201 is complete it is planned to switch this so that the checks
    are instead enabled by default.

    :param str name: the name of this scope. Will be the name of the \
                     associated module or routine.
    :param parent: the symbol table within which this one is nested (if any).
    :type parent: :py:class:`fparser.two.symbol_table.SymbolTable.Symbol`
    :param bool checking_enabled: whether or not validity checks are \
        performed for symbols added to the table.

    """

    # TODO #201 add support for other symbol properties (kind, shape
    # and visibility). We may need a distinct Symbol class so as to provide
    # type checking for the various properties.
    Symbol = namedtuple("Symbol", "name primitive_type")

    def __init__(self, name, parent=None, checking_enabled=False):
        self._name = name.lower()
        # Symbols defined in this scope that represent data.
        self._data_symbols = {}
        # Modules imported into this scope.
        self._modules = {}
        # Reference to a SymbolTable that contains this one (if any). Actual
        # value (if any) is set via setter method.
        self._parent = None
        self.parent = parent
        # Whether or not to perform validity checks when symbols are added.
        self._checking_enabled = checking_enabled
        # Symbol tables nested within this one.
        self._children = []

    def __str__(self):
        header = "===========\n"
        symbols = "Symbols:\n"
        if self._data_symbols:
            symbols += "\n".join(list(self._data_symbols.keys())) + "\n"
        uses = "Used modules:\n"
        if self._modules:
            uses += "\n".join(list(self._modules.keys())) + "\n"
        return (
            "{0}Symbol Table '{1}'\n".format(header, self._name)
            + symbols
            + uses
            + header
        )

    def add_data_symbol(self, name, primitive_type):
        """
        Creates a new Symbol with the specified properties and adds it to
        the symbol table. The supplied name is converted to lower case.

        TODO #201 add support for other symbol properties (kind, shape
        and visibility).

        :param str name: the name of the symbol.
        :param str primitive_type: the primitive type of the symbol.

        :raises TypeError: if any of the supplied parameters are of the \
                           wrong type.
        :raises SymbolTableError: if the symbol table already contains an
                                  entry with the supplied name.
        """
        if not isinstance(name, str):
            raise TypeError(
                "The name of the symbol must be a str but got "
                "'{0}'".format(type(name).__name__)
            )
        # TODO #201 use an enumeration for the primitive type
        if not isinstance(primitive_type, str):
            raise TypeError(
                "The primitive type of the symbol must be specified as a str "
                "but got '{0}'".format(type(primitive_type).__name__)
            )

        lname = name.lower()

        if self._checking_enabled:
            if lname in self._data_symbols:
                raise SymbolTableError(
                    f"Symbol table already contains a symbol for"
                    f" a variable with name '{name}'"
                )
            if lname in self._modules:
                raise SymbolTableError(
                    f"Symbol table already contains a use of a "
                    f"module with name '{name}'"
                )
            for mod_name, var_list in self._modules.items():
                if var_list and lname in var_list:
                    raise SymbolTableError(
                        f"Symbol table already contains a use of a symbol "
                        f"named '{name}' from module '{mod_name}'"
                    )

        self._data_symbols[lname] = SymbolTable.Symbol(lname, primitive_type.lower())

    def add_use_symbols(self, name, only_list=None):
        """
        Creates an entry in the table for the USE of a module with the supplied
        name. If no `only_list` is supplied then this USE represents a wildcard
        import of all public symbols in the named module. If the USE statement
        has an ONLY clause but without any named symbols then `only_list`
        should be an empty list.

        :param str name: the name of the module being imported via a USE. Not \
            case sensitive.
        :param only_list: Whether or not there is an 'only:' clause on the \
            USE statement and, if so, the names of the symbols being imported \
            (not case sensitive).
        :type only_list: NoneType or list of str

        :raises TypeError: if either of the supplied parameters are of the \
                           wrong type.
        """
        if not isinstance(name, str):
            raise TypeError(
                "The name of the module must be a str but got "
                "'{0}'".format(type(name).__name__)
            )
        if only_list and not isinstance(only_list, list):
            raise TypeError(
                "If present, the only_list must be a list but got "
                "'{0}'".format(type(only_list).__name__)
            )
        if only_list and not all(isinstance(item, str) for item in only_list):
            raise TypeError(
                "If present, the only_list must be a list of str "
                "but got: {0}".format([type(item).__name__ for item in only_list])
            )

        # Convert the list of names to lower case
        if only_list is not None:
            lowered_list = [var_name.lower() for var_name in only_list]
        else:
            lowered_list = None

        lname = name.lower()
        if lname in self._modules:
            # The same module can appear in more than one use statement
            # in Fortran.
            if lowered_list:
                if self._modules[lname] is None:
                    # We already have a wildcard import for this module but
                    # now we also know the names of some specific symbols that
                    # are imported.
                    # TODO #294 improve the data structures used to hold
                    # information on use statements so that we can capture
                    # this.
                    pass
                else:
                    self._modules[lname].extend(lowered_list)
        else:
            self._modules[lname] = lowered_list

    def lookup(self, name):
        """
        Lookup the symbol with the supplied name.

        :param str name: the name of the symbol to lookup (not case sensitive).

        :returns: the named symbol.
        :rtype: :py:class:`fparser.two.symbol_table.SymbolTable.Symbol`

        :raises KeyError: if the named symbol cannot be found in this or any \
                          parent scope.
        """
        # Fortran is not case sensitive so convert input to lowercase.
        lname = name.lower()
        if lname in self._data_symbols:
            return self._data_symbols[lname]
        # No match in this scope - search in parent scope (if any)
        if self.parent:
            return self.parent.lookup(lname)
        raise KeyError("Failed to find symbol named '{0}'".format(lname))

    @property
    def name(self):
        """
        :returns: the name of this symbol table (scoping region).
        :rtype: str
        """
        return self._name

    @property
    def parent(self):
        """
        :returns: the parent symbol table (scoping region) that contains \
                  this one (if any).
        :rtype: :py:class:`fparser.two.symbol_table.SymbolTable` or NoneType
        """
        return self._parent

    @parent.setter
    def parent(self, value):
        """
        Set the parent scope for this symbol table.

        :param value: the parent symbol table.
        :type value: :py:class:`fparser.two.symbol_table.SymbolTable`

        :raises TypeError: if the supplied value is not None or a SymbolTable.

        """
        if value is not None and not isinstance(value, SymbolTable):
            raise TypeError(
                "Unless it is None, the parent of a SymbolTable must also be "
                "a SymbolTable but got '{0}'".format(type(value).__name__)
            )
        self._parent = value

    def add_child(self, child):
        """
        Adds a child symbol table (scoping region nested within this one).

        :param child: the nested symbol table.
        :type child: :py:class:`fparser.two.symbol_table.SymbolTable`

        :raises TypeError: if the supplied child is not a SymbolTable.

        """
        if not isinstance(child, SymbolTable):
            raise TypeError(
                "Expected a SymbolTable instance but got '{0}'".format(
                    type(child).__name__
                )
            )
        self._children.append(child)

    def del_child(self, name):
        """
        Removes the named symbol table.

        :param str name: the name of the child symbol table to delete (not \
                         case sensitive).

        :raises KeyError: if the named table is not a child of this one.

        """
        lname = name.lower()
        for child in self._children:
            if child.name == lname:
                self._children.remove(child)
                break
        else:
            raise KeyError(
                "Symbol table '{0}' does not contain a table named "
                "'{1}'".format(self.name, name)
            )

    @property
    def children(self):
        """
        :returns: the child (nested) symbol tables, if any.
        :rtype: list of :py:class:`fparser.two.symbol_table.SymbolTable`
        """
        return self._children

    @property
    def root(self):
        """
        :returns: the top-level symbol table that contains the current \
                  scoping region (symbol table).
        :rtype: :py:class:`fparser.two.symbol_table.SymbolTable`

        """
        current = self
        while current.parent:
            current = current.parent
        return current


#: The single, global container for all symbol tables constructed while
#: parsing.
SYMBOL_TABLES = SymbolTables()


__all__ = ["SymbolTableError", "SymbolTables", "SymbolTable", "SYMBOL_TABLES"]
