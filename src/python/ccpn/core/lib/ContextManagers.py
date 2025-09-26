"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2025"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2025-09-09 18:55:13 +0100 (Tue, September 09, 2025) $"
__version__ = "$Revision: 3.3.2.3 $"
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
# from inspect import signature, Parameter
import traceback
import re
import signal
import pandas as pd
import numpy as np
import weakref
from functools import partial

from PyQt5 import QtWidgets
from PyQt5.QtGui import QPainter

from contextlib import contextmanager, nullcontext, suppress
from collections.abc import Iterable

from ccpn.core.lib import Util as coreUtil
from ccpn.core.lib.Notifiers import Notifier
from ccpn.util.Logging import getLogger
from ccpn.framework.Application import getApplication

from ccpn.ui.gui.guiSettings import _styleMagenta, _styleRed

#--------------------------------------------------------------------------------------------

def _debugUndo(undo, text, enter):
    """debug info for entering/exiting undo blocks
    """
    from ccpn.util.Common import reduceText
    indent = '-'*(undo._waypointBlockingLevel)
    arrow = f'|{indent}>' if enter else f'<{indent}|'
    getLogger().debug2(_styleMagenta(f'{arrow:7} {reduceText(text)}'))

#--------------------------------------------------------------------------------------------

_REPLACEPERCENT = r'%(?!s)'


@contextmanager
def echoCommand(obj, funcName, *params, values=None, defaults=None,
                parName=None, propertySetter=False, **objectParameters):
    # from ccpn.core.lib import Util as coreUtil

    try:
        project = obj._project
    except Exception:
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
    getLogger().debug2(f'_enterEchoCommand: command={commands[0]}')

    try:
        # transfer control to the calling function
        yield

    finally:
        getLogger().debug2('_exitEchoCommand')


# def _resumeNotification(application):
#     """A try/except here because resume Notification MAY in exceptional circumstances
#     cause fatal errors.
#     """
#     with catchExceptions(application=application,
#                          errorStringTemplate='*** FATAL ERROR in resumeNotification: %s',
#                          popupAsWarning=False, printTraceBack=True):
#         application.project.resumeNotification()


@contextmanager
def undoBlockWithSideBar(application=None, debugText=''):
    """Wrap all the contained operations into a single undo/redo event.
    """

    # get the current application
    if not application:
        application = getApplication()
    if application is None:
        raise RuntimeError('Error getting application')

    # get the undo stack
    if (undo := application._getUndo()) is None:
        raise RuntimeError(f'Unable to get the undo stack')

    _debugUndo(undo, f'UndoBlockWithSideBar: {debugText}', enter=True)

    undo.newWaypoint()  # DO NOT CHANGE
    undo.increaseWaypointBlocking()

    if application.ui and application.ui.mainWindow:
        sidebar = application.ui.mainWindow._getSideBar()
        sidebar.increaseSidebarBlocking(withSideBarUpdate=True)

    application.project._suspendNotification()

    try:
        # transfer control to the calling function
        yield

    finally:
        # GWV do not do this: it is masking other errors
        # triggering strange behavior in-turn
        # _resumeNotification(application)
        application.project._resumeNotification()

        if application.ui and application.ui.mainWindow:
            sidebar = application.ui.mainWindow._getSideBar()
            sidebar.decreaseSidebarBlocking(withSideBarUpdate=True)

        if undo is not None:
            undo.decreaseWaypointBlocking()

        _debugUndo(undo, f'UndoBlockWithSideBar: {debugText}', enter=False)


@contextmanager
def undoBlockWithoutSideBar(application=None, debugText=''):
    """Wrap all the contained operations into a single undo/redo event. To be deprecated. Use just undoBlock
    """

    # get the current application
    if not application:
        application = getApplication()
    if application is None:
        raise RuntimeError('Error getting application')

    # get the undo stack
    if (undo := application._getUndo()) is None:
        raise RuntimeError(f'Unable to get the undo stack')

    _debugUndo(undo, f'UndoBlockWithoutSideBar: {debugText}', enter=True)

    undo.newWaypoint()  # DO NOT CHANGE
    undo.increaseWaypointBlocking()

    if application.ui and application.ui.mainWindow:
        sidebar = application.ui.mainWindow._getSideBar()
        sidebar.increaseSidebarBlocking(withSideBarUpdate=False)

    application.project._suspendNotification()

    try:
        # transfer control to the calling function
        yield

    finally:
        # GWV do not do this: it is masking other errors
        # triggering strange behavior in-turn
        # _resumeNotification(application)
        application.project._resumeNotification()

        if application.ui and application.ui.mainWindow:
            sidebar = application.ui.mainWindow._getSideBar()
            sidebar.decreaseSidebarBlocking(withSideBarUpdate=False)

        if undo is not None:
            undo.decreaseWaypointBlocking()

        _debugUndo(undo, f'UndoBlockWithoutSideBar: {debugText}', enter=False)


undoBlock = undoBlockWithSideBar


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
        getLogger().debug(_styleRed(f'Caught exception: {es}'))

        if errorStringTemplate is None or errorStringTemplate.count('%s') != 1:
            errorStringTemplate = f'%s\n[malformed template]'

        errorStringTemplate = re.sub(_REPLACEPERCENT, '%%', errorStringTemplate)
        getLogger().warning(errorStringTemplate % str(es))

        if printTraceBack or application._isInDebugMode:
            traceback.print_exc()  # please give more info about the error!

        if application.hasGui and popupAsWarning:
            from ccpn.ui.gui.widgets import MessageDialog  # Local import: in case of no-gui, we never get here

            MessageDialog.showWarning('Warning', errorStringTemplate % str(es))
        # if application._isInDebugMode:
        #     raise es


