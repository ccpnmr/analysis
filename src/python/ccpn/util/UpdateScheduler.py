"""
Module Documentation here
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
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-04-13 19:00:26 +0100 (Wed, April 13, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-04-07 15:46:38 +0100 (Thu, April 07, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import time
from PyQt5.QtCore import QTimer
from ccpn.util.Logging import getLogger


class UpdateScheduler:
    """Class for deferred processing of events when the Qt GUI thread is idle
    """

    def __init__(self, project, updaterCallback, name='unknown', startOnAdd=False, log=False, completeCallback=None):
        """Initialise a new scheduler

        :param project: project container - used to reference top-level scheduler suspension
        :param updaterCallback: callback to execute
        :param name: optional str name for the scheduler
        :param startOnAdd: True|False - if True, timer starts on creation, defaults to False
        :param log: True|False - log timer events, defaults to False
        :param completeCallback: callback to execute at end of timer event
        """
        # check the callbacks are valid
        if not callable(updaterCallback):
            raise ValueError(f'updaterCallback {updaterCallback} must be callable')
        if completeCallback is not None and not callable(completeCallback):
            raise ValueError(f'completeCallback {completeCallback} must be callable or None')
        if not isinstance(name, str):
            raise ValueError(f'name {name} must be of type str')
        if not isinstance(startOnAdd, bool):
            raise ValueError(f'startOnAdd {startOnAdd} must be True|False')
        if not isinstance(log, bool):
            raise ValueError(f'log {log} must be True|False')

        self._project = project
        self._name = name
        self._startOnAdd = startOnAdd
        self._log = log

        self._updaterCallback = updaterCallback
        self._completeCallback = completeCallback

        # set up the local variables
        self._timer = None
        self._startTime = None
        self._busy = False
        self._restart = False

        # not sure whether this is needed - to fire a single update even if suspended
        self._overrideSuspension = False

        # initialise the timer
        self._initialiseTimer()

        if startOnAdd:
            # start if required
            self.start()

    @property
    def isActive(self):
        if self._timer:
            return self._timer.isActive()

        return False

    @property
    def isBusy(self):
        return self._busy

    def signalRestart(self):
        """Signal the timer to restart when it has finished processing
        """
        if self._busy:
            self._restart = True

    def signalOverride(self):
        """Signal the update to execute a single event overriding the _progressSuspension flag
        """
        # not tested properly yet
        self._overrideSuspension = True

    def _applyUpdates(self):
        """Call the user callbacks when the timer has expired
        """
        try:
            self._busy = True

            # Check busy-state of app at top-level
            #   defer processing again until not busy
            if not self._project._progressSuspension or self._overrideSuspension:
                # process the callbacks
                self._logUpdateStart()

                # apply the updates
                self._updaterCallback()
                if self._completeCallback:
                    self._completeCallback()

                self._logUpdateEnd()

                # flag to force an update
                self._overrideSuspension = False

            else:
                self._restart = True

        except Exception:
            self._logException()
            raise

        finally:
            # release busy flag and restart if required
            if self._restart:
                self._restart = False
                self.start()
            self._busy = False

    def _initialiseTimer(self):
        """Initialise the timer
        """
        if self._timer is None:
            self._timer = QTimer()
            self._timer.timeout.connect(self._applyUpdates)
            self._timer.setSingleShot(True)

    def start(self, value=0):
        """Start the timer
        """
        self._initialiseTimer()

        self._restart = False
        self._overrideSuspension = False
        self._timer.start(value)

    def stop(self, cleanup=False):
        """Stop the timer
        """
        if self._timer:
            self._timer.stop()

            if cleanup:
                self._cleanupTimer()

    def _cleanupTimer(self):
        """Clean-up the timer ready for a restart
        """
        self._timer.stop()
        self._timer.timeout.disconnect(self._applyUpdates)
        self._timer.deleteLater()
        self._timer = None

    def _logException(self):
        """Log an excepion if an error occurs
        """
        logger = getLogger()
        msg = f'Exception in apply update for updater {repr(self._name)} with target {repr(self._applyUpdates)}'
        logger.exception(msg)

    def _logUpdateStart(self):
        """Log the start of the callback sequence
        """
        if self._log:
            self._startTime = time.time()
            logger = getLogger()
            msg = f'start apply update {repr(self._name)} with target {repr(self._applyUpdates)}'
            logger.info(msg)

    def _logUpdateEnd(self):
        """Log the end of the callback sequence
        """
        if self._log:
            logger = getLogger()
            updateTime = (time.time() - self._startTime) / 1000
            msg = f'end apply update {repr(self._name)} with target {repr(self._applyUpdates)} in time {updateTime}s'
            logger.info(msg)
