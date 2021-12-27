"""
Errors that can be raised by cutplace.
"""
# Copyright (C) 2009-2021 Thomas Aglassinger
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import copy
import os
import traceback

#: Symbolic names that can be used to improve the legibility of the CID.
NAME_TO_ASCII_CODE_MAP = {"cr": 13, "ff": 12, "lf": 10, "tab": 9, "vt": 11}


class Location(object):
    """
    Location in an input file, consisting of ``line``, an optional ``column``
    (pointing at a single character) and an optional cell (pointing to a cell
    in a structured input such as CSV).
    """

    def __init__(self, file_path, has_column=False, has_cell=False, has_sheet=False):
        """
        Create a new :py:class:`Location` for the input described by
        ``file_path``. This can also be a symbolic name such as
        ``"<source>"`` or ``"<string>"`` in case the input is no actual file.
        If ``file_path`` is no string type, ``"<io>"`` will be used.

        If the input is a text or binary file, ``has_column`` should be
        ``True`` and :py:meth:`~.advance_column` should be called on every
        character or byte read.

        If the input is a tabular file such as CSV, ``has_cell`` should be
        ``True`` and :py:meth:`~.advance_cell()` or :py:meth:`~.set_cell` be
        called on each cell processed.

        If the input is a spreadsheet format such as ODS or Excel,
        :py:meth:`~.advance_sheet()` should be called each time a new sheet
        starts.

        You can also combine these properties, for example to exactly point
        out an error location in a spreadsheet cell, all of ``has_column``,
        ``has_cell`` and ``has_sheet`` can be ``True`` with the column
        pointing at a broken character in a cell.

        Common examples:

        >>> from cutplace import Location
        >>> Location("data.txt", has_column=True)
        data.txt (1;1)
        >>> Location("data.csv", has_cell=True)
        data.csv (R1C1)
        >>> Location("data.ods", has_cell=True, has_sheet=True)
        data.ods (Sheet1!R1C1)
        >>> Location("data.ods", has_column=True, has_cell=True, has_sheet=True) # for very detailed parsers
        data.ods (Sheet1!R1C1;1)
        >>> from io import StringIO
        >>> Location(StringIO("some text"), has_column=True)
        <io> (1;1)
        """
        assert file_path
        if isinstance(file_path, str):
            self.file_path = file_path
        else:
            try:
                self.file_path = file_path.name
            except AttributeError:
                self.file_path = "<io>"
        self._line = 0
        self._column = 0
        self._cell = 0
        self._sheet = 0
        self._has_column = has_column
        self._has_cell = has_cell
        self._has_sheet = has_sheet

    def __copy__(self):
        result = type(self)(self.file_path)
        result.__dict__.update(self.__dict__)
        return result

    def advance_column(self, amount=1):
        assert amount is not None
        assert amount > 0
        assert self._has_column
        self._column += amount

    def advance_cell(self, amount=1):
        assert amount is not None
        assert amount > 0
        assert self._has_cell
        self._cell += amount

    def set_cell(self, new_cell):
        assert new_cell is not None
        assert new_cell >= 0
        assert self._has_cell
        self._cell = new_cell

    def advance_line(self, amount=1):
        assert amount is not None
        assert amount > 0
        # TODO: enable assertion for cell consistency.
        # assert self._has_cell or self._has_column, "has_cell=%r, has_column=%r" % (self._has_cell, self._has_column)
        self._line += amount
        self._column = 0
        self._cell = 0

    def advance_sheet(self):
        self._sheet += 1
        self._line = 0
        self._column = 0
        self._cell = 0

    @property
    def cell(self):
        """The current cell in the input."""
        assert self._has_cell
        return self._cell

    @property
    def column(self):
        """The current column in the current line or cell in the input."""
        assert self._has_column
        return self._column

    @property
    def line(self):
        """The current line or row in the input."""
        return self._line

    def _get_sheet(self):
        assert self._has_sheet
        return self._sheet

    def _set_sheet(self, new_sheet):
        self._sheet = new_sheet

    sheet = property(_get_sheet, _set_sheet, doc="The current sheet in the input.")

    def __str__(self):
        """
        Human readable representation of the input location; see `__init__()` for some examples.
        """
        result = os.path.basename(self.file_path) + " ("
        if self._has_cell:
            if self._has_sheet:
                result += "Sheet%d!" % (self.sheet + 1)
            result += "R%dC%d" % (self.line + 1, self.cell + 1)
        else:
            result += "%d" % (self.line + 1)
        if self._has_column:
            result += ";%d" % (self.column + 1)
        result += ")"
        return result

    def __repr__(self):
        return self.__str__()

    def __lt__(self, other):
        return (
            (self.file_path < other.file_path)
            and (self.line < other.line)
            and (not self._has_column or (self.column < other.column))
            and (not self._has_cell or (self.cell < other.cell))
            and (not self._has_sheet or (self.sheet < other.sheet))
        )

    def __eq__(self, other):
        return (
            (self.file_path == other.file_path)
            and (self.line == other.line)
            and (not self._has_column or (self.column == other.column))
            and (not self._has_cell or (self.cell == other.cell))
            and (not self._has_sheet or (self.sheet == other.sheet))
        )

    # Note: There is no ``Location.__hash__()`` because it is a mutable class that cannot be
    # used as dictionary key.


