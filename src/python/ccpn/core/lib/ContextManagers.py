"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

from contextlib import contextmanager
import functools
import itertools
import operator
import typing
import decorator
from functools import partial
from collections import OrderedDict
from ccpn.core import _importOrder
# from ccpn.core.lib import CcpnSorting
from ccpn.core.lib import Util as coreUtil
from ccpn.util import Common as commonUtil
from ccpn.core.lib import Pid
from ccpnmodel.ccpncore.api.memops import Implementation as ApiImplementation
from ccpn.util.Logging import getLogger
from ccpn.framework.Application import getApplication


@contextmanager
def echoCommand(obj, funcName, *params, values=None, defaults=None,
                parName=None, propertySetter=False, **objectParameters):
    try:
        project = obj._project
    except:
        project = obj.project

    parameterString = coreUtil.commandParameterString(*params, values=values, defaults=defaults)

    if obj is project:
        if propertySetter:
            if parameterString:
                command = "project.%s = %s" % (funcName, parameterString)
            else:
                command = "project.%s" % funcName
        else:
            command = "project.%s(%s)" % (funcName, parameterString)
    else:
        if propertySetter:
            if parameterString:
                command = "project.getByPid('%s').%s = %s" % (obj.pid, funcName, parameterString)
            else:
                command = "project.getByPid('%s').%s" % (obj.pid, funcName)
        else:
            command = "project.getByPid('%s').%s(%s)" % (obj.pid, funcName, parameterString)

    if parName:
        command = ''.join((parName, ' = ', command))

    # Get list of command strings to follow the main command
    commands = []
    for parameter, value in sorted(objectParameters.items()):
        if value is not None:
            if not isinstance(value, str):
                value = value.pid
            commands.append("%s = project.getByPid(%s)\n" % (parameter, repr(value)))
    commands.append(command)

    if not project.application._echoBlocking:
        project.application.ui.echoCommands(commands)
    getLogger().debug('_enterEchoCommand: command=%s' % commands[0])

    try:
        # transfer control to the calling function
        yield

    finally:
        getLogger().debug('_exitEchoCommand')


@contextmanager
def undoBlock():
    # usually called from application

    application = getApplication()

    # undo = application.project._undo
    undo = application._getUndo()

    if undo is not None:  # ejb - changed from if undo:
        undo.newWaypoint()  # DO NOT CHANGE

        if not application.project._blockSideBar and not undo._blocked:
            if undo._waypointBlockingLevel < 1 and application.ui and application.ui.mainWindow:
                application._storedState = application.ui.mainWindow.sideBar._saveExpandedState()

        undo.increaseWaypointBlocking()

    if not application._echoBlocking:
        application.project.suspendNotification()

    # application._echoBlocking += 1
    application._increaseNotificationBlocking()

    getLogger().debug2('_enterUndoBlock')

    try:
        # transfer control to the calling function
        yield

    finally:
        # if application._echoBlocking > 0:
        #     application._echoBlocking -= 1
        application._decreaseNotificationBlocking()

        if not application._echoBlocking:
            application.project.resumeNotification()

        if undo is not None:
            undo.decreaseWaypointBlocking()

            if not application.project._blockSideBar and not undo._blocked:
                if undo._waypointBlockingLevel < 1 and application.ui and application.ui.mainWindow:
                    application.ui.mainWindow.sideBar._restoreExpandedState(application._storedState)

        getLogger().debug2('_exitUndoBlock: echoBlocking=%s' % application._echoBlocking)


# @contextmanager
# def blankNotification(obj, message, *args, **kwargs):
#     print('Starting', message)
#     try:
#         yield
#     finally:
#         print('Done', message)

