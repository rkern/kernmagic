""" Robert Kern's magics for IPython.
"""


def _define_magic(ip, *args, **kwds):
    """ Compatibility wrapper for defining magics.
    """
    shell = getattr(ip, 'shell', ip)
    shell.define_magic(*args, **kwds)

def activate(ip, *args):
    """ Activate the given magics, all of them by default.
    """
    from . import mymagics

    if not args:
        args = mymagics.__all__
    for name in args:
        if not name.startswith('magic_'):
            continue
        magic_name = name[len('magic_'):]
        _define_magic(ip, magic_name, getattr(mymagics, name))

def activate_aliases(ip, *args):
    """ Activate the requests aliases, all of them by default.
    """
    from . import mymagics

    if not args:
        args = mymagics.aliases.keys()
    for name in args:
        magic_name = mymagics.aliases[name]
        _define_magic(ip, magic_name, getattr(mymagics, name))

def load_ipython_extension(ip):
    activate(ip)
    activate_aliases(ip)
