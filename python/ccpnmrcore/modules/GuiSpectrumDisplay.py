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


from ccpncore.gui.Label import Label
from ccpncore.gui.ScrollArea import ScrollArea
from ccpncore.gui.ToolBar import ToolBar

from ccpnmrcore.DropBase import DropBase
from ccpnmrcore.gui.Frame import Frame as GuiFrame
from ccpnmrcore.modules.GuiModule import GuiModule

def _findPpmRegion(spectrum, axisDim, spectrumDim):

  pointCount = spectrum.pointCounts[spectrumDim]
  if axisDim < 2: # want entire region
    region = (0, pointCount)
  else:
    n = pointCount // 2
    region = (n, n+1)

  firstPpm, lastPpm = spectrum.getDimValueFromPoint(spectrumDim, region)

  return 0.5*(firstPpm+lastPpm), abs(lastPpm-firstPpm)


class GuiSpectrumDisplay(DropBase, GuiModule):

  def __init__(self):
    GuiModule.__init__(self)
    # DropBase.__init__(self, self._appBase, self.dropCallback)
    self.setAcceptDrops(True)
    self.spectrumToolBar = ToolBar(self.dock)#, grid=(0, 0), gridSpan=(1, 2))
    self.dock.addWidget(self.spectrumToolBar, 0, 0, 1, 2)#, grid=(0, 0), gridSpan=(1, 2))

    self.spectrumToolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
    screenWidth  = QtGui.QApplication.desktop().screenGeometry().width()
    # self.spectrumToolBar.setFixedWidth(screenWidth*0.5)
    self.spectrumUtilToolBar = ToolBar(self.dock)#, grid=(0, 2), gridSpan=(1, 2))
    # self.spectrumUtilToolBar.setFixedWidth(screenWidth*0.4)
    self.dock.addWidget(self.spectrumUtilToolBar, 0, 2)# grid=(0, 2), gridSpan=(1, 1))
    toolBarColour = QtGui.QColor(214,215,213)
    palette = QtGui.QPalette(self.spectrumUtilToolBar.palette())
    palette2 = QtGui.QPalette(self.spectrumToolBar.palette())
    palette.setColor(QtGui.QPalette.Button,toolBarColour)
    palette2.setColor(QtGui.QPalette.Button,toolBarColour)
    self.positionBox = Label(self.dock)#, grid=(0, 3), gridSpan=(1, 1))
    self.dock.addWidget(self.positionBox, 0, 3)#, grid=(0, 3), gridSpan=(1, 1))
    # self.positionBox.setFixedWidth(screenWidth*0.1)
    self.scrollArea = ScrollArea(self.dock, grid=(1, 0), gridSpan=(1, 4))
    # self.dock.addWidget(self.scrollArea, 1, 0, 1, 4)
    self.scrollArea.setWidgetResizable(True)
    self.stripFrame = GuiFrame(self.scrollArea, grid=(0, 0), appBase=self._appBase)
    # self.stripFrame.layout().setContentsMargins(0, 0, 2, 0)
    self.stripFrame.setAcceptDrops(True)
    self.assignmentDirection = 'i-1'

    self.scrollArea.setWidget(self.stripFrame)

  def fillToolBar(self):

    self.spectrumUtilToolBar.addAction('+', lambda self=self: self.orderedStrips[0].clone()) # clone first strip
    self.spectrumUtilToolBar.addAction('-', lambda self=self: self.orderedStrips[-1].delete()) # remove last strip

  def zoomYAll(self):
    for strip in self.strips:
      strip.zoomYAll()

  def zoomXAll(self):
    self.currentStrip.zoomXAll()

  def restoreZoom(self):
    self.currentStrip.restoreZoom()

  def storeZoom(self):
    self.currentStrip.storeZoom()
    
    