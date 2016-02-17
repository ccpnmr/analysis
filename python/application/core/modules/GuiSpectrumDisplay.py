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

from ccpncore.api.ccp.nmr.Nmr import DataSource as ApiDataSource
from ccpncore.api.ccp.nmr.Nmr import Peak as ApiPeak

from ccpncore.api.ccpnmr.gui.Task import StripSpectrumView as ApiStripSpectrumView
from ccpncore.api.ccpnmr.gui.Task import StripPeakListView as ApiStripPeakListView

from ccpncore.gui.Frame import Frame as CoreFrame
from ccpncore.gui.Icon import Icon
from ccpncore.gui.Label import Label
from ccpncore.gui.ScrollArea import ScrollArea
from ccpncore.gui.ToolBar import ToolBar

from ccpncore.util import Types

from application.core.DropBase import DropBase
from application.core.gui.Frame import Frame as GuiFrame
from application.core.gui.PhasingFrame import PhasingFrame
from application.core.gui.SpectrumToolBar import SpectrumToolBar
from application.core.modules.GuiModule import GuiModule
# from application.core.util.Svg import Svg

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
    # grid=(0, 2), gridSpan=(1, 1))
    self.dock.addWidget(self.spectrumUtilToolBar, 0, 2)
    if self._appBase.preferences.general.toolbarHidden is True:
      self.spectrumUtilToolBar.hide()
    else:
      self.spectrumUtilToolBar.show()
    # toolBarColour = QtGui.QColor(214,215,213)
    self.positionBox = Label(self.dock)
    self.dock.addWidget(self.positionBox, 0, 3)#, grid=(0, 3), gridSpan=(1, 1))
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

    includeDirection = not self._wrappedData.is1d
    self.phasingFrame = PhasingFrame(self.dock, includeDirection=includeDirection, callback=self.updatePhasing, returnCallback=self.updatePivot,
                                     directionCallback=self.changedPhasingDirection, grid=(2, 0), gridSpan=(1, 3))
    self.phasingFrame.setVisible(False)

  def printToFile(self, path, width=800, height=800):

    #generator = QtSvg.QSvgGenerator()
    #generator.setFileName(path)
    #generator.setSize(QtCore.QSize(1600, 1600)) # TBD
    #generator.setViewBox(QtCore.QRect(0, 0, 1600, 1600))
    #if title:
    #  generator.setTitle(title)

    #painter = QtGui.QPainter()
    #painter.begin(generator)
    #self.plotWidget.scene().render(painter)
    #painter.end()
    
    nstrips = len(self.strips)
    if nstrips == 0:
      return
    # with open(path, 'wt') as fp:
    #   printer = Svg(fp, width, height) # TBD: more general
    #
    #   # box
    #   printer.writeLine(0, 0, width, 0)
    #   printer.writeLine(width, 0, width, height)
    #   printer.writeLine(width, height, 0, height)
    #   printer.writeLine(0, height, 0, 0)
    #
    #   for n, strip in enumerate(self.strips):
    #     # TBD need to calculate offset, etc., for coords, and pass those along
    #     if self.stripDirection == 'X':
    #       xOutputRegion = (0, width)
    #       yOutputRegion = (n*height/nstrips, (n+1)*height/nstrips)
    #       if n > 0:
    #         # strip separator
    #         printer.writeLine(0, yOutputRegion[0], width, yOutputRegion[0])
    #     else:
    #       xOutputRegion = (n*width/nstrips, (n+1)*width/nstrips)
    #       yOutputRegion = (0, height)
    #       if n > 0:
    #         # strip separator
    #         printer.writeLine(xOutputRegion[0], 0, xOutputRegion[0], height)
    #     printer.startRegion(xOutputRegion, yOutputRegion)
    #     strip.printToFile(printer)
    #   printer.close()
      
  def updatePivot(self):
    """Updates pivot in all strips contained in the spectrum display."""
    for strip in self.strips:
      strip.updatePivot()
    
  def updatePhasing(self):
    """Updates phasing in all strips contained in the spectrum display."""
    for strip in self.strips:
      strip.updatePhasing()
    
  def changedPhasingDirection(self):
    """Changes direction of phasing from horizontal to vertical or vice versa."""
    for strip in self.strips:
      strip.changedPhasingDirection()
    
  def togglePhaseConsole(self):
    """
    Toggles whether phasing console is displayed.
    """
    isVisible = not self.phasingFrame.isVisible()
    self.phasingFrame.setVisible(isVisible)
    for strip in self.strips:
      if isVisible:
        strip.turnOnPhasing()
      else:
        strip.turnOffPhasing()
         
    self.updatePhasing()

  def closeDock(self):
    """
    Closes spectrum display and deletes it from the project.
    """
    self.delete()

  def fillToolBar(self):
    """
    Puts icons for addition and removal of strips into the spectrum utility toolbar.
    """
    addStripAction = self.spectrumUtilToolBar.addAction('Add Strip', self.duplicateStrip) #self.orderedStrips[0].clone()) # clone first strip
    addStripIcon = Icon('iconsNew/plus')
    addStripAction.setIcon(addStripIcon)
    removeStripAction = self.spectrumUtilToolBar.addAction('Remove Strip', lambda self=self: self.orderedStrips[-1].delete()) # remove last strip
    removeStripIcon = Icon('iconsNew/minus')
    removeStripAction.setIcon(removeStripIcon)
    self.removeStripAction = removeStripAction

  def duplicateStrip(self):
    """
    Creates a new strip identical to the last one created and adds it to right of the display.
    """
    newStrip = self.strips[-1].clone()

  def hideUtilToolBar(self):
    """
    Hides the spectrum utility toolbar
    """
    self.spectrumUtilToolBar.hide()


  def zoomYAll(self):
    """Zooms Y axis of current strip to show entire region"""
    self._appBase.current.strip.zoomYAll()

  def zoomXAll(self):
    """Zooms X axis of current strip to show entire region"""
    self._appBase.current.strip.zoomXAll()

  def restoreZoom(self):
    """Restores last saved zoom of current strip."""
    self._appBase.current.strip.restoreZoom()

  def storeZoom(self):
    """Saves zoomed region of current strip."""
    self._appBase.current.strip.storeZoom()
    
  def toggleCrossHair(self):
    """Toggles whether cross hair is displayed in all strips of spectrum display."""
    # toggle crosshairs for strips in this spectrumDisplay
    for strip in self.strips:
      strip.toggleCrossHair()
    
  def toggleGrid(self):
    """Toggles whether grid is displayed in all strips of spectrum display."""
    # toggle grid for strips in this spectrumDisplay
    for strip in self.strips:
      strip.toggleGrid()
    
  def setCrossHairPosition(self, axisPositionDict:Types.Dict[str, float]):
    """Sets the position of the cross in all strips of spectrum display."""
    for strip in self.strips:
      strip.setCrossHairPosition(axisPositionDict)

  def _setActionIconColour(self, apiDataSource):
    action = self.spectrumActionDict.get(apiDataSource)
    if action:
      pix=QtGui.QPixmap(QtCore.QSize(60, 10))
      if apiDataSource.numDim < 2:
        pix.fill(QtGui.QColor(apiDataSource.sliceColour))
        for strip in self.strips:
          for spectrumView in strip.spectrumViews:
            spectrumView.plot.setPen(apiDataSource.sliceColour)
      else:
        pix.fill(QtGui.QColor(apiDataSource.positiveContourColour))
      action.setIcon(QtGui.QIcon(pix))
    
