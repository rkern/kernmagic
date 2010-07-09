""" Robert Kern's magics for IPython.
"""


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
        ip.shell.define_magic(magic_name, getattr(mymagics, name))

def activate_aliases(ip, *args):
    """ Activate the requests aliases, all of them by default.
    """
    from . import mymagics

    if not args:
        args = mymagics.aliases.keys()
    for name in args:
        magic_name = mymagics.aliases[name]
        ip.shell.define_magic(magic_name, getattr(mymagics, name))

def load_ipython_extension(ip):
    activate(ip)
    activate_aliases(ip)
