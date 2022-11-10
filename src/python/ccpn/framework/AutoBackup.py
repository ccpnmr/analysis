"""
This file contains AutoBackup class
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-11-10 16:05:24 +0000 (Thu, November 10, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2022-02-05 10:28:48 +0000 (Saturday, February 5, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from threading import Thread
from time import time, sleep

from PyQt5 import QtCore, QtWidgets

from ccpn.util.Logging import getLogger
from ccpn.framework import Application


SECONDS_IN_MINUTE = 60


class AutoBackup(Thread):
    class MainThreadAccess(QtCore.QObject):

        _runOnMainThread = QtCore.pyqtSignal(object)

        def __init__(self):
            super().__init__()
            self._runOnMainThread.connect(QtWidgets.QApplication.instance().runFunctionOnThreadAtIdle)

        def emit(self, func):
            self._runOnMainThread.emit(func)


    def __init__(self, backupFrequencyQueue, backupFunction, sleepTime=1):
        super().__init__()

        # this is a hack as the loggers are a mess
        if Application.getApplication().args.debug3_backup_thread:
            self._logger = getLogger().debug3
        else:
            self._logger = lambda x: ...

        self._mainThreadAccess = AutoBackup.MainThreadAccess()
        self._sleepTime = sleepTime
        self._backupFrequencyQueue = backupFrequencyQueue
        self._backupFunction = backupFunction
        self._startTime = None
        self._logger(f'backup thread created at time stamp {time()}')

    def run(self):
        self._startTime = time()
        self._logger(f'backup thread started with start time {self._startTime} and with sleep time {self._sleepTime}s')
        waitTime = None
        while True:

            if not self._backupFrequencyQueue.empty():

                backupFrequency = None
                while not self._backupFrequencyQueue.empty():
                    backupFrequency = self._backupFrequencyQueue.get()

                if isinstance(backupFrequency, (int, float)):
                    backupFrequency *= SECONDS_IN_MINUTE

                waitTime = backupFrequency

                if waitTime is None:
                    self._logger(f'backup thread wait time is {waitTime} backup is disabled')
                else:
                    self._logger(f'backup thread wait time set to {waitTime}s')

            if waitTime is None:

                self._logger(f'backup thread wait time is {waitTime} backup is disabled')
                sleep(self._sleepTime)

            elif waitTime == 'kill':

                self._logger('backup thread received message: kill, exiting...')
                return

            elif (time() - self._startTime) < waitTime:

                current_seconds = time() - self._startTime
                remaining_seconds = waitTime - current_seconds
                self._logger(f'backup thread time stamp is {time()}, time count is {current_seconds}s backup will trigger in {remaining_seconds}s')
                sleep(self._sleepTime)

            else:

                self._logger(f'backup thread emit backup function {self._backupFunction}')
                self._mainThreadAccess.emit(self._backupFunction)
                self._startTime = time()
