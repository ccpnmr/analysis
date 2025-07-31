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
__dateModified__ = "$dateModified: 2025-06-27 13:30:47 +0100 (Fri, June 27, 2025) $"
__version__ = "$Revision: 3.3.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2020-12-10 12:15:19 +0000 (Thu, December 10, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Sequence, TYPE_CHECKING, Any
from functools import partial
from collections import namedtuple, Counter, defaultdict
from dataclasses import dataclass
from enum import IntEnum

from PyQt5 import QtWidgets, QtCore, QtGui
import numpy as np
from numpy.typing import NDArray

from ccpn.core.lib.WeakRefLib import WeakRefDescriptor
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Frame import Frame, ScrollableFrame
from ccpn.ui.gui.widgets.MessageDialog import showYesNoWarning
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.CompoundWidgets import PulldownListCompoundWidget
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget, handleDialogApply
from ccpn.ui.gui.guiSettings import getColours, SOFTDIVIDER, DIVIDER
from ccpn.core.lib.ContextManagers import undoStackBlocking
from ccpn.core.lib.SpectrumLib import _calibrateX1D, _calibrateY1D, _calibrateNDAxis
from ccpn.util.Logging import getLogger
from ccpn.util.OrderedSet import OrderedSet


_ItemPosition = namedtuple('_ItemPosition', ['row', 'column'])
"""
Namedtuple to store a row and column position.

:ivar row: The row index.
:vartype row: int
:ivar column: The column index.
:vartype column: int
"""


class _PeakType(IntEnum):
    """
    Enum to define the type of peak in the context of target/match.
    """
    any = 0
    target = 1
    match = 2


@dataclass
class _MatchPeak:
    """
    Class to store the links between widgets across a row in the table used in
    CalibrateSpectraFromPeaksPopupNd.

    :ivar target: The target pulldown list or label.
    :vartype target: _IdPulldownList | _IdLabel
    :ivar match: The match pulldown list or label. Can be None.
    :vartype match: _IdPulldownList | _IdLabel | None
    :ivar checkBox: The checkbox associated with the row. Can be None.
    :vartype checkBox: CheckBox | None
    :ivar origPpmLabel: Label displaying the original ppm position.
    :vartype origPpmLabel: Label
    :ivar ppmLabel: Label displaying the new ppm position. Can be None.
    :vartype ppmLabel: Label | None
    :ivar ppmDelta: Label displaying the ppm difference. Can be None.
    :vartype ppmDelta: Label | None
    :ivar peak: The Peak object associated with this row.
    :vartype peak: Peak
    :ivar dim: The dimension index.
    :vartype dim: int
    :ivar ind: The index within the peak's dimensions.
    :vartype ind: int
    :ivar realInd: The real index, often reflecting the original order or mapping.
    :vartype realInd: int
    """
    target: _IdPulldownList | _IdLabel
    match: _IdPulldownList | _IdLabel | None
    checkBox: CheckBox | None
    origPpmLabel: Label
    ppmLabel: Label | None
    ppmDelta: Label | None
    peak: Peak
    dim: int
    ind: int
    realInd: int


@dataclass(frozen=True)
class _KeyPeak:
    """
    Small class to be used as an index in dicts, providing a hashable key
    for peak-related data; hence the frozen=True.

    :ivar peakId: The unique identifier for the peak.
    :vartype peakId: str
    :ivar isotopeCode: The isotope code, e.g., '1H', '13C'. Can be None.
    :vartype isotopeCode: str | None
    :ivar dim: The dimension index. Can be None.
    :vartype dim: int | None
    :ivar ind: An index, typically related to a specific axis or position. Can be None.
    :vartype ind: int | None
    :ivar peakType: The type of peak (any, target, or match).
    :vartype peakType: _PeakType
    """
    peakId: str
    isotopeCode: str | None = None
    dim: int | None = None
    ind: int | None = None
    peakType: _PeakType = _PeakType.any


_HLINE_HEIGHT: int = 14
_BADCOLOR: QtGui.QColor = QtGui.QColor('tomato')
_INTERMEDIATECOLOR: QtGui.QColor = QtGui.QColor('orange')
_CHECKNUM: int = 0
_AXISNUM: int = 1
_MATCHAXISNUM: int = 2
_ISONUM: int = 3
_OLDPPMNUM: int = 4
_NEWPPMNUM: int = 5
_DELTANUM: int = 6

if TYPE_CHECKING:
    from ccpn.ui.gui.lib.GuiStrip import GuiStrip
    from ccpn.core.Peak import Peak
    from ccpn.core.Spectrum import Spectrum


class _IdPulldownList(PulldownList):
    """
    Custom PulldownList widget with additional attributes for peak-type and index.
    """
    _peakType: _PeakType
    _index: int

    def __init__(self, parent: QtWidgets.QWidget, peakType: _PeakType, index: int, *args: Any, **kwargs: Any):
        """
        Initialise the _IdPulldownList widget.

        :param parent: The parent widget.
        :type parent: QtWidgets.QWidget
        :param peakType: The type of peak this pulldown represents (target or match).
        :type peakType: _PeakType
        :param index: An index associated with this pulldown, often related to a dimension.
        :type index: int
        :param args: Positional arguments for the base PulldownList constructor.
        :type args: Any
        :param kwargs: Keyword arguments for the base PulldownList constructor.
        :type kwargs: Any
        """
        super().__init__(parent, *args, **kwargs)
        self._peakType = peakType
        self._index = index

    def getAsList(self) -> list:
        """Return the list of items in the pulldown as a list."""
        return [self.itemText(ii) for ii in range(self.count())]


class _IdLabel(Label):
    """
    Custom Label widget with additional attributes for peak-type and an optional index.
    """
    _peakType: _PeakType
    _index: int | None

    def __init__(self, parent: QtWidgets.QWidget, peakType: _PeakType, *args: Any, **kwargs: Any):
        """
        Initialise the _IdLabel widget.

        :param parent: The parent widget.
        :type parent: QtWidgets.QWidget
        :param peakType: The type of peak this label represents (target or match).
        :type peakType: _PeakType
        :param args: Positional arguments for the base Label constructor.
        :type args: Any
        :param kwargs: Keyword arguments for the base Label constructor.
        :type kwargs: Any
        """
        super().__init__(parent, *args, **kwargs)
        self._peakType = peakType
        self._index = None


#=========================================================================================
# CalibrateSpectraFromPeaksPopupNd
#=========================================================================================

