"""
Various internal utility functions.
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
import logging
import os
import token
import tokenize

from cutplace import _compat

#: Mapping for value of :option:`--log` to logging level.
LOG_LEVEL_NAME_TO_LEVEL_MAP = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


def mkdirs(folder):
    """
    Like :py:func:`os.mkdirs()` but does not raise an :py:exc:`OSError` if
    ``folder`` already exists.
    """
    assert folder is not None

    os.makedirs(folder, exist_ok=True)


def validated_python_name(name, value):
    """
    Validated and cleaned up ``value`` that represents a Python name with any
    whitespace removed. If validation fails, raise :py:exc:`NameError` with
    mentioning ``name`` as the name under which ``value`` is known to the
    user.
    """
    assert name
    assert value is not None

    toky = generated_tokens(value.strip())
    next_token = next(toky)
    next_type = next_token[0]
    result = next_token[1]
    if tokenize.ISEOF(next_type):
        raise NameError("%s must not be empty but was: %r" % (name, value))
    if next_type != token.NAME:
        raise NameError("%s must contain only ASCII letters, digits and underscore (_) but is: %r" % (name, value))
    second_token = next(toky)
    second_token_type = second_token[0]
    if second_token_type == token.NEWLINE and second_token[1] == "":
        # HACK: In Python 3.x a newline seems to be added either by generate_tokens() or readline().
        second_token = next(toky)
        second_token_type = second_token[0]
    if not tokenize.ISEOF(second_token_type):
        raise NameError("%s must be a single word, but after %r there also is %r" % (name, result, second_token[1]))
    return result


def generated_tokens(text):
    toky = list(tokenize.generate_tokens(_compat.token_io_readline(text)))
    if len(toky) >= 2 and is_newline_token(toky[-2]) and is_eof_token(toky[-1]):
        # HACK: Remove newline that generated_tokens() adds starting with Python 3.x but not before.
        del toky[-2]
    for result in toky:
        yield result


def human_readable_list(items, final_separator="or"):
    """
    All values in ``items`` in a human readable form. This is meant to be
    used in error messages, where dumping ``"%r"`` to the user does not cut
    it.
    """
    assert items is not None
    assert final_separator is not None
    item_count = len(items)
    if item_count == 0:
        result = ""
    elif item_count == 1:
        result = _compat.text_repr(items[0])
    else:
        result = ""
        for item_index in range(item_count):
            if item_index == item_count - 1:
                result += " " + final_separator + " "
            elif item_index > 0:
                result += ", "
            result += _compat.text_repr(items[item_index])
        assert result
    assert result is not None
    return result


def tokenize_without_space(text):
    """
    ``text`` split into token with any white space tokens removed.
    """
    assert text is not None
    for toky in generated_tokens(text):
        toky_type = toky[0]
        toky_text = toky[1]
        if ((toky_type != token.INDENT) and toky_text.strip()) or (toky_type == token.ENDMARKER):
            yield toky


def token_text(toky):
    assert toky is not None
    toky_type = toky[0]
    toky_text = toky[1]
    if toky_type == token.STRING:
        result = toky_text[1:-1]
    else:
        result = toky_text
    return result


def is_newline_token(some_token):
    assert some_token is not None
    return some_token[0] == token.NEWLINE and some_token[1] == ""


def is_eof_token(some_token):
    """
    True if ``some_token`` is a token that represents an "end of file".
    """
    assert some_token is not None
    return tokenize.ISEOF(some_token[0])


def is_comma_token(some_token):
    """
    True if ``some_token`` is a token that represents a comma (,).
    """
    assert some_token
    return (some_token[0] == token.OP) and (some_token[1] == ",")


def with_suffix(path, suffix=""):
    """
    Same as ``path`` but with suffix changed to ``suffix``.

    Examples:

    >>> with_suffix("eggs.txt", ".rst")
    'eggs.rst'
    >>> with_suffix("eggs.txt", "")
    'eggs'
    >>> with_suffix(os.path.join("spam", "eggs.txt"), ".rst").replace(os.sep, '/')
    'spam/eggs.rst'
    """
    assert path is not None
    assert suffix is not None
    result = os.path.splitext(path)[0]
    if suffix:
        result += suffix
    return result


def length_of_int(int_value):
    assert int_value is not None
    assert isinstance(int_value, int), "value=%r" % int_value

    return len(str(int_value))
