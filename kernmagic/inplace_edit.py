from __future__ import with_statement

import hashlib
import imp
import inspect
import linecache
import os
import sys
import tempfile
import textwrap
import weakref

from IPython.genutils import Term
from IPython import ipapi


def as_func(funcmeth):
    """ Return the underlying function for the given method (or the input itself
    if already a function).
    """
    return getattr(funcmeth, 'im_func', funcmeth)


class Inplace(object):
    """ Manage the inplace editing of methods and functions.
    """

    def __init__(self, shell):
        self.shell = weakref.ref(shell)

        # Map the new function objects to their original versions.
        self.originals = {}

        # Map original function objects to their current replacement source.
        self.current_sources = {}

    @classmethod
    def singleton(cls, shell):
        """ Return the global singleton.
        """
        if not hasattr(shell, '_inplace_singleton'):
            shell._inplace_singleton = cls(shell)
            ip = ipapi.get()
            ip.set_hook('shutdown_hook', shell._inplace_singleton.shutdown_hook)
        return shell._inplace_singleton

    def shutdown_hook(self, other):
        """ The shutdown hook.
        """
        if self.current_sources:
            self.dump_current_source()
        raise ipapi.TryNext()

    def monkeypatch(self, original, new):
        """ Monkeypatch a new function.
        """
        if inspect.ismethod(original):
            setattr(original.im_class, original.__name__, new)
        else:
            module = inspect.getmodule(original)
            setattr(module, original.__name__, new)

        self.originals[new] = original

    def revert(self, new):
        """ Revert a function to its original state.
        """
        new = as_func(new)
        original = self.originals.pop(new)
        self.current_sources.pop(as_func(original), None)
        if inspect.ismethod(original):
            setattr(original.im_class, original.__name__, original.im_func)
        else:
            module = inspect.getmodule(original)
            setattr(module, original.__name__, original)

    def revert_all(self):
        """ Revert all modified functions.
        """
        for new in self.originals.keys():
            self.revert(new)

    def execute_source(self, original, new_source):
        """ Execute source code to replace the original function/method.
        """
        # Create the module.
        hash = hashlib.sha1(new_source).hexdigest()
        filename = 'inplace_%s.py' % hash
        name = 'inplace_%s' % hash
        mod = imp.new_module(name)
        # Supply the correct globals.
        mod.__dict__.update(original.func_globals)
        linecache.cache[filename] = (len(new_source), None,
            [x+'\n' for x in new_source.splitlines()], filename)
        code = compile(new_source, filename, 'exec')
        exec code in mod.__dict__, mod.__dict__

        new = getattr(mod, original.__name__, None)
        if new is None or not callable(new):
            raise ValueError("There is no function %s in the user-edited source." % original.__name__)
        sys.modules[name] = mod

        self.current_sources[as_func(original)] = new_source
        return new
        
    def edit_object(self, original):
        """ Edit the source of the method or function.
        """
        # Make sure we have the real original.
        original_func = as_func(original)
        if original_func in self.originals:
            original = self.originals[original_func]
            original_func = as_func(original)
        if original_func in self.current_sources:
            # Use the current version if we have already edited it.
            original_source = self.current_sources[original_func]
        else:
            original_source = textwrap.dedent(inspect.getsource(original))

        # Create a temporary file.
        fd, filename = tempfile.mkstemp('.py', 'inplace_')
        try:
            with os.fdopen(fd, 'w') as f:
                f.write(original_source)
            # Let the user edit the file.
            self.shell().hooks.editor(filename)
            # Read the edited text back in.
            with open(filename) as f:
                new_source = f.read()
        finally:
            # Remove the temporary file.
            os.unlink(filename)

        new = self.execute_source(original, new_source)
        self.monkeypatch(original, new)

    def dump_current_source(self):
        """ Print the current edited sources.
        """
        # Find the filenames, line numbers and current sources for all of the
        # original objects.
        files_lines_sources = []
        for original, source in self.current_sources.items():
            lines, lineno = inspect.findsource(original)
            filename = inspect.getfile(original)
            files_lines_sources.append((filename, lineno, source))
        files_lines_sources.sort()
        print >>Term.cout, "The following edits have been applied:"
        print >>Term.cout, ""
        for fn, lineno, source in files_lines_sources:
            print >>Term.cout, '%s:%s' % (fn, lineno)
            print >>Term.cout, ""
            print >>Term.cout, source
            print >>Term.cout, ""
            print >>Term.cout, ""
