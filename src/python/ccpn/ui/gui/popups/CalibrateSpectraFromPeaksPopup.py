"""
Module Documentation here
"""
from __future__ import annotations


#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2025"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2025-06-23 19:00:00 +0100 (Mon, June 23, 2025) $"
__version__ = "$Revision: 3.3.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2020-12-10 12:15:19 +0000 (Thu, December 10, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Sequence, TYPE_CHECKING
from functools import partial
from collections import namedtuple, Counter, defaultdict

from PyQt5 import QtWidgets, QtCore, QtGui
import numpy as np
from numpy.typing import NDArray

from ccpn.core.lib.WeakRefLib import WeakRefDescriptor
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Frame import Frame, ScrollableFrame
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.CompoundWidgets import PulldownListCompoundWidget
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget, handleDialogApply
from ccpn.ui.gui.guiSettings import getColours, SOFTDIVIDER, DIVIDER
from ccpn.core.lib.ContextManagers import undoStackBlocking
from ccpn.core.lib.SpectrumLib import _calibrateX1D, _calibrateY1D, _calibrateNDAxis
from ccpn.core.lib.AxisCodeLib import getAxisCodeMatchIndices
from ccpn.util.Logging import getLogger


_ItemPosition = namedtuple('_ItemPosition', ['row', 'column'])
_MatchPeak = namedtuple('_MatchPeak', ['target', 'match', 'origPpmLabel', 'ppmLabel',
                                       'ppmDelta', 'dim', 'peak', 'ind', 'realInd', 'warning'])
_HLINE_HEIGHT = 14
_BADCOLOR = QtGui.QColor('tomato')

if TYPE_CHECKING:
    from ccpn.ui.gui.lib.GuiStrip import GuiStrip


