"""
Various utility functions.
"""
# Copyright (C) 2009-2010 Thomas Aglassinger
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
#  option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import codecs
import csv
import errno
import os
import platform
import re
import StringIO
import token
import tokenize
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
    Location in an input file, consisting of `line`, an optional `column` (pointing at a
    single character) and an optional cell (pointing a cell in a structured input such as CSV).  
    """
    def __init__(self, filePath, hasColumn=False, hasCell=False, hasSheet=False):
        assert filePath
        if isinstance(filePath, types.StringTypes):
            self.filePath = filePath
        else:
            self.filePath = "<io>"
        self.line = 0
        self.column = 0
        self.cell = 0
        self.sheet = 0
        self._hasColumn = hasColumn
        self._hasCell = hasCell
        self._hasSheet = hasSheet

    def advanceColumn(self, amount=1):
        assert amount is not None
        assert amount > 0
        assert self._hasColumn
        self.column += amount

    def advanceCell(self, amount=1):
        assert amount is not None
        assert amount > 0
        assert self._hasCell
        self.cell += amount

    def setCell(self, newCell):
        assert newCell is not None
        assert newCell >= 0
        assert self._hasCell
        self.cell = newCell

    def advanceLine(self):
        self.line += 1
        self.column = 0
        self.cell = 0

    def advanceSheet(self):
        self.sheet += 1
        self.line = 0
        self.column = 0
        self.cell = 0

    def __str__(self):
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

def createCallerInputLocation(modulesToIgnore=None):
    """
    ``InputLocation`` referring to the calling Python source code.
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
    result = InputLocation(sourcePath)
    result.line = sourceLine
    return result

class _BaseCutplaceError(Exception):
    """
    Exception that supports a `message` describing the error and an optional
    `location` in the input where the error happened.
    """
    def __init__(self, message, location=None, seeAlsoMessage=None, seeAlsoLocation=None, cause=None):
        """
        Create exception that supports a `message` describing the error and an optional
        `location` in the input where the error happened. If the message is related
        to another location (for example when attempting to redefine a field with
        the same name), `seeAlsoMessage` should describe the meaning of the other
        location and `seeAlsoLocation` should point to the location. If the exception is the
        result of another exception that happened earlier (for example a `UnicodeError`, 
        `cause` should contain this exception to simplify debugging.
        """
        assert message
        assert (seeAlsoLocation and seeAlsoMessage) or not seeAlsoLocation
        # Note: We cannot use `super` because `Exception` is an old style class.
        Exception.__init__(self, message)
        self._location = location
        self._seeAlsoMessage = seeAlsoMessage
        self._seeAlsoLocation = seeAlsoLocation
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
        """The location in the input related to the `seeAlsoMessage` or `None`."""
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
    
# The original source code for UTF8Recoder, UnicodeReader and UnicodeWriter
# is available from the Python documentation.
class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        # FIXME: This line raises UnicodeError describe in test_interface.testBrokenAsciiIcd().
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        try:
            result = self.reader.next().encode("utf-8")
        except UnicodeError, error:
            raise CutplaceUnicodeError("cannot decode input: %s" % error, cause=error)
        return result

class UnicodeCsvReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self

class UnicodeCsvWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = StringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

def valueOr(value, noneValue):
    """
    Value or noneValue in case value is None.
    """
    if value is None:
        result = noneValue
    else:
        result = value
    return result

def listdirMatching(folder, pattern):
    """
    Name of entries in folder that match regex pattern.
    """
    assert folder is not None
    assert pattern is not None
    
    regex = re.compile(pattern)
    for entry in os.listdir(folder):
        if regex.match(entry):
            yield entry

def mkdirs(folder):
    """
    Like `os.mkdirs()` but does not raise an `OSError` if `folder` already exists. 
    """
    assert folder is not None

    try:
        os.makedirs(folder)
    except OSError, error:
        if error.errno != errno.EEXIST:
            raise

