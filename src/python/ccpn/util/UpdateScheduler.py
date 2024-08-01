"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Joanna Fox, Morgan Hayward, Victoria A Higman, Luca Mureddu",
               "Eliza Płoskoń, Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2024-03-21 16:29:25 +0000 (Thu, March 21, 2024) $"
__version__ = "$Revision: 3.2.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-04-07 15:46:38 +0100 (Thu, April 07, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import time
from enum import Enum
# from queue import Queue
# from threading import Thread
from PyQt5.QtCore import QTimer
from ccpn.util.Logging import getLogger


#=========================================================================================
# UpdateScheduler
#=========================================================================================

class UpdateScheduler:
    """Class for deferred processing of events when the Qt GUI thread is idle
    """

    def __init__(self, project, updaterCallback, name='unknown', log=False, completeCallback=None):
        """Initialise a new scheduler

        :param project: project container - used to reference top-level scheduler suspension
        :param updaterCallback: callback to execute
        :param name: optional str name for the scheduler
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
        if not isinstance(log, bool):
            raise ValueError(f'log {log} must be True|False')

        self._project = project
        self._name = name
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

        # use the global threadpool
        self.threadpool = QtCore.QThreadPool.globalInstance()
        getLogger().debug2(f'Multithreading with maximum {self.threadpool.maxThreadCount()} threads')

        # initialise the timer
        self._initialiseTimer()

    @property
    def isActive(self):
        return self._timer.isActive() if self._timer else False

    @property
    def isBusy(self):
        return self._busy

    @property
    def isIdle(self):
        return not (self.isActive or self._busy)

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

    def _applyUpdates(self):  # , progress_callback):
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

        # worker = Worker(self._applyUpdates)  # Any other args, kwargs are passed to the run function
        # self._restart = False
        # self._overrideSuspension = False
        #
        # # Execute
        # self.threadpool.start(worker)

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


#=========================================================================================
# UpdateThreadScheduler
#=========================================================================================


class _State(Enum):
    WAITING = 0
    RUNNING = 1
    FINISHED = 2


# class UpdateThreadScheduler:
#     """Class for deferred processing of events when the Qt GUI thread is idle
#     """
#
#     def __init__(self, updaterCallback, name='unknown', log=False, completeCallback=None):
#         """Initialise a new scheduler
#
#         :param updaterCallback: callback to execute
#         :param name: optional str name for the scheduler
#         :param log: True|False - log timer events, defaults to False
#         :param completeCallback: callback to execute at end of timer event
#         """
#         # check the callbacks are valid
#         if not callable(updaterCallback):
#             raise ValueError(f'updaterCallback {updaterCallback} must be callable')
#         if completeCallback is not None and not callable(completeCallback):
#             raise ValueError(f'completeCallback {completeCallback} must be callable or None')
#         if not isinstance(name, str):
#             raise ValueError(f'name {name} must be of type str')
#         if not isinstance(log, bool):
#             raise ValueError(f'log {log} must be True|False')
#
#         self._name = name
#         self._log = log
#
#         self._updaterCallback = updaterCallback
#         self._completeCallback = completeCallback
#
#         # set up the local variables
#         self._timer = None
#         self._startTime = None
#         self._busy = False
#         self._restart = False
#
#         # initialise the timer
#         self._initialiseTimer()
#
#     @property
#     def isActive(self):
#         if self._timer:
#             return self._timer.isActive()
#
#         return False
#
#     @property
#     def isBusy(self):
#         return self._busy
#
#     @property
#     def restart(self):
#         """Signal the timer to restart when it has finished processing
#         """
#         return self._restart
#
#     @restart.setter
#     def restart(self, value):
#         if not isinstance(value, bool):
#             raise ValueError(f'restart {value} must be True|False')
#
#         self._restart = value
#
#     def _applyUpdates(self):
#         """Call the user callbacks when the timer has expired
#         """
#         while True:
#             self._busy = False
#             self._timer.get(True)  # block until an item on the stack
#
#             try:
#                 self._busy = True
#
#                 # process the callbacks
#                 self._logUpdateStart()
#                 self._updaterCallback()
#                 if self._completeCallback:
#                     self._completeCallback()
#                 self._logUpdateEnd()
#
#             except Exception:
#                 self._logException()
#                 raise
#
#             finally:
#                 # release busy flag and restart if required
#                 if self._restart:
#                     self._restart = False
#                     self.start()
#                 self._busy = False
#
#     def _initialiseTimer(self):
#         """Initialise the timer
#         """
#         if self._timer is None:
#             self._timer = Queue(maxsize=1)
#             self._thread = Thread(target=self._applyUpdates)
#
#     def start(self, value=0):
#         """Start the timer
#         """
#         self._initialiseTimer()
#
#         self._restart = False
#         self._timer.start(value)
#
#     def stop(self, cleanup=False):
#         """Stop the timer
#         """
#         if self._timer:
#             self._timer.stop()
#
#             if cleanup:
#                 self._cleanupTimer()
#
#     def _cleanupTimer(self):
#         """Clean-up the timer ready for a restart
#         """
#         self._timer.stop()
#         self._timer.timeout.disconnect(self._applyUpdates)
#         self._timer.deleteLater()
#         self._timer = None
#
#     def _logException(self):
#         """Log an excepion if an error occurs
#         """
#         logger = getLogger()
#         msg = f'Exception in apply update for updater {repr(self._name)} with target {repr(self._applyUpdates)}'
#         logger.exception(msg)
#
#     def _logUpdateStart(self):
#         """Log the start of the callback sequence
#         """
#         if self._log:
#             self._startTime = time.time()
#             logger = getLogger()
#             msg = f'start apply update {repr(self._name)} with target {repr(self._applyUpdates)}'
#             logger.info(msg)
#
#     def _logUpdateEnd(self):
#         """Log the end of the callback sequence
#         """
#         if self._log:
#             logger = getLogger()
#             updateTime = (time.time() - self._startTime) / 1000
#             msg = f'end apply update {repr(self._name)} with target {repr(self._applyUpdates)} in time {updateTime}s'
#             logger.info(msg)