@contextmanager
def rebuildSidebar(application=None):
    """
    This context manager clears and blocks the sidebar and rebuilds it afterwards
    """

    # get the current application
    if not application:
        application = getApplication()
    if application is None:
        raise RuntimeError('Error getting application')

    if application.hasGui:
        sidebar = application.mainWindow._getSideBar()
        sidebar.increaseSidebarBlocking(withSideBarUpdate=True)
        sidebar.clearSideBar()
    else:
        sidebar = None

    try:
        # transfer control to the calling function
        yield

    except AttributeError as es:
        raise

    finally:
        # clean up after suspending sidebar updates
        if sidebar is not None:
            sidebar.decreaseSidebarBlocking(withSideBarUpdate=True)
            sidebar.buildTree(application.project, clear=False)


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
        sidebar = application.ui.mainWindow._getSideBar()
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
            sidebar = application.ui.mainWindow._getSideBar()
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

    application.project._suspendNotification()
    try:
        # transfer control to the calling function
        yield

    except AttributeError as es:
        raise

    finally:
        # clean up after suspending notifications
        application.project._resumeNotification()


# @contextmanager
def notificationBlanking():
    """Block all notifiers, re-enable at the end of the function block.
    """
    return doBlock(notification=True)

    # # local import to avoid cycles
    # from ccpn.core.lib.Notifiers import NotifierBase
    #
    # NotifierBase._increaseNotificationBlanking()
    # try:
    #     # transfer control to the calling function
    #     yield
    #
    # except AttributeError as es:
    #     raise es
    #
    # finally:
    #     # clean up after blocking notifications
    #     NotifierBase._decreaseNotificationBlanking()


# @contextmanager
def apiNotificationBlanking(application=None):
    """Block api new/create/change/delete notifiers, re-enable at the end of the function block.
    """
    return doBlock(apiNotification=True)

    # # get the application
    # if not application and not (application := getApplication()):
    #     raise RuntimeError('Error getting application')
    # application.project._increaseApiNotificationBlanking()
    # try:
    #     # transfer control to the calling function
    #     yield
    # except AttributeError as es:
    #     raise es
    # finally:
    #     # clean up after blocking notifications
    #     application.project._decreaseApiNotificationBlanking()
    #     if application.project._apiNotificationBlanking < 0:
    #         raise RuntimeError('*** Code Error: _apiNotificationBlanking below zero')


@contextmanager
def _apiBlocking(application=None):
    """Block all api feedback to the current project, specifically for v2-upgrades.
    Re-enable at the end of the function block.
    CCPN Internal - use with care.
    """
    # get the application
    if not application and not (application := getApplication()):
        raise RuntimeError('Error getting application')
    application.project._apiBlocking += 1
    try:
        # transfer control to the calling function
        yield
    except AttributeError as es:
        raise es
    finally:
        # clean up after blocking notifications
        application.project._apiBlocking -= 1
        if application.project._apiBlocking < 0:
            raise RuntimeError('*** Code Error: _apiBlocking below zero')


# @contextmanager
def notificationEchoBlocking(application=None):
    """Disable echoing of commands to the terminal, re-enable at the end
    of the function block.
    """
    return doBlock(echoing=True)

    # # get the application
    # if not application:
    #     application = getApplication()
    # if application is None:
    #     raise RuntimeError('Error getting application')
    #
    # application._increaseEchoBlocking()
    # try:
    #     # transfer control to the calling function
    #     yield
    #
    # except AttributeError as es:
    #     raise es
    #
    # finally:
    #     # clean up after disabling echo blocking
    #     application._decreaseEchoBlocking()


@contextmanager
def logCommandManager(prefix, funcName, logLevel='INFO', *args, **kwds):
    """Echo commands as prefix.funcName( **kwds )"""
    from ccpn.util.decorators import _obj2pid

    application = getApplication()
    if application is None:
        raise RuntimeError('Error getting application')

    blocking = application._echoBlocking

    if blocking == 0 and application.ui is not None:
        if prefix[-1] != '.':
            prefix += '.'

        msg = prefix + funcName + '('
        for arg in args:
            msg += '%r, ' % _obj2pid(arg)
        for key, val in kwds.items():
            msg += '%s=%r, ' % (key, _obj2pid(val))
        # remove any unnecessary ', ' from the end
        if msg[-2:] == ', ':
            msg = msg[:-2]
        msg += ')'

        application.ui.echoCommands([msg], logLevel)

    with notificationEchoBlocking(application=application):
        yield


