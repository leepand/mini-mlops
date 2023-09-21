"""Utilities for make the code run both on Python2 and Python3.
"""
import sys

PY2 = sys.version_info[0] == 2

# urljoin
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin  # noqa: F401

# Dictionary iteration
if PY2:
    iterkeys = lambda d: d.iterkeys()
    itervalues = lambda d: d.itervalues()
    iteritems = lambda d: d.iteritems()
else:
    iterkeys = lambda d: iter(d.keys())
    itervalues = lambda d: iter(d.values())
    iteritems = lambda d: iter(d.items())

# string and text types
try:
    text_type = unicode
    string_types = (str, unicode)
    numeric_types = (int, long)
except NameError:
    text_type = str
    string_types = (str,)
    numeric_types = (int,)

if PY2:
    is_iter = lambda x: x and hasattr(x, "next")
else:
    is_iter = lambda x: x and hasattr(x, "__next__")

# imap
if PY2:
    from itertools import imap
else:
    imap = map


def safeunicode(obj, encoding="utf-8"):
    r"""
    Converts any given object to unicode string.
        >>> safeunicode('hello')
        u'hello'
        >>> safeunicode(2)
        u'2'
        >>> safeunicode('\xe1\x88\xb4')
        u'\u1234'
    """
    t = type(obj)
    if t is text_type:
        return obj
    elif t is bytes:
        return obj.decode(encoding)
    elif t in [int, float, bool]:
        return text_type(obj)
    # elif hasattr(obj, '__unicode__') or isinstance(obj, unicode):
    #    return unicode(obj)
    # else:
    #    return str(obj).decode(encoding)
    else:
        return text_type(obj)


def safestr(obj, encoding="utf-8"):
    r"""
    Converts any given object to utf-8 encoded string.
        >>> safestr('hello')
        'hello'
        >>> safestr(2)
        '2'
    """

    if PY2 and isinstance(obj, text_type):
        return obj.encode(encoding)
    elif is_iter(obj):
        return imap(safestr, obj)
    else:
        return str(obj)


if not PY2:
    # Since Python3, utf-8 encoded strings and unicode strings are the same thing
    safeunicode = safestr
