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
__dateModified__ = "$dateModified: 2022-06-07 18:51:14 +0100 (Tue, June 07, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-04-07 10:28:42 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore
from functools import partial
from ccpn.util.Logging import getLogger
from ccpn.core.Spectrum import Spectrum
from ccpn.core.lib.Notifiers import Notifier, _removeDuplicatedNotifiers
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar, notificationEchoBlocking
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.ListWidget import ListWidget
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.ProgressWidget import ProgressDialog
from ccpn.util.UpdateScheduler import UpdateScheduler
from ccpn.util.UpdateQueue import UpdateQueue


class CopyPeaks(CcpnDialog):

    def __init__(self, parent=None, mainWindow=None, title='Copy Peaks to PeakLists', **kwds):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, size=(700, 600), **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.current = self.application.current
        self.project = mainWindow.project

        self._createWidgets()
        self._registerNotifiers()

        self._enableButtons()

        # notifier queue handling
        self._scheduler = UpdateScheduler(self.project, self._queueProcess, name='CopyPeaks',
                                          startOnAdd=False, log=False, completeCallback=self.update)
        self._queuePending = UpdateQueue()
        self._queueActive = None
        self._lock = QtCore.QMutex()

    def _createWidgets(self):

        tipText = ' Select peaks and peakLists to be copied over then click copy'

        self.getLayout().setContentsMargins(10, 10, 10, 10)
        row = 0
        self.spectraLabel1 = Label(self, 'Select Origin Spectra', grid=(row, 0), hAlign='l')
        self.spectraLabel2 = Label(self, 'Select Destination Spectra', grid=(row, 1), hAlign='l')
        row += 1
        self.selectFromPullDown = PulldownList(self, texts=['All'], callback=self._populatePeakWidget, grid=(row, 0))
        self.selectToPullDown = PulldownList(self, texts=['All'], callback=self._populatePeakListsWidget, grid=(row, 1))
        row += 1
        self.inputPeaksWidgetLabel = Label(self, 'Select Peaks To Copy', grid=(row, 0), hAlign='l')
        self.outputPeakListsWidgetLabel = Label(self, 'Select Destination PeakLists', grid=(row, 1), hAlign='l')
        row += 1
        self.inputPeaksWidget = ListWidget(self, multiSelect=True, callback=self._activateCopy, tipText=tipText, grid=(row, 0))
        self.inputPeaksListWidget = ListWidget(self, multiSelect=True, callback=self._activateCopy, tipText=tipText, grid=(row, 1))
        row += 1
        self.selectButtons = ButtonList(self, texts=['Select Current Peaks', 'Clear All'],
                                        callbacks=[self._selectCurrentPeaks, self.clearSelections],
                                        tipTexts=['Select on the list all the current Peaks',
                                                  'Clear All Selections'], grid=(row, 0))

        self.copyButtons = ButtonList(self, texts=['Close', ' Copy '],
                                      callbacks=[self._closePopup, self._copyButton],
                                      tipTexts=['Close popup', tipText], grid=(row, 1))

        self.copyButtons.buttons[1].setDisabled(True)

        self._populatePeakWidget()
        self._populatePeakListsWidget()
        self._setPullDownData()

    def _setPullDownData(self):
        for spectrum in self.project.spectra:
            self.selectFromPullDown.addItem(text=spectrum.pid, item=spectrum)
            self.selectToPullDown.addItem(text=spectrum.pid, item=spectrum)

    def _populatePeakWidget(self, *args):
        obj = self.selectFromPullDown.getObject()

        if isinstance(obj, Spectrum):
            peaks = []
            for peakList in obj.peakLists:
                peaks.extend(peakList.peaks)
            self.inputPeaksWidget.setObjects(peaks, name='pid')
        else:
            self.inputPeaksWidget.setObjects(self.project.peaks, name='pid')

    def _populatePeakListsWidget(self, *args):

        obj = self.selectToPullDown.getObject()
        if isinstance(obj, Spectrum):
            self.inputPeaksListWidget.setObjects(obj.peakLists, name='pid')
        else:
            self.inputPeaksListWidget.setObjects(self.project.peakLists, name='pid')

    def _refreshInputPeaksWidget(self, *args):
        self._populatePeakWidget()

    def _refreshInputPeaksListWidget(self, *args):
        self._populatePeakListsWidget()

    def _selectSpectrum(self, spectrum):
        self.selectFromPullDown.select(spectrum)

    def _activateCopy(self):
        if len(self.inputPeaksListWidget.getSelectedObjects()) > 0 and len(self.inputPeaksWidget.getSelectedObjects()) > 0:
            self.copyButtons.buttons[1].setDisabled(False)

    def _copyButton(self):

        # TODO:ED trap copying to invalid spectra
        try:
            peakLists = self.inputPeaksListWidget.getSelectedObjects()
            peaks = self.inputPeaksWidget.getSelectedObjects()

            numPeaks = len(peaks)
            numPeakLists = len(peakLists)
            # use a larger step-size in the progress-bar if more peaks
            pDiv = 10 if numPeaks * numPeakLists > 100 else 1
            totalCopies = (numPeaks * numPeakLists) // pDiv

            try:
                if numPeaks > 0 and numPeakLists > 0:
                    with undoBlockWithoutSideBar():
                        with notificationEchoBlocking():
                            progress = ProgressDialog(self.mainWindow, text='Copying Peaks...', maximum=totalCopies)

                            # so the user gets some feedback that something happened
                            progress.setMinimumDuration(0)
                            progress.setModal(True)
                            for peakNumber, peak in enumerate(peaks):
                                for listNumber, peakList in enumerate(peakLists):
                                    if progress.wasCanceled():
                                        progress.setValue(totalCopies)
                                        raise RuntimeError('Progress was cancelled')
                                    progress.setValue((numPeaks * listNumber + peakNumber) // pDiv)
                                    peak.copyTo(peakList)

                            progress.setValue(totalCopies)

                    getLogger().info('Peaks copied. Finished')

            except Exception as es:
                if isinstance(es, RuntimeError):
                    raise es
                getLogger().warning('Error copying peaks: %s' % str(es))
                showWarning(str(self.windowTitle()), str(es))

        except RuntimeError:
            getLogger().info('Copy peaks cancelled')
            # undoManager = self._getUndo()
            # undoManager.undo()

        # self._closePopup()

    def _selectPeaks(self, peaks):
        self.inputPeaksWidget.selectObjects(peaks)
        self.inputPeaksWidget.scrollToFirstSelected()

    def clearSelections(self):
        self.inputPeaksWidget.clearSelection()
        self.inputPeaksListWidget.clearSelection()
        self.copyButtons.buttons[1].setDisabled(True)

    def _selectCurrentPeaks(self):
        self.inputPeaksWidget.clearSelection()
        peaks = self.current.peaks
        self._selectPeaks(peaks)

    def _enableButtons(self):
        if len(self.current.peaks) > 0:
            self.selectButtons.buttons[0].setDisabled(False)
        else:
            self.selectButtons.buttons[0].setDisabled(True)

    def _closePopup(self):
        """
        Re-implementation of closeModule function from CcpnModule to unregister notification
        """
        self._deregisterNotifiers()
        self.reject()

    def _registerNotifiers(self):

        self._peakNotifier = Notifier(self.project, [Notifier.DELETE, Notifier.CREATE, Notifier.RENAME], 'Peak',
                                      partial(self._queueGeneralNotifier, self._refreshInputPeaksWidget),
                                      )
        self._peakListNotifier = Notifier(self.project, [Notifier.DELETE, Notifier.CREATE, Notifier.RENAME], 'PeakList',
                                          partial(self._queueGeneralNotifier, self._refreshInputPeaksListWidget),
                                          )

    def _deregisterNotifiers(self):
        if self._peakNotifier:
            self._peakNotifier.unRegister()
        if self._peakListNotifier:
            self._peakListNotifier.unRegister()

    #=========================================================================================
    # Notifier queue handling
    #=========================================================================================

    def _queueGeneralNotifier(self, func, data):
        """Add the notifier to the queue handler
        """
        self._queueAppend([func, data])

    def _queueProcess(self):
        """Process current items in the queue
        """
        with QtCore.QMutexLocker(self._lock):
            # protect the queue switching
            self._queueActive = self._queuePending
            self._queuePending = UpdateQueue()

        executeQueue = _removeDuplicatedNotifiers(self._queueActive)
        for itm in executeQueue:
            # process item if different from previous
            try:
                func, data = itm
                func(data)
            except Exception as es:
                getLogger().debug(f'Error in {self.__class__.__name__} update - {es}')

    def _queueAppend(self, itm):
        """Append a new item to the queue
        """
        self._queuePending.put(itm)
        if not self._scheduler.isActive and not self._scheduler.isBusy:
            self._scheduler.start()

        elif self._scheduler.isBusy:
            # caught during the queue processing event, need to restart
            self._scheduler.signalRestart()