# def _startCommandBlock(self, command:str, quiet:bool=False, **objectParameters):
#   """Start block for command echoing, set undo waypoint, and echo command to ui and logger
#
#   MUST be paired with _endCommandBlock call - use try ... finally to ensure both are called
#
#   Set keyword:value objectParameters to point to the relevant objects in setup commands,
#   and pass setup commands and command proper to ui for echoing
#
#   Example calls:
#
#   _startCommandBlock("application.createSpectrumDisplay(spectrum)", spectrum=spectrumOrPid)
#
#   _startCommandBlock(
#      "newAssignment = peak.assignDimension(axisCode=%s, value=[newNmrAtom]" % axisCode,
#      peak=peakOrPid)"""
#
#   undo = self.project._undo
#   if undo is not None:                # ejb - changed from if undo:
#     # set undo step
#     undo.newWaypoint()                # DO NOT CHANGE
#
#     if not self.project._blockSideBar and not undo._blocked:
#       if undo._waypointBlockingLevel < 1 and self.ui and self.ui.mainWindow:
#         self._storedState = self.ui.mainWindow.sideBar._saveExpandedState()
#
#     undo.increaseWaypointBlocking()
#   if not self._echoBlocking:
#
#     self.project.suspendNotification()
#
#     # Get list of command strings
#     commands = []
#     for parameter, value in sorted(objectParameters.items()):
#       if value is not None:
#         if not isinstance(value, str):
#           value = value.pid
#         commands.append("%s = project.getByPid(%s)\n" % (parameter, repr(value)))
#     commands.append(command)    # ED: newLine NOT needed here
#
#     # echo command strings
#     # added 'quiet' mode to keep full functionality to 'startCommandEchoBLock'
#     # but without the screen output
#     if not quiet:
#       self.ui.echoCommands(commands)
#
#   self._echoBlocking += 1
#   getLogger().debug('command=%s, echoBlocking=%s, undo.blocking=%s'
#                              % (command, self._echoBlocking, undo.blocking))


# # temporary import from refactored
# """
# Context managers for controlling log, undo, sidebar, and project notifier blocking and unblocking.
# Contains:
#
#     logCommand:             log a command mirroring the console command
#     undoBlock:              wrap functions in a single undo/redo block
#     suspendSidebar:         suspend update of the sidebar until end of function block
#     suspendNotification:    suspend notifications until end of function block
#     blankNotification:      block all notifiers, re-enable at the end of the function block
#
# Context managers are currently nested in the following order:
#
#     logCommand:
#         undoBlock:
#             suspendSidebar:
#                 suspendNotification:
#
# Any level can be called, but will always contain the lower levels
#
# There is also blankNotification that disables all notifiers.
# This can be called inside any of the above.
# """
# #=========================================================================================
# # Licence, Reference and Credits
# #=========================================================================================
# __copyright__ = ""
# __credits__ = ""
# __licence__ = ("")
# __reference__ = ("")
# #=========================================================================================
# # Last code modification:
# #=========================================================================================
# __modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
# __dateModified__ = "$dateModified$"
# __version__ = "$Revision$"
# #=========================================================================================
# # Created:
# #=========================================================================================
# __author__ = "$Author: Ed Brooksbank $"
# __date__ = "$Date$"
# #=========================================================================================
# # Start of code
# #=========================================================================================

from contextlib import contextmanager
# from sandbox.Geerten.Refactored.logger import getLogger
from ccpn.util.Logging import getLogger


@contextmanager
def logCommandManager(prefix='', get=None, isProperty=False, showArguments=[], logCommandOnly=False):
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
    from ccpn.framework.Application import getApplication

    # get the current application
    application = getApplication()

    def log(funcName, *args, **kwargs):  # remember _undoBlocked, as first parameter
        if logger._loggingCommandBlock > 1:  # or _undoBlocked:
            return

        # get the caller from the getframe stack
        fr1 = sys._getframe(1)
        selfCaller = fr1.f_locals[get] if get else None
        pid = selfCaller.pid if selfCaller is not None and hasattr(selfCaller, 'pid') else ''

        # make a list for modifying the log string with more readable labels
        checkList = [(application, 'application.'),
                     (application.mainWindow, 'mainWindow.'),
                     (application.project, 'project.'),
                     (application.current, 'current.')]
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
            logs = prefix + getPrefix + funcName + ' = ' + repr(list(kwargs.values())[0])
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
                        or k in kwargs
                        or repr(fr1.f_locals[k]) != repr(v.default)]
            else:
                sig1 = {}

            # create the log string
            logs = prefix + getPrefix + funcName + '('
            for k in sig1:
                if k != 'self':
                    kval = str(kwargs[k]) if k in kwargs else repr(fr1.f_locals[k])
                    logs += str(k) + '=' + kval + ', '
            logs = logs.rstrip(', ')
            logs += ')'

        logger.log(logs)

    # log commands to the registered outputs
    logger = getLogger()
    logger._loggingCommandBlock += 1

    try:
        if logCommandOnly:
            # only execute the calling function
            yield log
        else:
            # transfer control to the calling function, create an undo waypoint
            with undoBlockManager(application=application):  # as _undoBlocking:
                yield log  # partial(log, _undoBlocking)

    except AttributeError as es:
        raise

    finally:
        # clean up log command block
        logger._loggingCommandBlock -= 1


