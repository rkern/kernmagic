""" Robert Kern's %magics for IPython.

These use argparse to conveniently handle argument parsing.

    http://argparse.python-hosting.com/
"""

import os
import shlex
import sys

import argparse

from IPython import ipapi

import utils


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


def add_argparse_help(magic_func, parser):
    """ Add the help text from the ArgumentParser.
    """
    help_text = parser.format_help()
    # Replace the starting 'usage: ' with IPython's %.
    if help_text.startswith('usage: '):
        help_text = help_text.replace('usage: ', '%', 1)
    else:
        help_text = '%' + help_text

    magic_func.__doc__ += help_text


fwrite_parser = MagicArgumentParser('fwrite')
fwrite_parser.add_argument('-e', '--encoding', default='utf-8',
    help="the encoding to use for unicode objects; no effect on str objects "
        "[default: %(default)s]")
fwrite_parser.add_argument('-m', '--mode', default='wb',
    help="the file mode to use when opening the file for writing")
fwrite_parser.add_argument('variable', help="the name of the variable")
fwrite_parser.add_argument('filename', nargs='?',
    help="the filename to write [default: the variable's name]")

def magic_fwrite(self, arg):
    """ Write text out to a file.

"""
    args = fwrite_parser.parse_argstring(arg)
    if args.filename is None:
        args.filename = args.variable
    filename = os.path.expanduser(args.filename)

    if args.variable not in self.user_ns:
        try:
            obj = eval(args.variable, self.user_global_ns, self.user_ns)
        except Exception, e:
            raise ipapi.UsageError('variable %r not in namespace' % args.variable)
    else:
        obj = self.user_ns[args.variable]
    if isinstance(obj, unicode):
        obj = obj.encode(args.encoding)
    elif not isinstance(obj, str):
        obj = str(obj)

    f = open(filename, args.mode)
    f.write(obj)
    f.close()

add_argparse_help(magic_fwrite, fwrite_parser)


fread_parser = MagicArgumentParser('fread')
fread_parser.add_argument('-e', '--encoding',
    help="decode the text using this encoding "
        "[default: do not attempt to decode]")
fread_parser.add_argument('-m', '--mode', default='rb',
    help="the file mode to use when opening the file for reading")
fread_parser.add_argument('variable', help="the name of the variable")
fread_parser.add_argument('filename',
    help="the filename to read from")

def magic_fread(self, arg):
    """ Read text from a file into a variable.

"""
    args = fread_parser.parse_argstring(arg)
    filename = os.path.expanduser(args.filename)
    f = open(filename, args.mode)
    contents = f.read()
    f.close()
    if args.encoding:
        contents = contents.decode(args.encoding)

    self.user_ns[args.variable] = contents

add_argparse_help(magic_fread, fread_parser)


sym_parser = MagicArgumentParser('sym')
sym_parser.add_argument('-r', '--real', action='store_const', dest='kind',
    const='real', help="symbols are real variables")
sym_parser.add_argument('-i', '--int', action='store_const', dest='kind',
    const='integer', help="symbols are integer variables")
sym_parser.add_argument('-c', '--complex', action='store_const', dest='kind',
    const='complex', help="symbols are complex variables")
sym_parser.add_argument('-f', '--function', action='store_const', dest='kind',
    const='function', help="symbols are functions")
sym_parser.add_argument('-q', '--quiet', action='store_true',
    help="do not print out verbose information")
sym_parser.add_argument('names', nargs='+',
    help="the names of the variables to create")

def magic_sym(self, arg):
    """ Create Sympy variables easily.

"""
    try:
        import sympy
    except ImportError:
        raise ipapi.UsageError("could not import sympy.")
    args = sym_parser.parse_argstring(arg)
    factory = sympy.Symbol
    kwds = {}
    if args.kind == 'integer':
        kwds = dict(integer=True)
    elif args.kind == 'real':
        kwds = dict(real=True)
    elif args.kind == 'complex':
        kwds = dict(complex=True)
    elif args.kind == 'function':
        factory = sympy.Function

    if not args.quiet:
        if args.kind is not None:
            print 'Adding %s variables:' % args.kind
        else:
            print 'Adding variables:'
    for name in args.names:
        var = factory(name, **kwds)
        self.user_ns[name] = var
        if not args.quiet:
            print '  %s' % name

add_argparse_help(magic_sym, sym_parser)


def print_numpy_printoptions(opts):
    """ Print the given numpy print options.
    """
    print "Precision:  %(precision)s" % opts
    print "Threshold:  %(threshold)s" % opts
    print "Edge items: %(edgeitems)s" % opts
    print "Line width: %(linewidth)s" % opts
    print "Suppress:   %(suppress)s" % opts
    print "NaN:        %(nanstr)s" % opts
    print "Inf:        %(infstr)s" % opts

