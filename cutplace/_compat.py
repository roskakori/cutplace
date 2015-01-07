"""
Utility functions for compatibility with Python 2 and 3.
"""
# TODO: Probably we can eventually replace ``six`` by ``future``from
# https://pypi.python.org/pypi/future and remove `_compat` all together.
import csv
import io

import six


def python_2_unicode_compatible(cls):
    """
    A class decorator that defines __unicode__ and __str__ methods under
    Python 2. Under Python 3 it does nothing.

    To support Python 2 and 3 with a single code base, define a __str__
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
    if six.PY2:
        token_io = six.StringIO(text)
    else:
        token_io = six.StringIO(text)
    # TODO: Test if six.StringIO(text).readline works for all versions.
    return token_io.readline


if six.PY2:
    class _UnicodeCsvWriter:
        """
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
            self._queue = io.BytesIO()
            self._csv_writer = csv.writer(self._queue, dialect=dialect, **keywords)
            self._target_stream = target_stream

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


def csv_writer(target, dialect=csv.excel, **keywords):
    """
    Same as Python 3's `csv.writer` but also works with Python 2.6+.
    """
    if six.PY2:
        result = _UnicodeCsvWriter(target, dialect=dialect, **keywords)
    else:
        result = csv.writer(target, dialect=dialect, **keywords)
    return result