@contextmanager
def undoBlockManager(application=None, undoBlockOnly=False):
    """
    Wrap all the following calls with a single undo/redo method.
    """

    # get the current application
    if not application:
        application = getApplication()

    undo = application.project._undo
    if undo is not None:  # ejb - changed from if undo:
        undo.newWaypoint()  # DO NOT CHANGE
        undo.increaseWaypointBlocking()

    logger = getLogger()
    logger.debug3('_enterUndoBlock')

    try:
        # transfer control to the calling function
        if undoBlockOnly:
            yield
        else:
            # transfer control to the calling function, with sidebar blocking
            with suspendSidebar(application=application):
                yield  # undo._blocked if undo is not None else False

    except AttributeError as es:
        raise

    finally:
        # clean up the undo block
        if undo is not None:
            undo.decreaseWaypointBlocking()

        logger.debug3('_exitUndoBlock')

    # with suspendSidebar():
    #     yield  # undo._blocked if undo is not None else False
    #
    # # clean up the undo block
    # if undo is not None:
    #     undo.decreaseWaypointBlocking()
    #
    # logger.debug2('_exitUndoBlock')


@contextmanager
def suspendSidebar(application=None, suspendSidebarOnly=False):
    """
    Block updating of the sidebar (if present) until end of function block.
    """

    # get the current application
    if not application:
        application = getApplication()
    if application is None:
        raise RuntimeError('Error getting application')

    storedState = None
    if application.mainWindow:
        sidebar = application.mainWindow.sideBar
        if not sidebar.sidebarBlocking:
            storedState = sidebar._saveExpandedState()
        sidebar.increaseSidebarBlocking()

    try:
        # transfer control to the calling function
        if suspendSidebarOnly:
            yield
        else:
            # transfer control to the calling function, suspending notifications
            with suspendNotification(application=application):
                yield

    except AttributeError as es:
        raise

    finally:
        # clean up after suspending sidebar updates
        if application.mainWindow:
            sidebar = application.mainWindow.sideBar
            sidebar.decreaseSidebarBlocking()
            if not sidebar.sidebarBlocking:
                sidebar._restoreExpandedState(storedState)


@contextmanager
def suspendNotification(application=None):
    """
    Suspend notifiers until the end of the current function block.
    """
    # get the application
    if not application:
        application = getApplication()
    if application is None:
        raise RuntimeError('Error getting application')

    application.project.suspendNotification()
    try:
        # transfer control to the calling function
        yield

    except AttributeError as es:
        raise

    finally:
        # clean up after suspending notifications
        application.project.resumeNotification()


@contextmanager
def blankNotification(application=None):
    """
    Block all notifiers, re-enable at the end of the function block.
    """

    # get the application
    if not application:
        application = getApplication()
    if application is None:
        raise RuntimeError('Error getting application')

    application.project.blankNotification()
    try:
        # transfer control to the calling function
        yield

    except AttributeError as es:
        raise es

    finally:
        # clean up after blocking notifications
        application.project.unblankNotification()

@contextmanager
def temporaryUnblankNotification():
    """
    Block all notifiers, re-enable at the end of the function block.
    Used inside blankNotification if a notifier is required for a single event
    """

    # get the current application
    application = getApplication()

    application.project.unblankNotification()
    try:
        # transfer control to the calling function
        yield

    except AttributeError as es:
        raise es

    finally:
        # clean up after blocking notifications
        application.project.blankNotification()


