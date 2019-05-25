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

import os
from functools import partial
from PyQt5 import QtWidgets, QtGui
from ccpn.core.lib import Util as ccpnUtil
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.guiSettings import getColours, DIVIDER
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.Splitter import Splitter
from ccpn.ui.gui.widgets.CompoundWidgets import PulldownListCompoundWidget
from ccpn.core.lib.ContextManagers import undoBlock
from ccpn.ui.gui.popups.Dialog import handleDialogApply
from ccpn.core.lib.ContextManagers import undoStackBlocking
from functools import partial
from ccpn.core.lib.SpectrumLib import _calibrateXND, _calibrateYND, _calibrateX1D, _calibrateY1D


class CalibrateSpectraFromPeaksPopupNd(CcpnDialog):
    """Popup to allow calibrating of spectra from a selection of peaks in the same spectrumDisplay
    Specifically for an Nd spectrumDisplay

    Calibration is applied to the current selection of peaks

    A single peak is selected as the primary peak from the pullDown,
    all other spectra are updated to align peaks with the primary peak
    """
    def __init__(self, parent=None, mainWindow=None, strip=None, spectrumCount=None,
                 title: str = 'Calibrate Spectra from Peaks', **kwds):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current

        self._parent = parent
        self.strip = strip
        self.spectrumCount = spectrumCount
        self.peaks = [peak for peak in self.spectrumCount.values()]

        self.spPulldowns = []

        self.scrollArea = ScrollArea(self, setLayout=True, grid=(0, 0))
        self.scrollArea.setWidgetResizable(True)

        self.scrollAreaWidgetContents = Frame(self, setLayout=True, showBorder=False)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.scrollAreaWidgetContents.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        self.scrollArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.scrollArea.setStyleSheet("""ScrollArea { border: 0px; }""")

        row = 0
        Label(self.scrollAreaWidgetContents, text=title, bold=True, grid=(row, 0), gridSpan=(1, 3))

        row += 1
        self.primaryPeakPulldown = PulldownListCompoundWidget(self.scrollAreaWidgetContents, labelText="Set Primary Peak",
                                                              grid=(row, 0), gridSpan=(1, 3), vAlign='t',
                                                              callback=self._setPrimaryPeak)
        self.primaryPeakPulldown.setPreSelect(self._fillPreferredWidget)
        self._fillPreferredWidget()

        row += 1
        Spacer(self.scrollAreaWidgetContents, 2, 2,
               QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(row, 2), gridSpan=(1, 1))

        self.buttonBox = ButtonList(self, grid=(1, 0), texts=['Close', 'Ok'],
                                    callbacks=[self.reject, self._accept], hAlign='r', vAlign='b')

        # self.setWindowTitle(title)

        self.setFixedHeight(self.sizeHint().height() + 24)
        self.setFixedWidth(self.sizeHint().width() + 24)

    def _fillPreferredWidget(self):
        """Fill the pullDown with the currently available permutations of the axis codes
        """
        ll = [peak.id for peak in self.peaks]
        self.primaryPeakPulldown.pulldownList.setData(ll)

        specIndex = ll.index(self.peaks[0].id)
        self.primaryPeakPulldown.setIndex(specIndex)

        self.primaryPeak = self.peaks[0]

    def _setPrimaryPeak(self, value):
        """Set the preferred axis ordering from the pullDown selection
        """
        index = self.primaryPeakPulldown.getIndex()
        self.primaryPeak = self.peaks[index]

    def _accept(self):
        self.accept()

        with handleDialogApply(self) as error:
            fromPos = self.primaryPeak.position

            # add an undo item to the stack
            with undoStackBlocking() as addUndoItem:
                # get the list of visible spectra in this strip
                spectra = [(specView, specView.spectrum, self.spectrumCount[specView.spectrum].position, fromPos) for specView in self.strip.spectrumViews
                           if specView.isVisible()
                           and specView.spectrum in self.spectrumCount
                           and self.spectrumCount[specView.spectrum] is not self.primaryPeak]

                self._calibrateSpectra(spectra, self.strip, 1.0)

                addUndoItem(undo=partial(self._calibrateSpectra, spectra, self.strip, -1.0),
                            redo=partial(self._calibrateSpectra, spectra, self.strip, 1.0))

    def _calibrateSpectra(self, spectra, strip, direction=1.0):

        for specView, spectrum, fromPeakPos, toPeakPos in spectra:

            if direction > 0:
                fromPos, toPos = fromPeakPos, toPeakPos
            else:
                toPos, fromPos = fromPeakPos, toPeakPos

            _calibrateXND(spectrum, fromPos[0], toPos[0])
            _calibrateYND(spectrum, fromPos[1], toPos[1])

            if specView and not specView.isDeleted:
                specView.buildContours = True


class CalibrateSpectraFromPeaksPopup1d(CalibrateSpectraFromPeaksPopupNd):
    """Popup to allow calibrating of spectra from a selection of peaks in the same spectrumDisplay
    Specifically for a 1d spectrumDisplay

    Calibration is applied to the current selection of peaks

    A single peak is selected as the primary peak from the pullDown,
    all other spectra are updated to align peaks with the primary peak
    """

    def _accept(self):
        self.accept()

        with handleDialogApply(self) as error:
            fromPos = self.primaryPeak.position + (self.primaryPeak.height,)

            # add an undo item to the stack
            with undoStackBlocking() as addUndoItem:
                # get the list of visible spectra in this strip
                spectra = [(specView, specView.spectrum,
                            self.spectrumCount[specView.spectrum].position + (self.spectrumCount[specView.spectrum].height,),
                            fromPos) for specView in self.strip.spectrumViews
                           if specView.isVisible()
                           and specView.spectrum in self.spectrumCount
                           and self.spectrumCount[specView.spectrum] is not self.primaryPeak]

                self._calibrateSpectra(spectra, self.strip, 1.0)

                addUndoItem(undo=partial(self._calibrateSpectra, spectra, self.strip, -1.0),
                            redo=partial(self._calibrateSpectra, spectra, self.strip, 1.0))

    def _calibrateSpectra(self, spectra, strip, direction=1.0):

        for specView, spectrum, fromPeakPos, toPeakPos in spectra:

            if direction > 0:
                fromPos, toPos = fromPeakPos, toPeakPos
            else:
                toPos, fromPos = fromPeakPos, toPeakPos

            _calibrateX1D(spectrum, fromPos[0], toPos[0])
            _calibrateY1D(spectrum, fromPos[1], toPos[1])

            if specView and not specView.isDeleted:
                specView.buildContours = True