@contextmanager
def doBlock(
        echoing: bool = False,  # commandline echoing blocking
        sideBar: bool = False,  # sidebar update blanking
        notification: bool = False, # notification blanking
        apiNotification: bool = False,  # API notification blanking
        undoAddition: bool = False,  # Undo adding to stack blocking
        undoWaypoint: bool = False, # Undo waypoint blocking
    ):
    """Context manager to set a variety of blocking behavior.
    """
    # local import to avoid cycles
    from ccpn.core.lib.Notifiers import NotifierBase

    _app = getApplication()
    _undo = _app._getUndo() if _app and _app.project else None
    _sideBarObj = _app.ui.mainWindow._getSideBar() \
                  if _app.hasGui and _app.ui.mainWindow is not None \
                  else None

    if echoing:
        _app._increaseEchoBlocking()

    if sideBar and _sideBarObj:
        _sideBarObj.increaseSidebarBlocking(withSideBarUpdate=True)

    if notification:
        NotifierBase._increaseNotificationBlanking()

    if apiNotification:
        NotifierBase._increaseApiNotificationBlanking()

    if _undo and undoAddition:
        _undo.increaseBlocking()

    if _undo and undoWaypoint:
        _undo.increaseWaypointBlocking()

    try:
        yield

    except Exception as es:
        getLogger().debug(f'doBalock return with exception: {es}')
        raise es

    finally:
        if echoing:
            _app._decreaseEchoBlocking()

        if sideBar and _sideBarObj:
            _sideBarObj.decreaseSidebarBlocking(withSideBarUpdate=True)

        if notification:
            NotifierBase._decreaseNotificationBlanking()

        if apiNotification:
            NotifierBase._decreaseApiNotificationBlanking()

        if _undo and undoAddition:
            _undo.decreaseBlocking()

        if _undo and undoWaypoint:
            _undo.decreaseWaypointBlocking()


def inactivity(project=None, debugText=''):
    """
    Block all notifiers, apiNotifiers, undo, sidebar and echo-ing
    re-enable at the end of the function block.
    We allow passing in of application and project, as this is used in the
    initialisation when not all is proper yet.
    """
    getLogger().debug2(f'> Enter Inactivity: {debugText}')
    return doBlock(echoing=True,
                   sideBar=True,
                   notification=True,
                   apiNotification=True,
                   undoAddition=True,
                   undoWaypoint=True,
                  )


@contextmanager
def undoStackRevert(application=None):
    """
    Revert the contents of the undo stack if an error occurred

    usage:

    e.g.
        with undoStackRevert() as revertStack:
            ...process

            if error:
                # set the error state of the context manager
                revertStack(True)

    'revertStack' could of course be any name, but best to keep relevant.
    """
    errorState = False

    def setErrorState(state):
        """Change the error state
        """
        # first time I've ever used nonlocal :)
        nonlocal errorState
        if not isinstance(state, bool):
            raise TypeError('state must be a bool')
        errorState = state

    # get the current application
    if not application:
        application = getApplication()
    if application is None:
        raise RuntimeError('Error getting application')

    undo = application._getUndo()
    if undo is None:
        raise RuntimeError("Unable to get the application's undo stack")

    # keep a shallow copy of the undo stack
    _oldUndo = undo.__dict__.copy()
    _oldUndoLen = len(undo)

    try:
        # transfer control to the calling function, and pass the setErrorState function
        yield setErrorState

    except Exception as es:
        raise es

    finally:
        if errorState and len(undo) > _oldUndoLen:
            # assumes that values have ONLY been added, not altered in the middle of the deque
            # and that the values need removing from top
            for rr in range(len(undo) - _oldUndoLen):
                undo.pop()
            # restore the state of the __dict__ to replace any other changed values
            undo.__dict__.update(_oldUndo)


@contextmanager
def undoStackBlocking(application=None, project=None, debugText=''):
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

    if project is None:
        project = application.project
    if project is None:
        raise RuntimeError('Error getting project')

    undo = project._undo
    if undo is None:
        raise RuntimeError("Unable to get the application's undo stack")
    _undoStack = []

    def addUndoItem(undo=None, redo=None):
        """This function allows for adding items onto the application's undo stack
        Collected in a temporary list, and added to the undo stack after the stack has been unblocked
        """
        # store the new undo/redo items for later addition to the stack
        _undoStack.append((undo, redo))

    _debugUndo(undo, f'UndoStackBlocking: {debugText}', enter=True)

    undo.newWaypoint()  # DO NOT CHANGE
    undo.increaseWaypointBlocking()
    undo.increaseBlocking()

    try:
        # transfer control to the calling function, and pass the addUndoItems function
        yield addUndoItem

    except Exception as es:
        getLogger().debug(_styleRed(f'UndoStack encountered an error: {es}'))
        raise es

    finally:
        # clean up after blocking undo items
        undo.decreaseBlocking()
        undo.decreaseWaypointBlocking()

        # add all undo items (collected via the addUndoItem function) to the application's undo stack
        for item in _undoStack:
            undo._newItem(undoPartial=item[0], redoPartial=item[1])

        _debugUndo(undo, f'UndoStackBlocking: {debugText}', enter=False)

undoStack = undoStackBlocking

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


class PandasChainedAssignment:
    """ Context manager to temporarily set pandas chained assignment warning. Usage:
        with ChainedAssignment():
             blah
    """

    def __init__(self, chained=None):
        acceptable = [None, 'warn', 'raise']
        assert chained in acceptable, f"chained must be in {acceptable}"
        self.swcw = chained

    def __enter__(self):
        self.saved_swcw = pd.options.mode.chained_assignment
        pd.options.mode.chained_assignment = self.swcw
        return self

    def __exit__(self, *args):
        pd.options.mode.chained_assignment = self.saved_swcw


