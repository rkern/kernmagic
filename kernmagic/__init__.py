""" Robert Kern's magics for IPython.

To enable these, put the following into your ~/.ipython/ipy_user_conf.py ::

    import kernmagic
    kernmagic.activate()

    # Some shortened aliases are provided for convenience, but you need to have
    # the following line to activate them, too.
    kernmagic.activate_alias()
"""


def activate(*args):
    """ Activate the given magics, all of them by default.
    """
    from IPython import ipapi
    import mymagics

    ip = ipapi.get()
    if not args:
        args = mymagics.__all__
    for name in args:
        if not name.startswith('magic_'):
            continue
        magic_name = name[len('magic_'):]
        ip.expose_magic(magic_name, getattr(mymagics, name))

def activate_aliases(*args):
    """ Activate the requests aliases, all of them by default.
    """
    from IPython import ipapi
    import mymagics

    ip = ipapi.get()
    if not args:
        args = mymagics.aliases.keys()
    for name in args:
        magic_name = mymagics.aliases[name]
        ip.expose_magic(magic_name, getattr(mymagics, name))