def create_caller_location(modules_to_ignore=None, has_column=False, has_cell=False, has_sheet=False):
    """
    :py:class:`~cutplace.errors.Location` referring to the calling Python
    source code.
    """
    actual_modules_to_ignore = ["errors", "traceback"]
    if modules_to_ignore:
        actual_modules_to_ignore.extend(modules_to_ignore)
    source_path = None
    source_line = 0
    for trace in traceback.extract_stack():
        ignore_trace = False
        if actual_modules_to_ignore:
            for module_to_ignore in actual_modules_to_ignore:
                # TODO: Minor optimization: end loop once ``ignore_trace`` is ``True``.
                traced_module_name = os.path.basename(trace[0])
                if traced_module_name == (module_to_ignore + ".py"):
                    ignore_trace = True
            if not ignore_trace:
                source_path = trace[0]
                source_line = trace[1] - 1
        if source_path is None:
            source_path = "<source>"
    result = Location(source_path, has_column, has_cell, has_sheet)
    if source_line:
        result.advance_line(source_line)
    return result


class CutplaceError(Exception):
    """
    Error caused by issues in the CID or data. Details are provided by the
    following properties:

    * :py:attr:`~cutplace.errors.CutplaceError.message` - a description of
      the condition that cause the error and possibly suggestions on what
      needs to be fixed.
    * :py:attr:`~cutplace.errors.CutplaceError.location` (can be ``None``) -
      :py:class:`~cutplace.errors.Location` pointing to the source of the
      error.
    * :py:attr:`~cutplace.errors.CutplaceError.see_also_message`,
      :py:attr:`~cutplace.errors.CutplaceError.see_also_location` (can be
      ``None``): a message and :py:class:`~cutplace.errors.Location`
      describing additional information. For example, when a key field has to
      be unique but two data rows use the same value, this points to the
      first value while the actual ``message`` and ``location`` point to the
      duplicate.

    Additionally :py:meth:`~cutplace.errors.CutplaceError.__str__()`
    summarizes all details about the error in a human readable way that can
    be presented to the end user.
    """

    def __init__(self, message, location=None, see_also_message=None, see_also_location=None, cause=None):
        """
        Create an :py:exc:`Exception` that provides a ``message`` describing
        the error and an optional ``Location`` in the input where the error
        happened. If the message is related to another location (for example
        when attempting to redefine a field with the same name),
        ``see_also_message`` should describe the meaning of the other
        location and ``see_also_location`` should point to that location. If
        the exception is the result of another exception that happened
        earlier (for example a :py:exc:`UnicodeError`, ``cause`` should
        refer to this exception to simplify debugging.
        """
        assert message
        assert (see_also_location and see_also_message) or not see_also_location
        super().__init__(message)
        self._location = copy.copy(location)
        self._see_also_message = see_also_message
        self._see_also_location = copy.copy(see_also_location)
        self._cause = cause
        # TODO #61: Replace self._message by calls to something like str(super()).
        self._message = message

    @property
    def location(self):
        """
        :py:class:`~cutplace.errors.Location` in the input that caused the
        error or ``None``.
        """
        return self._location

    @property
    def message(self):
        """
        Human readable description of the condition that caused the error and
        needs to be fixed.
        """
        return self._message

    @property
    def see_also_message(self):
        """
        A message further explaining the actual message by referring to
        :py:attr:`~cutplace.errors.CutplaceError.see_also_location` or
        ``None``.
        """
        return self._see_also_message

    @property
    def see_also_location(self):
        """
        The :py:class:`Location` in the input related to the
        :py:attr:`see_also_message` or ``None``.
        """
        return self._see_also_location

    @property
    def cause(self):
        """
        The :py:exc:`Exception` that caused this error or ``None``.
        """
        return self._cause

    def prepend_message(self, prefix, new_location):
        """
        Add ``prefix`` and ``': '`` at the beginning of :py:attr:`message`
        and change :py:attr:`location` to ``new_location``.

        :param str prefix: the prefix to add at the beginning of \
          :py:attr:`~cutplace.errors.Location.message`
        :param cutplace.errors.Location new_location: the value for \
          :py:attr:`~cutplace.errors.Location.location`
        """
        assert prefix is not None
        assert new_location is not None
        self._message = prefix + ": " + self._message
        self._location = copy.copy(new_location)

    def __str__(self):
        """
        Human readable summary of all details related to the error.
        """
        result = ""
        if self._location:
            result += str(self.location) + ": "
        result += self._message
        if self.see_also_message is not None:
            result += " (see also: "
            if self.see_also_location:
                result += str(self.see_also_location) + ": "
            result += self.see_also_message + ")"
        return result


class DataError(CutplaceError):
    """
    Error that can be fixed by providing proper data. Typically this is fixed
    by the end user on site.
    """

    pass


class InterfaceError(CutplaceError):
    """
    Error that can be fixed by providing a proper CID or API calls. Typically
    this is fixed by the domain expert or the developer.
    """

    pass


class RangeValueError(DataError):
    """
    Error raised when `ranges.Range.validate()` detects that a value is
    outside the expected ranges.
    """

    pass


class DataFormatError(DataError):
    """
    Error indicating that a data file cannot be processed due severe format
    violations, for example unterminated quotes at the end of a delimited
    file or an ODS file that cannot be unzipped.
    """

    pass


class FieldValueError(DataError):
    """
    Error raised when
    :py:meth:`cutplace.fields.AbstractFieldFormat.validated` detects an
    error.
    """

    pass


class CheckError(DataError):
    """
    Error to be raised when a check fails.
    """

    pass