class Timeout:
    """
    A simple No-UI context manager to wrap a long operation, which is not necessarily a loop.

    -- Do an operation until time runs out --

    ========================================

    Usage:
        # -- Single thread -- #
        with timeout(seconds=60, timeoutMessage='time is over') as t:
            # do a long operation   # if not finished before time runs out then it stops ...

    ========================================

    """

    def __init__(self, seconds: int = 60, timeoutMessage: str = "", loggingType='warning'):
        self.seconds = int(seconds)
        self.timeoutMessage = timeoutMessage
        allowedLoggers = ['warning', 'debug', 'debug1', 'debug2', 'debug3', 'critical']
        loggingType = loggingType if loggingType in allowedLoggers else 'warning'
        self.loggingType = loggingType

    def _timeout_handler(self, signum, frame):
        doLogger = getattr(getLogger(), self.loggingType)
        doLogger(self.timeoutMessage)
        raise TimeoutError(self.timeoutMessage)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self._timeout_handler)  # Set handler for SIGALRM
        signal.alarm(self.seconds)  # start countdown for SIGALRM to be raised

    def __exit__(self, exc_type, exc_val, exc_tb):
        signal.alarm(0)  # Cancel SIGALRM if it's scheduled
        return exc_type is TimeoutError  # Suppress TimeoutError


CURRENT_ATTRIBUTE_NAME = '_currentAttributeName'


class _ObjectStore(object):
    """A class to store a current setting"""

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
    if getattr(result, CURRENT_ATTRIBUTE_NAME, None) is not None:
        try:
            storeObj = _ObjectStore(result)
            thisAddUndoItem(undo=storeObj._storeCurrentSelectedObject,
                            redo=storeObj._restoreCurrentSelectedObject,
                            )
        except Exception:
            getLogger().debug(_styleRed(f'Current does not have attribute {result.__class__.__name__}'))


def _storeDeleteObjectCurrent(self, thisAddUndoItem):
    if hasattr(self, CURRENT_ATTRIBUTE_NAME):
        with suppress(Exception):
            storeObj = _ObjectStore(self)

            # store the current state - check because item already removed from current?
            storeObj._storeCurrentSelectedObject()

            # add it to the stack
            thisAddUndoItem(undo=storeObj._restoreCurrentSelectedObject,
                            redo=storeObj._storeCurrentSelectedObject
                            )


def newObject(klass):
    """A decorator wrap a newObject method's of the various classes in an undo block and calls
    result._finalise('create').
    Checks for appropriate klass; passes on None if that is the result of the decorated function call
    """
    from ccpn.core.lib import Undo

    @decorator.decorator
    def theDecorator(*args, **kwds):
        func = args[0]
        args = args[1:]  # Optional 'self' is now args[0]

        application = getApplication()  # pass it in to reduce overhead


        # sidebar needs to be silent;
        # make an undo black with sidebar suspended while creating
        # the new objects
        with undoBlockWithSideBar():
            # notification done after the creation
            with notificationBlanking():
                # undo/redo added explicitly
                with undoStackBlocking(application=application, debugText=f'newObject: {func}') as addUndoItem:

                    result = func(*args, **kwds)
                    if result is None:
                        return None

                    if not isinstance(result, klass):
                        raise RuntimeError(f'Expected an object of class {klass}, obtained {result.__class__}')

                    # set the _objectVersion
                    result._objectVersion = application.applicationVersion

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

                    if application.project._undo.storageBlockingLevel < 1:
                        # only add current if required
                        _storeNewObjectCurrent(result, addUndoItem)

            result._finaliseAction('create')

        return result

    return theDecorator


# TODO-DEVEL: combine into one with newObject
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

        # sidebar needs to be silent;
        # make an undo black with sidebar suspended while creating
        # the new objects
        with undoBlockWithSideBar():
            # notification done after the creation
            with notificationBlanking():
                # undo/redo added explicitly
                with undoStackBlocking(application=application) as addUndoItem:
                    results = func(*args, **kwds)
                    if not results or results[0].__class__.__name__ != klasses[0]:
                        raise RuntimeError(f'No new objects were created')

                    for result in results:
                        if result.__class__.__name__ not in klasses:
                            raise RuntimeError(f'Expected an object in class types {klasses}, obtained {result.__class__}')

                        # set the _objectVersion
                        result._objectVersion = application.applicationVersion

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

                        if application.project._undo.storageBlockingLevel < 1:
                            # only add current if required
                            _storeNewObjectCurrent(result, addUndoItem)


            # handle notifying all objects in the list - e.g. sampleComponent also makes a substance
            for result in results:
                result._finaliseAction('create')

        # return the primary object
        return results[0] if results else None

    return theDecorator


