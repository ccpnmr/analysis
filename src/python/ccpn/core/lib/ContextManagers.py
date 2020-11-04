"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-11-04 17:16:40 +0000 (Wed, November 04, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2018-12-20 15:44:34 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

import decorator
import inspect
from contextlib import contextmanager
from collections import Iterable
from functools import partial
from ccpn.core.lib import Util as coreUtil
from ccpn.util.Logging import getLogger
from ccpn.framework.Application import getApplication
from ccpn.util.Common import makeIterableList
import traceback

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
    getLogger().debug2('_enterEchoCommand: command=%s' % commands[0])

    try:
        # transfer control to the calling function
        yield

    finally:
        getLogger().debug2('_exitEchoCommand')


def _resumeNotification(application):
    """A try/except here because resume Notification MAY in exceptions circumstances
    cause fatal errors.
    """
    with catchExceptions(application=application,
                         errorStringTemplate='*** FATAL ERROR in resumeNotification: %s',
                         popupAsWarning=False, printTraceBack=True):
        application.project.resumeNotification()


@contextmanager
def undoBlockWithSideBar(application=None):
    """Wrap all the contained operations into a single undo/redo event.
    """

    # get the current application
    if not application:
        application = getApplication()
    if application is None:
        raise RuntimeError('Error getting application')

    getLogger().debug2('_enterUndoBlock')

    # get the undo stack
    undo = application._getUndo()

    if undo is not None:
        undo.newWaypoint()  # DO NOT CHANGE
        undo.increaseWaypointBlocking()

    if application.ui and application.ui.mainWindow:
        sidebar = application.ui.mainWindow.sideBar
        sidebar.increaseSidebarBlocking()

    application.project.suspendNotification()

    try:
        # transfer control to the calling function
        yield

    finally:
        _resumeNotification(application)

        if application.ui and application.ui.mainWindow:
            sidebar = application.ui.mainWindow.sideBar
            sidebar.decreaseSidebarBlocking()

        if undo is not None:
            undo.decreaseWaypointBlocking()

        getLogger().debug2('_exitUndoBlock: echoBlocking=%s' % application._echoBlocking)


@contextmanager
def undoBlockWithoutSideBar(application=None):
    """Wrap all the contained operations into a single undo/redo event. To be deprecated. Use just undoBlock
    """

    # get the current application
    if not application:
        application = getApplication()
    if application is None:
        raise RuntimeError('Error getting application')

    getLogger().debug2('_enterUndoBlockWithoutSideBar')

    # get the undo stack
    undo = application._getUndo()
    if undo is not None:
        undo.newWaypoint()  # DO NOT CHANGE
        undo.increaseWaypointBlocking()

    if application.ui and application.ui.mainWindow:
        sidebar = application.ui.mainWindow.sideBar
        sidebar.increaseSidebarBlocking(withSideBarUpdate=False)

    application.project.suspendNotification()

    try:
        # transfer control to the calling function
        yield

    finally:
        _resumeNotification(application)

        if application.ui and application.ui.mainWindow:
            sidebar = application.ui.mainWindow.sideBar
            sidebar.decreaseSidebarBlocking(withSideBarUpdate=False)

        if undo is not None:
            undo.decreaseWaypointBlocking()

        getLogger().debug2('_enterUndoBlockWithoutSideBar: echoBlocking=%s' % application._echoBlocking)


undoBlock = undoBlockWithSideBar


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
#         self.ui.mainWindow.sideBar._saveExpandedState()
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