class CalibrateSpectraFromPeaksPopupNd(CcpnDialogMainWidget):
    """Popup to allow calibrating of spectra from a selection of peaks in the same spectrumDisplay
    Specifically for an Nd spectrumDisplay

    Calibration is applied to the current selection of peaks

    A single peak is selected as the primary peak from the pullDown,
    all other spectra are updated to align peaks with the primary peak
    """
    FIXEDWIDTH = False
    FIXEDHEIGHT = False

    strip: GuiStrip = WeakRefDescriptor()

    def __init__(self, parent=None, mainWindow=None, strip=None, spectrumCount=None,
                 title: str = 'Calibrate Spectra from Peaks', **kwds):
        super().__init__(parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
        else:
            self.application = self.project = self.current = None

        self._parent = parent
        self.strip = strip
        self.spectrumCount: int = spectrumCount
        self._spectrumFrame: Frame | None = None

        # initialise the content
        self._checkItems()
        self._setWidgets()

        self.setOkButton(callback=self._accept, tipText='Ok')
        self.setCloseButton(callback=self.reject, tipText='Close')

        # set the buttons and the size
        self.adjustSize()

    def _postInit(self):
        # initialise the buttons and dialog size
        super()._postInit()

        # allow for the scrollbars
        newSize = self._spectrumFrame.minimumSizeHint()
        self.setMinimumHeight(300)
        self.setFixedWidth(newSize.width() + 50)

    def _setWidgets(self):
        """Add widgets to the popup
        """
        topWidget = self.mainWidget

        row = 0
        self.primaryPeakPulldown = PulldownListCompoundWidget(topWidget, labelText="Fixed Peak",
                                                              grid=(row, 0), gridSpan=(1, 3), hAlign='l',
                                                              callback=self._setPrimaryPeak)
        row += 1
        self.scrollAreaWidgetContents = ScrollableFrame(self.mainWidget, setLayout=True, grid=(row, 0), gridSpan=(1, 3),
                                                        scrollBarPolicies=('never', 'asNeeded'))
        # add the other peaks that will be moved
        self._backgroundFrame = _BorderUnderlay(self.scrollAreaWidgetContents, borderHeight=_HLINE_HEIGHT // 2)
        self._spectrumFrame = Frame(self.scrollAreaWidgetContents, setLayout=True, showBorder=False, grid=(0, 0),
                                    gridSpan=(1, 3))
        self._spectrumFrame.getLayout().setAlignment(QtCore.Qt.AlignLeft)
        self._backgroundFrame.setSourceLayout(self._spectrumFrame.getLayout())

        row += 1
        Spacer(topWidget, 2, 2,
               QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed,
               grid=(row, 2), gridSpan=(1, 1))

        self._fillPreferredWidget()
        self._fillSpectrumFrame()

    def _fillPreferredWidget(self):
        """Fill the pullDown with the currently available peak ids when the popup is initialised
        """
        ll = [peak.id for peak in self.peaks]
        self.primaryPeakPulldown.pulldownList.setData(ll)

        if ll and self._lastClickedObjects:
            specIndex = ll.index(self._lastClickedObjects[0].id)
            self.primaryPeakPulldown.setIndex(specIndex)
            self.primaryPeak = self.peaks[specIndex]

    def _checkItems(self):
        """Check the items are valid
        """
        if not isinstance(self.spectrumCount, dict):
            raise TypeError('spectrumCount is not of type dict')

        self.peaks = list(self.spectrumCount.values())

        # the last item that was clicked
        self._lastClickedObjects = self.strip._lastClickedObjects

        if not (self._lastClickedObjects and isinstance(self._lastClickedObjects, Sequence)):
            raise TypeError('last selected objects must be a list')
        if len(self._lastClickedObjects) > 1:
            raise TypeError('Too many objects selected')

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
        # remove all the old widgets from the frame - probably not the best strategy
        while layout.count():
            wid = layout.takeAt(0).widget()
            wid.setParent(None)
            wid.setVisible(False)

        FIELDS = 7
        start = end = _ItemPosition(0, 0)

        self._spectraCheckBoxes = {}
        self._matchToAxisPulldowns = {}
        self._linkedPulldowns = defaultdict(list)

        specRow = 0
        HLine(spectrumFrame, grid=(specRow, 0), gridSpan=(1, FIELDS), colour=getColours()[DIVIDER],
              height=_HLINE_HEIGHT)

        specRow += 1
        _incudeAxisLabel = Label(spectrumFrame, text="Include\nAxis", grid=(specRow, 0), hAlign='c')
        _axisLabel = Label(spectrumFrame, text="AxisCode", grid=(specRow, 1), hAlign='c')
        _matchAxisLabel = Label(spectrumFrame, text="Match to\nAxisCode\n(in Fixed Peak)", grid=(specRow, 2),
                                hAlign='c')
        _isoLabel = Label(spectrumFrame, text="Isotope\nCode", grid=(specRow, 3), hAlign='c')
        _oldPpmLabel = Label(spectrumFrame, text="Original\nppmPosition", grid=(specRow, 4), hAlign='c')
        _newPpmLabel = Label(spectrumFrame, text="New\nppmPosition", grid=(specRow, 5), hAlign='c')
        _deltaLabel = Label(spectrumFrame, text="Delta", grid=(specRow, 6), hAlign='c')

        specRow += 1
        HLine(spectrumFrame, grid=(specRow, 0), gridSpan=(1, FIELDS), colour=getColours()[SOFTDIVIDER],
              height=_HLINE_HEIGHT)

        specRow += 1
        for peak in self.peaks:
            # inside the loop to reset for every peak
            primarySpec = self.primaryPeak.peakList.spectrum
            primaryIsoCount = Counter(primarySpec.isotopeCodes)
            thisSpec = peak.spectrum
            thisSpecIsoCount = Counter(thisSpec.isotopeCodes)

            if specRow > 3:
                # add soft divider
                HLine(spectrumFrame, grid=(specRow, 0), gridSpan=(1, FIELDS), colour=getColours()[SOFTDIVIDER],
                      height=_HLINE_HEIGHT)
            specRow += 1
            Label(spectrumFrame, text=f'Peak: {str(peak.id)}', grid=(specRow, 0), gridSpan=(1, FIELDS), bold=True)

            if peak == self.primaryPeak:
                # get the co-ordinates for the bounding box
                start = _ItemPosition(row=specRow, column=0)

            _indCount: dict[str, int] = defaultdict(int)
            _isoCount: dict[str, int] = defaultdict(int)
            for ind in range(len(thisSpec.axisCodes)):
                thisIsoCode = thisSpec.isotopeCodes[ind]
                primaryIsotopeIndices = [idx if iso == thisSpec.isotopeCodes[ind] else None
                                         for idx, iso in enumerate(primarySpec.isotopeCodes)
                                         ]
                # the indices of the matching isotopeCodes
                thisIsoIndices = [idx for idx, iso in enumerate(primarySpec.isotopeCodes)
                                  if iso == thisSpec.isotopeCodes[ind]]

                # disallow any pulldowns that will give more selections than available target axes
                discard = (primaryIsoCount.get(thisIsoCode, 0) and
                           (_isoCount.get(thisIsoCode, 0) >= primaryIsoCount[thisIsoCode]))
                if discard:
                    continue

                specRow += 1
                _isoLabel = Label(spectrumFrame, text=thisIsoCode, grid=(specRow, 3))
                _ppmLabel = Label(spectrumFrame, text='%.3f' % peak.ppmPositions[ind], grid=(specRow, 4))

                if (peak == self.primaryPeak):
                    Label(spectrumFrame, text=thisSpec.axisCodes[ind], grid=(specRow, 1))
                else:
                    callbackId = f'{peak.id}_{ind}'  # NOT the real-row from the first pulldown
                    # create the first pulldown/label based on the count of the isotope-code in this peak
                    targetAxis: PulldownList | Label
                    if (primaryIsoCount.get(thisIsoCode, 0) and
                            (thisSpecIsoCount.get(thisIsoCode, 0) > primaryIsoCount.get(thisIsoCode, 0))):
                        # requires a pulldown
                        codes = [thisSpec.axisCodes[ii]
                                 for ii, iso in enumerate(thisSpec.isotopeCodes)
                                 if iso == thisIsoCode]
                        targetAxis = PulldownList(spectrumFrame, grid=(specRow, 1))
                        targetAxis.setData(codes)
                        targetAxis.setIndex(_isoCount.get(thisIsoCode, 0))
                        targetAxis.setCallback(partial(self._changeAxisOption,
                                                       targetAxis,
                                                       f'target{peak.id}{thisIsoCode}',
                                                       thisIsoCode,
                                                       callbackId))
                        realInd = thisSpec.axisCodes.index(codes[_isoCount.get(thisIsoCode, 0)])
                        _isoCount[thisIsoCode] += 1

                        self._linkedPulldowns[f'target{peak.id}{thisIsoCode}'].append(targetAxis)
                    else:
                        targetAxis = Label(spectrumFrame, text=thisSpec.axisCodes[ind], grid=(specRow, 1))
                        realInd = ind

                    matchToAxis: PulldownList | Label | None = None
                    ppmLabel: Label | None = None
                    ppmDelta: Label | None = None
                    dim: int = 0  # check this
                    # create the second pulldown/label based on the count of the isotope-code in the primary-peak
                    if thisIsoIndices:
                        if len(thisIsoIndices) > 1:
                            # just checking
                            dim = thisIsoIndices[min(_indCount.get(thisIsoCode, 0),
                                                     len(thisIsoIndices) - 1)]  # index of axis in primary

                            matchCodes = [primarySpec.axisCodes[ii] for ii, ind in enumerate(primaryIsotopeIndices)
                                          if ind is not None]
                            matchToAxis = PulldownList(spectrumFrame, grid=(specRow, 2))
                            matchToAxis.setData(matchCodes)
                            matchToAxis.setIndex(_indCount.get(thisIsoCode, 0))
                            matchToAxis.setCallback(partial(self._changeAxisOption,
                                                            matchToAxis,
                                                            f'match{peak.id}{thisIsoCode}',
                                                            thisIsoCode,
                                                            callbackId))
                            _indCount[thisIsoCode] += 1

                            self._linkedPulldowns[f'match{peak.id}{thisIsoCode}'].append(matchToAxis)
                        else:
                            dim = thisIsoIndices[0]
                            matchToAxis = Label(spectrumFrame, text=primarySpec.axisCodes[dim], grid=(specRow, 2))

                        ppmLabel = Label(spectrumFrame, text='%.3f' % self.primaryPeak.ppmPositions[dim],
                                         grid=(specRow, 5))
                        ppmDelta = Label(spectrumFrame,
                                         text='%.3f' % (self.primaryPeak.ppmPositions[dim] - peak.ppmPositions[ind]),
                                         grid=(specRow, 6))

                    if thisIsoIndices:
                        checked = thisSpec.axisCodes[ind] != 'intensity'
                        self._spectraCheckBoxes[callbackId] = CheckBox(spectrumFrame, grid=(specRow, 0),
                                                                       vAlign='c', hAlign='c',
                                                                       checked=checked)
                    # create the callback information for the pulldowns
                    self._matchToAxisPulldowns[callbackId] = _MatchPeak(target=targetAxis,
                                                                        match=matchToAxis,
                                                                        origPpmLabel=_ppmLabel,
                                                                        ppmLabel=ppmLabel,
                                                                        ppmDelta=ppmDelta,
                                                                        dim=dim,
                                                                        peak=peak,
                                                                        ind=ind,
                                                                        realInd=realInd,
                                                                        warning=False)
            if peak == self.primaryPeak:
                # get the co-ordinates for the bounding box
                end = _ItemPosition(row=specRow + 1, column=7)

            specRow += 1

        for linkId in self._linkedPulldowns:
            self._colourPulldowns(linkId)
        self._backgroundFrame.setCorners(start, end)

    def _accept(self):
        self.accept()

        with handleDialogApply(self) as error:
            fromPos = self.primaryPeak.position

            # add an undo item to the stack
            with undoStackBlocking() as addUndoItem:

                # get the list of visible spectra in this strip
                spectra = []
                for peak in self.peaks:
                    if peak != self.primaryPeak:
                        indices = list(getAxisCodeMatchIndices(peak.axisCodes, self.primaryPeak.axisCodes))
                        # peakFromPos = [fromPos[indices[ii]] if indices[ii] is not None else None for ii in
                        #                range(len(peak.position))]  # why?
                        peakFromPos = [None] * len(peak.position)

                        for ii in range(len(peak.axisCodes)):
                            callbackId = f'{peak.id}_{ii}'  # NOT the real-row from the first pulldown
                            if (found := self._matchToAxisPulldowns.get(callbackId)) is not None:
                                dim = found.dim
                                realInd = found.realInd
                                if callbackId in self._spectraCheckBoxes:
                                    peakFromPos[realInd] = (self.primaryPeak.ppmPositions[dim]
                                                            if self._spectraCheckBoxes[
                                        callbackId].isChecked() else None)
                                # else:
                                #     peakFromPos[realInd] = None
                        spectra.append((None, peak.peakList.spectrum,
                                        peak.position, peakFromPos))

                self._calibrateSpectra(spectra, self.strip, 1.0)

                addUndoItem(undo=partial(self._calibrateSpectra, spectra, self.strip, -1.0),
                            redo=partial(self._calibrateSpectra, spectra, self.strip, 1.0))

        # clear the last selected items
        self.strip._lastClickedObjects = None

    def _reject(self):
        self.reject()

        # clear the last selected items
        self.strip._lastClickedObjects = None

    def _changeAxisOption(self, widget, linkId, isoCode, matchKey, _value):
        try:
            # update the values for the new axisCode in the dict
            targetAxis, matchToAxis, origPpmLabel, ppmLabel, ppmDelta, _, peak, ind, realInd, warning \
                = self._matchToAxisPulldowns[matchKey]
            realInd = peak.axisCodes.index(targetAxis.get())
            dim = self.primaryPeak.axisCodes.index(matchToAxis.get())
            # update the labels
            origPpmLabel.setText(f'{peak.ppmPositions[realInd]:.3f}')
            ppmLabel.setText(f'{self.primaryPeak.ppmPositions[dim]:.3f}')
            ppmDelta.setText(f'{self.primaryPeak.ppmPositions[dim] - peak.ppmPositions[realInd]:.3f}')
            badDict = self._colourPulldowns(linkId)
            self._matchToAxisPulldowns[matchKey] = _MatchPeak(target=targetAxis,
                                                              match=matchToAxis,
                                                              origPpmLabel=origPpmLabel,
                                                              ppmLabel=ppmLabel,
                                                              ppmDelta=ppmDelta,
                                                              dim=dim,
                                                              peak=peak,
                                                              ind=ind,
                                                              realInd=realInd,
                                                              warning=badDict.get(linkId, False))
        except Exception as es:
            getLogger().debug(f'{es}')

    def _colourPulldowns(self, linkId: str) -> dict:
        badDict: dict[QtWidgets.QWidget, bool] = {}
        for ii, pulldown in enumerate(self._linkedPulldowns[linkId]):
            # get the list of texts from the other combos
            others = [combo.get() for combo in self._linkedPulldowns[linkId]
                      if combo != pulldown]
            if pulldown.get() in others:
                badDict[pulldown] = True

            model = pulldown.model()
            for ind in range(pulldown.count()):
                if (item := model.item(ind)) is not None:
                    txt = item.text()
                    if txt in others:
                        # paint duplicates red
                        item.setData(_BADCOLOR, role=QtCore.Qt.ForegroundRole)
                    else:
                        # clears the colour and reverts to palette.Text
                        item.setData(None, role=QtCore.Qt.ForegroundRole)
            # force a repaint to set the colour of the selected index
            pulldown.repaint()

        return badDict

    def _calibrateSpectra(self, spectra, strip, direction=1.0):

        for specView, spectrum, fromPeakPos, toPeakPos in spectra:

            if direction > 0:
                fromPos, toPos = fromPeakPos, toPeakPos
            else:
                toPos, fromPos = fromPeakPos, toPeakPos

            for ii in range(len(fromPos)):
                if fromPos[ii] is not None and toPos[ii] is not None:
                    _calibrateNDAxis(spectrum, ii, fromPos[ii], toPos[ii])


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
                            self.spectrumCount[specView.spectrum].position + (
                                self.spectrumCount[specView.spectrum].height,), fromPos,
                            self._spectraCheckBoxes[str(self.spectrumCount[specView.spectrum].id) + str(0)].isChecked(),
                            self._spectraCheckBoxes[str(self.spectrumCount[specView.spectrum].id) + str(1)].isChecked())
                           for specView in self.strip.spectrumViews
                           if specView.isDisplayed
                           and specView.spectrum in self.spectrumCount
                           and self.spectrumCount[specView.spectrum] is not self.primaryPeak]

                self._calibrateSpectra(spectra, self.strip, 1.0)

                addUndoItem(undo=partial(self._calibrateSpectra, spectra, self.strip, -1.0),
                            redo=partial(self._calibrateSpectra, spectra, self.strip, 1.0))

        # clear the last selected items
        self.strip._lastClickedObjects = None

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
                specView.refreshData()

    def _fillSpectrumFrame(self):
        """Rebuild the spectrum frame as the primary peak has been updated
        """
        spectrumFrame = self._spectrumFrame
        layout = spectrumFrame.getLayout()
        while layout.count():
            wid = layout.takeAt(0).widget()
            wid.setVisible(False)
            wid.setParent(None)

        fromPos = self.primaryPeak.position + (self.primaryPeak.height,)
        start = end = _ItemPosition(0, 0)

        self._spectraCheckBoxes = {}
        specRow = 0
        HLine(spectrumFrame, grid=(specRow, 0), gridSpan=(1, 6), colour=getColours()[DIVIDER],
              height=_HLINE_HEIGHT)

        specRow += 1
        incudeAxisLabel = Label(spectrumFrame, text="Include\nAxis", grid=(specRow, 0), hAlign='c')
        axisLabel = Label(spectrumFrame, text="AxisCode", grid=(specRow, 1), hAlign='c')
        isoLabel = Label(spectrumFrame, text="Isotope\nCode", grid=(specRow, 2), hAlign='c')
        oldPpmLabel = Label(spectrumFrame, text="Original\nppmPosition", grid=(specRow, 3), hAlign='c')
        newPpmLabel = Label(spectrumFrame, text="New\nppmPosition", grid=(specRow, 4), hAlign='c')
        deltaLabel = Label(spectrumFrame, text="Delta", grid=(specRow, 5), hAlign='c')

        specRow += 1
        HLine(spectrumFrame, grid=(specRow, 0), gridSpan=(1, 6), colour=getColours()[SOFTDIVIDER],
              height=_HLINE_HEIGHT)

        specRow += 1
        for peak in self.peaks:

            toPos = peak.position + (peak.height,)

            if specRow > 3:
                # add soft-divider
                HLine(spectrumFrame, grid=(specRow, 0), gridSpan=(1, 6), colour=getColours()[SOFTDIVIDER],
                      height=_HLINE_HEIGHT)

            if peak == self.primaryPeak:
                # get the co-ordinates for the bounding box
                start = _ItemPosition(row=specRow, column=0)

            specRow += 1
            Label(spectrumFrame, text=f'Peak: {str(peak.id)}', grid=(specRow, 0), gridSpan=(1, 6), bold=True)
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

                self._spectraCheckBoxes[str(peak.id) + str(dim)] = CheckBox(spectrumFrame, grid=(specRow, 0),
                                                                            vAlign='t', hAlign='c', checked=True)

            # do the intensity

            specRow += 1
            dim = 1
            Label(spectrumFrame, text='intensity', grid=(specRow, 1))
            Label(spectrumFrame, text='', grid=(specRow, 2))
            Label(spectrumFrame, text='%.3f' % toPos[dim], grid=(specRow, 3))

            if (peak != self.primaryPeak):
                Label(spectrumFrame, text='%.3f' % fromPos[dim], grid=(specRow, 4))
                Label(spectrumFrame, text='%.3f' % (fromPos[dim] - toPos[dim]), grid=(specRow, 5))

                self._spectraCheckBoxes[str(peak.id) + str(dim)] = CheckBox(spectrumFrame, grid=(specRow, 0),
                                                                            vAlign='t', hAlign='c', checked=False)

            if peak == self.primaryPeak:
                # get the co-ordinates for the bounding box
                end = _ItemPosition(row=specRow + 1, column=7)

            specRow += 1