def deleteObject():
    """A decorator to wrap delete(self) method of the V3 core classes
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

        with undoBlockWithoutSideBar():

            with undoStackBlocking(application=application) as addUndoItem:
                # moved above so that the current objects are preserved
                with notificationBlanking():
                    _storeDeleteObjectCurrent(self, addUndoItem)

                self._finaliseAction('delete')

                with notificationBlanking():
                    # retrieve list of created items from the api
                    apiObjectsCreated = self._getApiObjectTree()
                    addUndoItem(undo=BlankedPartial(self._wrappedData.root._unDelete,
                                                    topObjectsToCheck=(self._wrappedData.topObject,),
                                                    obj=self, trigger='create', preExecution=False,
                                                    objsToBeUnDeleted=apiObjectsCreated),
                                # use 'func' so that it calls the wrapped method (was previously 'self.delete')
                                # - shouldn't be any arguments
                                redo=BlankedPartial(partial(func, self),
                                                    obj=self, trigger='delete', preExecution=True)
                                )

                    # call the wrapped delete function (shouldn't be any arguments)
                    result = func(self)  # *args, **kwds)

        return result

    return theDecorator


def deleteWrapperWithoutSideBar():
    """A decorator to wrap delete(self) method of the V3 core classes
    calls self._finalise('delete') prior to deletion
    """

    @decorator.decorator
    def theDecorator(*args, **kwds):
        func = args[0]
        args = args[1:]  # Optional 'self' is now args[0]
        self = args[0]
        application = getApplication()  # pass it in to reduce overhead

        self._finaliseAction('delete')

        with notificationBlanking():
            with undoBlockWithoutSideBar():
                # must be done like this as the undo functions are not known
                with undoStackBlocking(application=application) as addUndoItem:
                    # incorporate the change notifier to simulate the decorator
                    addUndoItem(undo=partial(self._finaliseAction, 'create'),
                                redo=partial(self._finaliseAction, 'delete')
                                )
                    addUndoItem(undo=application.project._decreaseNotificationBlanking,
                                redo=application.project._increaseNotificationBlanking)

                # call the wrapped function
                result = func(*args, **kwds)

                with undoStackBlocking(application=application) as addUndoItem:
                    # incorporate the change notifier to simulate the decorator
                    addUndoItem(undo=application.project._increaseNotificationBlanking,
                                redo=application.project._decreaseNotificationBlanking)

        return result

    return theDecorator


def newV3Object():
    """ A decorator to wrap the creation of pure v3 method of the V3 core classes
    calls self._finalise('create') post-creation
    """

    @decorator.decorator
    def theDecorator(*args, **kwds):
        func = args[0]
        args = args[1:]  # Optional 'self' is now args[0]
        # self = args[0]
        application = getApplication()  # pass it in to reduce overhead

        with notificationBlanking():
            with undoBlockWithoutSideBar():
                # must be done like this as the undo functions are not known
                with undoStackBlocking(application=application) as addUndoItem:
                    # incorporate the change notifier to simulate the decorator
                    addUndoItem(undo=application.project._decreaseNotificationBlanking,
                                redo=application.project._increaseNotificationBlanking)

                # call the wrapped function
                result = func(*args, **kwds)
                # application.project._finalisePid2Obj(result, 'create')

                with undoStackBlocking(application=application) as addUndoItem:
                    # incorporate the change notifier to simulate the decorator
                    # addUndoItem(undo=partial(application.project._finalisePid2Obj, result, 'delete'),
                    #             redo=partial(application.project._finalisePid2Obj, result, 'create'))
                    addUndoItem(undo=application.project._increaseNotificationBlanking,
                                redo=application.project._decreaseNotificationBlanking)
                    addUndoItem(undo=partial(result._finaliseAction, 'delete'),
                                redo=partial(result._finaliseAction, 'create'))

                    # set the _objectVersion
                    result._objectVersion = application.applicationVersion

        result._finaliseAction('create')

        return result

    return theDecorator


def deleteV3Object():
    """ A decorator to wrap the delete(self) method of the V3 core classes
    calls self._finalise('delete') prior to deletion
    """

    @decorator.decorator
    def theDecorator(*args, **kwds):
        func = args[0]
        args = args[1:]  # Optional 'self' is now args[0]
        self = args[0]
        application = getApplication()  # pass it in to reduce overhead

        self._finaliseAction('delete')

        with notificationBlanking():
            with undoBlockWithoutSideBar():
                # must be done like this as the undo functions are not known
                with undoStackBlocking(application=application) as addUndoItem:
                    # incorporate the change notifier to simulate the decorator
                    addUndoItem(undo=partial(self._finaliseAction, 'create'),
                                redo=partial(self._finaliseAction, 'delete'))
                    addUndoItem(undo=application.project._decreaseNotificationBlanking,
                                redo=application.project._increaseNotificationBlanking)
                    # addUndoItem(undo=partial(application.project._finalisePid2Obj, self, 'create'),
                    #             redo=partial(application.project._finalisePid2Obj, self, 'delete'))

                # application.project._finalisePid2Obj(self, 'delete')
                # call the wrapped function
                result = func(*args, **kwds)

                with undoStackBlocking(application=application) as addUndoItem:
                    # incorporate the change notifier to simulate the decorator
                    addUndoItem(undo=application.project._increaseNotificationBlanking,
                                redo=application.project._decreaseNotificationBlanking)

        return result

    return theDecorator


def renameObject(blockSidebar=False):
    """ A decorator to wrap rename(self) method of the V3 core classes
    calls self._finaliseAction('rename') after the rename

    EJB 20191023: modified original contextManager to be decorator to match new/delete
    """

    @decorator.decorator
    def theDecorator(*args, **kwds):
        func = args[0]
        args = args[1:]  # Optional 'self' is now args[0]
        self = args[0]
        application = getApplication()  # pass it in to reduce overhead

        if blockSidebar:
            # currently required for nmrChain and chain as these rename children in the sidebar
            with undoBlockWithoutSideBar(application=application):
                return _renameInner(application, args, func, kwds, self)
        else:
            return _renameInner(application, args, func, kwds, self)

    def _renameInner(application, args, func, kwds, self) -> bool:
        """Add items to the undo stack and fire _finaliseAction 'rename'
        """
        with notificationBlanking():
            with undoStackBlocking(application=application) as addUndoItem:
                # call the wrapped rename function
                result = func(*args, **kwds)

                if result is None:
                    return False

                if isinstance(result, tuple) and len(result) == 2:
                    oldName, newName = result
                else:
                    raise RuntimeError(f'Rename function should return (oldName, newName) tuple; got {result}')

                addUndoItem(undo=partial(func, self, oldName),
                            redo=partial(func, self, newName)
                            )

        # trigger RENAME notifier on project, self and the whole tree down from self
        for obj in [self.project, self] + self._getAllDecendants():
            obj._finaliseAction('rename')

        return True

    return theDecorator


@contextmanager
def renameObjectContextManager(self):
    """ A decorator to wrap rename(self) method of the V3 core classes
    calls self._finaliseAction('rename', 'change') after the rename
    """
    # get the current application
    application = getApplication()

    with notificationBlanking():
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


@contextmanager
def progressHandler(parent=None, *, title: str = 'Progress',
                    text: str = 'Busy...', cancelButtonText: str = 'Cancel',
                    minimum: int = 0, maximum: int = 100, steps: int = 100,
                    delay: int = 1000, closeDelay: int = 250,
                    hideBar: bool = False, hideCancelButton: bool = False,
                    raiseErrors: bool = True):
    """A context manager to wrap a method in a progress dialog defined by the current gui state.
    """
    from ccpn.framework.Application import getApplication

    application = getApplication()
    try:
        handler = application.ui.getProgressHandler()
        # get the dialog handler from the gui state - use subclass
        progress = handler(parent,
                           title=title, text=text, cancelButtonText=cancelButtonText,
                           minimum=minimum, maximum=maximum, steps=steps,
                           delay=delay, closeDelay=closeDelay,
                           hideBar=hideBar, hideCancelButton=hideCancelButton,
                           )
        # need this to force the gui to catch up and display the busy dialog
        QtWidgets.QApplication.processEvents()
    except Exception as es:
        raise RuntimeError('progressHandler: Error initialising') from es
    try:
        # transfer control to the calling function
        yield progress
    except StopIteration:
        # handle pressing the cancel button, or calling progress.cancel()
        getLogger().debug('progressHandler: cancelled')
    except Exception as es:
        # handle other errors
        getLogger().debug(_styleRed(f'progressHandler: {es}'))
        progress.error = es
        if raiseErrors:
            raise es
    else:
        # set counter to 100%
        progress.finalise()
    finally:
        # set closing conditions here, or call progress.close()
        progress.waitForEvents()


@contextmanager
def busyHandler(parent=None, *, title: str = 'Busy',
                text: str = 'Busy...', cancelButtonText: str = 'Cancel',
                minimum: int = 0, maximum: int = 100, steps: int = 100,
                delay: int = 500, closeDelay: int = 250,
                hideBar: bool = True, hideCancelButton: bool = True,
                raiseErrors: bool = True):
    """A context manager to wrap a method in a busy dialog defined by the current gui state.
    """
    from ccpn.ui.gui.widgets.ProgressWidget import BusyDialog

    try:
        # get the dialog handler from the gui state - use subclass
        progress = BusyDialog(parent,
                              title=title, text=text, cancelButtonText=cancelButtonText,
                              minimum=minimum, maximum=maximum, steps=steps,
                              delay=delay, closeDelay=closeDelay,
                              hideBar=hideBar, hideCancelButton=hideCancelButton,
                              )
        # need this to force the gui to catch up and display the busy dialog
        QtWidgets.QApplication.processEvents()
    except Exception as es:
        raise RuntimeError('busyHandler: Error initialising') from es
    try:
        # transfer control to the calling function
        yield progress
    except StopIteration:
        # handle pressing the cancel button, or calling progress.cancel()
        getLogger().debug('busyHandler: cancelled')
    except Exception as es:
        # handle other errors
        getLogger().debug(_styleRed(f'busyHandler: {es}'))
        progress.error = es
        if raiseErrors:
            raise es
    else:
        # set counter to 100%
        progress.finalise()
    finally:
        # set closing conditions here, or call progress.close()
        progress.waitForEvents()


class BlankedPartial(object):
    """Wrapper (like partial) to call func(**kwds) with blanking
    optionally trigger the notification of obj, either pre- or post- execution.
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
            if isinstance(self._trigger, (list, tuple)):
                self._obj._finaliseAction(self._trigger[0], **self._trigger[1])
            else:
                self._obj._finaliseAction(self._trigger)

        with notificationBlanking():
            self._func(*self._args, **self._kwds)

        if self._postExecution:
            # call the notification
            if isinstance(self._trigger, (list, tuple)):
                self._obj._finaliseAction(self._trigger[0], **self._trigger[1])
            else:
                self._obj._finaliseAction(self._trigger)

    def __str__(self):

        _func = self._func.func if isinstance(self._func, partial) else self._func
        _func = str(_func)
        for _text in ["<ccpn.core.lib.ContextManager",
                      "<bound method ",
                      "<function "
                     ]:
            if _func.startswith(_text):
                _func = _func[len(_text):]

        return f'{_func}, obj={self._obj}'


