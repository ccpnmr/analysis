"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-04-20 13:29:26 +0100 (Tue, April 20, 2021) $"
__version__ = "$Revision: 3.0.4 $"
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
import traceback
from contextlib import contextmanager
from collections.abc import Iterable
from functools import partial
from ccpn.core.lib import Util as coreUtil
from inspect import signature, Parameter
from ccpn.util.Logging import getLogger
from ccpn.framework.Application import getApplication


@contextmanager
def echoCommand(obj, funcName, *params, values=None, defaults=None,
                parName=None, propertySetter=False, **objectParameters):

    from ccpn.core.lib import Util as coreUtil

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
    """A try/except here because resume Notification MAY in exceptional circumstances
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
            traceback.print_exc()  # please give more info about the error!
        if application.hasGui and popupAsWarning:
            from ccpn.ui.gui.widgets import MessageDialog  # Local import: in case of no-gui, we never get here

            MessageDialog.showWarning('Warning', errorStringTemplate % str(es))
        if application._isInDebugMode:
            raise es


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
def apiNotificationBlanking(application=None):
    """
    Block api 'change' notifier, re-enable at the end of the function block.
    """

    # get the application
    if not application:
        application = getApplication()
    if application is None:
        raise RuntimeError('Error getting application')

    application.project._apiNotificationBlanking += 1
    try:
        # transfer control to the calling function
        yield

    except AttributeError as es:
        raise es

    finally:
        # clean up after blocking notifications
        application.project._apiNotificationBlanking -= 1

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
def inactivity(application=None):
    """
    Block all notifiers, apiNotifiers, undo and echo-ing
    re-enable at the end of the function block.
    """

    # get the application
    if not application:
        application = getApplication()
    if application is None:
        raise RuntimeError('Error getting application')

    application.project.blankNotification()
    application._increaseNotificationBlocking()
    application.project._apiNotificationBlanking += 1

    try:
        with undoStackBlocking(application=application):
            # transfer control to the calling function
            yield

    except AttributeError as es:
        raise es

    finally:
        # clean up after blocking notifications
        application.project.unblankNotification()
        application._decreaseNotificationBlocking()
        application.project._apiNotificationBlanking -= 1

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
    result._finalise('create').
    Checks for appropriate klass; passes on None if that is the result of the decorated function call
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
                if result is None:
                    return None

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

        # handle notifying all objects in the list - e.g. sampleComponent also makes a substance
        for result in results:
            result._finaliseAction('create')
        # return the primary object
        return results[0] if results else None

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

        # moved outside so that the current objects are preserved
        with notificationBlanking(application=application):
            with undoStackBlocking(application=application) as addUndoItem:
                _storeDeleteObjectCurrent(self, addUndoItem)

        self._finaliseAction('delete')

        with notificationBlanking(application=application):
            with undoStackBlocking(application=application) as addUndoItem:
                # _storeDeleteObjectCurrent(self, addUndoItem)

                # retrieve list of created items from the api
                apiObjectsCreated = self._getApiObjectTree()
                addUndoItem(undo=BlankedPartial(self._wrappedData.root._unDelete,
                                                topObjectsToCheck=(self._wrappedData.topObject,),
                                                obj=self, trigger='create', preExecution=False,
                                                objsToBeUnDeleted=apiObjectsCreated),
                            redo=BlankedPartial(partial(func, self),
                                                obj=self, trigger='delete', preExecution=True)
                            )

                # call the wrapped delete function
                result = func(*args, **kwds)

        return result

    return theDecorator


def deleteWrapperWithoutSideBar():
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

        with notificationBlanking(application=application):
            with undoBlockWithoutSideBar():
                # must be done like this as the undo functions are not known
                with undoStackBlocking(application=application) as addUndoItem:
                    # incorporate the change notifier to simulate the decorator
                    addUndoItem(redo=partial(self._finaliseAction, 'delete'),
                                undo=partial(self._finaliseAction, 'create'))
                    addUndoItem(undo=application.project.unblankNotification,
                                redo=application.project.blankNotification)

                # call the wrapped function
                result = func(*args, **kwds)

                with undoStackBlocking(application=application) as addUndoItem:
                    # incorporate the change notifier to simulate the decorator
                    addUndoItem(undo=application.project.blankNotification,
                                redo=application.project.unblankNotification)

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

                addUndoItem(undo=BlankedPartial(func, self, 'change', False, self, oldValue),
                            redo=BlankedPartial(func, self, 'change', False, self, args[1]))

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
                # must be done like this as the undo functions are not known
                with undoStackBlocking(application=application) as addUndoItem:
                    # incorporate the change notifier to simulate the decorator
                    addUndoItem(undo=partial(self._finaliseAction, 'change'))
                    addUndoItem(undo=application.project.unblankNotification,
                                redo=application.project.blankNotification)

                # call the wrapped function
                result = func(*args, **kwds)

                with undoStackBlocking(application=application) as addUndoItem:
                    # incorporate the change notifier to simulate the decorator
                    addUndoItem(undo=application.project.blankNotification,
                                redo=application.project.unblankNotification)
                    addUndoItem(redo=partial(self._finaliseAction, 'change'))

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

if __name__ == '__main__':
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