#=========================================================================================
# _BorderUnderlay
#=========================================================================================

class _BorderUnderlay(QtWidgets.QWidget):
    """
    Underlay widget that draws a border around the rows/columns defining the selected object,
    ensuring a clean visual edge.

    :ivar start: Top-left corner of the selection.
    :vartype start: _ItemPosition
    :ivar end: Bottom-right corner of the selection.
    :vartype end: _ItemPosition
    :ivar _grid_layout: Weak reference to the associated QGridLayout.
    :vartype _grid_layout: QtWidgets.QGridLayout
    :ivar _background_rect: Rectangle defining the background highlight area.
    :vartype _background_rect: QtCore.QRect
    :ivar _borderHeight: Height of the border padding.
    :vartype _borderHeight: int
    """

    start: _ItemPosition = _ItemPosition(0, 0)
    end: _ItemPosition = _ItemPosition(0, 0)
    _grid_layout: QtWidgets.QGridLayout = WeakRefDescriptor()
    _background_rect = QtCore.QRect(0, 0, 0, 0)
    _borderHeight: int = 0

    def __init__(self, parent, borderHeight: int = 0):
        """
        Initialise the underlay widget.

        :param parent: Parent widget.
        :type parent: QtWidgets.QWidget
        :param borderHeight: Optional border height padding.
        :type borderHeight: int
        """
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self._backgroundColour = QtGui.QColor('#7f7f7f')
        self._backgroundColour.setAlphaF(0.1)
        self._highlightBrush = QtGui.QBrush(self._backgroundColour)
        self._borderHeight = borderHeight

    def setSourceLayout(self, layout: QtWidgets.QGridLayout):
        """
        Link an existing QGridLayout to this widget.

        :param layout: The layout to associate with this widget.
        :type layout: QtWidgets.QGridLayout
        :raises TypeError: If the layout is not a QGridLayout.
        """
        if not isinstance(layout, QtWidgets.QGridLayout):
            raise TypeError('Expected a QGridLayout')
        self._grid_layout = layout

    def setCorners(self, start: _ItemPosition, end: _ItemPosition):
        """
        Set the top-left and bottom-right corners of the selection rectangle.

        :param start: Starting position (top-left).
        :type start: _ItemPosition
        :param end: Ending position (bottom-right).
        :type end: _ItemPosition
        :raises TypeError: If either argument is not an _ItemPosition.
        """
        if not isinstance(start, _ItemPosition) or not isinstance(end, _ItemPosition):
            raise TypeError('Expected _ItemPosition(row, column)')
        self.start = start
        self.end = end
        self._repaint = True

    def resizeEvent(self, ev):
        """
        Handle widget resizing when the parent resizes.

        :param ev: Resize event.
        :type ev: QtGui.QResizeEvent
        """
        super().resizeEvent(ev)
        if (parent := self.parent()) and isinstance(parent, QtWidgets.QWidget):
            self.setGeometry(QtCore.QRect(parent.rect()))
        self._repaint = True

    def _resizeBackgroundRect(self):
        """
        Calculate the bounding rectangle for the selected grid cells
        and update the background rectangle accordingly.
        """
        if not self._repaint:
            return
        # Ensure the layout has been initialized and contains items
        if not self._grid_layout:
            return
        layout = self._grid_layout
        rSize: NDArray[np.int32] = np.full(layout.rowCount() + 1, -1, dtype=int)
        cSize: NDArray[np.int32] = np.full(layout.columnCount() + 1, -1, dtype=int)
        for itmNum in range(layout.count()):
            if (itm := layout.itemAt(itmNum)):
                row, col, spanY, spanX = layout.getItemPosition(itmNum)
                rect = itm.geometry()

                if rSize[row] == -1:
                    rSize[row] = rect.y()
                else:
                    rSize[row] = min(int(rSize[row]), rect.y())
                if rSize[row + spanY] == -1:
                    rSize[row + spanY] = rect.y() + rect.height()
                else:
                    rSize[row + spanY] = max(int(rSize[row + spanY]), rect.y() + rect.height())
                if cSize[col] == -1:
                    cSize[col] = rect.x()
                else:
                    cSize[col] = min(int(cSize[col]), rect.x())
                if cSize[col + spanX] == -1:
                    cSize[col + spanX] = rect.x() + rect.width()
                else:
                    cSize[col + spanX] = max(int(cSize[col + spanX]), rect.x() + rect.width())
        if self._removeNull(rSize) is None or self._removeNull(cSize) is None:
            return
        self._background_rect = QtCore.QRect(
                cSize[self.start.column],
                rSize[self.start.row] - self._borderHeight,
                cSize[self.end.column] - cSize[self.start.column],
                rSize[self.end.row] - rSize[self.start.row] + (2 * self._borderHeight)
                )
        self._repaint = False

    @staticmethod
    def _removeNull(arr: NDArray[np.int32]) -> NDArray[np.int32] | None:
        """
        Fill in missing (-1) values in the array using forward fill.

        :param arr: Array with potential -1 values.
        :type arr: NDArray[np.int32]
        :return: Filled array or None if all values are -1.
        :rtype: NDArray[np.int32] | None
        """
        is_valid = (arr != -1)
        if not np.any(is_valid):
            return None
        # copy the first valid column-position to all columns to the left
        _first_valid_index = np.argmax(is_valid)
        arr[:_first_valid_index] = arr[_first_valid_index]
        is_fill = (arr != -1)
        # fill all other valid column-positions to any invalid columns to their right
        index = np.where(is_fill, np.arange(len(arr)), 0)
        np.maximum.accumulate(index, out=index)
        arr[:] = arr[index]
        return arr

    def paintEvent(self, ev):
        """
        Paint the highlight rectangle on the widget.

        :param ev: Paint event.
        :type ev: QtGui.QPaintEvent
        """
        self._resizeBackgroundRect()
        # clear the bottom corners, and draw a rounded rectangle to cover the edges
        p = QtGui.QPainter(self)
        p.translate(0.5, 0.5)  # move to the pixel-centre
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        rgn = self._background_rect.adjusted(0, 0, -1, -1)
        # draw the new rectangle around the module
        p.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        p.setBrush(self._highlightBrush)
        p.drawRoundedRect(rgn, 2, 2)
        p.end()
