"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:44 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


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
# from ccpn.core.lib.ContextManagers import undoBlock
from ccpn.util.Logging import getLogger


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


def notify(trigger, preExecution=False):
    """A decorator wrap a method around a notification blanking with explicit notification pre- or post-execution
    """

    trigger = 'change' if trigger == 'observe' else trigger

    @decorator.decorator
    def theDecorator(*args, **kwds):

        func = args[0]
        args = args[1:]  # Optional 'self' is now args[0]
        self = args[0]
        project = self.project # we need a reference now, as the func could be deleting the obj

        if preExecution:
            # call the notification
            self._finaliseAction(trigger)

        # Execute the function with blanked notification
        project.blankNotification()
        result = func(*args, **kwds)
        project.unblankNotification()

        if not preExecution:
            # call the notification
            self._finaliseAction(trigger)

        return result

    return theDecorator


def propertyUndo():
    """A decorator to wrap a method in an undo block
    Requires that the 'self' has 'project' as an attribute
    """
    from ccpn.core.lib.ContextManagers import undoBlock

    @decorator.decorator
    def theDecorator(*args, **kwds):

        func = args[0]
        args = args[1:]  # Optional 'self' is now args[0]
        self = args[0]

        _undo = self.project._undo
        with undoBlock():

            # Execute the function while blocking all additions to the call undo stack
            _undo.increaseBlocking()

            # remember the old value, requires a property getter
            oldValue = getattr(self, func.__name__)

            # call the wrapped function
            result = func(*args, **kwds)

            _undo.decreaseBlocking()

            # add the wrapped function to the undo stack
            _undo._newItem(undoPartial=partial(func, self, oldValue),
                           redoPartial=partial(func, *args, **kwds))

        return result

    return theDecorator



#----------------------------------------------------------------------------------------------
# Adapted from from sandbox.Geerten.Refactored.decorators to fit current setup
#----------------------------------------------------------------------------------------------


def _makeLogString(prefix, addSelf, func, *args, **kwds):
    """Helper function to create the log string from func, args and kwds

    returns string:

    if addSelf == False:
      prefix+func.__name__(EXPANDED-ARGUMENTS)

    if addSelf == True
      prefix+CLASSNAME-of-SELF+'.'+func.__name__(EXPANDED-ARGUMENTS)

    """
    from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
    from ccpn.ui.gui.modules.CcpnModule import CcpnModule

    def obj2pid(obj):
        "Convert core objects and CcpnModules to pids"
        return obj.pid if isinstance(obj, (AbstractWrapperObject, CcpnModule)) else obj

    # get the signature
    sig = inspect.signature(func)
    # fill in the missing parameters
    ba = sig.bind(*args, **kwds)
    ba.apply_defaults()
    # get the parameters kinds that determine how to print them
    kinds = dict([(pName, p.kind) for pName, p in sig.parameters.items()])

    if 'self' in ba.arguments or 'cls' in ba.arguments:
        # we skip the first 'self' or 'cls' in the argument list
        pNames = list(ba.arguments.keys())[1:]
    else:
        pNames = list(ba.arguments.keys())

    # make a string for each parameter
    pStrings = []
    for pName in pNames:
        pValue = ba.arguments[pName]

        if kinds[pName] == inspect.Parameter.VAR_POSITIONAL:  # variable argument
            pStrings.extend([repr(obj2pid(p)) for p in pValue])

        elif kinds[pName] == inspect.Parameter.VAR_KEYWORD:  # variable keywords
            pStrings.extend(['{0!s}={1!r}'.format(k, obj2pid(v)) for (k, v) in pValue.items()])

        elif kinds[pName] == inspect.Parameter.POSITIONAL_ONLY or \
                kinds[pName] == inspect.Parameter.POSITIONAL_OR_KEYWORD:  # positional keywords
            pStrings.append(repr(obj2pid(pValue)))

        elif kinds[pName] == inspect.Parameter.KEYWORD_ONLY:  #  keywords
            pStrings.append('{0!s}={1!r}'.format(pName, obj2pid(pValue)))

    if ('self' in ba.arguments or 'cls' in ba.arguments) and addSelf:
        logString = prefix + '%s.%s' % (args[0].__class__.__name__, func.__name__)
    else:
        logString = prefix + '%s' % (func.__name__,)

    logString += '(%s)' % ', '.join(pStrings)
    return logString


def logCommand(prefix='', get=None, isProperty=False):
    """A decorator to log the invocation of the call to a Framework, Project, ... method.
    Use prefix to set the proper command context, e.g. 'application.' or 'project.'
    Use isProperty to get ' = 'args[1]
    """

    @decorator.decorator
    def theDecorator(*args, **kwds):
        # def logCommand(func, self, *args, **kwds):
        # to avoid potential conflicts with potential 'func' named keywords
        func = args[0]
        args = args[1:]  # Optional 'self' is now args[0]
        self = args[0]

        application = self.project.application
        blocking = application._echoBlocking
        if blocking == 0:
            _pref = prefix
            if get == 'self':
                _pref += "get('%s')." % args[0].pid

            if isProperty:
                logS = _pref + '%s = %r' % (func.__name__, args[1])
            else:
                logS = _makeLogString(_pref, False, func, *args, **kwds)

            application.ui.echoCommands([logS])

        blocking += 1
        result = func(*args, **kwds)
        blocking -= 1

        return result

    return theDecorator


