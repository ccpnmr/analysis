"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:41:04 +0100 (Fri, April 07, 2017) $"
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

  def __init__(self, qtParent, spectrumDisplay, application):
    """
        
        :param qtParent: QT parent to place widgets
        :param spectrumDisplay Main spectrum display Module object
        :param application: application instance
        
        This module inherits the following attributes from the Strip wrapper class
    """


    GuiStrip.__init__(self, qtParent=qtParent, spectrumDisplay=spectrumDisplay, application=application)

    # self.spectrumDisplay = spectrumDisplay
    self.application = application

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