# @contextmanager
# def logCommandBlock(prefix='', get=None, isProperty=False, showArguments=[], logCommandOnly=False, withSideBar=True):
#     """
#     Echo a command to the logger reflecting the python command required to call the function.
#
#     :param prefix: string to be prepended to the echo command
#     :param get: function containing the function
#     :param isProperty: is the function a property
#     :param showArguments: list of string names for arguments that need to be included.
#                         By default, the parameters set to the defaults are not included.
#
#     Examples:
#
#     ::
#
#     1)  def something(self, name=None, value=0):
#             logCommandManager(prefix='process.') as log:
#                 log('something')
#
#                 ... code here
#
#         call function                   echo command
#
#         something('Hello')              process.something(name='Hello')
#         something('Hello', 12)          process.something(name='Hello', value=12)
#
#         Parameters are not required in the log() command, parameters are picked up from
#         the containing function; however, changes can be inserted by including
#         the parameter, e.g., log('something', name=name+'There') will append 'There' to the name.
#
#             something('Hello')          process.something(name='HelloThere')
#
#     2)  def something(self, name=None, value=0):
#             logCommandManager(get='self') as log:
#                 log('something')
#
#                 ... code here
#
#         call function                   echo command
#
#         something('Hello')              get('parent:ID').something(name='Hello')
#         something('Hello', 12)          get('parent:ID').something(name='Hello', value=12)
#
#     3)  @property
#         def something(self, value=0):
#             logCommandManager(get='self', isProperty=True) as log:
#                 log('something', value=value)
#
#                 ... code here
#
#
#         call function                   echo command
#
#         something = 12                  get('parent:ID').something = 12
#
#         functions of this type can only contain one parameter, and
#         must be set as a keyword in the log.
#
#     4)  Mixing prefix and get:
#
#         def something(self, value=0):
#             logCommandManager(prefix='process.', get='self') as log:
#                 log('something')
#
#         if called from SpectrumDisplay:
#
#         call function                   echo command
#
#         spectrumDisplay.something(12)   process.get('spectrumDisplay:1').something(12)
#
#     5)  If the log command needs modifying, this can be included in the log command,
#         e.g., if the pid of an object needs inserting
#
#         def something(self, value=None):
#             logCommandManager(prefix='process.', get='self') as log:
#                 log('something', value=value.pid)
#
#         if called from SpectrumDisplay:
#
#         call function                   echo command
#
#         spectrumDisplay.something(<anObject>)   process.get('spectrumDisplay:1').something(value=anObject:pid)
#
#         To make quotes appear around the value use: log('something', value=repr(value.pid))
#
#     """
#
#     # get the current application
#     application = getApplication()
#
#     def log(funcName, *args, **kwargs):  # remember _undoBlocked, as first parameter
#         if application._echoBlocking > 1:  # already increased before entry
#             return
#
#         # get the caller from the getframe stack
#         fr1 = sys._getframe(1)
#         selfCaller = fr1.f_locals[get] if get else None
#         pid = selfCaller.pid if selfCaller is not None and hasattr(selfCaller, 'pid') else ''
#
#         # make a list for modifying the log string with more readable labels
#         checkList = [(application, 'application.'),
#                      (application.ui.mainWindow, 'mainWindow.'),
#                      (application.project, 'project.'),
#                      (application.current, 'current.')]
#         for obj, label in checkList:
#             if selfCaller is obj:
#                 getPrefix = label
#                 break
#         else:
#             getPrefix = "get('%s')." % pid if (get and pid) else ''
#
#         # search if caller matches the main items in the application namespace, e.g., 'application', 'project', etc.
#         # nameSpace = application._getNamespace()
#         # for k in nameSpace.keys():
#         #     if selfCaller == nameSpace[k]:
#         #         getPrefix = k+'.'
#         #         break
#         # else:
#         #     getPrefix = "get('%s')." % pid if get else ''
#
#         # construct the new log string
#         if isProperty:
#             logs = prefix + getPrefix + funcName + ' = ' + repr(list(kwargs.values())[0])
#         else:
#
#             # build the log command from the parameters of the caller function
#             # only those that are not in the default list are added, i.e. those defined
#             # explicitly by the caller
#             if selfCaller is not None:
#                 selfFunc = getattr(selfCaller, funcName)
#                 sig0 = [(k, v) for k, v in signature(selfFunc).parameters.items()]
#                 sig1 = [k for k, v in signature(selfFunc).parameters.items()
#                         if v.default is Parameter.empty
#                         or k in showArguments
#                         or k in kwargs]
#                 # or (k in fr1.f_locals and (repr(fr1.f_locals[k]) != repr(v.default)))]
#             else:
#                 sig1 = {}
#
#             # create the log string
#             logs = prefix + getPrefix + funcName + '('
#             for k in sig1:
#                 if k != 'self':
#                     kval = str(kwargs[k]) if k in kwargs else repr(fr1.f_locals[k])
#                     logs += str(k) + '=' + kval + ', '
#             logs = logs.rstrip(', ')
#             logs += ')'
#
#         # logger.log(logs)
#         logger.info(logs)
#
#     # log commands to the registered outputs
#     logger = getLogger()
#     application._increaseNotificationBlocking()
#
#     try:
#         if logCommandOnly:
#             # only execute the calling function
#             yield log
#         else:
#             # transfer control to the calling function, create an undo waypoint
#             if withSideBar:
#                 with undoBlock(application=application):  # as _undoBlocking:
#                     yield log  # partial(log, _undoBlocking)
#
#             else:
#                 with undoBlockWithoutSideBar(application=application):  # as _undoBlocking:
#                     yield log  # partial(log, _undoBlocking)
#
#     except AttributeError as es:
#         raise
#
#     finally:
#         # clean up log command block
#         application._decreaseNotificationBlocking()


