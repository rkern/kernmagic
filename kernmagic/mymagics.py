""" Robert Kern's %magics for IPython.

These use argparse to conveniently handle argument parsing.

    http://argparse.python-hosting.com/
"""

from collections import defaultdict
import inspect
import os
import sys
import types

from IPython import ipapi

from magic_arguments import argument, magic_arguments, parse_argstring
import utils


def get_variable(ipshell, variable):
    """ Get a variable from the shell's namespace.
    """
    if variable not in ipshell.user_ns:
        try:
            obj = eval(variable, ipshell.user_global_ns, ipshell.user_ns)
        except Exception, e:
            raise ipapi.UsageError('variable %r not in namespace' % variable)
    else:
        obj = ipshell.user_ns[variable]
    return obj


@magic_arguments()
@argument('-e', '--encoding', default='utf-8',
    help="the encoding to use for unicode objects; no effect on str objects "
        "[default: %(default)s]")
@argument('-m', '--mode', default='wb',
    help="the file mode to use when opening the file for writing")
@argument('variable', help="the name of the variable")
@argument('filename', nargs='?',
    help="the filename to write [default: the variable's name]")
def magic_fwrite(self, arg):
    """ Write text out to a file.

"""
    args = parse_argstring(magic_fwrite, arg)
    if args.filename is None:
        args.filename = args.variable
    filename = os.path.expanduser(args.filename)

    obj = get_variable(self, args.variable)
    if isinstance(obj, unicode):
        obj = obj.encode(args.encoding)
    elif not isinstance(obj, str):
        obj = str(obj)

    f = open(filename, args.mode)
    f.write(obj)
    f.close()


@magic_arguments()
@argument('-e', '--encoding',
    help="decode the text using this encoding "
        "[default: do not attempt to decode]")
@argument('-m', '--mode', default='rb',
    help="the file mode to use when opening the file for reading")
@argument('variable', help="the name of the variable")
@argument('filename',
    help="the filename to read from")
def magic_fread(self, arg):
    """ Read text from a file into a variable.

"""
    args = parse_argstring(magic_fread, arg)
    filename = os.path.expanduser(args.filename)
    f = open(filename, args.mode)
    contents = f.read()
    f.close()
    if args.encoding:
        contents = contents.decode(args.encoding)

    self.user_ns[args.variable] = contents


@magic_arguments()
@argument('-r', '--real', action='store_const', dest='kind',
    const='real', help="symbols are real variables")
@argument('-i', '--int', action='store_const', dest='kind',
    const='integer', help="symbols are integer variables")
@argument('-c', '--complex', action='store_const', dest='kind',
    const='complex', help="symbols are complex variables")
@argument('-f', '--function', action='store_const', dest='kind',
    const='function', help="symbols are functions")
@argument('-q', '--quiet', action='store_true',
    help="do not print out verbose information")
@argument('names', nargs='+',
    help="the names of the variables to create")
def magic_sym(self, arg):
    """ Create Sympy variables easily.

"""
    try:
        import sympy
    except ImportError:
        raise ipapi.UsageError("could not import sympy.")
    args = parse_argstring(magic_sym, arg)
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


@magic_arguments()
@argument('-p', '--precision', type=int,
    help="Number of digits of precision for floating point output.")
@argument('-t', '--threshold', type=int,
    help="Total number of array elements which trigger summarization "
         "rather than a full repr. 0 disables thresholding.")
@argument('-e', '--edgeitems', type=int,
    help="Number of array items in summary at beginning and end of each "
         "dimension.")
@argument('-l', '--linewidth', type=int,
    help="The number of characters per line for the purpose of inserting "
         "line breaks.")
@argument('-s', '--suppress', action='store_true',
    default=None,
    help="Suppress the printing of small floating point values.")
@argument('-S', '--no-suppress', action='store_false',
    dest='suppress', default=None,
    help="Do not suppress the printing of small floating point values.")
@argument('-n', '--nanstr',
    help="String representation of floating point not-a-number.")
