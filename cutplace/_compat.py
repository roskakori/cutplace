"""
Utility functions for compatibility with Python 2 and 3.

Part of the code found here is derived from
https://pypi.python.org/pypi/future and
https://docs.python.org/2/library/csv.html#examples.
"""
# TODO: Probably we can eventually replace ``six`` by ``future`` from
#  and remove `_compat` all together.
import csv

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
    assert (text is None) or isinstance(text, six.string_types)

    result = repr(text)
    if six.PY2 and result.startswith('u'):
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
    # Read CSV using Python 2.6+.
    import codecs

    def _key_to_str_value_map(key_to_value_map):
        """
        Similar to ``key_to_value_map`` but with values of type `unicode`
        converted to `str` because in Python 2 `csv.reader` can only process
        byte strings for formatting parameters, e.g. delimiter=b';' instead of
        delimiter=u';'. This quickly becomes an annoyance to the caller, in
        particular with `from __future__ import unicode_literals` enabled.
        """
        return dict((key, value if not isinstance(value, six.text_type) else str(value))
                    for key, value in key_to_value_map.items())

    class _UnicodeCsvWriter:
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
            row_as_list = list(row)
            try:
                row_to_write = [item.encode('utf-8') for item in row_as_list]
                self._csv_writer.writerow(row_to_write)
            except TypeError as error:
                raise TypeError('%s: %s' % (error, row_as_list))
            data = self._queue.getvalue()
            data = data.decode("utf-8")
            self._target_stream.write(data)
            # Clear the BytesIO before writing the next row.
            self._queue.seek(0)
            self._queue.truncate(0)

        def writerows(self, rows):
            for row in rows:
                self.writerow(row)

    # TODO: Check if the iterators below can be simplified using `six.Iterator` which already has `next()`.

    class _UTF8Recoder(object):
        """
        Iterator that reads an encoded stream and reencodes the input to UTF-8
        """

        def __init__(self, f, encoding):
            self.reader = codecs.getreader(encoding)(f)

        def __iter__(self):
            return self

        def next(self):
            return self.reader.next().encode('utf-8')

    class _UnicodeReader(object):
        """
        A CSV reader which will iterate over lines in the CSV file 'csv_file',
        which is encoded in the given encoding.
        """

        def __init__(self, csv_file, dialect=csv.excel, encoding='utf-8', **keywords):
            csv_file = _UTF8Recoder(csv_file, encoding)
            self.reader = csv.reader(csv_file, dialect=dialect, **keywords)
            self.line_num = -1

        def next(self):
            self.line_num += 1
            row = self.reader.next()
            result = [six.text_type(item, 'utf-8') for item in row]
            return result

        def __iter__(self):
            return self

    def delimited_reader(delimited_file, encoding, **keywords):
        """
        Similar to `csv.reader` but with support for unicode.
        """
        # TOOD: Provide a drop in replacement for `csv.reader()` that does not require ``encoding``.
        str_keywords = _key_to_str_value_map(keywords)
        return _UnicodeReader(delimited_file, encoding=encoding, **str_keywords)


def csv_writer(target, dialect=csv.excel, **keywords):
    """
    Same as Python 3's `csv.writer` but also works with Python 2.6+.
    """
    if six.PY2:
        result = _UnicodeCsvWriter(target, dialect=dialect, **keywords)
    else:
        result = csv.writer(target, dialect=dialect, **keywords)
    return result
