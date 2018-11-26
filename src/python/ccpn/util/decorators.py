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
from ccpn.core.lib.ContextManagers import undoBlock
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


def notify(trigger):
    """A decorator to wrap a method and trigger a _finaliseAction at the end
    Will trigger in the correct place on the undo/redo action
    """
    trigger = 'change' if trigger == 'observe' else trigger

    @decorator.decorator
    def theDecorator(*args, **kwds):

        func = args[0]
        args = args[1:]  # Optional 'self' is now args[0]
        self = args[0]

        # Execute the function with blanked notification
        self.project.blankNotification()
        result = func(*args, **kwds)
        self.project.unblankNotification()

        # now call the notification
        self._finaliseAction(trigger)

        return result

    return theDecorator


def propertyUndo():
    """A decorator to wrap a method in an undo block
    Requires that the 'self' has 'project' as an attribute
    """
    @decorator.decorator
    def theDecorator(*args, **kwds):

        func = args[0]
        args = args[1:]  # Optional 'self' is now args[0]
        self = args[0]

        _undo = self.project._undo
        with undoBlock(self.project.application):

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


def newObject():
    """A decorator wrap a newObject method in an undo block and calls
     result._finalise('create')
    """

    @decorator.decorator
    def theDecorator(*args, **kwds):

        func = args[0]
        args = args[1:]  # Optional 'self' is now args[0]
        self = args[0]

        # print('>>> in the newObject decorator:', func.__name__, args, kwds)

        _undo = self.project._undo
        self.project.blankNotification()
        with undoBlock(self.project.application):

            #_undo.increaseBlocking()
            # call the wrapped function
            result = func(*args, **kwds)
            #_undo.decreaseBlocking()

            # _undo._newItem(undoPartial=partial(self.project.deleteObjects, result),
            #                redoPartial=partial(func, *args, **kwds))

        self.project.unblankNotification()
        result._finaliseAction('create')
        return result

    return theDecorator


def ccpNmrSetter():

    @logCommand('peak.')
    @position.setter
    @propertyUndo()
    @notify('observe')

    @decorator.decorator
    def theDecorator(*args, **kwds):

        func = args[0]
        args = args[1:]  # Optional 'self' is now args[0]
        self = args[0]

        result = func(*args, **kwds)

        return result

    return theDecorator


#----------------------------------------------------------------------------------------------
# Adapted from from sandbox.Geerten.Refactored.decorators to fit current setup
#----------------------------------------------------------------------------------------------


def _makeLogString(prefix, addSelf, func, *args, **kwds):
    """Helper function to create the log string from func, args and kwds
    """

    ba = inspect.signature(func).bind(*args, **kwds)
    ba.apply_defaults()

    logs = prefix
    if 'self' in ba.arguments or 'cls' in ba.arguments:
        if addSelf:
            logs += '%s.' % (args[0].__class__.__name__,)
        allArgs = [(k, ba.arguments[k]) for k in list(ba.arguments.keys())[1:]]
    else:
        allArgs = [(k, ba.arguments[k]) for k in list(ba.arguments.keys())]

    logs += '%s(' % (func.__name__)
    logs += ', '.join(['{0!s}={1!r}'.format(k, v) for k, v in allArgs])
    logs += ')'
    return logs


