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

import importlib, os

from PyQt4 import QtGui, QtCore

from ccpn import Project

from ccpncore.api.ccpnmr.gui.Task import StripSpectrumView as ApiStripSpectrumView

from ccpncore.gui.Frame import Frame as CoreFrame
from ccpncore.gui.Icon import Icon
from ccpncore.gui.Label import Label
from ccpncore.gui.ScrollArea import ScrollArea
from ccpncore.gui.ToolBar import ToolBar

from ccpnmrcore.DropBase import DropBase
from ccpnmrcore.gui.Frame import Frame as GuiFrame
from ccpnmrcore.gui.PhasingFrame import PhasingFrame
from ccpnmrcore.gui.SpectrumToolBar import SpectrumToolBar
from ccpnmrcore.modules.GuiModule import GuiModule

# def _findPpmRegion(spectrum, axisDim, spectrumDim):
#
#   pointCount = spectrum.pointCounts[spectrumDim]
#   if axisDim < 2: # want entire region
#     region = (0, pointCount)
#   else:
#     n = pointCount // 2
#     region = (n, n+1)
#
#   firstPpm, lastPpm = spectrum.getDimValueFromPoint(spectrumDim, region)
#
#   return 0.5*(firstPpm+lastPpm), abs(lastPpm-firstPpm)


class GuiSpectrumDisplay(DropBase, GuiModule):

  def __init__(self):
    GuiModule.__init__(self)
    # DropBase.__init__(self, self._appBase, self.dropCallback)
    self.setAcceptDrops(True)
    self.spectrumToolBar = SpectrumToolBar(self.dock, widget=self)#, grid=(0, 0), gridSpan=(1, 2))
    self.dock.addWidget(self.spectrumToolBar, 0, 0, 1, 2)#, grid=(0, 0), gridSpan=(1, 2))
    self.dock.label.closeButton.clicked.connect(self.closeDock)
    self.spectrumToolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
    screenWidth  = QtGui.QApplication.desktop().screenGeometry().width()
    # self.spectrumToolBar.setFixedWidth(screenWidth*0.5)
    self.resize(self.sizeHint())

    self.spectrumUtilToolBar = ToolBar(self.dock)#, grid=(0, 2), gridSpan=(1, 2))
    # self.spectrumUtilToolBar.setFixedWidth(screenWidth*0.4)
    self.spectrumUtilToolBar.setFixedHeight(self.spectrumToolBar.height())
    self.dock.addWidget(self.spectrumUtilToolBar, 0, 2)# grid=(0, 2), gridSpan=(1, 1))
    
    # toolBarColour = QtGui.QColor(214,215,213)
    # self.positionBox = Label(self.dock)
    # self.dock.addWidget(self.positionBox, 0, 3)#, grid=(0, 3), gridSpan=(1, 1))
    # self.positionBox.setFixedWidth(screenWidth*0.1)
    self.scrollArea = ScrollArea(self.dock, grid=(1, 0), gridSpan=(1, 4))
    self.scrollArea.setWidgetResizable(True)
    # self.dock.addWidget(self.scrollArea, 1, 0, 1, 4)
    self.scrollArea.setWidgetResizable(True)
    self.stripFrame = GuiFrame(self.scrollArea, grid=(0, 0), appBase=self._appBase)
    self.stripFrame.guiSpectrumDisplay = self
    # self.stripFrame.layout().setContentsMargins(0, 0, 2, 0)
    self.stripFrame.setAcceptDrops(True)
    self.scrollArea.setWidget(self.stripFrame)
    
    self.setEnabled(True)

    self.phasingFrame = PhasingFrame(self.dock, callback=lambda ph0, ph1: self.updatePhasing(), grid=(2, 0), gridSpan=(1, 3))
    self.phasingFrame.setVisible(False)

  def updatePhasing(self):
    for strip in self.strips:
      strip.updatePhasing()
    
  def togglePhaseConsole(self):
        
    self.phasingFrame.setVisible(not self.phasingFrame.isVisible())
    self.updatePhasing()

  def closeDock(self):
    self.delete()

  def fillToolBar(self):
    addStripAction = self.spectrumUtilToolBar.addAction('Add Strip', self.duplicateStrip) #self.orderedStrips[0].clone()) # clone first strip
    addStripIcon = Icon('iconsNew/plus')
    addStripAction.setIcon(addStripIcon)
    removeStripAction = self.spectrumUtilToolBar.addAction('Remove Strip', lambda self=self: self.orderedStrips[-1].delete()) # remove last strip
    removeStripIcon = Icon('iconsNew/minus')
    removeStripAction.setIcon(removeStripIcon)
    self.removeStripAction = removeStripAction

  def duplicateStrip(self):
    newStrip = self.strips[-1].clone()

  def hideUtilToolBar(self):
    self.spectrumUtilToolBar.hide()

  def zoomYAll(self):
    for strip in self.strips:
      strip.zoomYAll()

  def zoomXAll(self):
    self._appBase.current.strip.zoomXAll()

  def restoreZoom(self):
    self._appBase.current.strip.restoreZoom()

  def storeZoom(self):
    self._appBase.current.strip.storeZoom()
    
  def toggleCrossHair(self):
    # toggle crosshairs for strips in this spectrumDisplay
    for strip in self.strips:
      strip.toggleCrossHair()
    
  def toggleGrid(self):
    # toggle grid for strips in this spectrumDisplay
    for strip in self.strips:
      strip.toggleGrid()
    
  def setCrossHairPosition(self, axisPositionDict):
    for strip in self.strips:
      strip.setCrossHairPosition(axisPositionDict)

    
def _createdStripSpectrumView(project:Project, apiStripSpectrumView:ApiStripSpectrumView):
  """Update interface when a strip is created"""
  
  getDataObj = project._data2Obj.get
  spectrumDisplay = getDataObj(apiStripSpectrumView.strip.spectrumDisplay)
  enabled = len(spectrumDisplay.strips) > 1
  spectrumDisplay.removeStripAction.setEnabled(enabled)
  
def _deletedStripSpectrumView(project:Project, apiStripSpectrumView:ApiStripSpectrumView):
  """Update interface when a strip is deleted"""
  
  getDataObj = project._data2Obj.get
  spectrumDisplay = getDataObj(apiStripSpectrumView.strip.spectrumDisplay)
  enabled = len(spectrumDisplay.strips) > 2  # 2 not 1 because this strip has not been deleted yet
  spectrumDisplay.removeStripAction.setEnabled(enabled)
  
Project._setupNotifier(_createdStripSpectrumView, ApiStripSpectrumView, 'postInit')
Project._setupNotifier(_deletedStripSpectrumView, ApiStripSpectrumView, 'preDelete')
