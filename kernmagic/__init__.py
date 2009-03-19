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

