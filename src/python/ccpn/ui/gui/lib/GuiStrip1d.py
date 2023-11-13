"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2023-10-16 13:13:51 +0100 (Mon, October 16, 2023) $"
__version__ = "$Revision: 3.2.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets
from ccpn.util.Colour import hexToRgbRatio
from functools import partial
from ccpn.core.PeakList import PeakList
from ccpn.util import Phasing
from ccpn.ui.gui.lib.GuiStrip import GuiStrip, DefaultMenu, PeakMenu, \
    IntegralMenu, MultipletMenu, PhasingMenu, AxisMenu
from ccpn.ui.gui.widgets.PlaneToolbar import StripHeaderWidget, StripLabelWidget
import numpy as np
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.lib.GuiStripContextMenus import _get1dPhasingMenu, _get1dDefaultMenu, \
    _get1dPeakMenu, _get1dIntegralMenu, _get1dMultipletMenu, _get1dAxisMenu
from ccpn.ui.gui.widgets.Frame import OpenGLOverlayFrame
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.util.Colour import colorSchemeTable


class GuiStrip1d(GuiStrip):
    """Strip class for display of 1D spectra

    This module inherits the following attributes from the Strip wrapper class:

    axisCodes         Fixed string Axis codes in original display order
                        :return <tuple>:(X, Y, Z1, Z2, ...)
    axisOrder         String Axis codes in display order, determine axis display order
                        axisOrder = <sequence>:(X, Y, Z1, Z2, ...)
                        :return <tuple>:(X, Y, Z1, Z2, ...)
    positions         Axis centre positions, in display order
                        positions = <Tuple>
                        :return <Tuple>:(<float>, ...)
    widths            Axis display widths, in display order
                        widths = <Tuple>
                        :return <Tuple>:(<float>, ...)
    units             Axis units, in display order
                        :return <Tuple>
    spectra           List of the spectra attached to the strip
                      (whether display is currently turned on or not)
                        :return <Tuple>:(<Spectrum>, ...)

    delete            Delete a strip
    clone             Create new strip that duplicates this one, appending it at the end
    moveTo            Move strip to index newIndex in orderedStrips
                        moveTo(newIndex:int)
                          :param newIndex:<int> new index position
    findAxis          Find axis
                        findAxis(axisCode)
                          :param axisCode:
                          :return axis
    displaySpectrum   Display additional spectrum on strip, with spectrum axes ordered according to axisOrder
                        displaySpectrum(spectrum:Spectrum, axisOrder:Sequence=()
                          :param spectrum:<Spectrum> additional spectrum to display
                          :param axisOrder:<Sequence>=() new axis ordering
    peakIsInPlane     Return whether the peak is in currently displayed planes for strip
                        peakIsInPlane(peak:Peak)
                          :param peak:<Peak> peak of interest
                          :return <bool>
    peakIsInFlankingPlane   Return whether the peak is in planes flanking currently displayed planes for strip
                              peakIsInFlankingPlane(peak:Peak)
                                :param peak:<Peak> peak of interest
                                :return <bool>
    peakPickPosition  Pick peak at position for all spectra currently displayed in strip
                        peakPickPosition(position:List[float])
                          :param position:<List> coordinates to test
                          :return <Tuple>:(<Peak>, ...)
    peakPickRegion    Peak pick all spectra currently displayed in strip in selectedRegion
                        selectedRegion:List[List[float])
                          :param selectedRegion:<List>  of <List> of coordinates to test
                          :return <Tuple>:(<Peak>, ...)
    """

    # MAXPEAKLABELTYPES = 6
    # MAXPEAKSYMBOLTYPES = 1

    def __init__(self, spectrumDisplay):
        """
        Initialise Nd spectra object

        :param spectrumDisplay Main spectrum display Module object
        """
        GuiStrip.__init__(self, spectrumDisplay)

        # self.viewBox.invertX()
        # self.plotWidget.showGrid(x=False, y=False)
        # self.gridShown = True

        # self.viewBox.menu = _get1dDefaultMenu(self)
        # self._defaultMenu = self.viewBox.menu

        # keep a common stackItem for both menus
        self._stackSpectraMenuItem = None

        self._defaultMenu = _get1dDefaultMenu(self)
        self._phasingMenu = _get1dPhasingMenu(self)
        self._peakMenu = _get1dPeakMenu(self)
        self._integralMenu = _get1dIntegralMenu(self)
        self._multipletMenu = _get1dMultipletMenu(self)
        self._axisMenu = _get1dAxisMenu(self)

        self._contextMenus.update({DefaultMenu  : self._defaultMenu,
                                   PhasingMenu  : self._phasingMenu,
                                   PeakMenu     : self._peakMenu,
                                   IntegralMenu : self._integralMenu,
                                   MultipletMenu: self._multipletMenu,
                                   AxisMenu     : self._axisMenu
                                   })

        # self.plotWidget.plotItem.setAcceptDrops(True)
        self.spectrumIndex = 0
        self.peakItems = {}
        # self._hideCrosshair()
        self.calibrateX1DWidgets = None
        self.calibrateY1DWidgets = None
        self.offsetWidget = None
        self.offsetValue = (0.0, 0.0)

        self.widgetIndex = 4  #start adding widgets from row 4

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # TEST: ED new plane widgets

        self.planeToolbar = None
        # set the axis controlled by the wheelMouse events
        self.activePlaneAxis = None
        self.zPlaneFrame = None

        # a large(ish) unbound widget to contain the text - may need more rows
        self._frameGuide = OpenGLOverlayFrame(self, setLayout=True)
        # self._frameGuide.setFixedSize(400, 400)

        # add spacer to the top left corner
        # self._frameGuide.addSpacer(8, 8, grid=(1, 0))
        row = 2

        self.stripLabel = StripLabelWidget(qtParent=self._frameGuide, mainWindow=self.mainWindow, strip=self, grid=(row, 1), gridSpan=(1, 1))
        row += 1
        # set the ID label in the new widget
        self.stripLabel._populate()

        self.header = StripHeaderWidget(qtParent=self._frameGuide, mainWindow=self.mainWindow, strip=self, grid=(row, 1), gridSpan=(1, 1))
        row += 1

        Spacer(self._frameGuide, 1, 1, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding, grid=(row, 2))

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        self.spectrumDisplay.phasingFrame.applyCallback = self._applyPhasing
        self.spectrumDisplay.phasingFrame.applyButton.setEnabled(True)
        self._noiseThresholdLines = {}
        self._pickingExclusionAreas = {}

        self._setStripTiling()

    def close(self):
        """Clean up and close
        """
        try:
            del self._defaultMenu
            del self._phasingMenu
            del self._peakMenu
            del self._integralMenu
            del self._multipletMenu
            del self._axisMenu
            del self._contextMenus
        except Exception:
            getLogger().debug(f'there was a problem cleaning-up strip {self}')
        else:
            getLogger().debug(f'cleaning-up strip {self}')

        super().close()

    @property
    def symbolType(self):
        """Get the symbol type for the strip
        """
        return self._CcpnGLWidget._symbolType

    @symbolType.setter
    def symbolType(self, value):
        """Set the symbol type for the strip
        """
        if not isinstance(value, int):
            raise TypeError('Error: symbolType not an int')

        oldValue = self._CcpnGLWidget._symbolType
        self._CcpnGLWidget._symbolType = value if (value in range(self.spectrumDisplay.MAXPEAKSYMBOLTYPES)) else 0
        if self._CcpnGLWidget._symbolType in [1, 2]:
            self._CcpnGLWidget._symbolType = 3
        if value != oldValue:
            self._setSymbolType()
            if self.spectrumViews:
                self._emitSymbolChanged()

    @property
    def arrowType(self):
        """Get the arrow type for the strip
        """
        return self._CcpnGLWidget._arrowType

    @arrowType.setter
    def arrowType(self, value):
        """Set the arrow type for the strip
        """
        if not isinstance(value, int):
            raise TypeError('Error: arrowType not an int')

        oldValue = self._CcpnGLWidget._arrowType
        self._CcpnGLWidget._arrowType = value if (value in range(self.spectrumDisplay.MAXARROWTYPES)) else 0
        if value != oldValue:
            self._setSymbolType()
            if self.spectrumViews:
                self._emitSymbolChanged()

    def _resize(self):
        """Resize event to handle resizing of frames that overlay the OpenGL frame
        """
        self._frameGuide._resizeFrames()

    def _checkMenuItems(self):
        """Update the menu check boxes from the strip
        """
        if self._defaultMenu:
            item = self.mainWindow.getMenuAction('Stack Spectra', self._defaultMenu)
            item.setChecked(self._CcpnGLWidget._stackingMode)

        if self._phasingMenu:
            item = self.mainWindow.getMenuAction('Stack Spectra', self._phasingMenu)
            item.setChecked(self._CcpnGLWidget._stackingMode)

    def showExportDialog(self):
        """show the export strip to file dialog
        """
        from ccpn.ui.gui.popups.ExportStripToFile import ExportStripToFilePopup as ExportDialog

        self.exportPdf = ExportDialog(parent=self.mainWindow,
                                      mainWindow=self.mainWindow,
                                      strips=self.spectrumDisplay.strips,
                                      )
        self.exportPdf.exec_()

    def _applyPhasing(self, phasingValues):
        """apply the phasing values
        phasingValues = { 'direction': 'horizontal',
                          'horizontal': {'ph0': float,
                                         'ph1': float,
                                       'pivot': float}}
        """
        values = phasingValues.get('horizontal')
        ph0 = values.get('ph0')
        ph1 = values.get('ph1')
        pivot = values.get('pivot')
        spectrumViews = self.spectrumViews
        for spectrum in [sv.spectrum for sv in spectrumViews if sv.isDisplayed]:
            intensities = Phasing.phaseRealData(spectrum.intensities, ph0, ph1, pivot)
            spectrum.intensities = intensities
        self.spectrumDisplay.togglePhaseConsole()

    def autoRange(self):
        try:
            self._CcpnGLWidget.autoRange()
        except Exception as es:
            getLogger().debugGL('OpenGL widget not instantiated', strip=self, error=es)

    def flipXYAxis(self):
        """
        Flip the X and Y axes
        """
        getLogger().warning('Function not permitted on 1D spectra')

    def flipXZAxis(self):
        """
        Flip the X and Y axes
        """
        getLogger().warning('Function not permitted on 1D spectra')

    def flipYZAxis(self):
        """
        Flip the X and Y axes
        """
        getLogger().warning('Function not permitted on 1D spectra')

    def _findPeakListView(self, peakList: PeakList):

        #peakListView = self.peakListViewDict.get(peakList)
        #if peakListView:
        #  return peakListView

        # NBNB TBD FIXME  - why is this different from nD version? is self.peakListViews: even set?

        for peakListView in self.peakListViews:
            if peakList is peakListView.peakList:
                #self.peakListViewDict[peakList] = peakListView
                return peakListView


    # -------- Noise threshold lines -------- #

    def _removeNoiseThresholdLines(self):
        for sp, lines in self._noiseThresholdLines.items():
            for line in lines:
                if line is not None:
                    self._CcpnGLWidget.removeInfiniteLine(line)
        self._noiseThresholdLines.clear()

    def _updateNoiseThresholdLines(self):
        """Re-draw the lines """
        if not self._noiseThresholdLines:
            return
        self._removeNoiseThresholdLines()
        self._initNoiseThresholdLines()

    def toggleNoiseThresholdLines(self, *args):
        value = self.sender().isChecked()
        self._noiseThresholdLinesActive = value
        if value:
            self._initNoiseThresholdLines()
        else:
            self._removeNoiseThresholdLines()


    def _updateVisibility(self):
        """Update visibility list in the OpenGL
        """
        self._CcpnGLWidget.updateVisibleSpectrumViews()
        self._updateNoiseThresholdLines()
        self._updatePeakPickingExclusionArea()

    def _initNoiseThresholdLines(self):
        from ccpn.util.Colour import hexToRgbRatio
        from functools import partial

        if not self._noiseThresholdLinesActive:
            return
        visibleSpectra = [sv.spectrum for sv in self.spectrumViews if sv.isDisplayed]
        for spectrum in visibleSpectra:
            posValue = spectrum.noiseLevel or spectrum.estimateNoise()
            if posValue is None:
                posValue = 0
            negValue = spectrum.negativeNoiseLevel or -posValue
            brush = hexToRgbRatio(spectrum.sliceColour) + (0.3,)  # sliceCol plus an offset
            positiveLine = self._CcpnGLWidget.addInfiniteLine(values=posValue, colour=brush, movable=True, lineStyle='dashed',
                                                              lineWidth=2.0, obj=spectrum, orientation='h', )
            negativeLine = self._CcpnGLWidget.addInfiniteLine(values=negValue, colour=brush, movable=True,
                                                              lineStyle='dashed', obj=spectrum, orientation='h', lineWidth=2.0)
            positiveLine.valuesChanged.connect(partial(self._lineThresholdChanged, positiveLine, spectrum, setPositiveThreshold=True))
            negativeLine.valuesChanged.connect(partial(self._lineThresholdChanged, negativeLine, spectrum, setPositiveThreshold=False))
            self._noiseThresholdLines[spectrum.pid] = [positiveLine ,negativeLine]

    def _lineThresholdChanged(self, line, spectrum, setPositiveThreshold):
        """ set the noise threshold to the spectrum based on the line move.
        TODO add notifier when editing is finished (so to set the noiseLevel once only)."""
        value = line.values
        if spectrum is not None:
            if setPositiveThreshold:
                if value >0:
                    spectrum.noiseLevel = value
            else:
                spectrum.negativeNoiseLevel = value

    # -------- Picking Exclusion Area -------- #

    def _removePickingExclusionArea(self):
        for sp, region in self._pickingExclusionAreas.items():
            if region is not None:
                self._CcpnGLWidget.removeExternalRegion(region)
        self._pickingExclusionAreas.clear()

    def _updatePeakPickingExclusionArea(self):
        """Re-draw the region """
        if not self._pickingExclusionAreaActive:
            return
        if not self._pickingExclusionAreas:
            return
        self._removePickingExclusionArea()
        self._initPickingExclusionArea()

    def togglePickingExclusionArea(self):
        value = self.sender().isChecked()
        self._pickingExclusionAreaActive = value
        if value:
            self._initPickingExclusionArea()
        else:
            self._removePickingExclusionArea()

    def _initPickingExclusionArea(self):

        if not self._pickingExclusionAreaActive:
            return

        visibleSpectra = [sv.spectrum for sv in self.spectrumViews if sv.isDisplayed]
        for spectrum in visibleSpectra:
            posValue = spectrum.positiveContourBase or spectrum.estimateNoise()
            if posValue is None:
                posValue = 0
            negValue = spectrum.negativeContourBase or -posValue
            colour = spectrum.positiveContourColour
            brush = hexToRgbRatio(spectrum.sliceColour) + (0.3,)  # sliceCol plus an offset
            _GLlinearRegions = self._CcpnGLWidget.addExternalRegion(values=(posValue, negValue), orientation='h', bounds=None,
                                                                   brush=brush, colour=colour, movable=True)
            # _GLlinearRegions.valuesChanged.connect(partial(self._setContourBaseValues, spectrum))
            _GLlinearRegions.editingFinished.connect(partial(self._setContourBaseValues, spectrum))
            self._pickingExclusionAreas[spectrum] = _GLlinearRegions

    def _setContourBaseValues(self,  spectrum, _dict, *args):
        values = _dict.get('values', [])
        if len(values) == 0:
            return
        pos, neg = np.max(values), np.min(values)
        if spectrum:
            if pos > 0:
                spectrum.positiveContourBase = float(pos)
            else:
                getLogger().warning('Setting Positive Contour Base Failed', 'Please use only positive values')
                spectrum.positiveContourBase = 1
                return
            if neg < 0:
                spectrum.negativeContourBase = float(neg)
            else:
                getLogger().warning('Setting Negative Contour Base Failed', 'Please use only negative values')
                spectrum.negativeContourBase = -1

    # ------- Calibrating ------- #

    def _addCalibrate1DXSpectrumWidget(self):
        """Add a new widget for calibrateX.
        """
        from ccpn.ui.gui.widgets.CalibrateXSpectrum1DWidget import CalibrateX1DWidgets

        sdWid = self.spectrumDisplay.mainWidget
        self.widgetIndex += 1
        self.calibrateX1DWidgets = CalibrateX1DWidgets(sdWid, mainWindow=self.mainWindow, strip=self,
                                                       grid=(self.widgetIndex, 0), gridSpan=(1, 7))

    def toggleCalibrateX(self):
        if self.calibrateXAction.isChecked():
            if self.calibrateX1DWidgets is None:
                self._addCalibrate1DXSpectrumWidget()
            self.calibrateX1DWidgets.setVisible(True)
        else:
            self.calibrateX1DWidgets.setVisible(False)

        self.calibrateX1DWidgets._toggleLines()

    def _addCalibrate1DYSpectrumWidget(self):
        """Add a new widget for calibrateY.
        """
        from ccpn.ui.gui.widgets.CalibrateYSpectrum1DWidget import CalibrateY1DWidgets

        sdWid = self.spectrumDisplay.mainWidget
        self.widgetIndex += 1
        self.calibrateY1DWidgets = CalibrateY1DWidgets(sdWid, mainWindow=self.mainWindow, strip=self,
                                                       grid=(self.widgetIndex, 0), gridSpan=(1, 7))

    def toggleCalibrateY(self):
        if self.calibrateYAction.isChecked():
            if self.calibrateY1DWidgets is None:
                self._addCalibrate1DYSpectrumWidget()
            self.calibrateY1DWidgets.setVisible(True)
        else:
            self.calibrateY1DWidgets.setVisible(False)

        self.calibrateY1DWidgets._toggleLines()

    def _closeCalibrateX(self):
        self.calibrateXAction.setChecked(False)
        self.toggleCalibrateX()

    def _closeCalibrateY(self):
        self.calibrateYAction.setChecked(False)
        self.toggleCalibrateY()

    def _getInitialOffset(self):
        offSets = []
        offSet = 0  # Default
        for spectrumView in self.spectrumViews:
            sp = spectrumView.spectrum
            y = sp.intensities
            offSet = np.std(y)
            offSets.append(offSet)
        if offSets:
            offSet = np.mean(offSets)

        return offSet

    def _toggleOffsetWidget(self):
        from ccpn.ui.gui.widgets.Stack1DWidget import Offset1DWidget

        if self.offsetWidget is None:
            sdWid = self.spectrumDisplay.mainWidget
            self.widgetIndex += 1
            self.offsetWidget = Offset1DWidget(sdWid, mainWindow=self.mainWindow, strip1D=self, grid=(self.widgetIndex, 0))
            initialOffset = self._getInitialOffset()

            # offset is now a tuple
            self.offsetWidget.setValue((0.0, initialOffset))
            self.offsetWidget.setVisible(True)
        else:
            self.offsetWidget.setVisible(not self.offsetWidget.isVisible())

    def setStackingMode(self, value):
        if value != self.stackAction.isChecked():
            self.stackAction.setChecked(value)
            self._toggleStack()

    def getStackingMode(self):
        return self.stackAction.isChecked()

    def _toggleStack(self):
        """Toggle stacking mode for 1d spectra
        This vertically stacks the spectra for clarity
        """
        if self.stackAction.isChecked():
            self._toggleOffsetWidget()
            self._stack1DSpectra(self.offsetWidget.value())
        else:
            self._toggleOffsetWidget()

            try:
                self._CcpnGLWidget.setStackingMode(False)
            except Exception:
                getLogger().debugGL('OpenGL widget not instantiated')

    def _toggleStackPhaseFromShortCut(self):
        self.stackActionPhase.setChecked(not self.stackActionPhase.isChecked())
        self._toggleStackPhase()

    def _toggleStackPhase(self):
        """Toggle stacking mode for 1d spectra
        This vertically stacks the spectra for clarity
        """
        if self.stackActionPhase.isChecked():
            self._toggleOffsetWidget()
            self._stack1DSpectra(self.offsetWidget.value())
        else:
            self._toggleOffsetWidget()

            try:
                self._CcpnGLWidget.setStackingMode(False)
            except Exception:
                getLogger().debugGL('OpenGL widget not instantiated')

    def _stack1DSpectra(self, offSet=(0.0, 0.0)):

        try:
            self._CcpnGLWidget.setStackingValue(offSet)
            self._CcpnGLWidget.setStackingMode(True)
        except Exception:
            getLogger().debugGL('OpenGL widget not instantiated')

    def toggleHorizontalTrace(self):
        """Toggles whether horizontal trace is displayed.
        """
        pass

    def toggleVerticalTrace(self):
        """Toggles whether vertical trace is displayed.
        """
        pass

    # def cycleSymbolLabelling(self):
    #     """Toggles whether peak labelling is minimal is visible in the strip.
    #     """
    #     pass

    # def cyclePeakSymbols(self):
    #     """Cycle through peak symbol types.
    #     """
    #     self.symbolType += 1

    def _createObjectMark(self, obj, axisIndex=None):
        """Create a mark at the object position.
        Could be Peak/Multiplet
        """
        try:
            _prefsGeneral = self.application.preferences.general
            defaultColour = _prefsGeneral.defaultMarksColour
            if not defaultColour.startswith('#'):
                colourList = colorSchemeTable[defaultColour] if defaultColour in colorSchemeTable else ['#FF0000']
                _prefsGeneral._defaultMarksCount = _prefsGeneral._defaultMarksCount % len(colourList)
                defaultColour = colourList[_prefsGeneral._defaultMarksCount]
                _prefsGeneral._defaultMarksCount += 1
        except Exception:
            defaultColour = '#FF0000'

        try:
            # defaultColour = self._preferences.defaultMarksColour
            position = (obj.ppmPositions[0], obj.height)
            axisCodes = self.axisCodes

            if axisIndex is not None:
                if (0 <= axisIndex < 2):
                    position = (position[axisIndex],)
                    axisCodes = (axisCodes[axisIndex],)
                else:
                    return

            self.mainWindow.newMark(defaultColour, position, axisCodes)

        except Exception as es:
            getLogger().warning('Error setting mark at position')
            raise (es)

    # def changeZPlane(self, n: int = 0, planeCount: int = None, position: float = None):
    #     """
    #     Changes the position of the z axis of the strip by number of planes or a ppm position, depending
    #     on which is specified.
    #     """
    #     # Not implemented for 1d strips
    #     pass

    # def _setPlaneAxisWidgets(self, ignoreSpectrumView=None):
    #     """
    #     # CCPN INTERNAL - Sets values for the widgets in the plane toolbar.
    #     """
    #     # Not implemented for 1d strips
    #     pass

    def _toggleLastAxisOnly(self):
        self.spectrumDisplay.setLastAxisOnly(lastAxisOnly=self.lastAxisOnlyCheckBox.isChecked())
        self.spectrumDisplay.showAxes()
