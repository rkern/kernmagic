import os
import struct
import sys
import textwrap


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
    from ctypes import windll, create_string_buffer

    width = 80
    height = 25

    # FIXME: wrap with a try: except:? What exceptions might I get?
    h = windll.kernel32.GetStdHandle(-12)
    csbi = create_string_buffer(22)
    res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)

    if res:
        (bufx, bufy, curx, cury, wattr,
         left, top, right, bottom, maxx, maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
        width = right - left + 1
        height = bottom - top + 1
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
        height, width = struct.unpack('hh', fcntl.ioctl(sys.stdout.fileno(),
            termios.TIOCGWINSZ, '1234'))
    except (ImportError, AttributeError, IOError), e:
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
    if width is None:
        width = terminal_size()[0]
    max_key = max(len(k) for k,v in key_values)
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
