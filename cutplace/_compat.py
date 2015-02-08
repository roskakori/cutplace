"""
Utility functions for compatibility with Python 2 and 3.

Part of the code found here is derived from
https://pypi.python.org/pypi/future and
https://docs.python.org/2/library/csv.html#examples.
"""
# Copyright (C) 2009-2015 Thomas Aglassinger
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
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import csv

# TODO: Probably we can eventually replace ``six`` by ``future`` from
#  and remove `_compat` all together.
import six


def python_2_unicode_compatible(cls):
    """
    Class decorator to defines ``__unicode__()`` and ``__str__()`` under
    Python 2. Under Python 3 it does nothing.

    To support Python 2 and 3 with a single code base, define a ``__str__()``
    method returning unicode text and apply this decorator to the class.

    The implementation is based on ``django.utils.encoding``.
    """
    if six.PY2:  # pragma: no cover
        cls.__unicode__ = cls.__str__
        cls.__str__ = lambda self: self.__unicode__().encode('utf-8')
    return cls


def text_repr(text):
    """
    Similar to `repr()` but ensures that even under Python 2 there is not
    'u' prefix for unicode strings.
    """
    result = repr(text)
    if six.PY2 and isinstance(text, six.text_type):
        assert result.startswith('u'), 'result=%r' % result
        result = result[1:]
    return result


def token_io_readline(text):
    """
    A readline function that can be used by `tokenize.generate_tokens()`.
    Using `io.StringIO.readline` under Python 2 would result in
    ``TypeError: initial_value must be unicode or None, not str``.
    """
    assert text is not None
    return six.StringIO(text).readline


if six.PY2:
    # Read and write CSV using Python 2.6+.
    import io

    def _key_to_str_value_map(key_to_value_map):
        """
        Similar to ``key_to_value_map`` but with values of type `unicode`
        converted to `str` because in Python 2 `csv.reader` can only process
        byte strings for formatting parameters, e.g. delimiter=b';' instead of
        delimiter=u';'. This quickly becomes an annoyance to the caller, in
        particular with `from __future__ import unicode_literals` enabled.
        """
        return dict((key, value if not isinstance(value, six.text_type) else six.binary_type(value))
                    for key, value in key_to_value_map.items())

    class _UnicodeCsvWriter(object):
        r"""
        A CSV writer for Python 2 which will write rows to `target_stream`
        which must be able to write unicode strings.

        To obtain a target stream for a file use for example (note the
        ``newline='``):

        >>> import io
        >>> import os
        >>> import tempfile
        >>> target_path = os.path.join(tempfile.tempdir, 'test_compat.UnicodeCsvWriter.csv')
        >>> target_stream = io.open(target_path, 'w', newline='', encoding='utf-8')

        This is based on ``UnicodeWriter`` from <https://docs.python.org/2/library/csv.html> but expects the
        target to accept unicode strings.
        """

        def __init__(self, target_stream, dialect=csv.excel, **keywords):
            self._target_stream = target_stream
            self._queue = io.BytesIO()
            str_keywords = _key_to_str_value_map(keywords)
            self._csv_writer = csv.writer(self._queue, dialect=dialect, **str_keywords)

        def writerow(self, row):
            assert row is not None

            row_as_list = list(row)
            # Convert ``row`` to a list of unicode strings.
            row_to_write = []
            for item in row_as_list:
                if item is None:
                    item = ''
                elif not isinstance(item, six.text_type):
                    item = six.text_type(item)
                row_to_write.append(item.encode('utf-8'))
            try:
                self._csv_writer.writerow(row_to_write)
            except TypeError as error:
                raise TypeError('%s: %s' % (error, row_as_list))
            data = self._queue.getvalue()
            data = data.decode('utf-8')
            self._target_stream.write(data)
            # Clear the BytesIO before writing the next row.
            self._queue.seek(0)
            self._queue.truncate(0)

        def writerows(self, rows):
            for row in rows:
                self.writerow(row)

    class _Utf8Recoder(object):
        """
        Iterator that reads a text stream and reencodes the input to UTF-8.
        """

        def __init__(self, text_stream):
            self._text_stream = text_stream

        def __iter__(self):
            return self

        def next(self):
            return self._text_stream.next().encode('utf-8')

    class _UnicodeCsvReader(object):
        """
        A CSV reader which will iterate over lines in the CSV file 'csv_file',
        which is encoded in the given encoding.
        """

        def __init__(self, csv_file, dialect=csv.excel, **keywords):
            csv_file = _Utf8Recoder(csv_file)
            str_keywords = _key_to_str_value_map(keywords)
            self.reader = csv.reader(csv_file, dialect=dialect, **str_keywords)
            self.line_num = -1

        def next(self):
            self.line_num += 1
            row = self.reader.next()
            result = [item.decode('utf-8') for item in row]
            return result

        def __iter__(self):
            return self


def csv_reader(source_text_stream, dialect=csv.excel, **keywords):
    """
    Same as Python 3's `csv.reader` but also works with Python 2.6+.
    """
    assert source_text_stream is not None

    if six.PY2:
        result = _UnicodeCsvReader(source_text_stream, dialect=dialect, **keywords)
    else:
        result = csv.reader(source_text_stream, dialect=dialect, **keywords)
    return result


def csv_writer(target_text_stream, dialect=csv.excel, **keywords):
    """
    Same as Python 3's `csv.writer` but also works with Python 2.6+.
    """
    assert target_text_stream is not None

    if six.PY2:
        result = _UnicodeCsvWriter(target_text_stream, dialect=dialect, **keywords)
    else:
        result = csv.writer(target_text_stream, dialect=dialect, **keywords)
    return result