@contextmanager
def blockUndoItems(application=None):
    """
    Block addition of items to the undo stack, re-enable at the end of the function block.
    New user items can be added to the undo stack after blocking is re-enabled
    Example:

        with blockUndoItems() as undoItem:
            ...
            do something here
            ...
            undoItem(undo=partial(<function>, <args and kwargs>),
                    redo=partial(<function>, <args and kwargs>))
            do more here

    Multiple undoItems can be appended.
    """

    # get the current application
    # get the application
    if not application:
        application = getApplication()
    if application is None:
        raise RuntimeError('Error getting application')

    undo = application._getUndo()
    if undo is None:
        raise RuntimeError("Unable to get the application's undo stack")
    _undoStack = []

    def undoItem(undo=None, redo=None):
        """This function allows for adding item's onto the application's undo stack
        They do get collected in a temporary list
        """
        # store the new undo/redo items for later addition to the stack
        _undoStack.append((undo, redo))

    undo.newWaypoint()  # DO NOT CHANGE
    undo.increaseWaypointBlocking()
    undo.increaseBlocking()

    try:
        # transfer control to the calling function
        yield undoItem

    except AttributeError as es:
        raise es

    finally:
        # clean up after blocking undo items
        undo.decreaseBlocking()
        undo.decreaseWaypointBlocking()

        # add all undo items (collected via the undoItem function) to the application's undo stack
        for item in _undoStack:
            undo._newItem(undoPartial=item[0], redoPartial=item[1])


@contextmanager
def deleteBlockManager(application=None, deleteBlockOnly=False):
    """
    Wrap all the following calls with a single undo/redo method.
    """

    # get the application
    if not application:
        application = getApplication()
    if application is None:
        raise RuntimeError('Error getting application')

    undo = application._getUndo()

    if undo is not None:  # ejb - changed from if undo:
        undo.newWaypoint()  # DO NOT CHANGE
        undo.increaseWaypointBlocking()

    logger = getLogger()
    logger.debug2('_enterDeleteBlock')

    try:
        # transfer control to the calling function
        if deleteBlockOnly:
            yield
        else:
            # transfer control to the calling function, with sidebar blocking
            with suspendSidebar(application=application):
                yield  # undo._blocked if undo is not None else False

    except AttributeError as es:
        raise es

    finally:
        # clean up the undo block
        if undo is not None:
            undo.decreaseWaypointBlocking()

        logger.debug2('_exitDeleteBlock')


CURRENT_ATTRIBUTE_NAME = '_currentAttributeName'

class _ObjectStore(object):
    "A class to store a current setting"
    def __init__(self, obj):
        self.attributeName = getattr(obj, CURRENT_ATTRIBUTE_NAME)
        self.currentObjects = None
        self.current = getApplication().current

    def _storeCurrentSelectedObject(self):
        self.currentObjects = list(getattr(self.current, self.attributeName))

    def _restoreCurrentSelectedObject(self):
        setattr(self.current, self.attributeName, self.currentObjects)


def newObject():
    """A decorator wrap a newObject method's of the various classes in an undo block and calls
    result._finalise('create')
    """
    from ccpn.util import Undo

    @decorator.decorator
    def theDecorator(*args, **kwds):
        func = args[0]
        args = args[1:]  # Optional 'self' is now args[0]

        application = getApplication() # pass it in to reduce overhead

        with blankNotification(application=application):
            with blockUndoItems(application=application) as undoItem:

                result = func(*args, **kwds)

                # retrieve list of created items from the api
                apiObjectsCreated = result._getApiObjectTree()
                undoItem(undo=BlankedPartial(Undo._deleteAllApiObjects,
                                             obj=result, trigger='delete', preExecution=True,
                                             objsToBeDeleted=apiObjectsCreated),
                         redo=BlankedPartial(result._wrappedData.root._unDelete,
                                             topObjectsToCheck=(result._wrappedData.topObject,),
                                             obj=result, trigger='create', preExecution=False,
                                             objsToBeUnDeleted=apiObjectsCreated)
                         )

                if hasattr(result, CURRENT_ATTRIBUTE_NAME):
                    storeObj = _ObjectStore(result)
                    undoItem(undo=storeObj._storeCurrentSelectedObject,
                             redo=storeObj._restoreCurrentSelectedObject,
                             )

        result._finaliseAction('create')
        return result

    return theDecorator


