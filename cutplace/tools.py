"""
Various utility classes and functions.
"""
# Copyright (C) 2009-2011 Thomas Aglassinger
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
import os
import traceback
import types

"""
Symbolic names that can be used to improve the legibility of the ICD.
"""
SYMBOLIC_NAMES_MAP = {
    "cr": 13,
    "ff": 12,
    "lf": 10,
    "tab": 9,
    "vt": 11
}

class InputLocation(object):
    """
    Location in an input file, consisting of ``line``, an optional ``column`` (pointing at a
    single character) and an optional cell (pointing a cell in a structured input such as CSV).
    """
    def __init__(self, filePath, hasColumn=False, hasCell=False, hasSheet=False):
        """
        Create a new ``InputLocation`` for the input described by ``filePath``. This can also be
        a symbolic name such as ``"<source>"`` or ``"<string>"`` in case the input is no actual
        file. If ``filePath`` is no string type, ``"<io>"`` will be used.

        If the input is a text or binary file, ``hasColumn`` should be ``True`` and
        `advanceColumn()` should be called on every character or byte read.

        If the input is a tabular file such as CSV, ``hasCell`` should be ``True`` and
        `advanceCell()` or `setCell` be called on each cell processed.

        If the input is a spreadsheet  format such as ODS or Excel, `advanceSheet()` should be called
        each time a new sheet starts.

        You can also combine these properties, for example to exactly point out an error location
        in a spreadsheet cell, all of ``hasColumn``, ``hasCell`` and ``hasSheet`` can be ``True``
        with the column pointing at a broken character in a cell.

        Common examples:

        >>> InputLocation("data.txt", hasColumn=True)
        data.txt (1;1)
        >>> InputLocation("data.csv", hasCell=True)
        data.csv (R1C1)
        >>> InputLocation("data.ods", hasCell=True, hasSheet=True)
        data.ods (Sheet1!R1C1)
        >>> InputLocation("data.ods", hasColumn=True, hasCell=True, hasSheet=True) # for very detailed parsers
        data.ods (Sheet1!R1C1;1)
        >>> from StringIO import StringIO
        >>> InputLocation(StringIO("some text"), hasColumn=True)
        <io> (1;1)
        """
        assert filePath
        if isinstance(filePath, types.StringTypes):
            self.filePath = filePath
        else:
            # TODO: Check for file object and use ``name`` in this case.
            self.filePath = "<io>"
        self._line = 0
        self._column = 0
        self._cell = 0
        self._sheet = 0
        self._hasColumn = hasColumn
        self._hasCell = hasCell
        self._hasSheet = hasSheet

    def advanceColumn(self, amount=1):
        assert amount is not None
        assert amount > 0
        assert self._hasColumn
        self._column += amount

    def advanceCell(self, amount=1):
        assert amount is not None
        assert amount > 0
        assert self._hasCell
        self._cell += amount

    # TODO: Change property ``cell`` to have getter and setter.
    def setCell(self, newCell):
        assert newCell is not None
        assert newCell >= 0
        assert self._hasCell
        self._cell = newCell

    def advanceLine(self, amount=1):
        assert amount is not None
        assert amount > 0
        # TODO: assert self._hasCell or self._hasColumn, "hasCell=%r, hasColumn=%r" % (self._hasCell, self._hasColumn)
        self._line += amount
        self._column = 0
        self._cell = 0

    def advanceSheet(self):
        self._sheet += 1
        self._line = 0
        self._column = 0
        self._cell = 0

    @property
    def cell(self):
        """The current cell in the input."""
        assert self._hasCell
        return self._cell

    @property
    def column(self):
        """The current column in the current line or cell in the input."""
        assert self._hasColumn
        return self._column

    @property
    def line(self):
        """The current line or row in the input."""
        return self._line

    @property
    def sheet(self):
        """The current sheet in the input."""
        assert self._hasSheet
        return self._sheet

    def __repr__(self):
        """
        Human readable representation of the input location; see `__init__()` for some examples.
        """
        result = os.path.basename(self.filePath) + " ("
        if self._hasCell:
            if self._hasSheet:
                result += "Sheet%d!" % (self.sheet + 1)
            result += "R%dC%d" % (self.line + 1, self.cell + 1)
        else:
            result += "%d" % (self.line + 1)
        if self._hasColumn:
            result += ";%d" % (self.column + 1)
        result += ")"
        return result

