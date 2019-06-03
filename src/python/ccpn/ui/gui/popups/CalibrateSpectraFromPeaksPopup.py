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
from typing import Sequence
from ccpn.core.lib import Util as ccpnUtil
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.guiSettings import getColours, SOFTDIVIDER, DIVIDER
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Splitter import Splitter
from ccpn.ui.gui.widgets.CompoundWidgets import PulldownListCompoundWidget
from ccpn.core.lib.ContextManagers import undoBlock
from ccpn.ui.gui.popups.Dialog import handleDialogApply
from ccpn.core.lib.ContextManagers import undoStackBlocking
from functools import partial
from ccpn.core.lib.SpectrumLib import _calibrateXND, _calibrateYND, _calibrateX1D, _calibrateY1D
from ccpn.util.Common import getAxisCodeMatchIndices


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
        self._spectrumFrame = None

        # the last item that was clicked
        self._lastSelectedObjects = strip._lastSelectedObjects

        if not (self._lastSelectedObjects and isinstance(self._lastSelectedObjects, Sequence)):
            raise TypeError('last selected objects must be a list')
        if len(self._lastSelectedObjects) > 1:
            raise TypeError('Too many objects selected')

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
        # self.primaryPeakPulldown.setPreSelect(self._fillPreferredWidget)
        self._fillPreferredWidget()

        # add the other peaks that will be moved
        row += 1
        self._spectrumFrame = Frame(self.scrollAreaWidgetContents, setLayout=True, showBorder=False, grid=(row, 0), gridSpan=(1, 3))

        self._fillSpectrumFrame()
        # specRow = 0
        # # add headers
        # for peak in self.peaks:
        #     if specRow > 0:
        #         # add softdivider
        #         HLine(spectrumFrame, grid=(specRow, 0), gridSpan=(1, 5), colour=getColours()[SOFTDIVIDER], height=15)
        #
        #     specRow += 1
        #     Label(spectrumFrame, text='Peak: %s' % str(peak.id), grid=(specRow, 0), gridSpan=(1, 5), bold=True)
        #     numDim = peak.peakList.spectrum.dimensionCount
        #     for dim in range(numDim):
        #
        #         specRow += 1
        #         Label(spectrumFrame, text=peak.peakList.spectrum.isotopeCodes[dim], grid=(specRow, 1))
        #         Label(spectrumFrame, text='%.3f' % peak.ppmPositions[dim], grid=(specRow, 2))
        #         Label(spectrumFrame, text='%.3f' % self.primaryPeak.ppmPositions[dim], grid=(specRow, 3))
        #         Label(spectrumFrame, text='%.3f' % (self.primaryPeak.ppmPositions[dim] - peak.ppmPositions[dim]), grid=(specRow, 4))
        #
        #     specRow += 1

        row += 1
        Spacer(self.scrollAreaWidgetContents, 2, 2,
               QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(row, 2), gridSpan=(1, 1))

        self.buttonBox = ButtonList(self, grid=(1, 0), texts=['Close', 'Ok'],
                                    callbacks=[self._reject, self._accept], hAlign='r', vAlign='b')

        # self.setWindowTitle(title)

        self.setFixedHeight(self.sizeHint().height() + 24)
        self.setFixedWidth(self.sizeHint().width() + 24)

    def _fillPreferredWidget(self):
        """Fill the pullDown with the currently available permutations of the axis codes
        """
        ll = [peak.id for peak in self.peaks]
        self.primaryPeakPulldown.pulldownList.setData(ll)

        # specIndex = ll.index(self.peaks[0].id)
        specIndex = ll.index(self._lastSelectedObjects[0].id)

        self.primaryPeakPulldown.setIndex(specIndex)

        self.primaryPeak = self.peaks[specIndex]

    def _setPrimaryPeak(self, value):
        """Set the preferred axis ordering from the pullDown selection
        """
        index = self.primaryPeakPulldown.getIndex()
        self.primaryPeak = self.peaks[index]

        if self._spectrumFrame:
            self._fillSpectrumFrame()

    def _fillSpectrumFrame(self):
        """Rebuild the spectrum frame as the primary peak has been updated
        """
        spectrumFrame = self._spectrumFrame
        layout = spectrumFrame.getLayout()
        while layout.count():
            wid = layout.takeAt(0).widget()
            wid.setParent(None)
            wid.setVisible(False)

        self._spectraCheckBoxes = {}
        specRow = 0
        HLine(spectrumFrame, grid=(specRow, 0), gridSpan=(1, 6), colour=getColours()[DIVIDER], height=15)

        specRow += 1
        incudeAxisLabel = Label(spectrumFrame, text="Include\nAxis", grid=(specRow, 0), hAlign='c')
        axisLabel = Label(spectrumFrame, text="AxisCode", grid=(specRow, 1), hAlign='c')
        isoLabel = Label(spectrumFrame, text="Isotope\nCode", grid=(specRow, 2), hAlign='c')
        oldPpmLabel = Label(spectrumFrame, text="Original\nppmPosition", grid=(specRow, 3), hAlign='c')
        newPpmLabel = Label(spectrumFrame, text="New\nppmPosition", grid=(specRow, 4), hAlign='c')
        deltaLabel = Label(spectrumFrame, text="Delta", grid=(specRow, 5), hAlign='c')

        specRow += 1
        HLine(spectrumFrame, grid=(specRow, 0), gridSpan=(1, 6), colour=getColours()[SOFTDIVIDER], height=10)

        specRow += 1
        for peak in self.peaks:

            if specRow > 3:
                # add softdivider
                HLine(spectrumFrame, grid=(specRow, 0), gridSpan=(1, 6), colour=getColours()[SOFTDIVIDER], height=10)

            specRow += 1
            Label(spectrumFrame, text='Peak: %s' % str(peak.id), grid=(specRow, 0), gridSpan=(1, 6), bold=True)
            numDim = peak.peakList.spectrum.dimensionCount

            indices = getAxisCodeMatchIndices(self.strip.axisCodes, peak.peakList.spectrum.axisCodes)

            for ind in range(2):

                dim = indices[ind]

                if not dim:
                    continue

                specRow += 1
                axisLabel = Label(spectrumFrame, text=peak.peakList.spectrum.axisCodes[dim], grid=(specRow, 1))
                isoLabel = Label(spectrumFrame, text=peak.peakList.spectrum.isotopeCodes[dim], grid=(specRow, 2))
                ppmLabel = Label(spectrumFrame, text='%.3f' % peak.ppmPositions[dim], grid=(specRow, 3))

                if (peak != self.primaryPeak):
                    Label(spectrumFrame, text='%.3f' % self.primaryPeak.ppmPositions[dim], grid=(specRow, 4))
                    Label(spectrumFrame, text='%.3f' % (self.primaryPeak.ppmPositions[dim] - peak.ppmPositions[dim]), grid=(specRow, 5))

                    self._spectraCheckBoxes[str(peak.id) + str(ind)] = CheckBox(spectrumFrame, grid=(specRow, 0), vAlign='t', hAlign='c', checked=True)

            specRow += 1

    def _accept(self):
        self.accept()

        with handleDialogApply(self) as error:
            fromPos = self.primaryPeak.position

            # add an undo item to the stack
            with undoStackBlocking() as addUndoItem:
                # get the list of visible spectra in this strip
                spectra = [(specView, specView.spectrum,
                            self.spectrumCount[specView.spectrum].position, fromPos,
                            self._spectraCheckBoxes[str(self.spectrumCount[specView.spectrum].id) + str(0)].isChecked(),
                            self._spectraCheckBoxes[str(self.spectrumCount[specView.spectrum].id) + str(1)].isChecked())
                           for specView in self.strip.spectrumViews
                           if specView.isVisible()
                           and specView.spectrum in self.spectrumCount
                           and self.spectrumCount[specView.spectrum] is not self.primaryPeak]

                self._calibrateSpectra(spectra, self.strip, 1.0)

                addUndoItem(undo=partial(self._calibrateSpectra, spectra, self.strip, -1.0),
                            redo=partial(self._calibrateSpectra, spectra, self.strip, 1.0))

        # clear the last selected items
        self.strip._lastSelectedObjects = None

    def _reject(self):
        self.reject()

        # clear the last selected items
        self.strip._lastSelectedObjects = None

    def _calibrateSpectra(self, spectra, strip, direction=1.0):

        for specView, spectrum, fromPeakPos, toPeakPos, doX, doY in spectra:

            if direction > 0:
                fromPos, toPos = fromPeakPos, toPeakPos
            else:
                toPos, fromPos = fromPeakPos, toPeakPos

            if doX:
                _calibrateXND(spectrum, strip, fromPos[0], toPos[0])
            if doY:
                _calibrateYND(spectrum, strip, fromPos[1], toPos[1])

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
                            self.spectrumCount[specView.spectrum].position + (self.spectrumCount[specView.spectrum].height,), fromPos,
                            self._spectraCheckBoxes[str(self.spectrumCount[specView.spectrum].id) + str(0)].isChecked(),
                            self._spectraCheckBoxes[str(self.spectrumCount[specView.spectrum].id) + str(1)].isChecked())
                           for specView in self.strip.spectrumViews
                           if specView.isVisible()
                           and specView.spectrum in self.spectrumCount
                           and self.spectrumCount[specView.spectrum] is not self.primaryPeak]

                self._calibrateSpectra(spectra, self.strip, 1.0)

                addUndoItem(undo=partial(self._calibrateSpectra, spectra, self.strip, -1.0),
                            redo=partial(self._calibrateSpectra, spectra, self.strip, 1.0))

        # clear the last selected items
        self.strip._lastSelectedObjects = None

    def _calibrateSpectra(self, spectra, strip, direction=1.0):

        for specView, spectrum, fromPeakPos, toPeakPos, doX, doY in spectra:

            if direction > 0:
                fromPos, toPos = fromPeakPos, toPeakPos
            else:
                toPos, fromPos = fromPeakPos, toPeakPos

            if doX:
                _calibrateX1D(spectrum, fromPos[0], toPos[0])
            if doY:
                _calibrateY1D(spectrum, fromPos[1], toPos[1])

            if specView and not specView.isDeleted:
                specView.buildContours = True

    def _fillSpectrumFrame(self):
        """Rebuild the spectrum frame as the primary peak has been updated
        """
        spectrumFrame = self._spectrumFrame
        layout = spectrumFrame.getLayout()
        while layout.count():
            wid = layout.takeAt(0).widget()
            wid.setParent(None)
            wid.setVisible(False)

        fromPos = self.primaryPeak.position + (self.primaryPeak.height,)

        self._spectraCheckBoxes = {}
        specRow = 0
        HLine(spectrumFrame, grid=(specRow, 0), gridSpan=(1, 6), colour=getColours()[DIVIDER], height=15)

        specRow += 1
        incudeAxisLabel = Label(spectrumFrame, text="Include\nAxis", grid=(specRow, 0), hAlign='c')
        axisLabel = Label(spectrumFrame, text="AxisCode", grid=(specRow, 1), hAlign='c')
        isoLabel = Label(spectrumFrame, text="Isotope\nCode", grid=(specRow, 2), hAlign='c')
        oldPpmLabel = Label(spectrumFrame, text="Original\nppmPosition", grid=(specRow, 3), hAlign='c')
        newPpmLabel = Label(spectrumFrame, text="New\nppmPosition", grid=(specRow, 4), hAlign='c')
        deltaLabel = Label(spectrumFrame, text="Delta", grid=(specRow, 5), hAlign='c')

        specRow += 1
        HLine(spectrumFrame, grid=(specRow, 0), gridSpan=(1, 6), colour=getColours()[SOFTDIVIDER], height=10)

        specRow += 1
        for peak in self.peaks:

            toPos = peak.position + (peak.height,)

            if specRow > 3:
                # add softdivider
                HLine(spectrumFrame, grid=(specRow, 0), gridSpan=(1, 6), colour=getColours()[SOFTDIVIDER], height=10)

            specRow += 1
            Label(spectrumFrame, text='Peak: %s' % str(peak.id), grid=(specRow, 0), gridSpan=(1, 6), bold=True)
            numDim = peak.peakList.spectrum.dimensionCount

            indices = getAxisCodeMatchIndices(self.strip.axisCodes, peak.peakList.spectrum.axisCodes)

            # do the X axis - the defined ppm axisCode

            specRow += 1
            dim = 0
            Label(spectrumFrame, text=peak.peakList.spectrum.axisCodes[dim], grid=(specRow, 1))
            Label(spectrumFrame, text=peak.peakList.spectrum.isotopeCodes[dim], grid=(specRow, 2))
            Label(spectrumFrame, text='%.3f' % toPos[dim], grid=(specRow, 3))

            if (peak != self.primaryPeak):
                Label(spectrumFrame, text='%.3f' % fromPos[dim], grid=(specRow, 4))
                Label(spectrumFrame, text='%.3f' % (fromPos[dim] - toPos[dim]), grid=(specRow, 5))

                self._spectraCheckBoxes[str(peak.id) + str(dim)] = CheckBox(spectrumFrame, grid=(specRow, 0), vAlign='t', hAlign='c', checked=True)

            # do the intensity

            specRow += 1
            dim = 1
            Label(spectrumFrame, text='intensity', grid=(specRow, 1))
            Label(spectrumFrame, text='', grid=(specRow, 2))
            Label(spectrumFrame, text='%.3f' % toPos[dim], grid=(specRow, 3))

            if (peak != self.primaryPeak):
                Label(spectrumFrame, text='%.3f' % fromPos[dim], grid=(specRow, 4))
                Label(spectrumFrame, text='%.3f' % (fromPos[dim] - toPos[dim]), grid=(specRow, 5))

                self._spectraCheckBoxes[str(peak.id) + str(dim)] = CheckBox(spectrumFrame, grid=(specRow, 0), vAlign='t', hAlign='c', checked=True)

            specRow += 1

