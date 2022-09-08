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
__dateModified__ = "$dateModified: 2022-09-08 11:41:10 +0100 (Thu, September 08, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-04-07 15:46:38 +0100 (Thu, April 07, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets, QtCore
import sys
import random
import time
import unittest
import datetime
from functools import partial
from itertools import zip_longest
from ccpn.util.UpdateQueue import UpdateQueue
from ccpn.util.UpdateScheduler import UpdateScheduler


def main():
    """Queue and scheduler testing

    Simulates multiple threads posting events and a user button also posting events.
    Example process prints labels and simulates taking two seconds to finish.
    """


    class SchedulerApplication(QtWidgets.QApplication):
        """Simple application class with timer to process a queue when not busy
        """

        def __init__(self, applicationName='Testing', applicationVersion='0.0.1', organizationName='CCPN', organizationDomain='ccpn.ac.uk'):
            super().__init__([applicationName, ])

            self.setApplicationVersion(applicationVersion)
            self.setOrganizationName(organizationName)
            self.setOrganizationDomain(organizationDomain)

            self._queuePending = UpdateQueue()
            self._queueActive = None
            self._scheduler = UpdateScheduler(self, self._queueProcess, name='QueueTester', log=False, completeCallback=None)

            self._lock = QtCore.QMutex()
            self._counter = 0
            self._realEvents = []
            self._handledEvents = []
            self._progressSuspension = 0

        def start(self):
            print(f'   GO!                 {datetime.datetime.now()}')
            # start loading random stuff on the queue form two threads
            QtCore.QTimer.singleShot(0, partial(self._startStuff, 'thread1'))
            QtCore.QTimer.singleShot(0, partial(self._startStuff, 'thread2'))
            QtCore.QTimer.singleShot(0, partial(self._startStuff, 'thread3'))

            def _enableBlocking():
                self._progressSuspension = 1

            def _disableBlocking():
                self._progressSuspension = 0

            # block after 3 seconds - simulate overriding block
            QtCore.QTimer.singleShot(3000, _enableBlocking)
            # unblock after 7 seconds - simulate overriding block
            QtCore.QTimer.singleShot(7000, _disableBlocking)

            self.exec_()

        def _queueProcess(self):
            """Process current items in the queue
            """
            print(f'   processing                 {datetime.datetime.now()}')
            with QtCore.QMutexLocker(self._lock):
                # protect the queue switching
                self._queueActive = self._queuePending
                self._queuePending = UpdateQueue()

            print(f'   len {len(self._queueActive)}')
            vals = []
            for itm in self._queueActive.items():
                vals.append(itm)
            print(f'       {vals}')

            # example pause for 1 second whilst processing events (may happen in qui)
            for ii in range(20):
                self.processEvents()
                time.sleep(1 / 20)
            self._handledEvents.extend(vals)
            print(f'       {vals} - end sleep')

        def _queueAppend(self, itm):
            """Append a new item to the queue
            """
            self._queuePending.put(itm)
            if not self._scheduler.isActive and not self._scheduler.isBusy:
                print(f'   append & run                    {datetime.datetime.now()}      {itm}')
                self._scheduler.start()

            elif self._scheduler.isBusy:
                print(f'   append busy                     {datetime.datetime.now()}      {itm}')
                self._scheduler.signalRestart()

            elif self._scheduler.isActive:
                print(f'   append queued                   {datetime.datetime.now()}      {itm}')

        def _startStuff(self, name, count=0):
            """Randomly add items to the queue
            """
            val = f'{name} - {count}'

            # add to the deferred queue and store in the realEvents list which holds when the events were created
            self._queueAppend(val)
            self._realEvents.append(val)

            if count < 15:
                # create another random event
                QtCore.QTimer.singleShot(int(random.random() * 1000), partial(self._startStuff, name, count + 1))

        def _buttonClicked(self, *args):
            """Handle user clicking button
            """
            if self._counter < 30:
                # add to the deferred queue and store in the realEvents list which holds when the events were created
                self._queueAppend(self._counter)
                self._realEvents.append(self._counter)

                self._counter += 1


    app = SchedulerApplication()

    # make a mall window with a button that adds events to the queue
    window = QtWidgets.QMainWindow()
    fr1 = QtWidgets.QFrame()
    _layout = QtWidgets.QGridLayout()
    fr1.setLayout(_layout)
    window.setCentralWidget(fr1)
    _button = QtWidgets.QPushButton('HELP')
    _layout.addWidget(_button, 0, 0)
    _button.clicked.connect(app._buttonClicked)

    window.show()
    app.start()

    print('\n'.join([f'{qVal}    {rVal}' for qVal, rVal in zip_longest(app._handledEvents, app._realEvents)]))
    assert app._handledEvents == app._realEvents