def logCommand(prefix='', get=None):
    """A decorator to log the invocation of the call to a Framework, Project, ... method.
    Use prefix to set the proper command context, e.g. 'application.' or 'project.'
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
            logS = _makeLogString(_pref, False, func, *args, **kwds)
            application.ui.echoCommands([logS])

        blocking += 1
        result = func(*args, **kwds)
        blocking -= 1

        return result

    return theDecorator






def logCommand2(prefix='', get=None, isProperty=False, showArguments=[], logCommandOnly=False):
    """
    Echo a command to the logger reflecting the python command required to call the function.

    :param prefix: string to be prepended to the echo command
    :param get: function containing the function
    :param isProperty: is the function a property
    :param showArguments: list of string names for arguments that need to be included.
                        By default, the parameters set to the defaults are not included.

    Examples:

    1)  def something(self, name=None, value=0):
            logCommandManager(prefix='process.') as log:
                log('something')

                ... code here

        call function                   echo command

        something('Hello')              process.something(name='Hello')
        something('Hello', 12)          process.something(name='Hello', value=12)

        Parameters are not required in the log() command, parameters are picked up from
        the containing function; however, changes can be inserted by including
        the parameter, e.g., log('something', name=name+'There') will append 'There' to the name.

            something('Hello')          process.something(name='HelloThere')

    2)  def something(self, name=None, value=0):
            logCommandManager(get='self') as log:
                log('something')

                ... code here

        call function                   echo command

        something('Hello')              get('parent:ID').something(name='Hello')
        something('Hello', 12)          get('parent:ID').something(name='Hello', value=12)

    3)  @property
        def something(self, value=0):
            logCommandManager(get='self', isProperty=True) as log:
                log('something', value=value)

                ... code here


        call function                   echo command

        something = 12                  get('parent:ID').something = 12

        functions of this type can only contain one parameter, and
        must be set as a keyword in the log.

    4)  Mixing prefix and get:

        def something(self, value=0):
            logCommandManager(prefix='process.', get='self') as log:
                log('something')

        if called from SpectrumDisplay:

        call function                   echo command

        spectrumDisplay.something(12)   process.get('spectrumDisplay:1').something(12)

    5)  If the log command needs modifying, this can be included in the log command,
        e.g., if the pid of an object needs inserting

        def something(self, value=None):
            logCommandManager(prefix='process.', get='self') as log:
                log('something', value=value.pid)

        if called from SpectrumDisplay:

        call function                   echo command

        spectrumDisplay.something(<anObject>)   process.get('spectrumDisplay:1').something(value=anObject:pid)

        To make quotes appear around the value use: log('something', value=repr(value.pid))

    """
    from inspect import signature, Parameter
    import sys
    # from sandbox.Geerten.Refactored.framework import getApplication

    # get the current application
    # application = getApplication()

    def log(funcName, *args, **kwds):  # remember _undoBlocked, as first parameter
        # if logger._loggingCommandBlock > 1:  # or _undoBlocked:
        #     return

        # get the caller from the getframe stack
        fr1 = sys._getframe(1)
        selfCaller = fr1.f_locals[get] if get else None
        pid = selfCaller.pid if selfCaller is not None and hasattr(selfCaller, 'pid') else ''

        # make a list for modifying the log string with more readable labels
        # checkList = [(application, 'application.'),
        #              (application.mainWindow, 'mainWindow.'),
        #              (application.project, 'project.'),
        #              (application.current, 'current.')]
        checkList = []

        for obj, label in checkList:
            if selfCaller is obj:
                getPrefix = label
                break
        else:
            getPrefix = "get('%s')." % pid if (get and pid) else ''

        # search if caller matches the main items in the application namespace, e.g., 'application', 'project', etc.
        # nameSpace = application._getNamespace()
        # for k in nameSpace.keys():
        #     if selfCaller == nameSpace[k]:
        #         getPrefix = k+'.'
        #         break
        # else:
        #     getPrefix = "get('%s')." % pid if get else ''

        # construct the new log string
        if isProperty:
            # if kwds.values():
            #     kwdsList = repr(list(kwds.values())[0])
            # else:
            #     kwdsList = ''
            logs = prefix + getPrefix + funcName + ' = ' + repr(args[1])     # repr(list(kwds.values())[0])
        else:

            # build the log command from the parameters of the caller function
            # only those that are not in the default list are added, i.e. those defined
            # explicitly by the caller
            if selfCaller is not None:
                selfFunc = getattr(selfCaller, funcName)
                sig0 = [(k, v) for k, v in signature(selfFunc).parameters.items()]
                sig1 = [k for k, v in signature(selfFunc).parameters.items()
                        if v.default is Parameter.empty
                        or k in showArguments
                        or k in kwds
                        or repr(fr1.f_locals[k]) != repr(v.default)]
            else:
                sig1 = {}

            # create the log string
            logs = prefix + getPrefix + funcName + '('
            for k in sig1:
                if k != 'self':
                    kval = str(kwds[k]) if k in kwds else repr(fr1.f_locals[k])
                    logs += str(k) + '=' + kval + ', '
            logs = logs.rstrip(', ')
            logs += ')'

        getLogger().info(logs)

    # log commands to the registered outputs
    logger = getLogger()
    # logger._loggingCommandBlock += 1


    @decorator.decorator
    def theDecorator(*args, **kwds):
        # def logCommand(func, self, *args, **kwds):
        # to avoid potential conflicts with potential 'func' named keywords
        func = args[0]
        args = args[1:]  # Optional 'self' is now args[0]
        self = args[0]

        log(func.__name__, *args, **kwds)
        result = func(*args, **kwds)

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