def deleteObject():
    """ A decorator to wrap the delete(self) method of the V3 core classes
    calls self._finalise('delete') prior to deletion

    GWV first try
    """

    @decorator.decorator
    def theDecorator(*args, **kwds):

        func = args[0]
        args = args[1:]  # Optional 'self' is now args[0]
        self = args[0]

        self._finaliseAction('delete')

        application = getApplication()  # pass it in to reduce overhead

        with blankNotification(application=application):
                #_undo.increaseBlocking()
                # call the wrapped function
                result = func(*args, **kwds)
                #_undo.decreaseBlocking()

                # _undo._newItem(undoPartial=partial(self.project.deleteObjects, result),
                #                redoPartial=partial(func, *args, **kwds))
        return result

    return theDecorator


class BlankedPartial(object):
    """Wrapper (like partial) to call func(**kwds) with blanking
    optionally trigger the notification of obj, either pre- or post execution
    """
    def __init__(self, func, obj=None, trigger=None, preExecution=False, **kwds):
        self._func = func
        self._kwds = kwds
        self._obj = obj
        self._trigger = trigger
        self._preExecution = obj is not None and trigger is not None and preExecution
        self._postExecution = obj is not None and trigger is not None and not preExecution

    def __call__(self):
        # kwds = self._kwds.update(kwds)
        if self._preExecution:
            # call the notification
            self._obj._finaliseAction(self._trigger)

        with blankNotification():
            self._func(**self._kwds)

        if self._postExecution:
            # call the notification
            self._obj._finaliseAction(self._trigger)


def ccpNmrV3CoreSetter():
    """A decorator wrap the property setters method in an undo block and triggering the
    'change' notification
    """

    @decorator.decorator
    def theDecorator(*args, **kwds):

        func = args[0]
        args = args[1:]  # Optional 'self' is now args[0]
        self = args[0]

        application = getApplication()  # pass it in to reduce overhead

        oldValue = getattr(self, func.__name__)

        with blankNotification(application=application):
            with blockUndoItems(application=application) as undoItem:

                # call the wrapped function
                result = func(*args, **kwds)

                undoItem(undo=partial(func, self, oldValue),
                         redo=partial(func, self, args[1])
                         )
        self._finaliseAction('change')
        return result

    return theDecorator


# if __name__ == '__main__':
#     # check that the undo mechanism is working with the new context managers
#     from sandbox.Geerten.Refactored.framework import Framework, getApplication, getProject, getColourScheme
#     from sandbox.Geerten.Refactored.programArguments import Arguments, defineProgramArguments
#     from functools import partial
#
#
#     class MyProgramme(Framework):
#         "My first app"
#         pass
#
#
#     def testUndo(value=None):
#         _value = value
#
#
#     def testRedo(value=None):
#         _value = value
#
#
#     myArgs = Arguments().parseCommandLineArguments()
#     myArgs.noGui = True
#     myArgs.debug2 = True
#     app = MyProgramme('MyProgramme', '3.0.0-beta3', args=myArgs)
#     app.project._resetUndo(debug=True)
#
#     with blockUndoItems() as undoItem:
#         print('>>>open')
#
#         undoItem(undo=partial(testUndo, value=3),
#                  redo=partial(testRedo, value=4))
#
#         undoItem(undo=partial(testUndo, value=7),
#                  redo=partial(testRedo, value=8))
#
#         print('>>>close')
#
#     with blockUndoItems() as undoItem:
#         print('>>>open')
#
#         undoItem(undo=partial(testUndo, value=3),
#                  redo=partial(testRedo, value=4))
#
#         undoItem(undo=partial(testUndo, value=7),
#                  redo=partial(testRedo, value=8))
#
#         print('>>>close')
