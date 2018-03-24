"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:45 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets

from ccpn.core.PeakList import PeakList

from ccpn.ui.gui.modules.GuiStrip import GuiStrip
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Menu import Menu
import numpy as np
from ccpn.util.Logging import getLogger


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

  def __init__(self, spectrumDisplay):
    """
    Initialise Nd spectra object

    :param spectrumDisplay Main spectrum display Module object
    """
    GuiStrip.__init__(self, spectrumDisplay)

    self.viewBox.invertX()
    self.plotWidget.showGrid(x=False, y=False)
    self.gridShown = True
    self.viewBox.menu = self._get1dContextMenu()
    self._defaultMenu = self.viewBox.menu
    self._phasingMenu = self._get1dContextPhasingMenu()

    self.plotWidget.plotItem.setAcceptDrops(True)
    self.spectrumIndex = 0
    self.peakItems = {}
    # self._hideCrossHair()
    self.calibrateX1DWidgets = None
    self.calibrateY1DWidgets = None
    self.offsetWidget = None
    self.offsetValue = 0
    self.widgetIndex = 2 #start adding widgets from row 2
    
  def _get1dContextMenu(self) -> Menu:
    """
    Creates and returns the 1d context menu
    """

    self.contextMenu = Menu('', self, isFloatWidget=True)
    action = self.contextMenu.addItem("Auto Scale", callback=self.resetYZoom)
    action.setIcon(Icon('icons/zoom-best-fit-1d'))
    self.contextMenu.addSeparator()
    action = self.contextMenu.addItem("Full", callback=self.resetXZoom)
    action.setIcon(Icon('icons/zoom-full-1d'))
    # self.contextMenu.addItem("Zoom", callback=self.showZoomPopup)
    action = self.contextMenu.addItem("Store Zoom", callback=self._storeZoom, shortcut='ZS')
    action.setIcon(Icon('icons/zoom-store'))
    action = self.contextMenu.addItem("Restore Zoom", callback=self._restoreZoom, shortcut='ZR')
    action.setIcon(Icon('icons/zoom-restore'))

    self.contextMenu.addSeparator()
    self.contextMenu.addItem("Calibrate X...", callback=self._toggleCalibrateXSpectrum)
    self.contextMenu.addItem("Calibrate Y...", callback=self._toggleCalibrateYSpectrum)
    self.contextMenu.addSeparator()
    self.stackAction = QtWidgets.QAction("Stack Spectra", self, triggered=self.toggleStack, checkable=True)
    self.stackAction.setChecked(False)
    self.contextMenu.addAction(self.stackAction)
    self.contextMenu.addSeparator()

    def tempMethod():  # ejb - how does this work?????
      return

    # add gridAction menu item
    action = self.contextMenu.addItem('Grid', callback=self.spectrumDisplay.toggleGrid,
                                      checkable=True, checked=self.gridIsVisible,
                                      shortcut='GS')
    tempMethod.__doc__ = ''
    tempMethod.__name__ = 'gridAction'
    setattr(self, tempMethod.__name__, action)

    # self.gridAction = QtWidgets.QAction("Grid", self, triggered=self.spectrumDisplay.toggleGrid, checkable=True)
    # # if self.gridShown:
    # #   self.gridAction.setChecked(True)
    # # else:
    # #   self.gridAction.setChecked(False)
    #
    # self.gridAction.setChecked(self.gridIsVisible)
    #
    # self.contextMenu.addAction(self.gridAction)
    self.contextMenu.addSeparator()

    action = self.contextMenu.addItem("Enter Phasing Console", callback=self.spectrumDisplay.togglePhaseConsole, shortcut='PC')
    action.setIcon(Icon('icons/phase-console'))

    self.contextMenu.addSeparator()
    self.contextMenu.addAction("Print to File...", self.showExportDialog)
    self.contextMenu.navigateToMenu = self.contextMenu.addMenu('Navigate To')
    return self.contextMenu

  def _get1dContextPhasingMenu(self) -> Menu:
    """
    Creates and returns the Nd context menu
    """
    class tType:
      menu, item, actn, sep = range(1,5)

    self._spectrumUtilActions = {}
    self.contextMenu = Menu('', self, isFloatWidget=True)     # generate new menu

    toolBarItems = [
       # type,      action name             icon                      tooltip/name                shortcut  active  checked,    callback,                             method
      (tType.actn, 'Add Trace',               None,                     'Add new trace',          'PT',   True,   True,       self._newPhasingTrace, ''),
      (tType.actn, 'Remove All Traces',       None,                     'Remove all traces',      'TR',   True,   True,       self.removePhasingTraces,''),
      (tType.actn, 'Set Pivot',               None,                     'Set pivot value',        'PV',   True,   True,       self._setPhasingPivot,''),
      # (tType.actn, 'Increase Trace Scale',    'icons/tracescale-up',  'Increase trace scale',   'TU',   True,   True,       self.spectrumDisplay._increaseTraceScale,''),
      # (tType.actn, 'Decrease Trace Scale',    'icons/tracescale-down','Decrease trace scale',   'TD',   True,   True,       self.spectrumDisplay._decreaseTraceScale,      ''),
      (tType.sep, None, None, None, None, None, None, None, None),
      (tType.actn, 'Exit Phasing Console',  'icons/phase-console',   'Exit phasing console',      'PC',   True,   True,       self.spectrumDisplay.togglePhaseConsole,    ''),
    ]

    for aType, aName, icon, tooltip, shortcut, active, checked, callback, attrib in toolBarItems:     # build the menu items/actions
      # self.contextMenu.navigateToMenu = self.contextMenu.addMenu('Navigate To')
      def tempMethod():           # ejb - how does this work?????
        return
      if aType == tType.menu:
        action = self.contextMenu.addMenu(aName)
        tempMethod.__doc__=''
        tempMethod.__name__=attrib
        setattr(self.contextMenu, tempMethod.__name__, action)      # add to the menu

      elif aType == tType.item:
        # self.gridAction = self.contextMenu.addItem("Grid", callback=self.toggleGrid, checkable=True)
        action = self.contextMenu.addItem(aName, callback=callback, checkable=active, checked=checked)
        tempMethod.__doc__=''
        tempMethod.__name__=attrib
        setattr(self, tempMethod.__name__, action)
        # add to self

      elif aType == tType.actn:
        # printAction = self.contextMenu.addAction("Print to File...", lambda: self.spectrumDisplay.window.printToFile(self.spectrumDisplay))
        action = self.contextMenu.addItem(aName, callback=callback, shortcut=shortcut)
        if icon is not None:
          ic = Icon(icon)
          action.setIcon(ic)
        self._spectrumUtilActions[aName] = action

      elif aType == tType.sep:
        self.contextMenu.addSeparator()

    # self.navigateToMenu = self.contextMenu.addMenu('Navigate To')
    # self.spectrumDisplays = self.getSpectrumDisplays()
    # for spectrumDisplay in self.spectrumDisplays:
    #   spectrumDisplayAction = self.navigateToMenu.addAction(spectrumDisplay.pid)
    #   receiver = lambda spectrumDisplay=spectrumDisplay.pid: self.navigateTo(spectrumDisplay)
    #   self.connect(spectrumDisplayAction, QtCore.SIGNAL('triggered()'), receiver)
    #   self.navigateToMenu.addAction(spectrumDisplay)

    # self.crossHairAction.setChecked(self.crossHairIsVisible)
    # self.gridAction.setChecked(self.gridIsVisible)
    # self.lastAxisOnlyCheckBox.setChecked(self.spectrumDisplay.lastAxisOnly)

    return self.contextMenu

  def showExportDialog(self):
    from ccpn.ui.gui.widgets.CustomExportDialog import CustomGLExportDialog
    self.exportDialog = CustomGLExportDialog(self._testCcpnOpenGLWidget, spectrumDimension='1D')
    self.exportDialog.show(self.viewBox)

  def resetYZoom(self):
    """
    Zooms y axis to maximum of data.
    """
    # y2 = self.viewBox.childrenBoundingRect().top()
    # y1 = y2 + self.viewBox.childrenBoundingRect().height()
    # self.viewBox.setYRange(y2, y1)
    try:
      self._testCcpnOpenGLWidget.resetYZoom()
    except:
      getLogger().debug('Error: OpenGL widget not instantiated for %s' % self)

  def resetXZoom(self):
    """
    Zooms x axis to maximum value of data.
    """
    # x2 = self.viewBox.childrenBoundingRect().left()
    # x1 = x2 + self.viewBox.childrenBoundingRect().width()
    # padding = self.application.preferences.general.stripRegionPadding
    # self.viewBox.setXRange(x2, x1, padding=padding)
    try:
      self._testCcpnOpenGLWidget.resetXZoom()
    except:
      getLogger().debug('Error: OpenGL widget not instantiated for %s' % self)

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

  def _findPeakListView(self, peakList:PeakList):

    #peakListView = self.peakListViewDict.get(peakList)
    #if peakListView:
    #  return peakListView

    # NBNB TBD FIXME  - why is this different from nD version? is self.peakListViews: even set?

    for peakListView in self.peakListViews:
      if peakList is peakListView.peakList:
        #self.peakListViewDict[peakList] = peakListView
        return peakListView

  def _addCalibrate1DXSpectrumWidget(self):
    from ccpn.ui.gui.widgets.CalibrateXSpectrum1DWidget import CalibrateX1DWidgets
    sdWid = self.spectrumDisplay.mainWidget
    self.widgetIndex+=1
    self.calibrateX1DWidgets = CalibrateX1DWidgets(sdWid, mainWindow=self.mainWindow, strip=self,
                                                   grid=(self.widgetIndex, 0))
    self.calibrateX1DWidgets.setVisible(True)

  def _toggleCalibrateXSpectrum(self):
    ''' calibrate the spectra in the strip to the new point '''

    if self.calibrateX1DWidgets is None:
      self._addCalibrate1DXSpectrumWidget()
    else:
      self.calibrateX1DWidgets.setVisible(not self.calibrateX1DWidgets.isVisible())
      self.calibrateX1DWidgets._toggleLines()


  def _addCalibrateYSpectrumWidget(self):
    from ccpn.ui.gui.widgets.CalibrateYSpectrum1DWidget import CalibrateY1DWidgets
    sdWid = self.spectrumDisplay.mainWidget
    self.widgetIndex += 1
    self.calibrateY1DWidgets = CalibrateY1DWidgets(sdWid, mainWindow=self.mainWindow,strip=self,
                                                   grid=(self.widgetIndex, 0))
    self.calibrateY1DWidgets.setVisible(True)

  def _toggleCalibrateYSpectrum(self):
    ''' calibrate the spectra in the strip to the new point '''

    if self.calibrateY1DWidgets is None:
      self._addCalibrateYSpectrumWidget()
    else:
      self.calibrateY1DWidgets.setVisible(not self.calibrateY1DWidgets.isVisible())
      self.calibrateY1DWidgets._toggleLines()

  def toggleOffsetWidget(self):
    from ccpn.ui.gui.widgets.Stack1DWidget import Offset1DWidget

    if self.offsetWidget is None:
      sdWid = self.spectrumDisplay.mainWidget
      self.widgetIndex += 1
      self.offsetWidget = Offset1DWidget(sdWid, mainWindow=self.mainWindow, strip1D=self, grid=(self.widgetIndex, 0))
      self.offsetWidget.setVisible(True)
    else:
      self.offsetWidget.setVisible(not self.offsetWidget.isVisible())


  def toggleStack(self):


    if self.stackAction.isChecked():
      self._stack1DSpectra()
      self.toggleOffsetWidget()

    else:
      self._restoreStacked1DSpectra()
      self.toggleOffsetWidget()

      try:
        self._testCcpnOpenGLWidget.setStackingValue(None)
      except:
        getLogger().debug('Error: OpenGL widget not instantiated for %s' % self)


  def _stack1DSpectra(self, offSet=None):

    try:
      self._testCcpnOpenGLWidget.setStackingValue(offSet)
    except:
      getLogger().debug('Error: OpenGL widget not instantiated for %s' % self)

    return

    for i, spectrumView in enumerate(self.spectrumViews):
      sp = spectrumView.spectrum
      x = sp.positions
      y = sp.intensities
      if offSet is None:
        offSet = np.std(y)
        self.offsetValue = offSet
      spectrumView.plot.curve.setData(x, y +(i*offSet))
      for peakListView in self.peakListViews:
        peakListView.setVisible(False)


  def _restoreStacked1DSpectra(self):
    for spectrumView in self.spectrumViews:
      spectrumView.plot.curve.setData(spectrumView.spectrum.positions, spectrumView.spectrum.intensities)
    # for peakListView in self.peakListViews:
    #   peakListView.setVisible(True)

  def toggleHorizontalTrace(self):
    """
    Toggles whether or not horizontal trace is displayed.
    """
    pass

  def toggleVerticalTrace(self):
    """
    Toggles whether or not vertical trace is displayed.
    """
    pass