def createCallerInputLocation(modulesToIgnore=None, hasColumn=False, hasCell=False, hasSheet=False):
    """
    `InputLocation` referring to the calling Python source code.
    """
    actualModulesToIgnore = ["tools"]
    if modulesToIgnore:
        actualModulesToIgnore.extend(modulesToIgnore)
    sourcePath = None
    sourceLine = 0
    for trace in traceback.extract_stack():
        ignoreTrace = False
        if modulesToIgnore:
            for moduleToIgnore in actualModulesToIgnore:
                # TODO: Minor optimization: end loop once ``ignoreTrace`` is ``True``.
                tracedModuleName = os.path.basename(trace[0])
                if tracedModuleName == (moduleToIgnore + ".py"):
                    ignoreTrace = True
            if not ignoreTrace:
                sourcePath = trace[0]
                sourceLine = trace[1] - 1
        if not sourcePath:
            sourcePath = "<source>"
    result = InputLocation(sourcePath, hasColumn, hasCell, hasSheet)
    if sourceLine:
        result.advanceLine(sourceLine)
    return result

def createCopyOfLocation(location):
    """
    `InputLocation` being an exact copy of `location`.
    """
    if location is None:
        result = None
    else:
        result = InputLocation(location.filePath, location._hasColumn, location._hasCell, location._hasSheet)
        result._line = location._line
        result._column = location._column
        result._cell = location._cell
        result._sheet = location._sheet
    return result

class _BaseCutplaceError(Exception):
    """
    Exception that supports a `message` describing the error and an optional
    `location` in the input where the error happened.
    """
    def __init__(self, message, location=None, seeAlsoMessage=None, seeAlsoLocation=None, cause=None):
        """
        Create exception that supports a `message` describing the error and an optional
        `InputLocation` in the input where the error happened. If the message is related
        to another location (for example when attempting to redefine a field with
        the same name), ``seeAlsoMessage`` should describe the meaning of the other
        location and ``seeAlsoLocation`` should point to the location. If the exception is the
        result of another exception that happened earlier (for example a `UnicodeError`,
        ``cause`` should contain this exception to simplify debugging.
        """
        assert message
        assert (seeAlsoLocation and seeAlsoMessage) or not seeAlsoLocation
        # Note: We cannot use `super` because `Exception` is an old style class.
        Exception.__init__(self, message)
        self._location = createCopyOfLocation(location)
        self._seeAlsoMessage = seeAlsoMessage
        self._seeAlsoLocation = createCopyOfLocation(seeAlsoLocation)
        self._cause = cause

    @property
    def location(self):
        """Location in the input that cause the error or `None`."""
        return self._location

    @property
    def seeAlsoMessage(self):
        """
        A message further explaining the actual message by referring to another location in the
        input.
        """
        return self._seeAlsoMessage

    @property
    def seeAlsoLocation(self):
        """The location in the input related to the ``seeAlsoMessage`` or ``None``."""
        return self._seeAlsoLocation

    @property
    def cause(self):
        """The `Exception` that cause this error or `None`."""
        return self._cause

    def __str__(self):
        result = ""
        if self._location:
            result += str(self.location) + ": "
        # Note: We cannot use `super` because `Exception` is an old style class.
        result += Exception.__str__(self)
        if self.seeAlsoMessage:
            result += " (see also: "
            if self.seeAlsoLocation:
                result += str(self.seeAlsoLocation) + ": "
            result += self.seeAlsoMessage + ")"
        return result

class CutplaceError(_BaseCutplaceError):
    """
    Error detected by cutplace caused by issues in the ICD or data.
    """

class CutplaceUnicodeError(_BaseCutplaceError):
    """
    Error detected by cutplace caused by improperly encoded ICD or data.

    This error is not derived from `CutplaceError` because it will not be handled in
    any meaningful way and simply results in the the termination of the validation.
    """