@argument('-i', '--infstr',
    help="String representation of floating point infinity.")
@argument('-q', '--quiet', action='store_true',
    help="Do not print the new settings.")
def magic_push_print(self, arg):
    """ Set numpy array printing options by pushing onto a stack.

"""
    try:
        import numpy
    except ImportError:
        raise ipapi.UsageError("could not import numpy.")
    args = parse_argstring(magic_push_print, arg)
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


@magic_arguments()
@argument('-q', '--quiet', action='store_true',
    help="Do not print the new settings.")
def magic_pop_print(self, arg):
    """ Pop the last set of print options from the stack and use them.

"""
    try:
        import numpy
    except ImportError:
        raise ipapi.UsageError("could not import numpy.")
    args = parse_argstring(magic_pop_print, arg)

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


def print_numpy_err(modes, errcall):
    """ Print the given numpy error modes.
    """
    print "Divide:    %(divide)s" % modes
    print "Overflow:  %(over)s" % modes
    print "Underflow: %(under)s" % modes
    print "Invalid:   %(invalid)s" % modes
    print "Call:      %r" % (errcall,)

error_choices = ["ignore", "warn", "raise", "call", "log"]

@magic_arguments()
@argument('-a', '--all', choices=error_choices, 
    help="Set the mode for all kinds of errors.")
@argument('-d', '--divide', choices=error_choices, 
    help="Set the mode for divide-by-zero errors.")
@argument('-o', '--over', choices=error_choices, 
    help="Set the mode for overflow errors.")
@argument('-u', '--under', choices=error_choices, 
    help="Set the mode for underflow errors.")
@argument('-i', '--invalid', choices=error_choices, 
    help="Set the mode for invalid domain errors (i.e. NaNs).")
@argument('-f', '--call-func',
    help="A function for use with the 'call' mode or a file-like "
        "object with a .write() method for use with the 'log' mode.")
@argument('-n', '--no-call-func', action='store_true',
    help="Remove any existing call function.")
@argument('-q', '--quiet', action='store_true',
    help="Do not print the new settings.")
def magic_push_err(self, arg):
    """ Set numpy numerical error handling via a stack.

"""
    try:
        import numpy
    except ImportError:
        raise ipapi.UsageError("could not import numpy.")

    sentinel = object()

    args = parse_argstring(magic_push_err, arg)
    kwds = {}
    errcall = sentinel
    for key in ['all', 'divide', 'over', 'under', 'invalid']:
        value = getattr(args, key)
        if value is not None:
            kwds[key] = value
    if args.call_func is not None:
        if args.no_call_func:
            raise ipapi.UsageError("You cannot specify both a --call-func and "
                "--no-call-func at the same time.")
        global_ns = self.shell.user_global_ns
        local_ns = self.shell.user_ns
        try:
            errcall = eval(args.call_func, global_ns, local_ns)
        except Exception, e:
            raise ipapi.UsageError('Could not find function %r.\n%s: %s' % 
                (args.call_func, e.__class__.__name__, e))
    elif args.no_call_func:
        errcall = None

    old_options = numpy.geterr()
    old_errcall = numpy.geterrcall()
    numpy.seterr(**kwds)
    if errcall is not sentinel:
        try:
            numpy.seterrcall(errcall)
        except ValueError, e:
            raise ipapi.UsageError(str(e))
    stack = getattr(self, '_numpy_err_stack', [])
    stack.append((old_options, old_errcall))
    self._numpy_err_stack = stack
    if not args.quiet:
        print_numpy_err(numpy.geterr(), numpy.geterrcall())


@magic_arguments()
@argument('-q', '--quiet', action='store_true',
    help="Do not print the new settings.")
