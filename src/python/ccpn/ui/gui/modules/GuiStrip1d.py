"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtGui

from ccpn.core.PeakList import PeakList

from ccpn.ui.gui.modules.GuiStrip import GuiStrip
from ccpn.ui.gui.widgets.Menu import Menu

class GuiStrip1d(GuiStrip):

  def __init__(self):
    GuiStrip.__init__(self)
    self.viewBox.invertX()
    self.plotWidget.showGrid(x=True, y=True)
    self.gridShown = True
    self.crossHairShown = True
    self.autoIntegration = True
    self.viewBox.menu = self._get1dContextMenu()
    self.plotWidget.plotItem.setAcceptDrops(True)
    self.spectrumIndex = 0
    self.peakItems = {}
    # below causes a problem because wrapper not ready yet at this point
    #for spectrumView in self.spectrumViews:
    #  spectrumView.plot = self.plotWidget.plotItem.plot(spectrumView.data[0],
    #                        spectrumView.data[1], pen=spectrumView.spectrum.sliceColour,
    #                        strip=self)

  def _printToFile(self, printer):
    
    raise Exception('1D printing not enabled yet')
    
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
    # self.contextMenu.addItem("Print", callback=self.raisePrintMenu)
    self.contextMenu.navigateToMenu = self.contextMenu.addMenu('Navigate To')
    return self.contextMenu

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
    padding = self._appBase.preferences.general.stripRegionPadding
    self.viewBox.setXRange(x2, x1, padding=padding)

  # def showPeaks(self, peakList:PeakList, peaks=None):
  #   """
  #   Displays peaks in specified peaklist in the strip.
  #   """
  #   if not peaks:
  #     peaks = peakList.peaks
  #
  #   peakListView = self._findPeakListView(peakList)
  #   if not peakListView:
  #     return
  #
  #   peaks = [peak for peak in peaks if self.peakIsInPlane(peak)]
  #   self.stripFrame.guiSpectrumDisplay.showPeaks(peakListView, peaks)

  # def hidePeaks(self, peakList:PeakList):
  #   """
  #   Hides peaks in specified peaklist from strip.
  #   """
  #   peakListView = self._findPeakListView(peakList)
  #   peakListView.setVisible(False)

  def _findPeakListView(self, peakList:PeakList):

    #peakListView = self.peakListViewDict.get(peakList)
    #if peakListView:
    #  return peakListView

    # NBNB TBD FIXME  - why is this different from nD version? is self.peakListViews: even set?

    for peakListView in self.peakListViews:
      if peakList is peakListView.peakList:
        #self.peakListViewDict[peakList] = peakListView
        return peakListView



