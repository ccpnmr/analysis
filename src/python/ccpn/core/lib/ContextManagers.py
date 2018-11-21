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
from collections import OrderedDict

from ccpn.core import _importOrder
# from ccpn.core.lib import CcpnSorting
from ccpn.core.lib import Util as coreUtil
from ccpn.util import Common as commonUtil
from ccpn.core.lib import Pid
from ccpnmodel.ccpncore.api.memops import Implementation as ApiImplementation
from ccpn.util.Logging import getLogger


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
def undoBlock(obj):
    # usually called from application
    undo = obj.project._undo
    if undo is not None:  # ejb - changed from if undo:
        undo.newWaypoint()  # DO NOT CHANGE

        if not obj.project._blockSideBar and not undo._blocked:
            if undo._waypointBlockingLevel < 1 and obj.ui and obj.ui.mainWindow:
                obj._storedState = obj.ui.mainWindow.sideBar._saveExpandedState()

        undo.increaseWaypointBlocking()

    if not obj._echoBlocking:
        obj.project.suspendNotification()

    obj._echoBlocking += 1

    getLogger().debug('_enterUndoBlock')

    try:
        # transfer control to the calling function
        yield

    finally:
        undo = obj.project._undo

        if obj._echoBlocking > 0:
            obj._echoBlocking -= 1

        if not obj._echoBlocking:
            obj.project.resumeNotification()

        if undo is not None:
            undo.decreaseWaypointBlocking()

            if not obj.project._blockSideBar and not undo._blocked:
                if undo._waypointBlockingLevel < 1 and obj.ui and obj.ui.mainWindow:
                    obj.ui.mainWindow.sideBar._restoreExpandedState(obj._storedState)

        getLogger().debug2('_exitUndoBlock: echoBlocking=%s' % obj._echoBlocking)


@contextmanager
def blankNotification(obj, message, *args, **kwargs):
    print('Starting', message)
    try:
        yield
    finally:
        print('Done', message)

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