@contextmanager
def catchExceptions(application=None, errorStringTemplate='Error: "%s"', popupAsWarning=True, printTraceBack=False):
    """Catches exceptions in try except; logging it as warning;

    errorStringTemplate: string with one '%s'; used to output the exception to logger as warning
    popupAsWarning: flag to report output as a warning popup

    raises the error again in debug mode
    """
    # get the current application
    if not application:
        application = getApplication()
    if application is None:
        raise RuntimeError('Error getting application')

    try:
        yield

    except Exception as es:
        getLogger().warning(errorStringTemplate % str(es))
        if printTraceBack:
            traceback.print_exc() # please give more info about the error!
        if application.hasGui and popupAsWarning:
            from ccpn.ui.gui.widgets import MessageDialog  # Local import: in case of no-gui, we never get here

            MessageDialog.showWarning('Warning', errorStringTemplate % str(es))
        if application._isInDebugMode:
            raise es


# @contextmanager
# def undoBlockManager(application=None, undoBlockOnly=False):
#     """Wrap all the contained operations into a single undo/redo event.
#     """
#
#     # get the current application
#     if not application:
#         application = getApplication()
#     if application is None:
#         raise RuntimeError('Error getting application')
#
#     undo = application._getUndo()
#     if undo is not None:  # ejb - changed from if undo:
#         undo.newWaypoint()  # DO NOT CHANGE
#         undo.increaseWaypointBlocking()
#
#     logger = getLogger()
#     logger.debug3('_enterUndoBlock')
#
#     try:
#         # transfer control to the calling function
#         if undoBlockOnly:
#             yield
#         else:
#             # transfer control to the calling function, with sidebar blocking
#             with sidebarBlocking(application=application):
#                 yield  # undo._blocked if undo is not None else False
#
#     except Exception as es:
#         raise
#
#     finally:
#         # clean up the undo block
#         if undo is not None:
#             undo.decreaseWaypointBlocking()
#
#         logger.debug3('_exitUndoBlock')
#
#     # with suspendSidebar():
#     #     yield  # undo._blocked if undo is not None else False
#     #
#     # # clean up the undo block
#     # if undo is not None:
#     #     undo.decreaseWaypointBlocking()
#     #
#     # logger.debug2('_exitUndoBlock')


@contextmanager
def sidebarBlocking(application=None, blockSidebarOnly=False):
    """
    Block updating of the sidebar (if present) until end of function block.
    """

    # get the current application
    if not application:
        application = getApplication()
    if application is None:
        raise RuntimeError('Error getting application')

    if application.ui and application.ui.mainWindow:
        sidebar = application.ui.mainWindow.sideBar
        sidebar.increaseSidebarBlocking()

    try:
        # transfer control to the calling function
        if blockSidebarOnly:
            yield
        else:
            # transfer control to the calling function, suspending notifications
            with notificationSuspend(application=application):
                yield

    except AttributeError as es:
        raise

    finally:
        # clean up after suspending sidebar updates
        if application.ui and application.ui.mainWindow:
            sidebar = application.ui.mainWindow.sideBar
            sidebar.decreaseSidebarBlocking()