def magic_pop_err(self, arg):
    """ Pop the last set of numpy numerical error handling settings from the
    stack.

"""
    try:
        import numpy
    except ImportError:
        raise ipapi.UsageError("could not import numpy.")
    args = parse_argstring(magic_pop_err, arg)

    stack = getattr(self, '_numpy_err_stack', [])
    if stack:
        kwds, errcall = stack.pop()
        numpy.seterr(**kwds)
        numpy.seterrcall(errcall)
    elif not args.quiet:
        print "At the end of the stack."
        print
    self._numpy_err_stack = stack
    if not args.quiet:
        print_numpy_err(numpy.geterr(), numpy.geterrcall())


@magic_arguments()
@argument('-n', '--no-group', dest='group', action='store_false',
    help="Do not group by the defining class.")
@argument('variable', help="the name of the variable")
def magic_print_traits(self, arg):
    """ Print the traits of an object.

"""
    try:
        from IPython.external.pretty import pretty
    except ImportError:
        import pprint
        pretty = pprint.pformat
    args = parse_argstring(magic_print_traits, arg)

    obj = get_variable(self, args.variable)
    if not hasattr(obj, 'trait_names'):
        raise ipapi.UsageError('variable %r is not a HasTraits instance' % args.variable)
    from enthought.traits.has_traits import not_event
    from enthought.traits.trait_errors import TraitError
    names = obj.trait_names(type=not_event)
    names.sort()
    key_values = []
    for name in names:
        try:
            value = getattr(obj, name)
        except (AttributeError, TraitError), e:
            pvalue = '<undefined>'
        else:
            pvalue = pretty(value)
        key_values.append((name, pvalue))
    if not args.group:
        print utils.wrap_key_values(key_values)
    else:
        trait_values = dict(key_values)
        for cls in inspect.getmro(type(obj))[::-1]:
            if hasattr(cls, 'class_trait_names'):
                local_key_values = []
                for trait in cls.class_trait_names():
                    if trait in trait_values:
                        local_key_values.append((trait, trait_values.pop(trait)))
                if local_key_values:
                    name = getattr(cls, '__name__', repr(cls))
                    print name
                    print '-'*len(name)
                    print utils.wrap_key_values(sorted(local_key_values))
                    print


@magic_arguments()
@argument('-n', '--no-group', dest='group', action='store_false',
    help="Do not group by the defining class.")
@argument('-p', '--private', action='store_true',
    help="Also display private methods that begin with an underscore.")
@argument('variable', help="The name of the variable.")
def magic_print_methods(self, arg):
    """ Print the methods of an object or type.

"""
    args = parse_argstring(magic_print_methods, arg)
    obj = get_variable(self, args.variable)
    if not isinstance(obj, (type, types.ClassType)):
        klass = type(obj)
    else:
        klass = obj
    attrs = inspect.classify_class_attrs(klass)
    grouped = defaultdict(list)
    all = []
    for name, kind, defining, value in attrs:
        if kind not in ('method', 'class method', 'static method'):
            continue
        if args.private or not name.startswith('_'):
            grouped[defining].append(name)
            all.append(name)
    if args.group:
        for cls in inspect.getmro(klass)[::-1]:
            if grouped[cls]:
                name = getattr(cls, '__name__', repr(cls))
                print name
                print '-'*len(name)
                print utils.columnize(grouped[cls])
    else:
        print utils.columnize(all)


@magic_arguments()
def magic_replace_context(self, parameter_s=''):
    """Replace the IPython namespace with a DataContext.

"""
    ip = ipapi.get()
    if hasattr(self.user_ns, 'subcontext'):
        # Toggle back to plain dict.
        user_ns = self.user_ns.subcontext
    else:
        from enthought.contexts.api import DataContext
        user_ns = DataContext(subcontext=self.user_ns)
        # Keep the plain dict as the globals.
        self.user_global_ns = self.user_ns
    self.user_ns = ip.user_ns = user_ns


__all__ = ['magic_fread', 'magic_fwrite', 'magic_sym', 'magic_push_print',
    'magic_pop_print', 'magic_push_err', 'magic_pop_err', 'magic_print_traits',
    'magic_replace_context', 'magic_print_methods']

aliases = dict(
    magic_print_traits='pt',
    magic_print_methods='pm',
)
