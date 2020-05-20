"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-05-20 13:06:48 +0100 (Wed, May 20, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets
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


class GuiStrip1d(GuiStrip):
    """
    Main Strip for 1d spectra object

    This module inherits the following attributes from the Strip wrapper class:

    serial          serial number of Strip, used in Pid and to identify the Strip
                      :return <str>
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
    resetAxisOrder    Reset display to original axis order
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

    MAXPEAKLABELTYPES = 1
    MAXPEAKSYMBOLTYPES = 1

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

        # keep a common stackItem for both menues
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

        self.widgetIndex = 3  #start adding widgets from row 3

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # TEST: ED new plane widgets

        self.planeToolbar = None
        # set the axis controlled by the wheelMouse events
        self.activePlaneAxis = None

        # a large(ish) unbound widget to contain the text - may need more rows
        self._frameGuide = OpenGLOverlayFrame(self, setLayout=True)
        self._frameGuide.setFixedSize(400, 400)

        # add spacer to the top left corner
        self._frameGuide.addSpacer(8, 8, grid=(1, 0))
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
                                      preferences=self.mainWindow.application.preferences)
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
        for spectrum in [view.spectrum for view in spectrumViews if view.isVisible()]:
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
            self.calibrateX1DWidgets._toggleLines()

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
            self.calibrateY1DWidgets._toggleLines()

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
        for i, spectrumView in enumerate(self.spectrumViews):
            sp = spectrumView.spectrum
            y = sp.intensities
            offSet = np.std(y)
            offSets.append(offSet)
        if len(offSets) > 0:
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
            except:
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
            except:
                getLogger().debugGL('OpenGL widget not instantiated')

    def _stack1DSpectra(self, offSet=(0.0, 0.0)):

        try:
            self._CcpnGLWidget.setStackingValue(offSet)
            self._CcpnGLWidget.setStackingMode(True)
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

    def toggleHorizontalTrace(self):
        """Toggles whether or not horizontal trace is displayed.
        """
        pass

    def toggleVerticalTrace(self):
        """Toggles whether or not vertical trace is displayed.
        """
        pass

    def cycleSymbolLabelling(self):
        """Toggles whether peak labelling is minimal is visible in the strip.
        """
        pass

    def cyclePeakSymbols(self):
        """Cycle through peak symbol types.
        """
        pass

    def _createObjectMark(self, obj, axisIndex=None):
        """Create a mark at the object position.
        Could be Peak/Multiplet
        """
        try:
            defaultColour = self._preferences.defaultMarksColour
            position = (obj.ppmPositions[0], obj.height)
            axisCodes = self.axisCodes

            if axisIndex is not None:
                if (0 <= axisIndex < 2):
                    position = (position[axisIndex],)
                    axisCodes = (axisCodes[axisIndex],)
                else:
                    return

            self._project.newMark(defaultColour, position, axisCodes)

        except Exception as es:
            getLogger().warning('Error setting mark at position')
            raise (es)

    def changeZPlane(self, n: int = 0, planeCount: int = None, position: float = None):
        """
        Changes the position of the z axis of the strip by number of planes or a ppm position, depending
        on which is specified.
        """
        # Not implemented for 1d strips
        pass