def _equal(a, b, **_):
    """
    Checks if two objects are equal, handling Python primitives and NumPy/Pandas arrays.
    There is a more comprehension deep_equal in CHeckEqual.
    """
    # first check that match
    if type(a) != type(b):
        return False
    elif isinstance(a, (np.ndarray, np.generic)):
        # For arrays, use np.array_equal to check for equivalence
        return np.array_equal(a, b)
    elif isinstance(a, (pd.Series, pd.DataFrame)):
        return a.equals(b)
    else:
        # For standard Python objects, the simple '==' works
        return a == b


# The cache is now conditional, so it's defined here
_cached_values = weakref.WeakKeyDictionary()

def ccpNmrV3CoreSetter(doNotify=True, noUndo=False, useCache=False, **actionKwds):
    """
    A decorator to wrap property setters, with an optional cache to check
    if the value has changed. An undo block wraps the setter.
    A 'change' notification is triggered if doNotify is True.
    """

    @decorator.decorator
    def theDecorator(func, self, new_value):
        # --- Conditional logic based on the 'useCache' flag ---
        if useCache:
            old_value = _cached_values.get(self)
        else:
            # Original, non-cached approach: get the value directly
            # Note: This will re-trigger the getter method if it exists
            old_value = getattr(self, func.__name__)
        # NOTE:ED - need to move the check here, but isn't working correctly :|
        # If the value is the same, we can skip the process
        # if _equal(new_value, old_value):
        #     return
        # --- End of conditional logic ---

        application = getApplication()  # pass it in to reduce overhead
        with notificationBlanking(application=application):
            with undoStackBlocking(application=application) as addUndoItem:
                try:
                    # Call the original setter method to update the attribute
                    result = func(self, new_value)
                except Exception as es:
                    getLogger().debug(_styleRed(f'ccpNmrV3CoreSetter: {es}'))
                    raise
                finally:
                    # Only add an undo item if the old value was different.
                    if not noUndo and not _equal(new_value, old_value):
                        addUndoItem(undo=BlankedPartial(func, self, ('change', actionKwds), False, self, old_value),
                                    redo=BlankedPartial(func, self, ('change', actionKwds), False, self, new_value))
                        # If caching is enabled, update the cache with the new value
                        if useCache:
                            _cached_values[self] = new_value

        if doNotify:
            self._finaliseAction(Notifier.CHANGE, **actionKwds)

        return result

    return theDecorator


