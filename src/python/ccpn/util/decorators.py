#===========================================================================================================
# Decorators
#===========================================================================================================

import sys
import os
import linecache
import functools
import cProfile
import decorator
import inspect
from functools import partial


def trace(f):
    def globaltrace(frame, why, arg):
        if why == "call":
            return localtrace
        return None

    def localtrace(frame, why, arg):
        if why == "line":
            # record the file name and line number of every trace
            filename = frame.f_code.co_filename
            lineno = frame.f_lineno

            bname = os.path.basename(filename)
            sys.stderr.write("{}({}): {}".format(bname,
                                                 lineno,
                                                 linecache.getline(filename, lineno)),
                             )
        return localtrace

    def _f(*args, **kwds):
        sys.settrace(globaltrace)
        result = f(*args, **kwds)
        sys.settrace(None)
        return result

    return _f


def singleton(cls):
    """ Use class as singleton.
    From: https://wiki.python.org/moin/PythonDecoratorLibrary#Singleton
    Annotated by GWV
    """

    @functools.wraps(cls.__new__)
    def singleton_new(cls, *args, **kwds):
        # check if it already exists
        it = cls.__dict__.get('__it__')
        if it is not None:
            return it
        # it did not yet exist; generate an instance
        cls.__it__ = it = cls.__new_original__(cls, *args, **kwds)
        it.__init_original__(*args, **kwds)
        return it

    # keep the new method and replace by singleton_new
    cls.__new_original__ = cls.__new__
    cls.__new__ = singleton_new
    # keep the init method and replace by the object init
    cls.__init_original__ = cls.__init__
    cls.__init__ = object.__init__
    return cls


def profile(func):
    @functools.wraps(func)
    def profileWrapper(*args, **kwargs):
        # path = ''
        profiler = cProfile.Profile()
        try:
            profiler.enable()
            ret = func(*args, **kwargs)
            profiler.disable()
            return ret
        finally:
            filename = os.path.expanduser(os.path.join('~', func.__name__ + '.pstat'))
            profiler.dump_stats(filename)

    return profileWrapper


def notify(action, subClass=''):
    """A decorator wrap a method in an undo block
    """

    @decorator.decorator
    def theDecorator(*args, **kwds):

        def undo(self):
            """preRedo/postUndo function, needed for undo/redo
            """
            print('>>>UNDO notify decorator')
            pass

        def redo(self):
            """preUndo/postRedo function, needed for undo/redo, and fire single change notifiers
            """
            self._finaliseAction(action=action)
            for obj in getattr(self, subClass, []):
                obj._finaliseAction(action)
            print('>>>REDO notify decorator')

        func = args[0]
        args = args[1:]  # Optional 'self' is now args[0]

        self = args[0]
        _undo = self.project._undo

        _undo._newItem(undoPartial=partial(redo, self),
                       redoPartial=partial(undo, self))
        undo(self)
        try:

            # call the wrapped function
            result = func(*args, **kwds)

        finally:
            redo(self)
            _undo._newItem(undoPartial=partial(undo, self),
                           redoPartial=partial(redo, self))

        return result

    return theDecorator


def undo():
    """A decorator wrap a method in an undo block
    """

    @decorator.decorator
    def theDecorator(*args, **kwds):

        def undo(self):
            """preRedo/postUndo function, needed for undo/redo
            """
            self.project.blankNotification()
            print('>>>UNDO undo decorator')

        def redo(self):
            """preUndo/postRedo function, needed for undo/redo, and fire single change notifiers
            """
            self.project.unblankNotification()
            print('>>>REDO undo decorator')

        func = args[0]
        args = args[1:]  # Optional 'self' is now args[0]

        self = args[0]
        self._startCommandEchoBlock(func.__name__, *args, propertySetter=True)
        _undo = self.project._undo

        _undo._newItem(undoPartial=partial(redo, self),
                       redoPartial=partial(undo, self))
        undo(self)
        try:

            # call the wrapped function
            result = func(*args, **kwds)

        finally:
            redo(self)
            _undo._newItem(undoPartial=partial(undo, self),
                           redoPartial=partial(redo, self))
            self._endCommandEchoBlock()

        return result

    return theDecorator