#=========================================================================================
# WorkerSignals
#=========================================================================================

import traceback, sys
import weakref
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import pyqtSignal as Signal, pyqtSlot as Slot
from ccpn.ui.gui.guiSettings import consoleStyle


_PROGRESS_CALLBACK = 'progress_callback'


class WorkerSignals(QtCore.QObject):
    """
    Defines the signals available from a running worker thread.
    QRunnable is not derived from QObject and does not support signals :|

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    progress
        int indicating % progress

    """
    # Need a wrapper to hold the signals as QRunnable is not a QObject as such
    started = Signal(object)
    finished = Signal(object)
    error = Signal(object, tuple)
    result = Signal(object, object)
    progress = Signal(object, int)

    def __init__(self, worker):
        super().__init__()
        # keep a link to the parent
        self._worker = weakref.ref(worker)


class Worker(QtCore.QRunnable):
    """
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    """

    def __init__(self, fn, *args, **kwargs):
        super().__init__()

        print(f'{consoleStyle.fg.green}NEW WORKER ({id(self)}){consoleStyle.reset}')
        # Store constructor arguments (re-used for processing)
        self._func = fn
        self._args = args
        self._kwargs = kwargs
        # QRunnable class does not support signals
        self._signals = WorkerSignals(self)

        # Add the callback to our kwargs
        self._kwargs[_PROGRESS_CALLBACK] = self._signals.progress

    @Slot()
    def run(self):
        """
        Initialise the runner function with passed args, kwargs.
        """

        # Retrieve args/kwargs here; and fire processing using them
        #   pass the worker-thread(self) as the first argument to all signals
        try:
            self._signals.started.emit(self)
            result = self._func(self, *self._args, **self._kwargs)
        except Exception:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self._signals.error.emit(self, (exctype, value, traceback.format_exc()))
        else:
            self._signals.result.emit(self, result)  # Return the result of the processing
        finally:
            self._signals.finished.emit(self)  # Done


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._setWidgets()

        self._counter = 0
        self._threadpool = QtCore.QThreadPool.globalInstance()
        print(f"Multithreading with maximum {self._threadpool.maxThreadCount():d} threads")

        # set timer to update the label-widget
        self._timer = QTimer()
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self.recurring_timer)
        self._timer.start()

        # create a timer to close the app if there are no threads in the thread-pool
        QTimer.singleShot(3000, self._kill)

        self.show()

    def _setWidgets(self):
        """Create the widgets in the popup.
        """
        layout = QtWidgets.QVBoxLayout()

        self._label = QtWidgets.QLabel("Start")
        btn = QtWidgets.QPushButton("DANGER!\nDon't press :)")
        btn.pressed.connect(self.oh_no)

        layout.addWidget(self._label)
        layout.addWidget(btn)

        widg = QtWidgets.QWidget()
        widg.setLayout(layout)

        self.setCentralWidget(widg)

    def _kill(self):
        if self._threadpool.activeThreadCount() == 0:
            # close the window, will exit exec_
            self.close()
        else:
            # test again when free
            QTimer.singleShot(0, self._kill)

    @staticmethod
    def progress_fn(thread, n):
        print(f"{consoleStyle.fg.darkyellow}{n:d}% done ({id(thread)}){consoleStyle.reset}")

    @staticmethod
    def execute_this_fn(thread, progress_callback):
        for n in range(5):
            time.sleep(1)
            progress_callback.emit(thread, int(n * 100 / 4))

        return "Done."

    @staticmethod
    def print_start(thread):
        print(f'{consoleStyle.fg.darkmagenta}started ({id(thread)}){consoleStyle.reset}')

    @staticmethod
    def print_output(thread, s):
        print(f'{consoleStyle.fg.darkblue}result ({id(thread)}) - {s}{consoleStyle.reset}')

    @staticmethod
    def thread_complete(thread):
        print(f"{consoleStyle.fg.blue}THREAD COMPLETE! ({id(thread)}){consoleStyle.reset}")

    def oh_no(self):
        # Pass the function to execute
        worker = Worker(self.execute_this_fn)  # Any other args, kwargs are passed to the run function
        worker._signals.started.connect(self.print_start)
        worker._signals.result.connect(self.print_output)
        worker._signals.finished.connect(self.thread_complete)
        worker._signals.progress.connect(self.progress_fn)

        # Execute
        self._threadpool.start(worker)


    def recurring_timer(self):
        self._counter += 1
        self._label.setText(f'Time:{self._counter}s'
                            f'Threads:{self._threadpool.activeThreadCount()}')


def main():
    app = QtWidgets.QApplication([])
    window = MainWindow()
    app.exec_()

    QtCore.QThreadPool.globalInstance().waitForDone()
    print(f'{consoleStyle.fg.red}KILLED :|{consoleStyle.reset}')


if __name__ == '__main__':
    main()