def _createdStripSpectrumView(project:Project, apiStripSpectrumView:ApiStripSpectrumView):
  """Update interface when a strip is created"""
  
  spectrumDisplay = project._data2Obj[apiStripSpectrumView.strip.spectrumDisplay]
  enabled = len(spectrumDisplay.strips) > 1
  spectrumDisplay.removeStripAction.setEnabled(enabled)
  
def _deletedStripSpectrumView(project:Project, apiStripSpectrumView:ApiStripSpectrumView):
  """Update interface when a strip is deleted"""
  
  spectrumView = project._data2Obj[apiStripSpectrumView]
  strip = spectrumView.strip
  spectrumDisplay = strip.spectrumDisplay
  scene = strip.plotWidget.scene()
  scene.removeItem(spectrumView)
  if hasattr(spectrumView, 'plot'):  # 1d
    scene.removeItem(spectrumView.plot)
  
  enabled = len(spectrumDisplay.strips) > 2  # 2 not 1 because this strip has not been deleted yet
  spectrumDisplay.removeStripAction.setEnabled(enabled)
  
  
Project._setupNotifier(_createdStripSpectrumView, ApiStripSpectrumView, 'postInit')
Project._setupNotifier(_deletedStripSpectrumView, ApiStripSpectrumView, 'preDelete')

def _createdStripPeakListView(project:Project, apiStripPeakListView:ApiStripPeakListView):
  apiDataSource = apiStripPeakListView.stripSpectrumView.spectrumView.dataSource
  getDataObj = project._data2Obj.get
  peakListView = getDataObj(apiStripPeakListView)
  spectrumView = peakListView.spectrumView
  action = spectrumView.strip.spectrumDisplay.spectrumActionDict.get(apiDataSource)
  if action:
    action.toggled.connect(peakListView.setVisible) # TBD: need to undo this if peakListView removed

  strip = spectrumView.strip
  for apiPeakList in apiDataSource.sortedPeakLists():
    strip.showPeaks(getDataObj(apiPeakList))

Project._setupNotifier(_createdStripPeakListView, ApiStripPeakListView, 'postInit')

def _setActionIconColour(project:Project, apiDataSource:ApiDataSource):

  # TBD: the below might not be the best way to get hold of the spectrumDisplays
  for task in project.tasks:
    if task.status == 'active':
      for spectrumDisplay in task.spectrumDisplays:
        spectrumDisplay._setActionIconColour(apiDataSource)

for apiFuncName in ('setPositiveContourColour', 'setSliceColour'):
  Project._setupNotifier(_setActionIconColour, ApiDataSource, apiFuncName)

def _deletedPeak(project:Project, apiPeak:ApiPeak):
  
  # TBD: the below might not be the best way to get hold of the spectrumDisplays
  for task in project.tasks:
    if task.status == 'active':
      for spectrumDisplay in task.spectrumDisplays:
        spectrumDisplay._deletedPeak(apiPeak)

Project._setupNotifier(_deletedPeak, ApiPeak, 'preDelete')

