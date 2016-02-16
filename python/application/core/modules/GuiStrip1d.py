"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
__author__ = 'simon'


from PyQt4 import QtGui, QtCore

from ccpn import Project
from ccpn import PeakList

from ccpncore.api.ccpnmr.gui.Task import StripPeakListView as ApiStripPeakListView

from application.core.modules.GuiStrip import GuiStrip

from ccpncore.gui.Icon import Icon
from ccpncore.util.Colour import spectrumColours
from ccpncore.gui.Menu import Menu
# from ccpncore.util import Logging

from application.core.modules.spectrumItems.GuiPeakListView import Peak1d, GuiPeakListView
class GuiStrip1d(GuiStrip):

  def __init__(self):
    GuiStrip.__init__(self)
    self.viewBox.invertX()
    self.plotWidget.showGrid(x=True, y=True)
    self.gridShown = True
    self.crossHairShown = True
    self.autoIntegration = True
    # self.viewBox.menu = self.get1dContextMenu()
    self.plotWidget.plotItem.setAcceptDrops(True)
    self.spectrumIndex = 0
    self.peakItems = {}
    for spectrumView in self.spectrumViews:  # are there ever any??
      spectrumView.plot = self.plotWidget.plotItem.plot(spectrumView.data[0],
                            spectrumView.data[1], pen=spectrumView.spectrum.sliceColour,
                            strip=self)

  def printToFile(self, printer):
    
    raise Exception('1D printing not enabled yet')
    
  def get1dContextMenu(self) -> Menu:
    """
    Creates and returns the 1d context menu
    """

    self.contextMenu = Menu(self, isFloatWidget=True)
    self.contextMenu.addItem("Auto Scale", callback=self.zoomYAll)
    self.contextMenu.addSeparator()
    self.contextMenu.addItem("Full", callback=self.zoomXAll)
    self.contextMenu.addItem("Zoom", callback=self.raiseZoomPopup)
    self.contextMenu.addItem("Store Zoom", callback=self.storeZoom)
    self.contextMenu.addItem("Restore Zoom", callback=self.restoreZoom)
    self.contextMenu.addSeparator()
    self.crossHairAction = QtGui.QAction("Crosshair", self, triggered=self.toggleCrossHair,
                                         checkable=True)
    if self.crossHairShown:
      self.crossHairAction.setChecked(True)
    else:
      self.crossHairAction.setChecked(False)
    self.contextMenu.addAction(self.crossHairAction, isFloatWidget=True)
    self.gridAction = QtGui.QAction("Grid", self, triggered=self.toggleGrid, checkable=True)
    if self.gridShown:
      self.gridAction.setChecked(True)
    else:
      self.gridAction.setChecked(False)
    self.contextMenu.addAction(self.gridAction, isFloatWidget=True)
    self.contextMenu.addSeparator()
    # self.contextMenu.addItem("Print", callback=self.raisePrintMenu)
    return self.contextMenu

  def zoomYAll(self):
    """
    Zooms y axis to maximum of data.
    """
    y2 = self.viewBox.childrenBoundingRect().top()
    y1 = y2 + self.viewBox.childrenBoundingRect().height()
    self.viewBox.setYRange(y2,y1)

  def zoomXAll(self):
    """
    Zooms x axis to maximum value of data.
    """
    x2 = self.viewBox.childrenBoundingRect().left()
    x1 = x2 + self.viewBox.childrenBoundingRect().width()
    self.viewBox.setXRange(x2,x1)

  def showPeaks(self, peakList:PeakList):
    """
    Displays peaks in specified peaklist in the strip.
    """
    # # self.plotWidget.scene().addItem(peakListItem)
    # print(self.plotWidget.scene().items())
    #peakLayer = GuiPeakListView(self.plotWidget.scene(), self.plotWidget, peakList)
    peakItems = []
    self.peakItems[peakList] = []
    for peak in peakList.peaks:
     # peakItem =
     peakItem = Peak1d(self.plotWidget.scene(), self.plotWidget, peak,  peakList)
     self.peakItems[peakList].append(peakItem)
    #   peakItem = PeakItem(peak)
    #   self.plotWidget.addItem(peakItem)
     self.plotWidget.addItem(peakItem)
    # print(self.plotWidget.scene().items())
    #   self.plotWidget.addItem(peakItem.peakAnnotationItem.peakTextItem)
    #   self.plotWidget.addItem(peakItem.peakAnnotationItem.peakSymbolItem)
    # # print(self.plotWidget.scene().items())

  def hidePeaks(self, peakList:PeakList):
    """
    Hides peaks in specified peaklist from strip.
    """
    for item in self.peakItems[peakList]:
      self.plotWidget.removeItem(item)
      
def _deletedStripPeakListView(project:Project, apiStripPeakListView:ApiStripPeakListView):
  
  getDataObj = project._data2Obj.get
  peakListView = getDataObj(apiStripPeakListView)
  spectrumView = peakListView.spectrumView
  strip = spectrumView.strip
 
  if not isinstance(strip, GuiStrip1d):
    return
    
  scene = strip.plotWidget.scene()
  peakList = peakListView.peakList
  for peakItem in strip.peakItems[peakList]:
    scene.removeItem(peakItem.annotation)
    scene.removeItem(peakItem.symbol)
    scene.removeItem(peakItem)
  
Project._setupNotifier(_deletedStripPeakListView, ApiStripPeakListView, 'preDelete')