@contextmanager
def notificationSuspend(application=None):
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
def notificationBlanking(application=None):
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
def notificationEchoBlocking(application=None):
    """
    Disable echoing of commands to the terminal, re-enable at the end of the function block.
    """

    # get the application
    if not application:
        application = getApplication()
    if application is None:
        raise RuntimeError('Error getting application')

    application._increaseNotificationBlocking()
    try:
        # transfer control to the calling function
        yield

    except AttributeError as es:
        raise es

    finally:
        # clean up after disabling echo blocking
        application._decreaseNotificationBlocking()


@contextmanager
def notificationUnblanking():
    """
    Unblock all notifiers, disable at the end of the function block.
    Used inside notificationBlanking if a notifier is required for a single event
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
def undoStackBlocking(application=None):
    """
    Block addition of items to the undo stack, re-enable at the end of the function block.

    New user items can be added to the undo stack after blocking is re-enabled.

    Example:

    ::

        with undoStackBlocking() as addUndoItem:
            ...
            do something here
            ...
            addUndoItem(undo=partial(<function>, <args and kwargs>),
                        redo=partial(<function>, <args and kwargs>))
            do more here

    Multiple undoItems can be appended.

    """

    # get the current application
    if not application:
        application = getApplication()
    if application is None:
        raise RuntimeError('Error getting application')

    undo = application._getUndo()
    if undo is None:
        raise RuntimeError("Unable to get the application's undo stack")
    _undoStack = []

    def addUndoItem(undo=None, redo=None):
        """This function allows for adding items onto the application's undo stack
        Collected in a temporary list, and added to the undo stack after the stack has been unblocked
        """
        # store the new undo/redo items for later addition to the stack
        _undoStack.append((undo, redo))

    undo.newWaypoint()  # DO NOT CHANGE
    undo.increaseWaypointBlocking()
    undo.increaseBlocking()

    try:
        # transfer control to the calling function, and pass the addUndoItems function
        yield addUndoItem

    except AttributeError as es:
        raise es

    finally:
        # clean up after blocking undo items
        undo.decreaseBlocking()
        undo.decreaseWaypointBlocking()

        # add all undo items (collected via the addUndoItem function) to the application's undo stack
        for item in _undoStack:
            undo._newItem(undoPartial=item[0], redoPartial=item[1])


# @contextmanager
# def undoStackUnblocking(application=None):
#     """
#     Temporarily release the undoStack (for newObject)
#     """
#
#     # get the current application
#     if not application:
#         application = getApplication()
#     if application is None:
#         raise RuntimeError('Error getting application')
#
#     undo = application._getUndo()
#     if undo is None:
#         raise RuntimeError("Unable to get the application's undo stack")
#     _undoStack = []
#
#     undo.decreaseBlocking()
#
#     try:
#         # transfer control to the calling function
#         yield
#
#     except AttributeError as es:
#         raise es
#
#     finally:
#         # clean up after blocking undo items
#         undo.increaseBlocking()


@contextmanager
def waypointBlocking(application=None):
    """
    Block addition of new waypoints
    """

    # get the current application
    if not application:
        application = getApplication()
    if application is None:
        raise RuntimeError('Error getting application')

    undo = application._getUndo()
    if undo is None:
        raise RuntimeError("Unable to get the application's undo stack")
    _undoStack = []

    undo.newWaypoint()  # DO NOT CHANGE
    undo.increaseWaypointBlocking()

    try:
        # transfer control to the calling function, and pass the addUndoItems function
        yield

    except AttributeError as es:
        raise es

    finally:
        # clean up after blocking undo items
        undo.decreaseWaypointBlocking()


