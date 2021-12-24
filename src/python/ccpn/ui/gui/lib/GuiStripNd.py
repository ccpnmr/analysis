"""
This widget implements the nD (n>2) strip. 
Strips are contained within a SpectrumDisplay.

Some of the available methods:

changeZPlane(n:int=0, planeCount:int=None, position:float=None): Changes the position 
    of the z axis of the strip by number of planes or a ppm position, depending
    on which is specified.
nextZPlane(n:int=0): Decreases z ppm position by one plane
prevZPlane(n:int=0): Decreases z ppm position by one plane

resetZoom(axis=None): Resets zoom of strip axes to limits of maxima and minima of 
    the limits of the displayed spectra.
    
toggleHorizontalTrace(self): Toggles display of the horizontal trace.
toggleVerticalTrace(self): Toggles display of the vertical trace.

setStripLabelText(text:str):  set the text of the stripLabel
getStripLabelText() -> str:  get the text of the stripLabel
showStripLabel(doShow:bool):  show/hide the stripLabel
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2021-12-24 15:23:20 +0000 (Fri, December 24, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets
import numpy
from ccpn.core.PeakList import PeakList
from ccpn.core.lib.AxisCodeLib import getAxisCodeMatchIndices
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar, undoStackBlocking
from ccpn.ui.gui.lib.GuiStrip import GuiStrip, DefaultMenu, PeakMenu, IntegralMenu, MultipletMenu, PhasingMenu, AxisMenu
from ccpn.ui.gui.lib.GuiStripContextMenus import _getNdPhasingMenu, _getNdDefaultMenu, _getNdPeakMenu, \
    _getNdIntegralMenu, _getNdMultipletMenu, _getNdAxisMenu
from ccpn.ui.gui.lib.StripLib import copyStripAxisPositionsAndWidths
from ccpn.ui.gui.guiSettings import ZPlaneNavigationModes
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.Frame import OpenGLOverlayFrame
from ccpn.ui.gui.widgets.PlaneToolbar import ZPlaneToolbar
from ccpn.ui.gui.widgets.PlaneToolbar import StripHeaderWidget, PlaneAxisWidget, StripLabelWidget, \
    EMITSOURCE, EMITCLICKED, EMITIGNORESOURCE
from ccpn.util.Colour import colorSchemeTable
from ccpn.util.Logging import getLogger
from ccpn.util.decorators import logCommand
from ccpn.util.Constants import AXISUNIT_PPM, AXISUNIT_HZ, AXISUNIT_POINT


class GuiStripNd(GuiStrip):
    """
    Main Strip for Nd spectra object
  
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

    # TODO:ED: complete the above; also port to GuiStrip1d

    def __init__(self, spectrumDisplay):
        """
        Initialise Nd Strip object
    
        :param spectrumDisplay: spectrumDisplay instance
        """

        super().__init__(spectrumDisplay)

        # the scene knows which items are in it but they are stored as a list and the below give fast access from API object to QGraphicsItem
        ###self.peakLayerDict = {}  # peakList --> peakLayer
        ###self.peakListViewDict = {}  # peakList --> peakListView
        # self.spectrumActionDict = {}  # apiDataSource --> toolbar action (i.e. button); used in SpectrumToolBar

        # self.haveSetupZWidgets = False

        self.viewStripMenu = _getNdDefaultMenu(self)
        self._defaultMenu = self.viewStripMenu
        self._phasingMenu = _getNdPhasingMenu(self)
        self._peakMenu = _getNdPeakMenu(self)
        self._integralMenu = _getNdIntegralMenu(self)
        self._multipletMenu = _getNdMultipletMenu(self)
        self._axisMenu = _getNdAxisMenu(self)

        self._contextMenus.update({DefaultMenu  : self._defaultMenu,
                                   PhasingMenu  : self._phasingMenu,
                                   PeakMenu     : self._peakMenu,
                                   IntegralMenu : self._integralMenu,
                                   MultipletMenu: self._multipletMenu,
                                   AxisMenu     : self._axisMenu
                                   })

        # self.viewBox.invertX()
        # self.viewBox.invertY()
        ###self.region = guiSpectrumDisplay.defaultRegion()
        self.planeLabel = None
        self.axesSwapped = False
        self.calibrateXNDWidgets = None
        self.calibrateYNDWidgets = None
        self.widgetIndex = 4  #start adding widgets from row 4

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # TEST: ED new plane widgets

        self.planeToolbar = None

        # tuple of "plane-selection" widgets; i.e. for 3D, 4D, etc
        self.planeAxisBars = ()

        # a large(ish) unbound widget to contain the text - may need more rows
        self._frameGuide = OpenGLOverlayFrame(self, setLayout=True)
        # self._frameGuide.setFixedSize(200, 200)

        # add spacer to the top left corner
        self._frameGuide.addSpacer(8, 8, grid=(1, 0))
        row = 2

        self.stripLabel = StripLabelWidget(qtParent=self._frameGuide, mainWindow=self.mainWindow, strip=self, grid=(row, 1), gridSpan=(1, 1))
        row += 1
        # set the ID label in the new widget
        self.stripLabel._populate()

        self.header = StripHeaderWidget(qtParent=self._frameGuide, mainWindow=self.mainWindow, strip=self, grid=(row, 1), gridSpan=(1, 1))
        row += 1

        for ii, axis in enumerate(self.axisCodes[2:]):
            # add a plane widget for each dimension > 1
            fr = PlaneAxisWidget(qtParent=self._frameGuide, mainWindow=self.mainWindow, strip=self, axis=ii + 2,
                                 grid=(row, 1), gridSpan=(1, 1))
            row += 1

            # fill the widget
            fr._populate()

            self.planeAxisBars += (fr,)

        Spacer(self._frameGuide, 1, 1, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding, grid=(row, 2))

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # set the axis controlled by the wheelMouse events
        self.activePlaneAxis = None

        if self.planeAxisBars:
            self.planeAxisBars[0]._setLabelBorder(False)
            # set the axis in the strip for modifying with the wheelMouse event - not implemented yet
            self.activePlaneAxis = self.planeAxisBars[0].axis

            # set the active axis to the first available planeAxisBar
            self.optionsChanged.emit({EMITSOURCE      : self.planeAxisBars[0],
                                      EMITCLICKED     : True,
                                      EMITIGNORESOURCE: False})

        if len(self.orderedAxes) < 3:  # hide if only 2D
            self._stripToolBarWidget.setVisible(False)

        # add container for the zPlane navigation widgets for 'Per Strip' mode
        self.zPlaneFrame = ZPlaneToolbar(self._stripToolBarWidget, self.mainWindow, self, grid=(0, 0),
                                         showHeader=False, showLabels=False, margins=(2, 2, 2, 2))

        if self.spectrumDisplay.zPlaneNavigationMode == ZPlaneNavigationModes.PERSTRIP.label:
            self.zPlaneFrame.attachZPlaneWidgets(self)
        self.zPlaneFrame.setVisible(self.spectrumDisplay.zPlaneNavigationMode == ZPlaneNavigationModes.PERSTRIP.label)

        if self.spectrumDisplay.zPlaneNavigationMode == ZPlaneNavigationModes.PERSPECTRUMDISPLAY.label:
            self.spectrumDisplay.zPlaneFrame.attachZPlaneWidgets(self)

        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Preferred)

    def _resize(self):
        """Resize event to handle resizing of frames that overlay the OpenGL frame
        """
        self._frameGuide._resizeFrames()

    def _printWidgets(self, wid, level=0):
        try:
            print('  ' * level, '>>>', wid)
            layout = wid.layout()

            for ww in range(layout.count()):
                wid = layout.itemAt(ww).widget()
                self._printWidgets(wid, level + 1)
                wid.setMinimumWidth(10)
        except Exception as es:
            pass

    def showExportDialog(self):
        """show the export strip to file dialog
        """
        from ccpn.ui.gui.popups.ExportStripToFile import ExportStripToFilePopup

        self.exportPdf = ExportStripToFilePopup(parent=self.mainWindow,
                                                mainWindow=self.mainWindow,
                                                strips=self.spectrumDisplay.strips,
                                                selectedStrip=self.current.strip
                                                )
        self.exportPdf.exec_()

    @logCommand(get='self')
    def copyStrip(self):
        """
        Copy the strip into new SpectrumDisplay
        """
        # with undoBlockWithoutSideBar():
        with undoStackBlocking() as _:  # Do not add to undo/redo stack
            # create a new spectrum display
            newDisplay = self.mainWindow.createSpectrumDisplay(self.spectra[0], axisCodes=self.axisOrder)
            for spectrum in self.spectra:
                newDisplay.displaySpectrum(spectrum)

            # newDisplay.autoRange()
            copyStripAxisPositionsAndWidths(self, newDisplay.strips[0])

    @logCommand(get='self')
    def flipXYAxis(self):
        """
        Flip the X and Y axes
        """
        nDim = len(self.axisOrder)
        if nDim < 2:
            getLogger().warning('Too few dimensions for XY flip')
        else:
            axisOrder = [self.axisOrder[1], self.axisOrder[0]]
            if nDim > len(axisOrder):
                axisOrder.extend(self.axisOrder[2:])

            # with undoBlockWithoutSideBar():
            with undoStackBlocking() as _tmp:  # Do not add to undo/redo stack
                # create a new spectrum display with the new axis order
                newDisplay = self.mainWindow.createSpectrumDisplay(self.spectra[0], axisCodes=axisOrder)
                for spectrum in self.spectra:
                    newDisplay.displaySpectrum(spectrum)

                # newDisplay.autoRange()
                copyStripAxisPositionsAndWidths(self, newDisplay.strips[0])

    @logCommand(get='self')
    def flipXZAxis(self):
        """
        Flip the X and Z axes
        """
        nDim = len(self.axisOrder)
        if nDim < 3:
            getLogger().warning('Too few dimensions for XZ flip')
        else:
            axisOrder = [self.axisOrder[2], self.axisOrder[1], self.axisOrder[0]]

            # add any remaining axes of the strip to the list
            if nDim > len(axisOrder):
                axisOrder.extend(self.axisOrder[3:])

            # with undoBlockWithoutSideBar():
            with undoStackBlocking() as _:  # Do not add to undo/redo stack
                # create a new spectrum display with the new axis order
                newDisplay = self.mainWindow.createSpectrumDisplay(self.spectra[0], axisCodes=axisOrder)
                for spectrum in self.spectra:  #[1:]:
                    newDisplay.displaySpectrum(spectrum)

                # newDisplay.autoRange()
                copyStripAxisPositionsAndWidths(self, newDisplay.strips[0])

    @logCommand(get='self')
    def flipYZAxis(self):
        """
        Flip the Y and Z axes
        """
        nDim = len(self.axisOrder)
        if nDim < 3:
            getLogger().warning('Too few dimensions for YZ flip')
        else:
            axisOrder = [self.axisOrder[0], self.axisOrder[2], self.axisOrder[1]]

            # add any remaining axes of the strip to the list
            if nDim > len(axisOrder):
                axisOrder.extend(self.axisOrder[3:])

            # with undoBlockWithoutSideBar():
            with undoStackBlocking() as _:  # Do not add to undo/redo stack
                # create a new spectrum display with the new axis order
                newDisplay = self.mainWindow.createSpectrumDisplay(self.spectra[0], axisCodes=axisOrder)
                for spectrum in self.spectra:
                    newDisplay.displaySpectrum(spectrum)

                # newDisplay.autoRange()
                copyStripAxisPositionsAndWidths(self, newDisplay.strips[0])

    @logCommand(get='self')
    def extractVisiblePlanes(self, openInSpectrumDisplay=True) -> list:
        """Extract all visible planes of strip to file, creating a Spectrum instance for each plane
        :param openInSpectrumDisplay: optionally open in a new SpectrumDisplay
        :returns: a list of Spectrum instances
        """
        display = self.spectrumDisplay

        result = []
        for specView in [spv for spv in display.spectrumViews if spv.isVisible]:
            ppmPositions = self.positions
            plane = specView._extractXYplaneToFile(ppmPositions)
            result.append(plane)

        if openInSpectrumDisplay:
            display.mainWindow.newSpectrumDisplay(spectra=result, axisCodes=self.axisCodes[0:2])

        return result

    def reorderSpectra(self):
        pass

    def resetAxisRange(self, axis):
        if axis is None:
            return

        positionArray = []

        for spectrumView in self.spectrumViews:
            # Get spectrum dimension index matching display X or Y
            _spectrumLimits = spectrumView.spectrum.getByAxisCodes('spectrumLimits', spectrumView.strip.axisCodes)
            positionArray.append(_spectrumLimits[axis])

        positionArrayFlat = numpy.array(positionArray).flatten()
        zoomArray = ([min(positionArrayFlat), max(positionArrayFlat)])
        if axis == 0:
            self.zoomX(*zoomArray)
        elif axis == 1:
            self.zoomY(*zoomArray)

    def getAxisLimits(self, axis):
        if axis is None:
            return

        positionArray = []

        for spectrumView in self.spectrumViews:
            # Get spectrum dimension index matching display X or Y
            _spectrumLimits = spectrumView.spectrum.getByAxisCodes('spectrumLimits', spectrumView.strip.axisCodes)
            positionArray.append(_spectrumLimits[axis])

        positionArrayFlat = numpy.array(positionArray).flatten()
        zoomArray = ([min(positionArrayFlat), max(positionArrayFlat)])

        return zoomArray
        # if axis == 0:
        #   self.zoomX(*zoomArray)
        # elif axis == 1:
        #   self.zoomY(*zoomArray)

    # def _updateRegion(self, viewBox):
    #     # this is called when the viewBox is changed on the screen via the mouse
    #
    #     GuiStrip._updateRegion(self, viewBox)
    #     self._updateTraces()

    def _toggleLastAxisOnly(self):
        self.spectrumDisplay.setLastAxisOnly(lastAxisOnly=self.lastAxisOnlyCheckBox.isChecked())
        self.spectrumDisplay.showAxes()

    def _updateTraces(self):

        try:
            self._CcpnGLWidget.updateHTrace = self.hTraceAction.isChecked()
            self._CcpnGLWidget.updateVTrace = self.vTraceAction.isChecked()

            # don't need this now - should be turned on with togglePhasingConsole, mode: PC
            # for strip in self.spectrumDisplay.strips:
            #   if strip.hTraceAction.isChecked() or strip.vTraceAction.isChecked():
            #     self.spectrumDisplay.phasingFrame.setVisible(True)
            #     break
            # else:
            #   self.spectrumDisplay.phasingFrame.setVisible(False)

        except Exception as es:
            getLogger().debugGL('OpenGL widget not instantiated')

        # return
        #
        # cursorPosition = self.current.cursorPosition
        # if cursorPosition:
        #     position = list(cursorPosition)
        #     for axis in self.orderedAxes[2:]:
        #         position.append(axis.position)
        #     point = QtCore.QPointF(cursorPosition[0], cursorPosition[1])
        #     pixel = self.viewBox.mapViewToScene(point)
        #     cursorPixel = (pixel.x(), pixel.y())
        #     updateHTrace = self.hTraceAction.isChecked()
        #     updateVTrace = self.vTraceAction.isChecked()
        #
        #     for spectrumView in self.spectrumViews:
        #         spectrumView._updateTrace(position, cursorPixel, updateHTrace, updateVTrace)

    def toggleHorizontalTrace(self):
        """
        Toggles whether or not horizontal trace is displayed.
        """
        if not self.spectrumDisplay.phasingFrame.isVisible():
            self.spectrumDisplay.setHorizontalTraces(self.hTraceAction.isChecked())

    def _setHorizontalTrace(self, trace):
        """
        Toggles whether or not horizontal trace is displayed.
        """
        if not self.spectrumDisplay.phasingFrame.isVisible():
            self.hTraceAction.setChecked(trace)
            self._updateTraces()

    def toggleVerticalTrace(self):
        """
        Toggles whether or not vertical trace is displayed.
        """
        if not self.spectrumDisplay.phasingFrame.isVisible():
            self.spectrumDisplay.setVerticalTraces(self.vTraceAction.isChecked())

    def _setVerticalTrace(self, trace):
        """
        Toggles whether or not vertical trace is displayed.
        """
        if not self.spectrumDisplay.phasingFrame.isVisible():
            self.vTraceAction.setChecked(trace)
            self._updateTraces()

    def toggleLastAxisOnly(self):
        """
        Toggles whether the axis is displayed in the last strip of the display.
        """
        self.lastAxisOnlyCheckBox.setChecked(not self.lastAxisOnlyCheckBox.isChecked())
        self._toggleLastAxisOnly()

    def _mouseMoved(self, positionPixel):

        if self.isDeleted:
            return

        #GuiStrip._mouseMoved(self, positionPixel)
        self._updateTraces()

    def _setPlaneAxisWidgets(self, ignoreSpectrumView=None, axis=None):
        """Sets values for the planeAxis widgets in the plane toolbar.
        # CCPNINTERNAL - called from several places
        """

        _displayedSpectra = [ds for ds in self._displayedSpectra
                                if (ds.spectrumView is not ignoreSpectrumView and
                                    ds.spectrum.dimensionCount > 2
                                   )
                            ]

        if len(_displayedSpectra) == 0:
            getLogger().debug('_setPlaneAxisWidgets: no spectra displayed')
            return

        def _getVals(attrName, idx) -> list:
            """A simple helper function to get values by attrName
            Remove any None's
            """
            result = [getattr(ds, attrName)[idx] for ds in _displayedSpectra]
            return [val for val in result if val is not None]

        for idx, stripAxis in enumerate(self.axes[2:]):
            axisIndex = idx+2

            _vals = _getVals('axisIncrementsByType', axisIndex)
            _planeSize = min(_vals)

            _position = stripAxis.position

            _vals = _getVals('minAxisLimitsByType', axisIndex)
            _minPlaneValue = min(_vals)

            _vals = _getVals('maxAxisLimitsByType', axisIndex)
            _maxPlaneValue = min(_vals)

            # set PlaneSelectorWidget values; BUT "unit" argument is ignored (GWV)
            planeAxisBar = self.planeAxisBars[idx]
            planeAxisBar.setPlaneValues(_planeSize, _minPlaneValue, _maxPlaneValue, _position, unit=stripAxis.unit)

        # GWV:not sure about this
        # self.haveSetupZWidgets = True

    # @logCommand(get='self')
    def changeZPlane(self, axisIndex:int = None, planeCount:int = None, position:float = None):
        """
        Changes the position of the z,a,b axis of the strip by number of planes or a ppm position, depending
        on which is specified.
        """
        if self.isDeleted:
            return

        if not (self.planeAxisBars and self.activePlaneAxis is not None):
            return

        axisIndex = (axisIndex if isinstance(axisIndex, int) else self.activePlaneAxis)
        if not (0 <= (axisIndex - 2) < len(self.planeAxisBars)):
            getLogger().warning('axisIndex out of range %s' % axisIndex)
            return

        stripAxis = self.orderedAxes[axisIndex]  # was + 2
        planeAxisBar = self.planeAxisBars[axisIndex - 2]

        # get current plane minValue, maxValue, stepSize, value, planeDepth
        planeMin, planeMax, _tmp, position, planeDepth = planeAxisBar.getPlaneValues()

        # below is hack to prevent initial setting of value to 99.99 when dragging spectrum onto blank display
        if planeMin == 0 and position == 99.99 and planeMax == 99.99:
            return

        _specView = self.firstVisibleSpectrum()
        if not (_specView and not _specView.isDeleted):
            return
        specDim = _specView.spectrumDimensions[axisIndex]

        if stripAxis.unit == AXISUNIT_PPM:
            # planeSize = specDim._valuePerPoint/ specDim.spectrometerFrequency  # specDim is in Hz
            planeSize = specDim.ppmPerPoint

        elif stripAxis.unit == AXISUNIT_POINT:
            position = specDim.pointToPpm(position)
            # planeSize = specDim._valuePerPoint/ specDim.spectrometerFrequency  # specDim is in Hz
            planeSize = specDim.ppmPerPoint

        elif stripAxis.unit == AXISUNIT_HZ:
            # first change to ppm and scale by spectrometerFrequencies
            position = position / specDim.spectrometerFrequency
            # planeSize = specDim._valuePerPoint/ specDim.spectrometerFrequency  # specDim is in Hz
            planeSize = specDim.ppmPerPoint

        else:
            getLogger().warning(f'Axis {stripAxis.unit} not found')
            return

        def _wrapPosition(_position):
            # wrap around the aliasing limits
            _aliasMin, _aliasMax = _specView.aliasingLimits[axisIndex]
            if _position > _aliasMax:
                _position = _aliasMin
            if _position < _aliasMin:
                _position = _aliasMax
            return _position

        if planeCount:
            delta = planeSize * planeCount
            position = position + delta

            # wrap around the aliasing limits
            position = _wrapPosition(position)
            # _aliasMin, _aliasMax = _specView.aliasingLimits[axisIndex]
            # if position > _aliasMax:
            #     position = _aliasMin
            # if position < _aliasMin:
            #     position = _aliasMax

            stripAxis.position = position
            stripAxis.width = planeSize * planeDepth

            self.axisRegionChanged(stripAxis)
            self.refresh()

        else:
            if position is not None:
                # _aliasMin, _aliasMax = _specView.spectrum.aliasingLimits[_index]
                # position = _aliasMin + (position - _aliasMin) % (_aliasMax - _aliasMin)
                position = _wrapPosition(position)

                stripAxis.position = position
                stripAxis.width = planeSize * planeDepth

                self.axisRegionChanged(stripAxis)
                self.refresh()

    def _setZPlanePosition(self, n: int, value: float):
        """
        Sets the value of the z plane position box if the specified value is within the displayable limits.
        """
        planeLabel = self.planeToolbar.planeLabels[n]
        if 1:  # planeLabel.valueChanged: (<-- isn't that always true??)
            value = planeLabel.value()
        # 8/3/2016 Rasmus Fogh. Fixed untested (obvious bug)
        # if planeLabel.minimum() <= planeLabel.value() <= planeLabel.maximum():

        if planeLabel.minimum() <= value <= planeLabel.maximum():
            self.changeZPlane(n, position=value)

    def _findPeakListView(self, peakList: PeakList):
        if hasattr(self, 'spectrumViews'):
            for spectrumView in self.spectrumViews:
                for peakListView in spectrumView.peakListViews:
                    if peakList is peakListView.peakList:
                        #self.peakListViewDict[peakList] = peakListView
                        return peakListView

    def _addCalibrateXNDSpectrumWidget(self, enableClose=True):
        """add a new widget for calibrateX
        """
        from ccpn.ui.gui.widgets.CalibrateXSpectrumNDWidget import CalibrateXNDWidgets

        sdWid = self.spectrumDisplay.mainWidget
        self.widgetIndex += 1
        self.calibrateXNDWidgets = CalibrateXNDWidgets(sdWid, mainWindow=self.mainWindow, strip=self, enableClose=enableClose,
                                                       grid=(self.widgetIndex, 0), gridSpan=(1, 7))

    def toggleCalibrateX(self):
        if self.calibrateXAction.isChecked():
            if self.calibrateXNDWidgets is None:
                self._addCalibrateXNDSpectrumWidget()
            self.calibrateXNDWidgets.setVisible(True)
            self.calibrateXNDWidgets._toggleLines()
            # self.calibrateXNDWidgets.resetUndos()

        else:
            self.calibrateXNDWidgets.setVisible(False)
            self.calibrateXNDWidgets._toggleLines()

    def _addCalibrateYNDSpectrumWidget(self):
        """add a new widget for calibrateY
        """
        from ccpn.ui.gui.widgets.CalibrateYSpectrumNDWidget import CalibrateYNDWidgets

        sdWid = self.spectrumDisplay.mainWidget
        self.widgetIndex += 1
        self.calibrateYNDWidgets = CalibrateYNDWidgets(sdWid, mainWindow=self.mainWindow, strip=self,
                                                       grid=(self.widgetIndex, 0), gridSpan=(1, 7))

    def toggleCalibrateY(self):
        if self.calibrateYAction.isChecked():
            if self.calibrateYNDWidgets is None:
                self._addCalibrateYNDSpectrumWidget()
            self.calibrateYNDWidgets.setVisible(True)
            self.calibrateYNDWidgets._toggleLines()
            # self.calibrateYNDWidgets.resetUndos()

        else:
            self.calibrateYNDWidgets.setVisible(False)
            self.calibrateYNDWidgets._toggleLines()

    def toggleCalibrateXY(self):
        """Toggle widgets for both axes
        """
        if self.calibrateXYAction.isChecked():
            if self.calibrateXNDWidgets is None:
                self._addCalibrateXNDSpectrumWidget(enableClose=False)
            self.calibrateXNDWidgets.setVisible(True)
            self.calibrateXNDWidgets._toggleLines()
            # self.calibrateXNDWidgets.resetUndos()

            if self.calibrateYNDWidgets is None:
                self._addCalibrateYNDSpectrumWidget()
            self.calibrateYNDWidgets.setVisible(True)
            self.calibrateYNDWidgets._toggleLines()
            # self.calibrateYNDWidgets.resetUndos()

        else:
            self.calibrateXNDWidgets.setVisible(False)
            self.calibrateXNDWidgets._toggleLines()
            self.calibrateYNDWidgets.setVisible(False)
            self.calibrateYNDWidgets._toggleLines()

    def _closeCalibrateX(self):
        self.calibrateXYAction.setChecked(False)
        self.toggleCalibrateXY()

    def _closeCalibrateY(self):
        self.calibrateXYAction.setChecked(False)
        self.toggleCalibrateXY()

    def _createObjectMark(self, obj, axisIndex=None):
        """Create a mark at the object position.
        Could be Peak/Multiplet.
        """
        try:
            _prefsGeneral = self.application.preferences.general
            defaultColour = _prefsGeneral.defaultMarksColour
            if not defaultColour.startswith('#'):
                colourList = colorSchemeTable[defaultColour] if defaultColour in colorSchemeTable else ['#FF0000']
                _prefsGeneral._defaultMarksCount = _prefsGeneral._defaultMarksCount % len(colourList)
                defaultColour = colourList[_prefsGeneral._defaultMarksCount]
                _prefsGeneral._defaultMarksCount += 1
        except:
            defaultColour = '#FF0000'

        try:
            # defaultColour = self._preferences.defaultMarksColour
            ppmPositions = obj.ppmPositions
            axisCodes = obj.axisCodes

            indices = getAxisCodeMatchIndices(self.axisCodes, obj.axisCodes)

            if axisIndex is not None:
                objAxisIndex = indices[axisIndex]
                if objAxisIndex is not None and (0 <= objAxisIndex < len(ppmPositions)):
                    position = (ppmPositions[objAxisIndex],)
                    axisCode = (axisCodes[objAxisIndex],)
                    self.mainWindow.newMark(defaultColour, position, axisCode)
            else:
                self.mainWindow.newMark(defaultColour, ppmPositions, axisCodes)

            # add the marks for the double cursor - needs to be enabled in preferences
            if self.doubleCrosshairVisible and self._CcpnGLWidget._matchingIsotopeCodes:
                ppmPositions = obj.ppmPositions
                axisCodes = obj.axisCodes

                if axisIndex is not None:

                    if (0 <= axisIndex < 2):
                        # get the same position in the opposite axisCode
                        doubleIndex = 1 - axisIndex

                        objAxisIndex = indices[axisIndex]
                        objDoubleAxisIndex = indices[doubleIndex]

                        if objAxisIndex is not None and objDoubleAxisIndex is not None:
                            position = (ppmPositions[objAxisIndex],)
                            axisCode = (axisCodes[objDoubleAxisIndex],)
                            self.mainWindow.newMark(defaultColour, position, axisCode)
                else:
                    # flip the XY axes for the peak
                    if None not in indices:
                        ppmPositions = [ppmPositions[ii] for ii in indices]
                        axisCodes = [axisCodes[ii] for ii in indices]
                        ppmPositions = [ppmPositions[1], ppmPositions[0]] + ppmPositions[2:]
                        self.mainWindow.newMark(defaultColour, ppmPositions, axisCodes)

        except Exception as es:
            getLogger().warning('Error setting mark at position')
            raise (es)
