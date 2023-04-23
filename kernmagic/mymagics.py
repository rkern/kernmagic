""" Robert Kern's %magics for IPython.
"""

from __future__ import print_function

from collections import defaultdict
from io import StringIO
import doctest
import importlib
import inspect
import os
import sys
import types

from IPython.core.error import UsageError
from IPython.core.magic import Magics, line_magic, magics_class
from IPython.core.magic_arguments import (
    argument, magic_arguments, parse_argstring)
from IPython.lib import demo
from IPython.utils import io

from . import utils


ERROR_CHOICES = ["ignore", "warn", "raise", "call", "log"]


def print_numpy_printoptions(opts):
    """ Print the given numpy print options.
    """
    text = ("Precision:  {precision}\n"
            "Threshold:  {threshold}\n"
            "Edge items: {edgeitems}\n"
            "Line width: {linewidth}\n"
            "Suppress:   {suppress}\n"
            "NaN:        {nanstr}\n"
            "Inf:        {infstr}").format(**opts)
    print(text, file=io.stdout)


def print_numpy_err(modes, errcall):
    """ Print the given numpy error modes.
    """
    text = ("Divide:    {divide}\n"
            "Overflow:  {over}\n"
            "Underflow: {under}\n"
            "Invalid:   {invalid}\n"
            "Call:      {errcall}").format(errcall=errcall, **modes)
    print(text, file=io.stdout)


class DoctestDemo(demo.IPythonDemo):
    """ Extract doctest blocks for demo purposes.
    """

    def reset(self):
        """Reset the namespace and seek pointer to restart the demo"""
        self.user_ns = {}
        self.user_ns.update(self.ip_ns)
        self.finished = False
        self.block_index = 0

    def reload(self):
        """ Reload source and initialize state.
        """
        self.fload()
        docstring = self.fobj.read()
        parser = doctest.DocTestParser()
        parser = parser.parse(docstring)
        self.preludes = {}
        self.wants = {}
        self.src_blocks = []
        index = 0
        for item in parser:
            if isinstance(item, basestring):
                self.preludes[index] = item
            else:
                self.src_blocks.append(item.source)
                if item.want != '':
                    self.wants[index] = item.want
                index += 1
        self.src = ''.join(self.src_blocks)
        nblocks = len(self.src_blocks)
        self._silent = [False]*nblocks
        self._auto = [False]*nblocks
        self.auto_all = False
        self.nblocks = nblocks

        # also build syntax-highlighted source
        self.src_blocks_colored = map(self.ip_colorize, self.src_blocks)

        # ensure clean namespace and seek offset
        self.reset()

    def displayhook(self, obj):
        """ Simple displayhook.
        """
        if obj is not None:
            print('output:', file=io.stdout)
            print(repr(obj), file=io.stdout)

    def runlines(self, source):
        """ Execute a string with one or more lines of code.
        """
        code = compile(source, '<string>', 'single')
        oldhook = sys.displayhook
        sys.displayhook = self.displayhook
        try:
            exec(code, self.user_ns)
        finally:
            sys.displayhook = oldhook

    def show(self, index=None):
        """ Show a single block on screen.
        """
        index = self._get_index(index)
        if index is None:
            return
        if index in self.preludes:
            print(self.preludes[index], file=io.stdout)
        lines = self.src_blocks_colored[index].splitlines()
        lines[0] = '>>> ' + lines[0]
        for i in range(1, len(lines)):
            lines[i] = '... ' + lines[i]
        print(''.join(lines), file=io.stdout)
        if index in self.wants:
            print(self.wants[index], file=io.stdout)
        sys.stdout.flush()

    # These methods are meant to be overridden by subclasses who may wish to
    # customize the behavior of of their demos.
    def marquee(self, txt='', width=78, mark='*'):
        """ Return the input string formatted nicely.
        """
        return txt