# @contextmanager
# def deleteBlockManager(application=None, deleteBlockOnly=False):
#     """
#     Wrap all the following calls with a single undo/redo method.
#     """
#
#     # get the application
#     if not application:
#         application = getApplication()
#     if application is None:
#         raise RuntimeError('Error getting application')
#
#     undo = application._getUndo()
#
#     if undo is not None:  # ejb - changed from if undo:
#         undo.newWaypoint()  # DO NOT CHANGE
#         undo.increaseWaypointBlocking()
#
#     logger = getLogger()
#     logger.debug2('_enterDeleteBlock')
#
#     try:
#         # transfer control to the calling function
#         if deleteBlockOnly:
#             yield
#         else:
#             # transfer control to the calling function, with sidebar blocking
#             with sidebarBlocking(application=application):
#                 yield  # undo._blocked if undo is not None else False
#
#     except AttributeError as es:
#         raise es
#
#     finally:
#         # clean up the undo block
#         if undo is not None:
#             undo.decreaseWaypointBlocking()
#
#         logger.debug2('_exitDeleteBlock')


CURRENT_ATTRIBUTE_NAME = '_currentAttributeName'


class _ObjectStore(object):
    "A class to store a current setting"

    def __init__(self, obj):
        self.current = getApplication().current
        self.attributeName = getattr(obj, CURRENT_ATTRIBUTE_NAME)
        if not hasattr(self.current, self.attributeName):
            raise RuntimeError('Current object does not have attribute "%s"' % self.attributeName)
        self.currentObjects = None
        self.singularOnly = False

    def _storeCurrentSelectedObject(self):
        items = getattr(self.current, self.attributeName)
        if isinstance(items, Iterable):
            self.currentObjects = tuple(items)
            self.singularOnly = False
        else:
            self.currentObjects = items
            self.singularOnly = True

    def _restoreCurrentSelectedObject(self):
        self.current.increaseBlanking()
        setattr(self.current, self.attributeName, self.currentObjects)
        self.current.decreaseBlanking()


def _storeNewObjectCurrent(result, thisAddUndoItem):
    if hasattr(result, CURRENT_ATTRIBUTE_NAME):
        storeObj = _ObjectStore(result)
        thisAddUndoItem(undo=storeObj._storeCurrentSelectedObject,
                        redo=storeObj._restoreCurrentSelectedObject,
                        )


def _storeDeleteObjectCurrent(self, thisAddUndoItem):
    if hasattr(self, CURRENT_ATTRIBUTE_NAME):
        storeObj = _ObjectStore(self)

        # store the current state - check because item already removed from current?
        storeObj._storeCurrentSelectedObject()

        # add it to the stack
        thisAddUndoItem(undo=storeObj._restoreCurrentSelectedObject,
                        redo=storeObj._storeCurrentSelectedObject
                        )


def newObject(klass):
    """A decorator wrap a newObject method's of the various classes in an undo block and calls
    result._finalise('create')
    """
    from ccpn.core.lib import Undo

    @decorator.decorator
    def theDecorator(*args, **kwds):
        func = args[0]
        args = args[1:]  # Optional 'self' is now args[0]

        application = getApplication()  # pass it in to reduce overhead

        with notificationBlanking(application=application):
            with undoStackBlocking(application=application) as addUndoItem:
                result = func(*args, **kwds)
                if not isinstance(result, klass):
                    raise RuntimeError('Expected an object of class %s, obtained %s' % (klass, result.__class__))

                # retrieve list of created api objects from the result
                apiObjectsCreated = result._getApiObjectTree()
                addUndoItem(undo=BlankedPartial(Undo._deleteAllApiObjects,
                                                obj=result, trigger='delete', preExecution=True,
                                                objsToBeDeleted=apiObjectsCreated),
                            redo=BlankedPartial(result._wrappedData.root._unDelete,
                                                topObjectsToCheck=(result._wrappedData.topObject,),
                                                obj=result, trigger='create', preExecution=False,
                                                objsToBeUnDeleted=apiObjectsCreated)
                            )

                _storeNewObjectCurrent(result, addUndoItem)
                # if hasattr(result, CURRENT_ATTRIBUTE_NAME):
                #     storeObj = _ObjectStore(result)
                #     addUndoItem(undo=storeObj._storeCurrentSelectedObject,
                #                 redo=storeObj._restoreCurrentSelectedObject,
                #                 )

        result._finaliseAction('create')
        return result

    return theDecorator


