""" Robert Kern's magics for IPython.
"""


def load_ipython_extension(ip):
    from .mymagics import KernMagics

    ip.register_magics(KernMagics)
    ip.magics_manager.register_alias('pt', 'print_traits')
    ip.magics_manager.register_alias('pm', 'print_methods')
