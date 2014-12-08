"""
Utility functions for compatibility with Python 2 and 3.

"""
# TODO: Probably we can eventually replace ``six`` by ``future``from
# https://pypi.python.org/pypi/future and remove compar all together.
import six

def python_2_unicode_compatible(cls):
    """
    A class decorator that defines __unicode__ and __str__ methods under
    Python 2. Under Python 3 it does nothing.

    To support Python 2 and 3 with a single code base, define a __str__
    method returning unicode text and apply this decorator to the class.

    The implementation is based on ``django.utils.encoding``.
    """
    if six.PY2:
        cls.__unicode__ = cls.__str__
        cls.__str__ = lambda self: self.__unicode__().encode('utf-8')
    return cls