class SchedulerTester(QtCore.QObject):
    """Queue and scheduler testing

    Simulates multiple threads posting events.
    Example process add labels to a list and simulates taking two seconds to finish.
    """

    def __init__(self, application):
        super().__init__()

        self._application = application
        self._queuePending = UpdateQueue()
        self._queueActive = None
        self._scheduler = UpdateScheduler(self, self._queueProcess, name='QueueTester',
                                          log=False, completeCallback=None)

        self._lock = QtCore.QMutex()
        self._counter = 0
        self._realEvents = []
        self._handledEvents = []
        self._progressSuspension = 0
        self._exitSignal = False

    def start(self):
        print(f'   GO!                 {datetime.datetime.now()}')

        # start loading random stuff on the queue form two threads
        QtCore.QTimer.singleShot(0, partial(self._startStuff, 'thread1'))
        QtCore.QTimer.singleShot(0, partial(self._startStuff, 'thread2'))
        QtCore.QTimer.singleShot(0, partial(self._startStuff, 'thread3'))

        def _enableBlocking():
            self._progressSuspension = 1

        def _disableBlocking():
            self._progressSuspension = 0

        # block after 3 seconds - simulate overriding block
        QtCore.QTimer.singleShot(3000, _enableBlocking)
        # unblock after 7 seconds - simulate overriding block
        QtCore.QTimer.singleShot(7000, _disableBlocking)

    def _queueProcess(self):
        """Process current items in the queue
        """
        print(f'   processing                 {datetime.datetime.now()}')
        with QtCore.QMutexLocker(self._lock):
            # protect the queue switching
            self._queueActive = self._queuePending
            self._queuePending = UpdateQueue()

        vals = []
        for itm in self._queueActive.items():
            vals.append(itm)

        # example pause for 1 second whilst processing events (may happen in qui)
        for ii in range(20):
            self._application.processEvents()
            time.sleep(1 / 20)

        # add the events to the processed queue
        self._handledEvents.extend(vals)
        print(f'       {vals} - end sleep')

    def _queueAppend(self, itm):
        """Append a new item to the queue
        """
        self._queuePending.put(itm)
        if not self._scheduler.isActive and not self._scheduler.isBusy:
            print(f'   append & run                    {datetime.datetime.now()}      {itm}')
            self._scheduler.start()

        elif self._scheduler.isBusy:
            print(f'   append busy                     {datetime.datetime.now()}      {itm}')
            self._scheduler.signalRestart()

        elif self._scheduler.isActive:
            print(f'   append queued                   {datetime.datetime.now()}      {itm}')

    def _startStuff(self, name, count=0):
        """Randomly add items to the queue
        """
        val = f'{name} - {count}'
        print(f'new event  -  _startStuff  {val}')

        # add to the deferred queue and store in the realEvents list which holds when the events were created
        self._queueAppend(val)
        self._realEvents.append(val)

        if count < 15:
            # create another random event
            QtCore.QTimer.singleShot(int(random.random() * 1000), partial(self._startStuff, name, count + 1))
        else:
            self._exitSignal += 1


class TestScheduler(unittest.TestCase):

    @staticmethod
    def _queueEnd():
        print(f'END')

    def test_scheduler(self):
        # create a simple app
        app = QtWidgets.QApplication(sys.argv)

        # create and start a scheduler test-case
        obj = SchedulerTester(app)
        obj.start()

        # wait until all the threads have finished
        while obj._exitSignal != 3:
            app.processEvents()

        # process any remaining threads/timers
        QtCore.QTimer.singleShot(0, self._queueEnd)
        app.processEvents()

        print('\n'.join([f'{qVal}    {rVal}' for qVal, rVal in zip_longest(obj._handledEvents, obj._realEvents)]))
        self.assertListEqual(obj._handledEvents, obj._realEvents)


if __name__ == '__main__':
    main()