def ccpNmrV3CoreUndoBlock(action='change', **actionKwds):
    """A decorator wrap the property setters method in an undo block and triggering the
    action notification; default is 'change' but occasionally may use 'rename'
    """

    @decorator.decorator
    def theDecorator(*args, **kwds):
        func = args[0]
        args = args[1:]  # Optional 'self' is now args[0]
        self = args[0]

        application = getApplication()  # pass it in to reduce overhead

        with notificationBlanking():
            with undoBlock(debugText=f'ccpNmrV3CoreUndoBlock: {func}'):
                # must be done like this as the undo functions are not known
                with undoStackBlocking(application=application, debugText=f'-> ccpNmrV3CoreUndoBlock, before try') as addUndoItem:
                    # incorporate the change notifier to simulate the decorator
                    addUndoItem(undo=partial(self._finaliseAction, action, **actionKwds))
                    addUndoItem(undo=application.project._decreaseNotificationBlanking,
                                redo=application.project._increaseNotificationBlanking)

                try:
                    # call the wrapped function
                    result = func(*args, **kwds)
                except Exception as es:
                    getLogger().debug(_styleRed(f'ccpNmrV3CoreUndoBlock: {es}'))
                    raise

                finally:
                    with undoStackBlocking(application=application, debugText=f'-> ccpNmrV3CoreUndoBlock, finally') as addUndoItem:
                        # incorporate the change notifier to simulate the decorator
                        addUndoItem(undo=application.project._increaseNotificationBlanking,
                                    redo=application.project._decreaseNotificationBlanking)
                        addUndoItem(redo=partial(self._finaliseAction, action, **actionKwds))

        self._finaliseAction(action, **actionKwds)

        return result

    return theDecorator


nullContext = nullcontext  # an empty context manager