def newObjectList(klasses):
    """A decorator wrap a newObject method's of the various classes in an undo block and calls
    result._finalise('create') for each object in the results list
    klasses is a list of strings of type klass.__class__.__name__ to remove restriction on circular imports
    The primary object (first in the list) is returned and must be the first type in klasses list
    """
    from ccpn.core.lib import Undo

    @decorator.decorator
    def theDecorator(*args, **kwds):
        func = args[0]
        args = args[1:]  # Optional 'self' is now args[0]

        application = getApplication()  # pass it in to reduce overhead

        with notificationBlanking(application=application):
            with undoStackBlocking(application=application) as addUndoItem:
                results = func(*args, **kwds)
                if not (results and results[0].__class__.__name__ == klasses[0]):
                    raise RuntimeError('Expected an object of class %s, obtained %s' % (repr(klasses[0]), results[0].__class__))

                for result in results:
                    if not result.__class__.__name__ in klasses:
                        raise RuntimeError('Expected an object in class types %s, obtained %s' % (klasses, result.__class__))

                    # retrieve list of created api objects from the result
                    apiObjectsCreated = result._getApiObjectTree()
                    addUndoItem(undo=BlankedPartial(Undo._deleteAllApiObjects,
                                                    obj=result, trigger='delete', preExecution=True,
                                                    objsToBeDeleted=apiObjectsCreated),
                                redo=BlankedPartial(result._wrappedData.root._unDelete,
                                                    topObjectsToCheck=(result._wrappedData.topObject,),
                                                    obj=result, trigger='create', preExecution=False,
                                                    objsToBeUnDeleted=apiObjectsCreated)
                                )

                    _storeNewObjectCurrent(result, addUndoItem)
                    # if hasattr(result, CURRENT_ATTRIBUTE_NAME):
                    #     storeObj = _ObjectStore(result)
                    #     addUndoItem(undo=storeObj._storeCurrentSelectedObject,
                    #                 redo=storeObj._restoreCurrentSelectedObject,
                    #                 )

        # handle notifying all objects in the list - e.g. sampleComponent also makes a substance
        for result in results:
            result._finaliseAction('create')
        # return the primary object
        return results[0] if result else None

    return theDecorator


def deleteObject():
    """ A decorator to wrap the delete(self) method of the V3 core classes
    calls self._finalise('delete') prior to deletion

    GWV first try
    EJB 20181130: modified
    """

    @decorator.decorator
    def theDecorator(*args, **kwds):
        func = args[0]
        args = args[1:]  # Optional 'self' is now args[0]
        self = args[0]
        application = getApplication()  # pass it in to reduce overhead

        self._finaliseAction('delete')

        with notificationBlanking(application=application):
            with undoStackBlocking(application=application) as addUndoItem:
                _storeDeleteObjectCurrent(self, addUndoItem)

                # retrieve list of created items from the api
                apiObjectsCreated = self._getApiObjectTree()
                addUndoItem(undo=BlankedPartial(self._wrappedData.root._unDelete,
                                                topObjectsToCheck=(self._wrappedData.topObject,),
                                                obj=self, trigger='create', preExecution=False,
                                                objsToBeUnDeleted=apiObjectsCreated),
                            redo=BlankedPartial(self.delete,
                                                obj=self, trigger='delete', preExecution=True)
                            )

                # call the wrapped delete function
                result = func(*args, **kwds)

        return result

    return theDecorator


def renameObject():
    """ A decorator to wrap the rename(self) method of the V3 core classes
    calls self._finaliseAction('rename') after the rename

    EJB 20191023: modified original contextManager to be decorator to match new/delete
    """

    @decorator.decorator
    def theDecorator(*args, **kwds):
        func = args[0]
        args = args[1:]  # Optional 'self' is now args[0]
        self = args[0]
        application = getApplication()  # pass it in to reduce overhead

        with notificationBlanking(application=application):
            with undoStackBlocking(application=application) as addUndoItem:
                # call the wrapped rename function
                result = func(*args, **kwds)

                addUndoItem(undo=BlankedPartial(func, self, 'rename', False, self, *result),
                            redo=BlankedPartial(func, self, 'rename', False, *args, **kwds)
                            )

        self._finaliseAction('rename')

        return True

    return theDecorator


