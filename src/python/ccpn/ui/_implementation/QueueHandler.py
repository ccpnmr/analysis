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
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-10-12 15:27:09 +0100 (Wed, October 12, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-09-07 11:25:37 +0100 (Wed, September 07, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import typing
from PyQt5 import QtCore
from time import time_ns
from ccpn.core.lib.Notifiers import _removeDuplicatedNotifiers
from ccpn.util.Logging import getLogger
from ccpn.util.UpdateScheduler import UpdateScheduler
from ccpn.util.UpdateQueue import UpdateQueue
from ccpn.framework.Application import getApplication


_DEFAULT_QUEUE_LENGTH = 25


class QueueHandler():
    """Small class holding the queue-handler information
    """
    _parent = None
    application = None
    project = None
    name = 'unknown'
    _scheduler = None
    _queuePending = UpdateQueue()
    _queueActive = None
    _lock = QtCore.QMutex()
    _completeCallback = None
    _queueFullCallback = None

    # set the queue handling parameters
    log = False
    maximumQueueLength = _DEFAULT_QUEUE_LENGTH

    def __init__(self, parent,
                 # updaterCallback: callable,
                 completeCallback: typing.Optional[callable] = None,
                 queueFullCallback: typing.Optional[callable] = None,
                 name: str = 'unknown',
                 log: bool = False,
                 maximumQueueLength: typing.Optional[int] = _DEFAULT_QUEUE_LENGTH):
        """Initialise the scheduler for the queue-handler.

        :param parent: Class object container
        :param callback completeCallback: optional callback toexecute when queue becomes empty
        :param callback queueFullCallback: optional callback when queue exceeds maximumQueueLength
        :param str name: optional str name for the scheduler
        :param bool log: True|False - log timer events, defaults to False
        :param int maximumQueueLength: maximum number of events in the queue
        """
        # check parameters
        if not parent:
            raise TypeError(f'{self.__class__.__name__}.__init__: parent is not defined')

        # if not (callable(updaterCallback) or updaterCallback is None):
        #     raise TypeError(f'{self.__class__.__name__}.__init__: updaterCallback is not callable|None')
        if not (callable(completeCallback) or completeCallback is None):
            raise TypeError(f'{self.__class__.__name__}.__init__: completeCallback is not callable|None')
        if not (callable(queueFullCallback) or queueFullCallback is None):
            raise TypeError(f'{self.__class__.__name__}.__init__: queueFullCallback is not callable|None')

        if not (isinstance(name, str) and name):
            raise TypeError(f'{self.__class__.__name__}.__init__: name is not of type str')
        if not isinstance(log, bool):
            raise TypeError(f'{self.__class__.__name__}.__init__: log is not True/False')
        if not isinstance(maximumQueueLength, (int, type(None))):
            raise TypeError(f'{self.__class__.__name__}.__init__: maximumQueueLength must be of type int|None')

        # store parameters
        self._parent = parent

        if not (app := getApplication()):
            raise RuntimeError(f'{self.__class__.__name__}.__init__: application is not defined')
        self.application = app
        self.project = app._project

        self.name = name
        self.log = log
        self._completeCallback = completeCallback
        self._queueFullCallback = queueFullCallback

        _project = getApplication().project

        # initialise a scheduler
        self._scheduler = UpdateScheduler(self.project, self._queueProcess, name, log, completeCallback)

    def __enter__(self):
        # 'with' initialisation here?
        return self._queueActive, self._queuePending, self._lock

    def __exit__(self, exc_type, exc_val, exc_tb):
        #Exception handling here
        pass

    def _queueGeneralNotifier(self, func, data):
        """Add the notifier to the queue handler
        """
        self.queueAppend([func, data])

    def queueFull(self):
        """Method that is called when the queue is deemed to be too big.
        Apply overall operation instead of all individual notifiers.
        """
        if self._queueFullCallback:
            self._queueFullCallback()

    def _queueProcess(self):
        """Process current items in the queue
        """
        with QtCore.QMutexLocker(self._lock):
            # protect the queue switching
            self._queueActive = self._queuePending
            self._queuePending = UpdateQueue()

        _startTime = time_ns()
        _useQueueFull = (self.maximumQueueLength not in [0, None] and len(self._queueActive) > self.maximumQueueLength)
        if self.log:
            # log the queue-time if required
            getLogger().debug(f'_queueProcess  {self._parent}  len: {len(self._queueActive)}  useQueueFull: {_useQueueFull}')

        if _useQueueFull:
            # rebuild from scratch if the queue is too big
            if self.application and self.application._disableModuleException:
                self._queueActive = None
                self.queueFull()
            else:
                try:
                    self._queueActive = None
                    self.queueFull()
                except Exception as es:
                    getLogger().debug(f'Error in {self._parent.__class__.__name__} update queueFull: {es}')

        else:
            executeQueue = _removeDuplicatedNotifiers(self._queueActive)
            for itm in executeQueue:
                if self.application and self.application._disableModuleException:
                    func, data = itm
                    func(data)
                else:
                    # Exception is handled with debug statement
                    try:
                        func, data = itm
                        func(data)
                    except Exception as es:
                        getLogger().debug(f'Error in {self._parent.__class__.__name__} update - {es}')

        if self.log:
            getLogger().debug(f'_queueProcess  {self._parent}  elapsed time: {(time_ns() - _startTime) / 1e9}')

    def queueAppend(self, itm):
        """Append a new item to the queue
        """
        self._queuePending.put(itm)
        if not self._scheduler.isActive and not self._scheduler.isBusy:
            self._scheduler.start()

        elif self._scheduler.isBusy:
            # caught during the queue processing event, need to restart
            self._scheduler.signalRestart()