# def debugEnter(verbosityLevel=Logger.DEBUG1):
#     """A decorator to log the invocation of the call
#     """
#
#     @decorator.decorator
#     def decoratedFunc(*args, **kwds):
#         # def debugEnter(func, *args, **kwds):
#         # to avoid potential conflicts with potential 'func' named keywords
#         func = args[0]
#         args = args[1:]
#
#         logs = _makeLogString('ENTERING: ', True, func, *args, **kwds)
#
#         # get a logger and call the correct routine depending on verbosityLevel
#         logger = getLogger()
#         if verbosityLevel == Logger.DEBUG1:
#             logger.debug(logs)
#         elif verbosityLevel == Logger.DEBUG2:
#             logger.debug2(logs)
#         elif verbosityLevel == Logger.DEBUG3:
#             logger.debug3(logs)
#         else:
#             raise ValueError('invalid verbosityLevel "%s"' % verbosityLevel)
#
#         # execute the function and return the result
#         return func(*args, **kwds)
#
#     return decoratedFunc
#
#
# def debug1Enter():
#     """Convenience"""
#     return debugEnter(verbosityLevel=Logger.DEBUG1)
#
#
# def debug2Enter():
#     """Convenience"""
#     return debugEnter(verbosityLevel=Logger.DEBUG2)
#
#
# def debug3Enter():
#     """Convenience"""
#     return debugEnter(verbosityLevel=Logger.DEBUG3)
#
#
# def debugLeave(verbosityLevel=Logger.DEBUG1):
#     """A decorator to log the invocation of the call
#     """
#
#     @decorator.decorator
#     def decoratedFunc(*args, **kwds):
#         # def debugLeave(func, *args, **kwds):
#         # to avoid potential conflicts with potential 'func' named keywords
#         func = args[0]
#         args = args[1:]
#
#         ba = inspect.signature(func).bind(*args, **kwds)
#         ba.apply_defaults()
#         allArgs = ba.arguments
#
#         #execute the function
#         result = func(*args, **kwds)
#
#         if 'self' in allArgs or 'cls' in allArgs:
#             logs = 'LEAVING: %s.%s(); result=%r' % \
#                    (args[0].__class__.__name__, func.__name__, result)
#         else:
#             logs = 'LEAVING: %s(); result=%r' % (func.__name__, result)
#
#         # get a logger and call the correct routine depending on verbosityLevel
#         logger = getLogger()
#         if verbosityLevel == Logger.DEBUG1:
#             logger.debug(logs)
#         elif verbosityLevel == Logger.DEBUG2:
#             logger.debug2(logs)
#         elif verbosityLevel == Logger.DEBUG3:
#             logger.debug3(logs)
#         else:
#             raise ValueError('invalid verbosityLevel "%s"' % verbosityLevel)
#
#         #return the function result
#         return result
#
#     return decoratedFunc
#
#
# def debug1Leave():
#     """Convenience"""
#     return debugLeave(verbosityLevel=Logger.DEBUG1)
#
#
# def debug2Leave():
#     """Convenience"""
#     return debugLeave(verbosityLevel=Logger.DEBUG2)
#
#
# def debug3Leave():
#     """Convenience"""
#     return debugLeave(verbosityLevel=Logger.DEBUG3)


#==========================================================================================================================
# testing
#==========================================================================================================================

if __name__ == '__main__':

    def func(par, *args, flag=False, **kwds):

        sig = inspect.signature(func)  # get the signature
        ba = sig.bind(par, *args, flag=flag, **kwds)
        ba.apply_defaults()  # fill in the missing parameters
        kinds = dict([(pName, p.kind) for pName, p in sig.parameters.items()])  # get the parameters kinds that determine
                                                                                # how to print them

        pStrings = []
        for pName, pValue in ba.arguments.items():

            if kinds[pName] == inspect.Parameter.VAR_POSITIONAL:  # variable argument
                pStrings.extend([repr(p) for p in pValue])

            elif kinds[pName] == inspect.Parameter.VAR_KEYWORD:  # variable keywords
                pStrings.extend(['{0!s}={1!r}'.format(k, v) for (k,v) in pValue.items()])

            elif kinds[pName] == inspect.Parameter.POSITIONAL_ONLY or \
                    kinds[pName] == inspect.Parameter.POSITIONAL_OR_KEYWORD   :  # positional keywords
                pStrings.append(repr(pValue))

            elif kinds[pName] == inspect.Parameter.KEYWORD_ONLY:  #  keywords
                pStrings.append('{0!s}={1!r}'.format(pName, pValue))

        print(', '.join(pStrings))

    # logCommand('myPrefix.')

    def func2(**axisCodeEqValueKwds):
        pass


    func('test', 1, 2, myPar='myValue')