@contextmanager
def renameObjectContextManager(self):
    """ A decorator to wrap the rename(self) method of the V3 core classes
    calls self._finaliseAction('rename', 'change') after the rename
    """
    # get the current application
    application = getApplication()

    with notificationBlanking(application=application):
        with undoStackBlocking(application=application) as addUndoItem:

            try:
                # transfer control to the calling function
                yield addUndoItem

            except AttributeError as es:
                raise es

    self._finaliseAction('rename')


@contextmanager
def renameObjectNoBlanking(self):
    """ A decorator to wrap the rename(self) method of the V3 core classes
    calls self._finaliseAction('rename', 'change') after the rename
    """
    # get the current application
    application = getApplication()

    with undoStackBlocking(application=application) as addUndoItem:

        try:
            # transfer control to the calling function
            yield addUndoItem

        except AttributeError as es:
            raise es

    self._finaliseAction('rename')


class BlankedPartial(object):
    """Wrapper (like partial) to call func(**kwds) with blanking
    optionally trigger the notification of obj, either pre- or post execution.
    """

    def __init__(self, func, obj=None, trigger=None, preExecution=False, *args, **kwds):
        self._func = func
        self._args = args
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

        with notificationBlanking():
            self._func(*self._args, **self._kwds)

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

        with notificationBlanking(application=application):
            with undoStackBlocking(application=application) as addUndoItem:
                # call the wrapped function
                result = func(*args, **kwds)

                addUndoItem(undo=partial(func, self, oldValue),
                            redo=partial(func, self, args[1])
                            )

        self._finaliseAction('change')
        return result

    return theDecorator


def ccpNmrV3CoreUndoBlock():
    """A decorator wrap the property setters method in an undo block and triggering the
    'change' notification
    """

    @decorator.decorator
    def theDecorator(*args, **kwds):
        func = args[0]
        args = args[1:]  # Optional 'self' is now args[0]
        self = args[0]

        application = getApplication()  # pass it in to reduce overhead

        with notificationBlanking(application=application):
            with undoBlock():
                # call the wrapped function
                result = func(*args, **kwds)

        self._finaliseAction('change')
        return result

    return theDecorator


def ccpNmrV3CoreSimple():
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

        with undoBlockWithoutSideBar(application=application):
            with undoStackBlocking(application=application) as addUndoItem:
                # call the wrapped function
                result = func(*args, **kwds)

                addUndoItem(undo=partial(func, self, oldValue),
                            redo=partial(func, self, args[1])
                            )

        # self._finaliseAction('change')
        return result

    return theDecorator


DEFINEDPARAMETERS = ('option', 'attr', 'parameter', 'dim')


def queueStateChange(verify):
    """A decorator to wrap a state change event with a verify function
    """

    @decorator.decorator
    def theDecorator(*args, **kwds):
        func = args[0]
        args = args[1:]  # Optional 'self' is now args[0]
        self = args[0]

        # get the signature
        sig = inspect.signature(func)
        # fill in the missing parameters
        ba = sig.bind(*args, **kwds)
        ba.apply_defaults()

        # get specific arguments - cannot just grab all as may contain variants
        pars = [ba.arguments.get(par) for par in DEFINEDPARAMETERS]

        # call the function - should return None if returning to unmodified state
        result = func(*args, **kwds)

        # call the verify function to update the _changes dict
        verify(self, func.__name__, result, *pars)

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
#     with blockUndoItems() as addUndoItem:
#         print('>>>open')
#
#         addUndoItem(undo=partial(testUndo, value=3),
#                  redo=partial(testRedo, value=4))
#
#         addUndoItem(undo=partial(testUndo, value=7),
#                  redo=partial(testRedo, value=8))
#
#         print('>>>close')
#
#     with blockUndoItems() as addUndoItem:
#         print('>>>open')
#
#         addUndoItem(undo=partial(testUndo, value=3),
#                  redo=partial(testRedo, value=4))
#
#         addUndoItem(undo=partial(testUndo, value=7),
#                  redo=partial(testRedo, value=8))
#
#         print('>>>close')
