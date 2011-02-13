"""
Various internal utility functions.
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
import codecs
import csv
import errno
import logging
import os
import platform
import re
import StringIO
import token
import tokenize


# Mapping for value of --log to logging level.
LogLevelNameToLevelMap = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}

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
            from tools import CutplaceUnicodeError
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
    Like ``os.mkdirs()`` but does not raise an `OSError` if ``folder`` already exists.
    """
    assert folder is not None

    try:
        os.makedirs(folder)
    except OSError, error:
        if error.errno != errno.EEXIST:
            raise

def attemptToRemove(filePath):
    """
    Like ``os.remove()`` but does not raise an `OSError` if ``filePath`` does not exist.
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
    If validation fails, raise `NameError` with mentioning ``name`` as the name under which
    ``value``  is known to the user.
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

def decamelized(name):
    """
    Decamlized, all lower case ``name`` with former upper case letters marking words separated by blanks.

    Examples:

    >>> decamelized('some')
    'some'
    >>> decamelized('someMore')
    'some more'
    >>> decamelized('EvenMore')
    'Even more'
    >>> decamelized('')
    ''
    """
    assert name is not None
    assert name == name.strip(), "name must be trimmed"
    if name:
        result = name[0]
        for c in name[1:]:
            if c.isdigit() or c.islower():
                result += c
            else:
                result += " " + c.lower()
    else:
        result = ""
    return result

def basedText(longNumber, base, numerals="0123456789abcdefghijklmnopqrstuvwxyz"):
    # Based on code found at:
    # http://stackoverflow.com/questions/2267362/convert-integer-to-a-string-in-a-given-numeric-base-in-python
    assert longNumber is not None
    assert numerals is not None
    assert base > 0
    assert base <= len(numerals)

    zero = numerals[0]
    result = ((longNumber == 0) and  zero) \
        or ( basedText(longNumber // base, base, numerals).lstrip(zero) + numerals[longNumber % base])
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
    All values in `items` in a human readable form. This is meant to be used in error messages, where
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

def withSuffix(path, suffix=""):
    """
    Same as `path` but with suffix changed to `suffix`.

    Examples:

    >>> withSuffix("eggs.txt", ".rst")
    'eggs.rst'
    >>> withSuffix("eggs.txt", "")
    'eggs'
    >>> withSuffix(os.path.join("spam", "eggs.txt"), ".rst")
    'spam/eggs.rst'
    """
    assert path is not None
    assert suffix is not None
    result = os.path.splitext(path)[0]
    if suffix:
        result += suffix
    return result

def asBytes(text):
    """
    Same as ``text`` but represented as list of integers.

    >>> asBytes("abc")
    [97, 98, 99]
    >>> asBytes("\\x00\\xff")
    [0, 255]
    """
    assert text is not None
    return [ord(item) for item in text]

def isEqualBytes(some, other):
    """
    ``True`` if the bytes of ``some`` and ``other`` match. This allows to
    compare two raw strings with none ASCII characters without running into
    a "UnicodeWarning: Unicode equal comparison failed to convert both
    arguments to Unicode - interpreting them as being unequal".
    """
    assert some is not None
    assert other is not None
    someBytes = asBytes(some)
    otherBytes = asBytes(other)
    return someBytes == otherBytes
