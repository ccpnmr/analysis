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
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================

__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtGui

from ccpn.core.PeakList import PeakList

from ccpn.ui.gui.modules.GuiStrip import GuiStrip
from ccpn.ui.gui.widgets.Menu import Menu

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
    self.plotWidget.showGrid(x=True, y=True)
    self.gridShown = True
    self.crossHairShown = True
    self.autoIntegration = True
    self.viewBox.menu = self._get1dContextMenu()
    self.plotWidget.plotItem.setAcceptDrops(True)
    self.spectrumIndex = 0
    self.peakItems = {}
    
  def _get1dContextMenu(self) -> Menu:
    """
    Creates and returns the 1d context menu
    """

    self.contextMenu = Menu('', self, isFloatWidget=True)
    self.contextMenu.addItem("Auto Scale", callback=self.resetYZoom)
    self.contextMenu.addSeparator()
    self.contextMenu.addItem("Full", callback=self.resetXZoom)
    self.contextMenu.addItem("Zoom", callback=self.showZoomPopup)
    self.contextMenu.addItem("Store Zoom", callback=self._storeZoom)
    self.contextMenu.addItem("Restore Zoom", callback=self._restoreZoom)
    self.contextMenu.addSeparator()
    self.crossHairAction = QtGui.QAction("Crosshair", self, triggered=self._toggleCrossHair,
                                         checkable=True)
    if self.crossHairShown:
      self.crossHairAction.setChecked(True)
    else:
      self.crossHairAction.setChecked(False)
    self.contextMenu.addAction(self.crossHairAction)
    self.gridAction = QtGui.QAction("Grid", self, triggered=self.toggleGrid, checkable=True)
    if self.gridShown:
      self.gridAction.setChecked(True)
    else:
      self.gridAction.setChecked(False)
    self.contextMenu.addAction(self.gridAction)
    self.contextMenu.addSeparator()
    self.contextMenu.addAction("Print to File...", self.showExportDialog)
    self.contextMenu.navigateToMenu = self.contextMenu.addMenu('Navigate To')
    return self.contextMenu

  def showExportDialog(self):
    from ccpn.ui.gui.widgets.CustomExportDialog import CustomExportDialog
    self.exportDialog = CustomExportDialog(self.viewBox.scene(), spectrumDimension='1D')
    self.exportDialog.show(self.viewBox)

  def resetYZoom(self):
    """
    Zooms y axis to maximum of data.
    """
    y2 = self.viewBox.childrenBoundingRect().top()
    y1 = y2 + self.viewBox.childrenBoundingRect().height()
    self.viewBox.setYRange(y2, y1)

  def resetXZoom(self):
    """
    Zooms x axis to maximum value of data.
    """
    x2 = self.viewBox.childrenBoundingRect().left()
    x1 = x2 + self.viewBox.childrenBoundingRect().width()
    padding = self.application.preferences.general.stripRegionPadding
    self.viewBox.setXRange(x2, x1, padding=padding)


  def _findPeakListView(self, peakList:PeakList):

    #peakListView = self.peakListViewDict.get(peakList)
    #if peakListView:
    #  return peakListView

    # NBNB TBD FIXME  - why is this different from nD version? is self.peakListViews: even set?

    for peakListView in self.peakListViews:
      if peakList is peakListView.peakList:
        #self.peakListViewDict[peakList] = peakListView
        return peakListView