push_print_parser = MagicArgumentParser('push_print')
push_print_parser.add_argument('-p', '--precision', type=int,
    help="Number of digits of precision for floating point output.")
push_print_parser.add_argument('-t', '--threshold', type=int,
    help="Total number of array elements which trigger summarization "
         "rather than a full repr. 0 disables thresholding.")
push_print_parser.add_argument('-e', '--edgeitems', type=int,
    help="Number of array items in summary at beginning and end of each "
         "dimension.")
push_print_parser.add_argument('-l', '--linewidth', type=int,
    help="The number of characters per line for the purpose of inserting "
         "line breaks.")
push_print_parser.add_argument('-s', '--suppress', action='store_true',
    default=None,
    help="Suppress the printing of small floating point values.")
push_print_parser.add_argument('-S', '--no-suppress', action='store_false',
    dest='suppress', default=None,
    help="Do not suppress the printing of small floating point values.")
push_print_parser.add_argument('-n', '--nanstr',
    help="String representation of floating point not-a-number.")
push_print_parser.add_argument('-i', '--infstr',
    help="String representation of floating point infinity.")
push_print_parser.add_argument('-q', '--quiet', action='store_true',
    help="Do not print the new settings.")

def magic_push_print(self, arg):
    """ Set numpy array printing options by pushing onto a stack.

"""
    try:
        import numpy
    except ImportError:
        raise ipapi.UsageError("could not import numpy.")
    args = push_print_parser.parse_argstring(arg)
    kwds = {}
    if args.precision is not None:
        kwds['precision'] = args.precision
    if args.threshold is not None:
        if args.threshold == 0:
            args.threshold = sys.maxint
        kwds['threshold'] = args.threshold
    if args.edgeitems is not None:
        kwds['edgeitems'] = args.edgeitems
    if args.linewidth is not None:
        kwds['linewidth'] = args.linewidth
    if args.suppress is not None:
        kwds['suppress'] = args.suppress
    if args.nanstr is not None:
        kwds['nanstr'] = args.nanstr
    if args.infstr is not None:
        kwds['infstr'] = args.infstr

    old_options = numpy.get_printoptions()
    numpy.set_printoptions(**kwds)
    stack = getattr(self, '_numpy_printoptions_stack', [])
    stack.append(old_options)
    self._numpy_printoptions_stack = stack
    if not args.quiet:
        print_numpy_printoptions(numpy.get_printoptions())

add_argparse_help(magic_push_print, push_print_parser)


pop_print_parser = MagicArgumentParser('pop_print')
pop_print_parser.add_argument('-q', '--quiet', action='store_true',
    help="Do not print the new settings.")

def magic_pop_print(self, arg):
    """ Pop the last set of print options from the stack and use them.

"""
    try:
        import numpy
    except ImportError:
        raise ipapi.UsageError("could not import numpy.")
    args = pop_print_parser.parse_argstring(arg)

    stack = getattr(self, '_numpy_printoptions_stack', [])
    if stack:
        kwds = stack.pop()
        numpy.set_printoptions(**kwds)
    elif not args.quiet:
        print "At the end of the stack."
        print
    self._numpy_printoptions_stack = stack
    if not args.quiet:
        print_numpy_printoptions(numpy.get_printoptions())

add_argparse_help(magic_pop_print, pop_print_parser)


pt_parser = MagicArgumentParser('pt')
pt_parser.add_argument('variable', help="the name of the variable")

def magic_pt(self, arg):
    """ Print the traits of an object.

"""
    try:
        from IPython.external.pretty import pretty
    except ImportError:
        import pprint
        pretty = pprint.pformat
    args = pt_parser.parse_argstring(arg)

    if args.variable not in self.user_ns:
        try:
            obj = eval(args.variable, self.user_global_ns, self.user_ns)
        except Exception, e:
            raise ipapi.UsageError('variable %r not in namespace' % args.variable)
    else:
        obj = self.user_ns[args.variable]

    if not hasattr(obj, 'trait_names'):
        raise ipapi.UsageError('variable %r is not a HasTraits instance' % args.variable)
    from enthought.traits.has_traits import not_event
    names = obj.trait_names(type=not_event)
    names.sort()
    key_values = []
    for name in names:
        try:
            value = getattr(obj, name)
        except AttributeError:
            pvalue = '<undefined>'
        else:
            pvalue = pretty(value)
        key_values.append((name, pvalue))
    text = utils.wrap_key_values(key_values)
    print text

add_argparse_help(magic_pt, pt_parser)