def ccpNmrV3CoreSimple():
    """A decorator wrap the property setters method in an undo block
    Notifiers are not explicitly triggered
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

                try:
                    # call the wrapped function
                    result = func(*args, **kwds)
                except Exception as es:
                    getLogger().debug(_styleRed(f'ccpNmrV3CoreSimple: {es}'))
                    raise

                finally:
                    addUndoItem(undo=partial(func, self, oldValue),
                                redo=partial(func, self, args[1])
                                )

        return result

    return theDecorator


def checkDeleted():
    """A decorator to wrap the property getter/setter methods with a check on deletion flag
    """

    @decorator.decorator
    def theDecorator(*args, **kwds):
        func = args[0]
        args = args[1:]  # Optional 'self' is now args[0]
        self = args[0]  # this is the object

        if self.isDeleted:
            getLogger().debug(f'object {self} is deleted {func} {args} {kwds}')
            return
            # raise RuntimeError(f'object {self} is deleted {func} {args} {kwds}')
        return func(*args, **kwds)

    return theDecorator


DEFINEDPARAMETERS = ('option', 'attr', 'parameter', 'dim')


def queueStateChange(verify, last=True):
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
        verify(self, func.__name__, result, last, *pars)

        return result

    return theDecorator


class PaintContext:
    """context manager for closing painters correctly"""

    def __init__(self, painter):
        self._painter = painter

    def __enter__(self):
        return self._painter

    def __exit__(self, *args):
        self._painter.end()
        return True


class AntiAliasedPaintContext(PaintContext):

    def __init__(self, painter):
        super(AntiAliasedPaintContext, self).__init__(painter)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.HighQualityAntialiasing)


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


def main():
    from ccpn.ui.gui.widgets.Application import newTestApplication

    # import at top
    # from ccpn.framework.Application import getApplication

    def _undoTest(value):
        pass

    app = newTestApplication()
    application = getApplication()

    with undoStackBlocking() as addUndoItem:
        addUndoItem(undo=partial(_undoTest, 1),
                    redo=partial(_undoTest, 2))
        addUndoItem(undo=partial(_undoTest, 3),
                    redo=partial(_undoTest, 4))
        addUndoItem(undo=partial(_undoTest, 5),
                    redo=partial(_undoTest, 6))

    print(f'>>> {application.project._undo.undoList}')
    print(f'>>> {application.project._undo}')
    for value in application.project._undo:
        print(f'>>>   {value}')
    with undoStackRevert() as errorState:
        with undoStackBlocking() as addUndoItem:
            addUndoItem(undo=partial(_undoTest, 7),
                        redo=partial(_undoTest, 8))
            addUndoItem(undo=partial(_undoTest, 9),
                        redo=partial(_undoTest, 10))

        errorState(True)

    print(f'>>> {application.project._undo.undoList}')
    print(f'>>> {application.project._undo}')
    for value in application.project._undo:
        print(f'>>>   {value}')

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    deep_equal = _equal
    print("### Deep Equal Examples ###")

    # --- primitives ---
    print("int vs int:", deep_equal(5, 5))
    print("int vs float (strict=False):", deep_equal(5, 5.0))
    print("int vs float (strict=True):", deep_equal(5, 5.0, strict_type=True))
    print("nan vs nan (equal_nan=True):", deep_equal(float("nan"), float("nan"), equal_nan=True))
    print("nan vs nan (equal_nan=False):", deep_equal(float("nan"), float("nan"), equal_nan=False))

    # --- numpy ---
    arr1 = np.array([1.0, 2.0, np.nan])
    arr2 = np.array([1.0, 2.0, np.nan])
    print("NumPy arrays with NaN:", deep_equal(arr1, arr2))
    print("NumPy arrays tolerant compare:", deep_equal([1.0, 2.0000001], [1.0, 2.0], rtol=1e-6))

    # numpy scalar vs Python scalar
    print("np.int64 vs int:", deep_equal(np.int64(42), 42))

    # --- pandas ---
    s1 = pd.Series([1, 2, np.nan], name="x")
    s2 = pd.Series([1, 2, np.nan], name="x")
    s3 = pd.Series([1, 2, np.nan], name="y")
    print("Series equal:", deep_equal(s1, s2))
    print("Series with different names (check_names=True):", deep_equal(s1, s3))
    print("Series with different names (check_names=False):", deep_equal(s1, s3, pandas_check_names=False))

    df1 = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    df2 = pd.DataFrame({"b": [3, 4], "a": [1, 2]})
    print("DataFrames column order ignored:", deep_equal(df1, df2, pandas_check_like=True))
    print("DataFrames column order required:", deep_equal(df1, df2, pandas_check_like=False))

    print("Series to DataFame equal:", deep_equal(s1, df1))

    # --- containers ---
    print("List vs tuple:", deep_equal([1, 2], (1, 2)))
    print("List vs tuple strict:", deep_equal([1, 2], (1, 2), strict_type=True))
    print("Unordered sequence compare:", deep_equal([1, 2, 3], [3, 2, 1], sequence_unordered=True))

    print("Dicts equal:", deep_equal({"a": 1, "b": 2}, {"b": 2, "a": 1}))
    print("Sets equal:", deep_equal({1, 2, 3}, {3, 2, 1}))


    from dataclasses import dataclass
    from datetime import datetime, timedelta, timezone

    # --- dataclass ---
    @dataclass
    class Point:
        x: int
        y: int


    p1 = Point(1, 2)
    p2 = Point(1, 2)
    p3 = Point(2, 3)
    print("Dataclass equal:", deep_equal(p1, p2))
    print("Dataclass not equal:", deep_equal(p1, p3))

    # --- datetime ---
    dt1 = datetime(2020, 1, 1, 12, tzinfo=timezone.utc)
    dt2 = datetime(2020, 1, 1, 7, tzinfo=timezone(timedelta(hours=-5)))
    print("Timezone-aware datetimes (normalize_tz=True):", deep_equal(dt1, dt2))
    print("Timezone-aware datetimes (normalize_tz=False):", deep_equal(dt1, dt2, normalize_tz=False))

    # --- tricky ---
    print("None vs NaN (none_equals_nan=True):", deep_equal(None, float("nan")))
    print("None vs NaN (none_equals_nan=False):", deep_equal(None, float("nan"), none_equals_nan=False))


if __name__ == '__main__':
    main()
