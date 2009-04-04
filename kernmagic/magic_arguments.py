""" A decorator-based method of constructing IPython magics with argparse option
handling.
"""

import shlex

from IPython.external import argparse
from IPython import ipapi


class MagicArgumentParser(argparse.ArgumentParser):
    """ An ArgumentParser tweaked for use by IPython magics.
    """
    def __init__(self,
                 prog=None,
                 usage=None,
                 description=None,
                 epilog=None,
                 version=None,
                 parents=None,
                 formatter_class=argparse.HelpFormatter,
                 prefix_chars='-',
                 argument_default=None,
                 conflict_handler='error',
                 add_help=False):
        if parents is None:
            parents = []
        super(MagicArgumentParser, self).__init__(prog=prog, usage=usage,
            description=description, epilog=epilog, version=version,
            parents=parents, formatter_class=formatter_class,
            prefix_chars=prefix_chars, argument_default=argument_default,
            conflict_handler=conflict_handler, add_help=add_help)

    def error(self, message):
        """ Raise a catchable error instead of exiting.
        """
        raise ipapi.UsageError(message)

    def parse_argstring(self, argstring):
        """ Split a string into an argument list and parse that argument list.
        """
        argv = shlex.split(argstring)
        return self.parse_args(argv)


def construct_parser(magic_func):
    """ Construct an argument parser using the function decorations.
    """
    kwds = getattr(magic_func, 'argcmd_kwds', {})
    if 'description' not in kwds:
        kwds['description'] = getattr(magic_func, '__doc__', None)
    arg_name = real_name(magic_func)
    parser = MagicArgumentParser(arg_name, **kwds)
    # Reverse the list of decorators in order to apply them in the
    # order in which they appear in the source.
    group = None
    for deco in magic_func.decorators[::-1]:
        result = deco.add_to_parser(parser, group)
        if result is not None:
            group = result

    # Replace the starting 'usage: ' with IPython's %.
    help_text = parser.format_help()
    if help_text.startswith('usage: '):
        help_text = help_text.replace('usage: ', '%', 1)
    else:
        help_text = '%' + help_text

    # Replace the magic function's docstring with the full help text.
    magic_func.__doc__ = help_text

    return parser


def parse_argstring(magic_func, argstring):
    """ Parse the string of arguments for the given magic function.
    """
    args = magic_func.parser.parse_argstring(argstring)
    return args


def real_name(magic_func):
    """ Find the real name of the magic.
    """
    magic_name = magic_func.__name__
    if magic_name.startswith('magic_'):
        magic_name = magic_name[len('magic_'):]
    arg_name = getattr(magic_func, 'argcmd_name', magic_name)
    return arg_name


def add_exposer(magic_func):
    """ Add a function to the magic which will expose it.
    """
    def expose(ip=None):
        if ip is None:
            from IPython import ipapi
            ip = ipapi.get()
        ip.expose_magic(real_name(magic_func), magic_func)
    magic_func.expose = expose


class ArgDecorator(object):
    """ Base class for decorators to add ArgumentParser information to a method.
    """

    def __call__(self, func):
        if not getattr(func, 'has_arguments', False):
            func.has_arguments = True
            func.decorators = []
            add_exposer(func)
        func.decorators.append(self)
        return func

    def add_to_parser(self, parser, group):
        """ Add this object's information to the parser, if necessary.
        """
        pass


class magic_arguments(ArgDecorator):
    """ Mark the magic as having argparse arguments and possibly adjust the
    name.
    """

    def __init__(self, name=None):
        self.name = name

    def __call__(self, func):
        if not getattr(func, 'has_arguments', False):
            func.has_arguments = True
            func.decorators = []
            add_exposer(func)
        if self.name is not None:
            func.argcmd_name = self.name
        # This should be the first decorator in the list of decorators, thus the
        # last to execute. Build the parser.
        func.parser = construct_parser(func)
        return func


class argument(ArgDecorator):
    """ Store arguments and keywords to pass to add_argument().

    Instances also serve to decorate command methods.
    """
    def __init__(self, *args, **kwds):
        self.args = args
        self.kwds = kwds

    def add_to_parser(self, parser, group):
        """ Add this object's information to the parser.
        """
        if group is not None:
            parser = group
        parser.add_argument(*self.args, **self.kwds)
        return None


class argument_group(ArgDecorator):
    """ Store arguments and keywords to pass to add_argument_group().

    Instances also serve to decorate command methods.
    """
    def __init__(self, *args, **kwds):
        self.args = args
        self.kwds = kwds

    def add_to_parser(self, parser, group):
        """ Add this object's information to the parser.
        """
        group = parser.add_argument_group(*self.args, **self.kwds)
        return group


class kwds(ArgDecorator):
    """ Provide other keywords to the sub-parser constructor.
    """
    def __init__(self, **kwds):
        self.kwds = kwds

    def __call__(self, func):
        func = super(kwds, self).__call__(func)
        func.argcmd_kwds = self.kwds
        return func


__all__ = ['magic_arguments', 'argument', 'argument_group', 'kwds',
    'parse_argstring']
