import os
import struct
import sys
import textwrap
import warnings


def terminal_size():
    """ Return the width and height of the terminal in a cross-platform manner.
    """
    if sys.platform == 'win32':
        width, height = _terminal_size_win32()
    else:
        width, height = _terminal_size_unix()
    return width, height


def _terminal_size_win32():
    """ Return the width and height of the terminal on 32-bit Windows.

    This code derives from the Python Cookbook recipe by Alexander Belchenko
    available under the PSF license.
    http://code.activestate.com/recipes/440694/
    """
    width = 80
    height = 25

    try:
        from ctypes import windll, create_string_buffer

        # FIXME: wrap with a try: except:? What exceptions might I get?
        h = windll.kernel32.GetStdHandle(-12)
        csbi = create_string_buffer(22)
        res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)

        if res:
            (bufx, bufy, curx, cury, wattr,
             left, top, right, bottom, maxx, maxy) = struct.unpack(
                 "hhhhHhhhhhh", csbi.raw)
            width = right - left + 1
            height = bottom - top + 1
    except Exception as e:
        warnings.warn("Could not get terminal size due to exception.\n%s: %s"
                      % (type(e).__name__, e))
    # Windows consoles appear to treat the \n as a character.
    width -= 1
    return width, height


def _terminal_size_unix():
    """ Return the width and height of the terminal on UNIX-type systems.
    """
    width = -1
    height = -1
    try:
        import fcntl
        import termios
        height, width = struct.unpack('hh', fcntl.ioctl(
            sys.stdout.fileno(), termios.TIOCGWINSZ, '1234'))
    except (ImportError, AttributeError, IOError):
        pass
    if width <= 0:
        width = os.environ.get('COLUMNS', -1)
    if height <= 0:
        height = os.environ.get('LINES', -1)
    if width <= 0:
        width = 80
    if height <= 0:
        height = 25
    return width, height


def wrap_key_values(key_values, sep=':', width=None):
    """ Format key-value pairs of strings.
    """
    if not key_values:
        # Early exit so we can assume at least one item later.
        return ""
    if width is None:
        width = terminal_size()[0]
    max_key = max(len(k) for k, v in key_values)
    len_prefix = max_key + len(sep) + 1
    blank = ' ' * len_prefix
    lines = []
    for key, value in key_values:
        value_lines = textwrap.wrap(value, width=width - len_prefix)
        lines.append('%-*s%s' % (len_prefix, key+sep, value_lines[0]))
        for vl in value_lines[1:]:
            lines.append('%s%s' % (blank, vl))
    text = '\n'.join(lines)
    return text


# Adapted from cmd.py
def columnize(strings, displaywidth=None):
    """ Format a list of strings as a compact set of columns.

    Each column is only as wide as necessary.
    Columns are separated by two spaces (one was not legible enough).
    """
    if displaywidth is None:
        displaywidth = terminal_size()[0]
    if not strings:
        return ''
    nonstrings = [i for i in range(len(strings))
                  if not isinstance(strings[i], str)]
    if nonstrings:
        raise TypeError("Not strings: %r" % (nonstrings,))
    size = len(strings)
    if size == 1:
        return '%s\n' % strings[0]
    # Try every row count from 1 upwards
    for nrows in range(1, len(strings)):
        ncols = (size+nrows-1) // nrows
        colwidths = []
        totwidth = -2
        for col in range(ncols):
            colwidth = 0
            for row in range(nrows):
                i = row + nrows*col
                if i >= size:
                    break
                x = strings[i]
                colwidth = max(colwidth, len(x))
            colwidths.append(colwidth)
            totwidth += colwidth + 2
            if totwidth > displaywidth:
                break
        if totwidth <= displaywidth:
            break
    else:
        nrows = len(strings)
        ncols = 1
        colwidths = [0]
    lines = []
    for row in range(nrows):
        texts = []
        for col in range(ncols):
            i = row + nrows*col
            if i >= size:
                x = ""
            else:
                x = strings[i]
            texts.append(x)
        while texts and not texts[-1]:
            del texts[-1]
        for col in range(len(texts)):
            texts[col] = texts[col].ljust(colwidths[col])
        lines.append('%s\n' % str('  '.join(texts)))
    formatted = ''.join(lines)
    return formatted