class CalibrateSpectraFromPeaksPopupNd(CcpnDialogMainWidget):
    """
    Popup to allow calibrating of spectra from a selection of peaks in the same spectrumDisplay.
    Specifically for an Nd spectrumDisplay.

    Calibration is applied to the current selection of peaks.

    A single peak is selected as the primary peak from the pulldown,
    all other spectra are updated to align peaks with the primary peak.

    :ivar strip: The GuiStrip instance associated with this popup.
    :vartype strip: GuiStrip
    :ivar peaks: A list of Peak objects selected for calibration.
    :vartype peaks: list[Peak]
    :ivar _spectrumFrame: The frame widget containing the spectrum details. Can be None.
    :vartype _spectrumFrame: Frame | None
    :ivar mainWindow: Reference to the main application window.
    :vartype mainWindow: Any
    :ivar application: Reference to the CCPN application instance.
    :vartype application: Any
    :ivar project: Reference to the current CCPN project.
    :vartype project: Any
    :ivar current: Reference to the current selection/context in the application.
    :vartype current: Any
    :ivar _parent: The parent QWidget of this dialog.
    :vartype _parent: QtWidgets.QWidget | None
    :ivar spectrumCount: A dictionary mapping Spectrum objects to their associated Peak.
    :vartype spectrumCount: dict[Spectrum, Peak]
    :ivar primaryPeakPulldown: The PulldownListCompoundWidget for selecting the fixed peak.
    :vartype primaryPeakPulldown: PulldownListCompoundWidget
    :ivar scrollAreaWidgetContents: The scrollable frame containing the background and spectrum frames.
    :vartype scrollAreaWidgetContents: ScrollableFrame
    :ivar _backgroundFrame: The underlay widget for drawing highlights.
    :vartype _backgroundFrame: _GridLayoutUnderlay
    :ivar _spectraCheckBoxes: Dictionary mapping _KeyPeak to CheckBox instances for 'include' options.
    :vartype _spectraCheckBoxes: dict[_KeyPeak, CheckBox]
    :ivar _matchToAxisPulldowns: Dictionary mapping _KeyPeak to _MatchPeak instances.
    :vartype _matchToAxisPulldowns: dict[_KeyPeak, _MatchPeak]
    :ivar _linkedPulldowns: Defaultdict linking _KeyPeak to a list of _IdPulldownList.
    :vartype _linkedPulldowns: defaultdict[_KeyPeak, list[_IdPulldownList]]
    :ivar primaryPeak: The Peak object selected as the primary (fixed) peak.
    :vartype primaryPeak: Peak | None
    :ivar _lastClickedObjects: The last clicked objects from the GuiStrip.
    :vartype _lastClickedObjects: Sequence[Any] | None
    """
    FIXEDWIDTH: bool = False
    FIXEDHEIGHT: bool = False

    strip: GuiStrip = WeakRefDescriptor()
    peaks: list[Peak] = []
    _spectrumFrame: Frame | None = None
    primaryPeak: Peak | None = None
    _lastChecked: dict[_KeyPeak, bool]  # indexed by [peak.id, ind]

    def __init__(self, parent: QtWidgets.QWidget | None = None, mainWindow: Any = None, strip: GuiStrip | None = None,
                 spectrumCount: dict[Spectrum, Peak] | None = None, title: str = 'Calibrate Spectra from Peaks',
                 **kwds: Any):
        """
        Initialise the CalibrateSpectraFromPeaksPopupNd popup.

        :param parent: The parent widget.
        :type parent: QtWidgets.QWidget | None
        :param mainWindow: The main application window.
        :type mainWindow: Any
        :param strip: The GuiStrip instance.
        :type strip: GuiStrip | None
        :param spectrumCount: A dictionary mapping Spectrum objects to their associated Peak.
                              If None, will be initialized as an empty dict.
        :type spectrumCount: dict[Spectrum, Peak] | None
        :param title: The window title of the popup.
        :type title: str
        :param kwds: Additional keyword arguments for the base CcpnDialogMainWidget constructor.
        :type kwds: Any
        """
        super().__init__(parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
        else:
            self.application = self.project = self.current = None

        self.strip = strip
        self.spectrumCount: dict[Spectrum, Peak] = spectrumCount if spectrumCount is not None else {}
        self._spectrumFrame = None
        self.primaryPeak = None  # Explicitly initialize

        # initialise the content
        self._checkItems()
        self._setWidgets()

        # define the dialog buttons
        self.setOkButton(callback=self._accept, tipText='Ok')
        self.setCloseButton(callback=self.reject, tipText='Close')

        # set the buttons and the size
        self.adjustSize()

    def _postInit(self) -> None:
        """
        Perform post-initialization tasks, including setting dialog size.
        """
        super()._postInit()

        # allow for the scrollbars
        newSize = self._spectrumFrame.minimumSizeHint()
        self.setMinimumHeight(300)
        self.setFixedWidth(newSize.width() + 50)

    def _setWidgets(self) -> None:
        """
        Add widgets to the popup's main widget.
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
        self._backgroundFrame = _GridLayoutUnderlay(self.scrollAreaWidgetContents, borderHeight=_HLINE_HEIGHT // 2)
        self._spectrumFrame = Frame(self.scrollAreaWidgetContents, setLayout=True, showBorder=False, grid=(0, 0),
                                    gridSpan=(1, 3))
        self._spectrumFrame.getLayout().setAlignment(QtCore.Qt.AlignLeft)
        self._backgroundFrame.setSourceLayout(self._spectrumFrame.getLayout())

        row += 1
        Spacer(topWidget, 2, 2,
               QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed,
               grid=(row, 2), gridSpan=(1, 1))

        self._lastChecked = {}  # indexed by [peak.id, ind]
        self._fillPreferredWidget()
        self._fillSpectrumFrame()

    def _fillPreferredWidget(self) -> None:
        """
        Fill the primary peak pulldown with the currently available peak IDs when the popup is initialised.
        """
        ll: list[str] = [peak.id for peak in self.peaks]
        self.primaryPeakPulldown.pulldownList.setData(ll)

        if ll and self._lastClickedObjects:
            # Type cast to Sequence[Any] for safety with index access
            self._lastClickedObjects: Sequence[Any]
            specIndex = ll.index(self._lastClickedObjects[0].id)
            self.primaryPeakPulldown.setIndex(specIndex)
            self.primaryPeak = self.peaks[specIndex]

    def _checkItems(self) -> None:
        """
        Validate the input items and initial peak selection.

        :raises TypeError: If spectrumCount is not a dict, or if last selected objects are invalid.
        """
        if not isinstance(self.spectrumCount, dict):
            raise TypeError('spectrumCount is not of type dict')

        self.peaks = list(self.spectrumCount.values())

        # the last item that was clicked
        # Accessing private attribute `_lastClickedObjects` from `strip`
        self._lastClickedObjects: Sequence[Any] | None = self.strip._lastClickedObjects

        if not (self._lastClickedObjects and isinstance(self._lastClickedObjects, Sequence)):
            raise TypeError('last selected objects must be a list')
        if len(self._lastClickedObjects) > 1:
            raise TypeError('Too many objects selected')

    def _setPrimaryPeak(self, value: Any) -> None:  # _value is not used
        """
        Set the primary (fixed) peak from the pulldown selection and rebuild the display.

        :param value: The value selected in the pulldown (not directly used, index is used).
        :type value: Any
        """
        index: int = self.primaryPeakPulldown.getIndex()
        self.primaryPeak = self.peaks[index]

        if self._spectrumFrame:
            self._fillSpectrumFrame()

    def _fillSpectrumFrame(self) -> None:
        """
        Rebuild the spectrum frame's content when the primary peak has been updated.
        This populates the table with peak information and controls.
        """
        spectrumFrame = self._spectrumFrame
        layout = spectrumFrame.getLayout()
        # remove all the old widgets from the frame - probably not the best strategy
        while layout.count():
            wid: QtWidgets.QWidget = layout.takeAt(0).widget()
            wid.setParent(None)
            wid.setVisible(False)

        FIELDS: int = 7
        start: _ItemPosition = _ItemPosition(0, 0)
        end: _ItemPosition = _ItemPosition(0, 0)

        self._spectraCheckBoxes: dict[_KeyPeak, CheckBox] = {}  # indexed by [peak.id, ind]
        self._matchToAxisPulldowns: dict[_KeyPeak, _MatchPeak] = {}  # indexed by [peak.id, ind]
        self._linkedPulldowns: defaultdict[_KeyPeak, list[_IdPulldownList]] = defaultdict(
                list)  # indexed by [type, peak.id, isotope]

        specRow: int = 0
        HLine(spectrumFrame, grid=(specRow, _CHECKNUM), gridSpan=(1, FIELDS), colour=getColours()[DIVIDER],
              height=_HLINE_HEIGHT)

        specRow += 1
        _includeAxisLabel = Label(spectrumFrame, text="Include\nAxis", grid=(specRow, _CHECKNUM), hAlign='c')
        _axisLabel = Label(spectrumFrame, text="AxisCode", grid=(specRow, _AXISNUM), hAlign='c')
        _matchAxisLabel = Label(spectrumFrame, text="Match to\nAxisCode\n(in Fixed Peak)",
                                grid=(specRow, _MATCHAXISNUM),
                                hAlign='c')
        _isoLabel = Label(spectrumFrame, text="Isotope\nCode", grid=(specRow, _ISONUM), hAlign='c')
        _oldPpmLabel = Label(spectrumFrame, text="Original\nppmPosition", grid=(specRow, _OLDPPMNUM), hAlign='c')
        _newPpmLabel = Label(spectrumFrame, text="New\nppmPosition", grid=(specRow, _NEWPPMNUM), hAlign='c')
        _deltaLabel = Label(spectrumFrame, text="Delta", grid=(specRow, _DELTANUM), hAlign='c')

        specRow += 1
        HLine(spectrumFrame, grid=(specRow, _CHECKNUM), gridSpan=(1, FIELDS), colour=getColours()[SOFTDIVIDER],
              height=_HLINE_HEIGHT)

        specRow += 1
        for peak in self.peaks:
            # inside the loop to reset for every peak
            primarySpec: Spectrum = self.primaryPeak.peakList.spectrum
            primaryIsoCount: Counter[str] = Counter(primarySpec.isotopeCodes)
            thisSpec: Spectrum = peak.spectrum
            thisSpecIsoCount: Counter[str] = Counter(thisSpec.isotopeCodes)

            if specRow > 3:
                # add soft divider
                HLine(spectrumFrame, grid=(specRow, _CHECKNUM), gridSpan=(1, FIELDS), colour=getColours()[SOFTDIVIDER],
                      height=_HLINE_HEIGHT)
            specRow += 1
            Label(spectrumFrame, text=f'Peak: {str(peak.id)}', grid=(specRow, _CHECKNUM), gridSpan=(1, FIELDS),
                  bold=True)

            if peak == self.primaryPeak:
                # get the co-ordinates for the bounding box
                start = _ItemPosition(row=specRow, column=0)

            _indCount: dict[str, int] = defaultdict(int)
            _isoCount: dict[str, int] = defaultdict(int)
            for ind in range(len(thisSpec.axisCodes)):
                thisIsoCode: str = thisSpec.isotopeCodes[ind]
                primaryIsotopeIndices: list[int | None] = [idx if iso == thisSpec.isotopeCodes[ind] else None
                                                           for idx, iso in enumerate(primarySpec.isotopeCodes)
                                                           ]
                # the indices of the matching isotopeCodes
                thisIsoIndices: list[int] = [idx for idx, iso in enumerate(primarySpec.isotopeCodes)
                                             if iso == thisIsoCode]

                # disallow any pulldowns that will give more selections than available target axes
                discard: bool = (primaryIsoCount.get(thisIsoCode, 0) and
                                 (_isoCount.get(thisIsoCode, 0) >= primaryIsoCount[thisIsoCode]))
                if discard:
                    continue

                specRow += 1
                _isoLabel = Label(spectrumFrame, text=thisIsoCode, grid=(specRow, _ISONUM))
                _ppmLabel = Label(spectrumFrame, text='%.3f' % peak.ppmPositions[ind], grid=(specRow, _OLDPPMNUM))

                if (peak == self.primaryPeak):
                    # no selections are required
                    Label(spectrumFrame, text=thisSpec.axisCodes[ind], grid=(specRow, _AXISNUM))
                else:
                    # create the first pulldown/label based on the count of the isotope-code in this peak
                    callbackId: _KeyPeak = _KeyPeak(peakId=peak.id, ind=ind)  # NOT the real-row from the first pulldown
                    targetAxis: _IdPulldownList | _IdLabel
                    realInd: int

                    if (primaryIsoCount.get(thisIsoCode, 0) and
                            (thisSpecIsoCount.get(thisIsoCode, 0) > primaryIsoCount.get(thisIsoCode, 0))):
                        # requires a pulldown
                        codes: list[str] = [thisSpec.axisCodes[ii]
                                            for ii, iso in enumerate(thisSpec.isotopeCodes)
                                            if iso == thisIsoCode]
                        targetAxis = _IdPulldownList(spectrumFrame, grid=(specRow, _AXISNUM),
                                                     peakType=_PeakType.target, index=ind)
                        # populate with the axisCodes matching this isotopeCode
                        targetAxis.setData(codes)
                        targetAxis.setIndex(_isoCount.get(thisIsoCode, 0))
                        _linkedPulldownId: _KeyPeak = _KeyPeak(peakId=peak.id, peakType=_PeakType.target,
                                                               isotopeCode=thisIsoCode)
                        targetAxis.setCallback(partial(self._changeAxisOption,
                                                       targetAxis,
                                                       _linkedPulldownId,
                                                       thisIsoCode,
                                                       callbackId))
                        realInd = thisSpec.axisCodes.index(codes[_isoCount.get(thisIsoCode, 0)])
                        _isoCount[thisIsoCode] += 1
                        # the left (target) pulldown identifier
                        self._linkedPulldowns[_linkedPulldownId].append(targetAxis)
                    else:
                        # does not require a pulldown - just a label
                        targetAxis = _IdLabel(spectrumFrame, text=thisSpec.axisCodes[ind], grid=(specRow, _AXISNUM),
                                              peakType=_PeakType.target)
                        realInd = ind

                    matchToAxis: _IdPulldownList | _IdLabel | None = None
                    ppmLabel: Label | None = None
                    ppmDelta: Label | None = None
                    dim: int = 0
                    checkBox: CheckBox | None = None
                    # create the second pulldown/label based on the count of the isotope-code in the primary-peak
                    if thisIsoIndices:
                        checked: bool = thisSpec.axisCodes[ind] != 'intensity'
                        checkBox = self._spectraCheckBoxes[callbackId] = CheckBox(spectrumFrame,
                                                                                  grid=(specRow, _CHECKNUM),
                                                                                  vAlign='c', hAlign='c',
                                                                                  checked=checked,
                                                                                  callback=self._selectCheckBoxCallback)
                        if len(thisIsoIndices) > 1:
                            # requires a pulldown
                            dim = thisIsoIndices[min(_indCount.get(thisIsoCode, 0),
                                                     len(thisIsoIndices) - 1)]  # index of axis in primary
                            # populate with the axisCodes matching the isotopeCodes
                            matchCodes: list[str] = [primarySpec.axisCodes[ii] for ii, ind_val in
                                                     enumerate(primaryIsotopeIndices)
                                                     if ind_val is not None]
                            matchToAxis = _IdPulldownList(spectrumFrame, grid=(specRow, _MATCHAXISNUM),
                                                          peakType=_PeakType.match, index=ind)
                            matchToAxis.setData(matchCodes)
                            matchToAxis.setIndex(_indCount.get(thisIsoCode, 0))
                            _linkedPulldownId = _KeyPeak(peakId=peak.id, peakType=_PeakType.match,
                                                         isotopeCode=thisIsoCode)
                            matchToAxis.setCallback(partial(self._changeAxisOption,
                                                            matchToAxis,
                                                            _linkedPulldownId,
                                                            thisIsoCode,
                                                            callbackId))
                            _indCount[thisIsoCode] += 1
                            # the right (match) pulldown identifier
                            self._linkedPulldowns[_linkedPulldownId].append(matchToAxis)
                        else:
                            # does not require a pulldown - just a label
                            dim = thisIsoIndices[0]
                            matchToAxis = _IdLabel(spectrumFrame, text=primarySpec.axisCodes[dim],
                                                   grid=(specRow, _MATCHAXISNUM),
                                                   peakType=_PeakType.match)

                        ppmLabel = Label(spectrumFrame, text=f'{self.primaryPeak.ppmPositions[dim]:.3f}',
                                         grid=(specRow, _NEWPPMNUM))
                        ppmDelta = Label(spectrumFrame,
                                         text=f'{self.primaryPeak.ppmPositions[dim] - peak.ppmPositions[ind]:.3f}',
                                         grid=(specRow, _DELTANUM))

                    # create the callback information for the pulldowns
                    self._matchToAxisPulldowns[callbackId] = _MatchPeak(target=targetAxis,
                                                                        match=matchToAxis,
                                                                        checkBox=checkBox,
                                                                        origPpmLabel=_ppmLabel,
                                                                        ppmLabel=ppmLabel,
                                                                        ppmDelta=ppmDelta,
                                                                        peak=peak,
                                                                        dim=dim,
                                                                        ind=ind,
                                                                        realInd=realInd,
                                                                        )
            if peak.spectrum.dimensionCount == 1:
                # do the intensity
                # NOTE:ED - this could be removed, need to check the validity of calibrating the `intensity`
                specRow += 1
                dim = 1
                fromPos: tuple[float, ...] = self.primaryPeak.position + (self.primaryPeak.height,)
                toPos: tuple[float, ...] = peak.position + (peak.height,)
                targetAxis = _IdLabel(spectrumFrame, text='intensity', grid=(specRow, _AXISNUM),
                                      peakType=_PeakType.target)
                matchToAxis = _IdLabel(spectrumFrame, text='', grid=(specRow, _MATCHAXISNUM),
                                       peakType=_PeakType.match)
                _ppmLabel = Label(spectrumFrame, text=f'{toPos[dim]:.3f}', grid=(specRow, _OLDPPMNUM))
                checkBox = None

                if (peak != self.primaryPeak):
                    ppmLabel = Label(spectrumFrame, text=f'{fromPos[dim]:.3f}', grid=(specRow, _NEWPPMNUM))
                    ppmDelta = Label(spectrumFrame, text=f'{fromPos[dim] - toPos[dim]:.3f}',
                                     grid=(specRow, _DELTANUM))

                    # callbackId = f'{peak.id}_1'
                    callbackId = _KeyPeak(peakId=peak.id, ind=1)
                    if self.primaryPeak.spectrum.dimensionCount == 1:
                        checkBox = self._spectraCheckBoxes[callbackId] = CheckBox(spectrumFrame,
                                                                                  grid=(specRow, _CHECKNUM),
                                                                                  vAlign='t', hAlign='c',
                                                                                  checked=False,
                                                                                  callback=self._selectCheckBoxCallback)
                    # create the callback information for the pulldowns
                    self._matchToAxisPulldowns[callbackId] = _MatchPeak(target=targetAxis,
                                                                        match=matchToAxis,
                                                                        checkBox=checkBox,
                                                                        origPpmLabel=_ppmLabel,
                                                                        ppmLabel=ppmLabel,
                                                                        ppmDelta=ppmDelta,
                                                                        peak=peak,
                                                                        dim=1,
                                                                        ind=1,
                                                                        realInd=1,
                                                                        )
            if peak == self.primaryPeak:
                # get the co-ordinates for the bounding box
                end = _ItemPosition(row=specRow + 1, column=7)
            specRow += 1

        for linkId in self._linkedPulldowns:
            self._colourPulldowns(linkId)
        self._backgroundFrame.setCorners(start, end)

        with self.blockWidgetSignals():
            # Restore the state of any existing checkboxes
            for checkCallBackId, checkBox in self._spectraCheckBoxes.items():
                if (state := self._lastChecked.get(checkCallBackId)) is not None:
                    checkBox.setChecked(state)

    def _selectCheckBoxCallback(self) -> None:
        """
        Callback function triggered when any checkbox associated with spectrum axes changes its state.

        This method iterates through all groups of linked pulldowns and triggers a recoloring
        operation to reflect the updated selection status of axes, potentially highlighting
        conflicts or duplicates. It also updates the stored state of all checkboxes.
        """
        # Iterate through each group of linked pulldowns (identified by linkId) and recolour
        for linkId in self._linkedPulldowns:
            self._colourPulldowns(linkId)
        # Update the internal record of the state of all checkboxes.
        for checkCallBackId, checkBox in self._spectraCheckBoxes.items():
            self._lastChecked[checkCallBackId] = checkBox.isChecked()

    def _accept(self) -> None:
        """
        Handle pressing the `accept` (OK) button.
        Performs the calibration based on user selections.
        """
        with (handleDialogApply(self) as _):  # Type of _ not specified, assume Any
            if self.primaryPeak is None:
                getLogger().warning("Primary peak not selected. Cannot perform calibration.")
                return

            if self.primaryPeak.spectrum.dimensionCount == 1:
                # get the primary 1d properties as an `Nd` (position, height)
                primaryPos: tuple[float, ...] = self.primaryPeak.ppmPositions + (self.primaryPeak.height,)
            else:
                primaryPos = self.primaryPeak.ppmPositions

            warning = OrderedSet()
            # get the list of visible spectra in this strip
            spectraCalList: list[tuple[Any, str, Sequence[float], list[
                float | None]]] = []  # (specViewPid, spectrumPid, fromPeakPos, toPeakPos)
            for peak in self.peaks:
                if peak != self.primaryPeak:
                    peakToPos: list[float | None]
                    peakOldPos: Sequence[float]
                    if peak.spectrum.dimensionCount == 1:
                        # get the 1d properties as an `Nd` (position, height)
                        peakToPos = [None, None]
                        peakOldPos = peak.ppmPositions + (peak.height,)
                    else:
                        peakToPos = [None] * len(peak.position)
                        peakOldPos = peak.position

                    for ii in range(len(peakToPos)):
                        # iterate through the axes
                        callbackId = _KeyPeak(peakId=peak.id, ind=ii)  # NOT the real-row from the first pulldown
                        checkBox: CheckBox | None = self._spectraCheckBoxes.get(callbackId)
                        foundMatchPeak: _MatchPeak | None = self._matchToAxisPulldowns.get(callbackId)

                        if checkBox and checkBox.isChecked() and foundMatchPeak:
                            # only those with checkboxes will generate potential warnings
                            dim: int = foundMatchPeak.dim
                            realInd: int = foundMatchPeak.realInd
                            peakToPos[realInd] = primaryPos[dim]

                            # iterate through the linked pulldowns for this peak, and add a warning of more than one
                            # has been selected (via checkbox)
                            for linkId in filter(lambda link: link.peakId == peak.id, self._linkedPulldowns):
                                pulldowns: list[_IdPulldownList] = self._linkedPulldowns[linkId]
                                for pulldown in pulldowns:
                                    # get the list of pulldowns with the same axisCode
                                    similar = list(filter(lambda combo: combo.get() == pulldown.get(), pulldowns))
                                    selected: list[bool] = [
                                        self._spectraCheckBoxes[
                                            _KeyPeak(peakId=linkId.peakId, ind=pp._index)].isChecked()
                                        for pp in similar]
                                    # add a warning of more than one selected, implies a conflict
                                    if len(list(filter(None, selected))) > 1:
                                        warning.add(peak.id)

                    if any(pp is not None for pp in peakToPos):
                        # add the required calibrate-action to the list
                        spectraCalList.append((None, peak.spectrum.pid,
                                               peakOldPos, peakToPos))

            if warning:
                warningStr = ''.join(f'  {pp}\n' for pp in warning)
                _msg: str = (f'There are conflicting axis-codes in the selected peaks:\n'
                             f'{warningStr}\nDo you want to Continue?')
                if not showYesNoWarning('Warning', _msg):
                    return

            if spectraCalList:
                with undoStackBlocking() as addUndoItem:
                    # perform the calibration on the selected spectra
                    self._calibrateSpectra(spectraCalList, 1.0)
                    # add an undo item to the stack
                    addUndoItem(undo=partial(self._calibrateSpectra, spectraCalList, -1.0),
                                redo=partial(self._calibrateSpectra, spectraCalList, 1.0))
                self.accept()

        # clear the last selected items
        self.strip._lastClickedObjects = None

    def _reject(self) -> None:
        """
        Handle pressing the `reject` (Cancel) button.
        """
        self.reject()
        # clear the last selected items
        self.strip._lastClickedObjects = None

    def _changeAxisOption(self, _widget: _IdPulldownList, linkId: _KeyPeak, isoCode: str,
                          callbackId: _KeyPeak, _value: Any) -> None:
        """
        Handle the new selection in a pulldown list, updating related labels and colours.

        :param _widget: The pulldown widget that triggered the callback (not directly used).
        :type _widget: _IdPulldownList
        :param linkId: The _KeyPeak identifying the linked pulldown group.
        :type linkId: _KeyPeak
        :param isoCode: The isotope code associated with the axis option.
        :type isoCode: str
        :param callbackId: The _KeyPeak identifying the specific _MatchPeak entry.
        :type callbackId: _KeyPeak
        :param _value: The new value of the pulldown (not directly used, value is retrieved from widget).
        :type _value: Any
        """
        try:
            matchedPeak: _MatchPeak = self._matchToAxisPulldowns[callbackId]
            targetAxis: _IdPulldownList | _IdLabel = matchedPeak.target
            matchToAxis: _IdPulldownList | _IdLabel | None = matchedPeak.match
            peak: Peak = matchedPeak.peak
            origPpmLabel: Label = matchedPeak.origPpmLabel
            ppmLabel: Label | None = matchedPeak.ppmLabel
            ppmDelta: Label | None = matchedPeak.ppmDelta
            realInd = peak.axisCodes.index(targetAxis.get())
            # update the labels
            origPpmLabel.setText(f'{peak.ppmPositions[realInd]:.3f}')
            if self.primaryPeak is None:
                getLogger().debug("Match axis or primary peak not suitable for update.")
                return  # Cannot proceed if matchToAxis is not a PulldownList or primaryPeak is missing
            dim: int = self.primaryPeak.axisCodes.index(matchToAxis.get())
            if ppmLabel:
                ppmLabel.setText(f'{self.primaryPeak.ppmPositions[dim]:.3f}')
            if ppmDelta:
                ppmDelta.setText(f'{self.primaryPeak.ppmPositions[dim] - peak.ppmPositions[realInd]:.3f}')
        except Exception as es:
            getLogger().debug(f'{es}')
        finally:
            self._colourPulldowns(linkId)

    def _colourPulldowns(self, linkId: _KeyPeak) -> None:
        """
        Recolour the pulldowns based on the axisCodes selected and the current axis selection via checkboxes.
        Highlights duplicate selections or selections in a conflicting state.

        :param linkId: The _KeyPeak identifying the group of linked pulldowns to colour.
        :type linkId: _KeyPeak
        """
        pulldowns: list[_IdPulldownList] = self._linkedPulldowns[linkId]
        selected: list[bool] = [self._spectraCheckBoxes[_KeyPeak(peakId=linkId.peakId, ind=pp._index)].isChecked()
                                for pp in pulldowns]
        # all the pulldowns of the same _linkedPulldowns will have the same list
        if not pulldowns:
            return

        referencePulldown = pulldowns[0]
        axisCodes = referencePulldown.getAsList()
        refsRed = np.zeros((len(axisCodes), len(pulldowns)), dtype=bool)
        refsAmber = np.zeros((len(axisCodes), len(pulldowns)), dtype=bool)
        for axIndex, axisCode in enumerate(axisCodes):
            for pdIndex, pulldown in enumerate(pulldowns):
                if pulldown.get() == axisCode:
                    if selected[pdIndex]:
                        refsRed[axIndex, pdIndex] = True
                    refsAmber[axIndex, pdIndex] = True

        for pulldown in pulldowns:
            model: QtGui.QStandardItemModel = pulldown.model()
            item: QtGui.QStandardItem | None
            for ind in range(pulldown.count()):
                if (item := model.item(ind)) is not None:
                    if refsRed.sum(axis=1)[ind] > 1:
                        item.setData(_BADCOLOR, role=QtCore.Qt.ForegroundRole)
                    elif refsAmber.sum(axis=1)[ind] > 1:
                        item.setData(_INTERMEDIATECOLOR, role=QtCore.Qt.ForegroundRole)
                    else:
                        # clears the colour and reverts to palette.Text
                        item.setData(None, role=QtCore.Qt.ForegroundRole)
            # force a repaint to set the colour of the selected index to update correctly
            pulldown.repaint()

    @staticmethod
    def _calibrateSpectra(spectra: list[tuple[Any, str, Sequence[float], list[float | None]]],
                          direction: float = 1.0) -> None:
        """
        Perform the actual spectrum calibration based on the provided list of spectra.

        :param spectra: A list of tuples, each containing (spectrumViewPid, spectrumPid, fromPeakPos, toPeakPos).
        :type spectra: list[tuple[Any, str, Sequence[float], list[float | None]]]
        :param direction: Direction of calibration (1.0 for forward, -1.0 for undo/reverse).
        :type direction: float
        """
        # not sure whether this should be in a .lib module
        from ccpn.framework.Application import getProject

        if not (project := getProject()):
            # project doesn't exist, no calibration
            return

        for specViewPid, spectrumPid, fromPeakPos, toPeakPos in spectra:
            if not (spectrum := project.getByPid(spectrumPid)):
                # no spectrum, skip this calibration
                continue
            specView: Any | None = project.getByPid(specViewPid)
            if direction > 0:
                fromPos, toPos = fromPeakPos, toPeakPos
            else:
                toPos, fromPos = fromPeakPos, toPeakPos

            if spectrum.dimensionCount == 1:
                # Handle 1D specific calibration for position and height
                if fromPos[0] is not None and toPos[0] is not None:
                    # is 1D spectrum, dimension 0 - position
                    _calibrateX1D(spectrum, fromPos[0], toPos[0])
                if fromPos[1] is not None and toPos[1] is not None:
                    # is 1D spectrum, dimension 1 - height (intensity)
                    _calibrateY1D(spectrum, fromPos[1], toPos[1])

                if specView and not specView.isDeleted:
                    specView.buildContours = True
                    specView.refreshData()
            else:
                # Handle ND calibration for each dimension
                for ii in range(len(fromPos)):
                    if fromPos[ii] is not None and toPos[ii] is not None:
                        # Ensure current_from_pos[ii] is float for _calibrateNDAxis
                        _calibrateNDAxis(spectrum, ii, fromPos[ii], toPos[ii])


#=========================================================================================
# CalibrateSpectraFromPeaksPopup1d
#=========================================================================================

# class CalibrateSpectraFromPeaksPopup1d(CalibrateSpectraFromPeaksPopupNd):
#     """Popup to allow calibrating of spectra from a selection of peaks in the same spectrumDisplay
#     Specifically for a 1d spectrumDisplay
#
#     Calibration is applied to the current selection of peaks
#
#     A single peak is selected as the primary peak from the pullDown,
#     all other spectra are updated to align peaks with the primary peak
#     """
#
#     def _accept(self):
#         self.accept()
#
#         with handleDialogApply(self) as error:
#             fromPos = self.primaryPeak.position + (self.primaryPeak.height,)
#
#             # add an undo item to the stack
#             with undoStackBlocking() as addUndoItem:
#                 # get the list of visible spectra in this strip
#                 spectraCalList = [(specView, specView.spectrum,
#                                    self.spectrumCount[specView.spectrum].position + (
#                                        self.spectrumCount[specView.spectrum].height,),
#                                    fromPos,
#                                    self._spectraCheckBoxes[
#                                        str(self.spectrumCount[specView.spectrum].id) + str(0)].isChecked(),
#                                    self._spectraCheckBoxes[
#                                        str(self.spectrumCount[specView.spectrum].id) + str(1)].isChecked())
#                                   for specView in self.strip.spectrumViews
#                                   if specView.isDisplayed
#                                   and specView.spectrum in self.spectrumCount
#                                   and self.spectrumCount[specView.spectrum] is not self.primaryPeak]
#
#                 self._calibrateSpectra(spectraCalList, self.strip, 1.0)
#
#                 addUndoItem(undo=partial(self._calibrateSpectra, spectraCalList, self.strip, -1.0),
#                             redo=partial(self._calibrateSpectra, spectraCalList, self.strip, 1.0))
#
#         # clear the last selected items
#         self.strip._lastClickedObjects = None
#
#     def _calibrateSpectra(self, spectra, strip, direction=1.0):
#
#         for specView, spectrum, fromPeakPos, toPeakPos, doX, doY in spectra:
#
#             if direction > 0:
#                 fromPos, toPos = fromPeakPos, toPeakPos
#             else:
#                 toPos, fromPos = fromPeakPos, toPeakPos
#
#             if spectrum.dimensionCount == 1:
#                 if doX:
#                     _calibrateX1D(spectrum, fromPos[0], toPos[0])
#                 if doY:
#                     _calibrateY1D(spectrum, fromPos[1], toPos[1])
#
#                 if specView and not specView.isDeleted:
#                     specView.buildContours = True
#                     specView.refreshData()
#             else:
#                 for ii in range(len(fromPos)):
#                     if fromPos[ii] is not None and toPos[ii] is not None:
#                         _calibrateNDAxis(spectrum, ii, fromPos[ii], toPos[ii])
#
#     def _fillSpectrumFrame(self):
#         """Rebuild the spectrum frame as the primary peak has been updated
#         """
#         spectrumFrame = self._spectrumFrame
#         layout = spectrumFrame.getLayout()
#         while layout.count():
#             wid = layout.takeAt(0).widget()
#             wid.setVisible(False)
#             wid.setParent(None)
#
#         fromPos = self.primaryPeak.position + (self.primaryPeak.height,)
#         start = end = _ItemPosition(0, 0)
#
#         self._spectraCheckBoxes = {}
#         specRow = 0
#         HLine(spectrumFrame, grid=(specRow, _CHECKNUM), gridSpan=(1, 6), colour=getColours()[DIVIDER],
#               height=_HLINE_HEIGHT)
#
#         specRow += 1
#         _includeAxisLabel = Label(spectrumFrame, text="Include\nAxis", grid=(specRow, _CHECKNUM), hAlign='c')
#         _axisLabel = Label(spectrumFrame, text="AxisCode", grid=(specRow, _AXISNUM), hAlign='c')
#         _isoLabel = Label(spectrumFrame, text="Isotope\nCode", grid=(specRow, 2), hAlign='c')
#         _oldPpmLabel = Label(spectrumFrame, text="Original\nppmPosition", grid=(specRow, 3), hAlign='c')
#         _newPpmLabel = Label(spectrumFrame, text="New\nppmPosition", grid=(specRow, 4), hAlign='c')
#         _deltaLabel = Label(spectrumFrame, text="Delta", grid=(specRow, 5), hAlign='c')
#
#         specRow += 1
#         HLine(spectrumFrame, grid=(specRow, _CHECKNUM), gridSpan=(1, 6), colour=getColours()[SOFTDIVIDER],
#               height=_HLINE_HEIGHT)
#
#         specRow += 1
#         for peak in self.peaks:
#
#             toPos = peak.position + (peak.height,)
#
#             if specRow > 3:
#                 # add soft-divider
#                 HLine(spectrumFrame, grid=(specRow, _CHECKNUM), gridSpan=(1, 6), colour=getColours()[SOFTDIVIDER],
#                       height=_HLINE_HEIGHT)
#
#             specRow += 1
#             Label(spectrumFrame, text=f'Peak: {str(peak.id)}', grid=(specRow, _CHECKNUM), gridSpan=(1, 6), bold=True)
#
#             if peak == self.primaryPeak:
#                 # get the co-ordinates for the bounding box
#                 start = _ItemPosition(row=specRow, column=0)
#
#             # do the X axis - the defined ppm axisCode
#             specRow += 1
#             dim = 0
#             Label(spectrumFrame, text=peak.peakList.spectrum.axisCodes[dim], grid=(specRow, _AXISNUM))
#             Label(spectrumFrame, text=peak.peakList.spectrum.isotopeCodes[dim], grid=(specRow, 2))
#             Label(spectrumFrame, text='%.3f' % toPos[dim], grid=(specRow, 3))
#
#             if (peak != self.primaryPeak):
#                 Label(spectrumFrame, text='%.3f' % fromPos[dim], grid=(specRow, 4))
#                 Label(spectrumFrame, text='%.3f' % (fromPos[dim] - toPos[dim]), grid=(specRow, 5))
#
#                 self._spectraCheckBoxes[str(peak.id) + str(dim)] = CheckBox(spectrumFrame, grid=(specRow, _CHECKNUM),
#                                                                             vAlign='t', hAlign='c', checked=True)
#
#             if peak.spectrum.dimensionCount == 1:
#                 # do the intensity
#                 specRow += 1
#                 dim = 1
#                 Label(spectrumFrame, text='intensity', grid=(specRow, _AXISNUM))
#                 Label(spectrumFrame, text='', grid=(specRow, 2))
#                 Label(spectrumFrame, text='%.3f' % toPos[dim], grid=(specRow, 3))
#
#                 if (peak != self.primaryPeak):
#                     Label(spectrumFrame, text='%.3f' % fromPos[dim], grid=(specRow, 4))
#                     Label(spectrumFrame, text='%.3f' % (fromPos[dim] - toPos[dim]), grid=(specRow, 5))
#
#                     self._spectraCheckBoxes[str(peak.id) + str(dim)] = CheckBox(spectrumFrame,
#                                                                                 grid=(specRow, _CHECKNUM),
#                                                                                 vAlign='t', hAlign='c', checked=False)
#
#             if peak == self.primaryPeak:
#                 # get the co-ordinates for the bounding box
#                 end = _ItemPosition(row=specRow + 1, column=6)
#             specRow += 1
#         self._backgroundFrame.setCorners(start, end)


#=========================================================================================
# _GridLayoutUnderlay
#=========================================================================================

class _GridLayoutUnderlay(QtWidgets.QWidget):
    """
    Underlay widget that draws a border around the rows/columns defining the selected object,
    ensuring a clean visual edge.

    :ivar start: Top-left corner of the selection.
    :vartype start: _ItemPosition
    :ivar end: Bottom-right corner of the selection.
    :vartype end: _ItemPosition
    :ivar _grid_layout: Weak reference to the associated QGridLayout.
    :vartype _grid_layout: QtWidgets.QGridLayout | None
    :ivar _background_rect: Rectangle defining the background highlight area.
    :vartype _background_rect: QtCore.QRect
    :ivar _borderHeight: Height of the border padding.
    :vartype _borderHeight: int
    :ivar _backgroundColour: The QColor used for the background highlight.
    :vartype _backgroundColour: QtGui.QColor
    :ivar _highlightBrush: The QBrush used for painting the highlight.
    :vartype _highlightBrush: QtGui.QBrush
    :ivar _repaint: Internal flag to indicate if a repaint is needed.
    :vartype _repaint: bool
    """

    start: _ItemPosition = _ItemPosition(0, 0)
    end: _ItemPosition = _ItemPosition(0, 0)
    _grid_layout: QtWidgets.QGridLayout | None = WeakRefDescriptor()  # Can be None initially
    _background_rect: QtCore.QRect = QtCore.QRect(0, 0, 0, 0)
    _borderHeight: int = 0
    _repaint: bool = False

    def __init__(self, parent: QtWidgets.QWidget, borderHeight: int = 0):
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
        self._repaint = True  # Ensure initial repaint

    def setSourceLayout(self, layout: QtWidgets.QGridLayout) -> None:
        """
        Link an existing QGridLayout to this widget.

        :param layout: The layout to associate with this widget.
        :type layout: QtWidgets.QGridLayout
        :raises TypeError: If the layout is not a QGridLayout.
        """
        if not isinstance(layout, QtWidgets.QGridLayout):
            raise TypeError('Expected a QGridLayout')
        self._grid_layout = layout

    def setCorners(self, start: _ItemPosition, end: _ItemPosition) -> None:
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
        self.update()  # Request a repaint

    def resizeEvent(self, ev: QtGui.QResizeEvent) -> None:
        """
        Handle widget resizing when the parent resizes.

        :param ev: Resize event.
        :type ev: QtGui.QResizeEvent
        """
        super().resizeEvent(ev)
        if (parent := self.parent()) and isinstance(parent, QtWidgets.QWidget):
            # sanity check to ensure has a `rect`
            self.setGeometry(QtCore.QRect(parent.rect()))
        self._repaint = True
        self.update()  # Request a repaint

    def _resizeBackgroundRect(self) -> None:
        """
        Calculates the bounding rectangle for selected grid cells within a QGridLayout
        and updates a background rectangle.

        This method determines the top-left and bottom-right coordinates of the
        specified grid cells. It creates internal arrays for row and column positions
        that are one dimension larger than the grid layout. This allows the last
        element in these arrays to represent the bottom-right edge of the final
        row or column in the grid, ensuring accurate bounding box calculation.
        """
        if not self._repaint:
            return
        # Ensure the layout has been initialized and contains items
        if not self._grid_layout:
            return
        layout: QtWidgets.QGridLayout = self._grid_layout
        row_count: int = layout.rowCount()
        col_count: int = layout.columnCount()
        # Initialize with -1, indicating no valid position found yet
        rSize: NDArray[np.int32] = np.full(row_count + 1, -1, dtype=np.int32)
        cSize: NDArray[np.int32] = np.full(col_count + 1, -1, dtype=np.int32)

        for itmNum in range(layout.count()):
            if (itm := layout.itemAt(itmNum)):
                row, col, spanY, spanX = layout.getItemPosition(itmNum)
                rect: QtCore.QRect = itm.geometry()

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
        # _removeNull is performed in-place
        if self._removeNull(rSize) is None or self._removeNull(cSize) is None:
            self._background_rect = QtCore.QRect(0, 0, 0, 0)  # Reset if no valid items
            return
        # Ensure indices are within the bounds of the filled arrays
        start_col_idx = self.start.column
        end_col_idx = min(self.end.column, len(cSize) - 1)
        start_row_idx = self.start.row
        end_row_idx = min(self.end.row, len(rSize) - 1)
        # Calculate the bounding rectangle
        self._background_rect = QtCore.QRect(
                cSize[start_col_idx],
                rSize[start_row_idx] - self._borderHeight,
                cSize[end_col_idx] - cSize[start_col_idx],
                rSize[end_row_idx] - rSize[start_row_idx] + (2 * self._borderHeight)
                )
        if (parent := self.parent()) and isinstance(parent, QtWidgets.QWidget):
            # sanity check to ensure has a `rect`
            if parent.rect() != self._background_rect:
                return
        self._repaint = False

    @staticmethod
    def _removeNull(arr: NDArray[np.int32]) -> NDArray[np.int32] | None:
        """
        Fill in missing (-1) values in the array using forward fill and then backward fill.
        This handles cases where initial items might not be at index 0.
        The fill is performed in-place.

        :param arr: Array with potential -1 values.
        :type arr: NDArray[np.int32]
        :return: Filled array or None if no valid values are present.
        :rtype: NDArray[np.int32] | None
        """
        is_valid = (arr != -1)
        if not np.any(is_valid):
            return None
        # Backward fill: for any -1s at the beginning (if first elements are -1)
        # Find the first non -1 value and fill backwards
        _first_valid_index = np.argmax(is_valid)
        arr[:_first_valid_index] = arr[_first_valid_index]
        is_fill = (arr != -1)
        # Forward fill: fill all other valid column-positions to any invalid columns to their right
        index = np.where(is_fill, np.arange(len(arr)), 0)
        np.maximum.accumulate(index, out=index)
        arr[:] = arr[index]
        return arr

    def paintEvent(self, ev: QtGui.QPaintEvent) -> None:
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