@magics_class
class KernMagics(Magics):
    """ Loose collection of my own magics.
    """

    def get_variable(self, variable):
        """ Get a variable from the shell's namespace.
        """
        ipshell = self.shell
        if variable not in ipshell.user_ns:
            try:
                obj = eval(variable, ipshell.user_global_ns, ipshell.user_ns)
            except Exception:
                raise UsageError('variable %r not in namespace' % variable)
        else:
            obj = ipshell.user_ns[variable]
        return obj

    @magic_arguments()
    @argument('-e', '--encoding', default='utf-8',
              help=("the encoding to use for unicode objects; no effect on "
                    "str objects [default: %(default)s]"))
    @argument('-m', '--mode', default='wb',
              help="the file mode to use when opening the file for writing")
    @argument('variable', help="the name of the variable")
    @argument('filename', nargs='?',
              help="the filename to write [default: the variable's name]")
    @line_magic
    def fwrite(self, arg):
        """ Write text out to a file.

    """
        args = parse_argstring(self.fwrite, arg)
        if args.filename is None:
            args.filename = args.variable
        filename = os.path.expanduser(args.filename)

        obj = self.get_variable(args.variable)
        if isinstance(obj, unicode):
            obj = obj.encode(args.encoding)
        elif not isinstance(obj, str):
            obj = str(obj)

        f = open(filename, args.mode)
        f.write(obj)
        f.close()

    @magic_arguments()
    @argument('-e', '--encoding',
              help=("decode the text using this encoding "
                    "[default: do not attempt to decode]"))
    @argument('-m', '--mode', default='rb',
              help="the file mode to use when opening the file for reading")
    @argument('variable', help="the name of the variable")
    @argument('filename', help="the filename to read from")
    @line_magic
    def fread(self, arg):
        """ Read text from a file into a variable.

    """
        args = parse_argstring(self.fread, arg)
        filename = os.path.expanduser(args.filename)
        f = open(filename, args.mode)
        contents = f.read()
        f.close()
        if args.encoding:
            contents = contents.decode(args.encoding)

        self.shell.user_ns[args.variable] = contents

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
    @line_magic
    def sym(self, arg):
        """ Create Sympy variables easily.

    """
        try:
            import sympy
        except ImportError:
            raise UsageError("could not import sympy.")
        args = parse_argstring(self.sym, arg)
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
                print('Adding %s variables:' % args.kind)
            else:
                print('Adding variables:')
        for name in args.names:
            name = name.encode('ascii')
            var = factory(name, **kwds)
            self.shell.user_ns[name] = var
            if not args.quiet:
                print('  %s' % name)

    @magic_arguments()
    @argument('-p', '--precision', type=int,
              help="Number of digits of precision for floating point output.")
    @argument('-t', '--threshold', type=int,
              help=("Total number of array elements which trigger "
                    "summarization rather than a full repr. 0 disables "
                    "thresholding."))
    @argument('-e', '--edgeitems', type=int,
              help=("Number of array items in summary at beginning and end of "
                    "each dimension."))
    @argument('-l', '--linewidth', type=int,
              help=("The number of characters per line for the purpose of "
                    "inserting line breaks."))
    @argument('-s', '--suppress', action='store_true', default=None,
              help="Suppress the printing of small floating point values.")
    @argument('-S', '--no-suppress', action='store_false', dest='suppress',
              default=None,
              help=("Do not suppress the printing of small floating point "
                    "values."))
    @argument('-n', '--nanstr',
              help="String representation of floating point not-a-number.")
    @argument('-i', '--infstr',
              help="String representation of floating point infinity.")
    @argument('-q', '--quiet', action='store_true',
              help="Do not print the new settings.")
    @line_magic
    def push_print(self, arg):
        """ Set numpy array printing options by pushing onto a stack.

    """
        try:
            import numpy
        except ImportError:
            raise UsageError("could not import numpy.")
        args = parse_argstring(self.push_print, arg)
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
    @line_magic
    def pop_print(self, arg):
        """ Pop the last set of print options from the stack and use them.

    """
        try:
            import numpy
        except ImportError:
            raise UsageError("could not import numpy.")
        args = parse_argstring(self.pop_print, arg)

        stack = getattr(self, '_numpy_printoptions_stack', [])
        if stack:
            kwds = stack.pop()
            numpy.set_printoptions(**kwds)
        elif not args.quiet:
            print("At the end of the stack.\n")
        self._numpy_printoptions_stack = stack
        if not args.quiet:
            print_numpy_printoptions(numpy.get_printoptions())

    @magic_arguments()
    @argument('-a', '--all', choices=ERROR_CHOICES,
              help="Set the mode for all kinds of errors.")
    @argument('-d', '--divide', choices=ERROR_CHOICES,
              help="Set the mode for divide-by-zero errors.")
    @argument('-o', '--over', choices=ERROR_CHOICES,
              help="Set the mode for overflow errors.")
    @argument('-u', '--under', choices=ERROR_CHOICES,
              help="Set the mode for underflow errors.")
    @argument('-i', '--invalid', choices=ERROR_CHOICES,
              help="Set the mode for invalid domain errors (i.e. NaNs).")
    @argument('-f', '--call-func',
              help=("A function for use with the 'call' mode or a file-like "
                    "object with a .write() method for use with the 'log' "
                    "mode."))
    @argument('-n', '--no-call-func', action='store_true',
              help="Remove any existing call function.")
    @argument('-q', '--quiet', action='store_true',
              help="Do not print the new settings.")
    @line_magic
    def push_err(self, arg):
        """ Set numpy numerical error handling via a stack.

    """
        try:
            import numpy
        except ImportError:
            raise UsageError("could not import numpy.")

        sentinel = object()

        args = parse_argstring(self.push_err, arg)
        kwds = {}
        errcall = sentinel
        for key in ['all', 'divide', 'over', 'under', 'invalid']:
            value = getattr(args, key)
            if value is not None:
                kwds[key] = value
        if args.call_func is not None:
            if args.no_call_func:
                raise UsageError(
                    "You cannot specify both a --call-func and "
                    "--no-call-func at the same time.")
            global_ns = self.shell.user_global_ns
            local_ns = self.shell.user_ns
            try:
                errcall = eval(args.call_func, global_ns, local_ns)
            except Exception as e:
                raise UsageError(
                    "Could not find function {0!r}\n{1}: {2}".format(
                        args.call_func, e.__class__.__name__, e))
        elif args.no_call_func:
            errcall = None

        old_options = numpy.geterr()
        old_errcall = numpy.geterrcall()
        numpy.seterr(**kwds)
        if errcall is not sentinel:
            try:
                numpy.seterrcall(errcall)
            except ValueError as e:
                raise UsageError(str(e))
        stack = getattr(self, '_numpy_err_stack', [])
        stack.append((old_options, old_errcall))
        self._numpy_err_stack = stack
        if not args.quiet:
            print_numpy_err(numpy.geterr(), numpy.geterrcall())

    @magic_arguments()
    @argument('-q', '--quiet', action='store_true',
              help="Do not print the new settings.")
    @line_magic
    def pop_err(self, arg):
        """ Pop the last set of numpy numerical error handling settings from the
        stack.

    """
        try:
            import numpy
        except ImportError:
            raise UsageError("could not import numpy.")
        args = parse_argstring(self.pop_err, arg)

        stack = getattr(self, '_numpy_err_stack', [])
        if stack:
            kwds, errcall = stack.pop()
            numpy.seterr(**kwds)
            numpy.seterrcall(errcall)
        elif not args.quiet:
            print("At the end of the stack.\n")
        self._numpy_err_stack = stack
        if not args.quiet:
            print_numpy_err(numpy.geterr(), numpy.geterrcall())

    @magic_arguments()
    @argument('-n', '--no-group', dest='group', action='store_false',
              help="Do not group by the defining class.")
    @argument('variable', help="the name of the variable")
    @line_magic
    def print_traits(self, arg):
        """ Print the traits of an object.

    """
        try:
            from IPython.external.pretty import pretty
        except ImportError:
            import pprint
            pretty = pprint.pformat
        args = parse_argstring(self.print_traits, arg)

        obj = self.get_variable(args.variable)
        if not hasattr(obj, 'trait_names'):
            raise UsageError('variable %r is not a HasTraits instance' %
                             args.variable)
        from traits.has_traits import not_event
        from traits.trait_errors import TraitError
        names = obj.trait_names(type=not_event)
        names.sort()
        key_values = []
        for name in names:
            try:
                value = getattr(obj, name)
            except (AttributeError, TraitError):
                pvalue = '<undefined>'
            else:
                pvalue = pretty(value)
            key_values.append((name, pvalue))
        if not args.group:
            print(utils.wrap_key_values(key_values))
        else:
            trait_values = dict(key_values)
            for cls in inspect.getmro(type(obj))[::-1]:
                if hasattr(cls, 'class_trait_names'):
                    local_key_values = []
                    for trait in cls.class_trait_names():
                        if trait in trait_values:
                            local_key_values.append(
                                (trait, trait_values.pop(trait)))
                    if local_key_values:
                        name = getattr(cls, '__name__', repr(cls))
                        print(name)
                        print('-'*len(name))
                        print(utils.wrap_key_values(sorted(local_key_values)))
                        print()

    @magic_arguments()
    @argument('-n', '--no-group', dest='group', action='store_false',
              help="Do not group by the defining class.")
    @argument('-p', '--private', action='store_true',
              help=("Also display private methods that begin with an "
                    "underscore."))
    @argument('variable', help="The name of the variable.")
    @line_magic
    def print_methods(self, arg):
        """ Print the methods of an object or type.

    """
        args = parse_argstring(self.print_methods, arg)
        obj = self.get_variable(args.variable)
        if not isinstance(obj, type):
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
                    print(name)
                    print('-'*len(name))
                    print(utils.columnize(grouped[cls]))
        else:
            print(utils.columnize(all))

    @magic_arguments()
    @line_magic
    def replace_context(self, parameter_s=''):
        """Replace the IPython namespace with a DataContext.

    """
        ipshell = self.shell
        if hasattr(ipshell.user_ns, 'subcontext'):
            # Toggle back to plain dict.
            user_ns = ipshell.user_ns.subcontext
        else:
            from codetools.contexts.api import DataContext
            user_ns = DataContext(subcontext=ipshell.user_ns)
        ipshell.user_ns = user_ns

    @magic_arguments()
    @argument('object', help="The name of the object.")
    @line_magic
    def run_examples(self, arg):
        """ Run doctest-format examples in an object's docstring.

    """
        args = parse_argstring(self.run_examples, arg)
        obj = self.get_variable(args.object)
        if not hasattr(obj, '__doc__'):
            raise UsageError("%s does not have a docstring" % args.object)
        d = DoctestDemo(StringIO(obj.__doc__))
        while not d.finished:
            d()

    @magic_arguments()
    @argument('-d', '--dump', action='store_true',
              help="Dump the current sources.")
    @argument('-r', '--revert', action='store_true',
              help=("Revert the function/method to its original "
                    "implementation."))
    @argument('function', nargs='?',
              help="The name of the function/method to edit in-place.")
    @line_magic
    def inplace(self, arg):
        """ Edit the source of a function or method and replace the original
        implementation.

    """
        from kernmagic.inplace_edit import Inplace
        args = parse_argstring(self.inplace, arg)

        inplace = Inplace.singleton(self.shell)
        if args.function is None:
            # Check for commands.
            if args.dump:
                inplace.dump_current_source()
            elif args.revert:
                print("Reverting all modified functions.", file=io.stdout)
                inplace.revert_all()
            return

        function = self.get_variable(args.function)
        if args.revert:
            inplace.revert(function)
        else:
            inplace.edit_object(function)

    @magic_arguments()
    @argument('modules', nargs='+', metavar='MODULE',
              help="module or modules to reload")
    @line_magic
    def reload(self, arg):
        """ Reload a module.

    """
        args = parse_argstring(self.reload, arg)
        for name in args.modules:
            mod = importlib.import_module(name)
            importlib.reload(mod)