def attemptToRemove(filePath):
    """
    Like `os.remove()` but does not raise an `OSError` if `filePath` does not exist. 
    """
    assert filePath is not None

    try:
        os.remove(filePath)
    except OSError, error:
        if error.errno != errno.EEXIST:
            raise
    
def validatedPythonName(name, value):
    """
    Validated and cleaned up `value` that represents a Python name with any whitespace removed.
    If validation fails, raise `NameError` with mentioning `name` as the name under which `value`
    is known to the user.
    """
    assert name
    assert value is not None
    
    readable = StringIO.StringIO(value.strip())
    toky = tokenize.generate_tokens(readable.readline)
    next = toky.next()
    nextType = next[0]
    result = next[1]
    if tokenize.ISEOF(nextType):
        raise NameError("%s must not be empty but was: %r" % (name, value))
    if nextType != token.NAME:
        raise NameError("%s must contain only ASCII letters, digits and underscore (_) but is: %r"
                         % (name, value))
    secondToken = toky.next()
    secondTokenType = secondToken[0]
    if not tokenize.ISEOF(secondTokenType):
        raise NameError("%s must be a single word, but after %r there also is %r" % (name, result, secondToken[1]))
    return result

def camelized(key, firstIsLower=False):
    """
    Camelized name of possibly multiple words separated by blanks that can be used for variables.
    """
    assert key is not None
    assert key == key.strip(), "key must be trimmed"
    result = ""
    for part in key.split():
        result += part[0].upper() + part[1:].lower() 
    if firstIsLower and result:
        result = result[0].lower() + result[1:]
    return result

def platformVersion():
    macVersion = platform.mac_ver()
    if (macVersion[0]):
        result = "Mac OS %s (%s)" % (macVersion[0], macVersion[2])
    else:
        result = platform.platform()
    return result
        
def pythonVersion():
        return platform.python_version()

def humanReadableList(items):
    """
    All values in `items` in a human readable form. This is ment to be used in error messages, where
    dumping "%r" to the user does not cut it.
    """
    assert items is not None
    itemCount = len(items)
    if itemCount == 0:
        result = ""
    elif itemCount == 1:
        result = "%r" % items[0]
    else:
        result = ""
        for itemIndex in range(itemCount):
            if itemIndex == itemCount - 1:
                result += " or "
            elif itemIndex > 0:
                result += ", "
            result += "%r" % items[itemIndex]
        assert result
    assert result is not None
    return result

def tokenizeWithoutSpace(text):
    """
    ``text`` split into token with any white space tokens removed.
    """
    assert text is not None
    for toky in tokenize.generate_tokens(StringIO.StringIO(text).readline):
        tokyType = toky[0]
        tokyText = toky[1]
        if ((tokyType != token.INDENT) and tokyText.strip()) or (tokyType == token.ENDMARKER):
            yield toky

def tokenText(toky):
    assert toky is not None
    tokyType = toky[0]
    tokyText = toky[1]
    if tokyType == token.STRING:
        result = tokyText[1:-1]
    else:
        result = tokyText
    return result

def isEofToken(someToken):
    """
    True if `someToken` is a token that represents an "end of file". 
    """
    assert someToken is not None
    return tokenize.ISEOF(someToken[0])

def isCommaToken(someToken):
    """
    True if `someToken` is a token that represents a comma (,). 
    """
    assert someToken
    return (someToken[0] == token.OP) and (someToken[1] == ",")
"""
Same as `path` but with suffix changed to `suffix`.

Examples:

>>> print tools.withSuffix("eggs.txt", ".rst")
eggs.rst
>>> print tools.withSuffix("eggs.txt", "")
eggs
>>> print tools.withSuffix(os.path.join("spam", "eggs.txt"), ".rst")
spam/eggs.rst
"""
def withSuffix(path, suffix=""):
    assert path is not None
    assert suffix is not None
    result = os.path.splitext(path)[0]
    if suffix:
        result += suffix
    return result
