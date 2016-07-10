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
__author__ = 'simon'

# import importlib, os

from PyQt4 import QtGui, QtCore

from ccpn.core.Project import Project
from ccpn.core.Peak import Peak

from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.ToolBar import ToolBar

import typing

from ccpn.ui.gui.DropBase import DropBase
from ccpn.ui.gui.base.Frame import Frame as GuiFrame
from ccpn.ui.gui.widgets.PhasingFrame import PhasingFrame
from ccpn.ui.gui.modules.GuiModule import GuiModule
from ccpn.ui.gui.widgets.SpectrumToolBar import SpectrumToolBar


class GuiSpectrumDisplay(DropBase, GuiModule):

  def __init__(self):
    GuiModule.__init__(self)
    # DropBase.__init__(self, self._appBase, self.dropCallback)
    self.setAcceptDrops(True)
    self.closeModule = self._closeModule
    self.spectrumToolBar = SpectrumToolBar(self.module, widget=self)#, grid=(0, 0), gridSpan=(1, 2))
    self.module.addWidget(self.spectrumToolBar, 0, 0, 1, 2)#, grid=(0, 0), gridSpan=(1, 2))
    self.module.label.closeButton.clicked.connect(self.closeModule)
    self.spectrumToolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
    # screenWidth = QtGui.QApplication.desktop().screenGeometry().width()
    # self.spectrumToolBar.setFixedWidth(screenWidth*0.5)
    self.resize(self.sizeHint())

    # Toolbar
    self.spectrumUtilToolBar = ToolBar(self.module)#, grid=(0, 2), gridSpan=(1, 2))
    # self.spectrumUtilToolBar.setFixedWidth(screenWidth*0.4)
    self.spectrumUtilToolBar.setFixedHeight(self.spectrumToolBar.height())
    # grid=(0, 2), gridSpan=(1, 1))
    self.module.addWidget(self.spectrumUtilToolBar, 0, 2)
    if self._appBase.preferences.general.showToolbar:
      self.showToolbar()
    else:
      self.hideToolbar()
    # toolBarColour = QtGui.QColor(214,215,213)

    # position box
    self.positionBox = Label(self.module)
    self.module.addWidget(self.positionBox, 0, 3)

    # scroll area
    self.scrollArea = ScrollArea(self.module, grid=(1, 0), gridSpan=(1, 4))
    self.scrollArea.setWidgetResizable(True)
    self.stripFrame = GuiFrame(self.scrollArea, grid=(0, 0), appBase=self._appBase)
    self.stripFrame.guiSpectrumDisplay = self
    self.stripFrame.setAcceptDrops(True)
    self.scrollArea.setWidget(self.stripFrame)
    
    self.setEnabled(True)

    includeDirection = not self._wrappedData.is1d
    self.phasingFrame = PhasingFrame(self.module, includeDirection=includeDirection, callback=self._updatePhasing, returnCallback=self._updatePivot,
                                     directionCallback=self._changedPhasingDirection, grid=(2, 0), gridSpan=(1, 3))
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
      
  def _updatePivot(self):
    """Updates pivot in all strips contained in the spectrum display."""
    for strip in self.strips:
      strip._updatePivot()
    
  def _updatePhasing(self):
    """Updates phasing in all strips contained in the spectrum display."""
    for strip in self.strips:
      strip._updatePhasing()
    
  def _changedPhasingDirection(self):
    """Changes direction of phasing from horizontal to vertical or vice versa."""
    for strip in self.strips:
      strip._changedPhasingDirection()
    
  def togglePhaseConsole(self):
    """Toggles whether phasing console is displayed.
    """
    isVisible = not self.phasingFrame.isVisible()
    self.phasingFrame.setVisible(isVisible)
    for strip in self.strips:
      if isVisible:
        strip.turnOnPhasing()
      else:
        strip.turnOffPhasing()
    self._updatePhasing()

  def showToolbar(self):
    """show the toolbar"""
    # showing the toolbar, but we need to update the checkboxes of all strips as well.
    self.spectrumUtilToolBar.show()
    for strip in self.strips:
      strip.toolbarAction.setChecked(True)

  def hideToolbar(self):
    """hide the toolbar"""
    # hiding the toolbar, but we need to update the checkboxes of all strips as well.
    self.spectrumUtilToolBar.hide()
    for strip in self.strips:
      strip.toolbarAction.setChecked(False)

  def toggleToolbar(self):
    """Toggle the toolbar """
    if not self.spectrumUtilToolBar.isVisible():
      self.showToolbar()
    else:
      self.hideToolbar()

  def _closeModule(self):
    """
    Closes spectrum display and deletes it from the project.
    """
    if len(self._appBase.project.spectrumDisplays) == 1:
      if self._appBase.ui.mainWindow is not None:
        mainWindow = self._appBase.ui.mainWindow
      else:
        mainWindow = self._appBase._mainWindow
      mainWindow.addBlankDisplay()
    # self.module.close()
    self.delete()

  def _fillToolBar(self):
    """
    # CCPN INTERNAL - called in _fillToolBar methods of GuiStripDisplay1d and GuiStripDisplayNd
    Puts icons for addition and removal of strips into the spectrum utility toolbar.
    """
    addStripAction = self.spectrumUtilToolBar.addAction('Add Strip', self.duplicateStrip) #self.orderedStrips[0].clone()) # clone first strip
    addStripIcon = Icon('icons/plus')
    addStripAction.setIcon(addStripIcon)
    removeStripAction = self.spectrumUtilToolBar.addAction('Remove Strip', self.removeStrip) # remove last strip
    removeStripIcon = Icon('icons/minus')
    removeStripAction.setIcon(removeStripIcon)
    self.removeStripAction = removeStripAction


  def removeStrip(self):
    # changed 6 Jul 2016
    #self.orderedStrips[-1]._unregisterStrip()
    #self.orderedStrips[-1].delete()
    if len(self.orderedStrips) > 1:
      strip = self._appBase.current.strip
      if strip:
        strip._unregisterStrip()
        strip.delete()

  def duplicateStrip(self):
    """
    Creates a new strip identical to the last one created and adds it to right of the display.
    """
    newStrip = self.strips[-1].clone()

  def resetYZooms(self):
    """Zooms Y axis of current strip to show entire region"""
    for strip in self.strips:
      strip.resetYZoom()

  def resetXZooms(self):
    """Zooms X axis of current strip to show entire region"""
    for strip in self.strips:
      strip.resetXZoom()

  def _restoreZoom(self):
    """Restores last saved zoom of current strip."""
    self._appBase.current.strip._restoreZoom()

  def _storeZoom(self):
    """Saves zoomed region of current strip."""
    self._appBase.current.strip._storeZoom()
    
  def toggleCrossHair(self):
    """Toggles whether cross hair is displayed in all strips of spectrum display."""
    # toggle crosshairs for strips in this spectrumDisplay
    for strip in self.strips:
      strip._toggleCrossHair()
    
  def toggleGrid(self):
    """Toggles whether grid is displayed in all strips of spectrum display."""
    # toggle grid for strips in this spectrumDisplay
    for strip in self.strips:
      strip.toggleGrid()
    
  def _setCrossHairPosition(self, axisPositionDict:typing.Dict[str, float]):
    """
    #CCPN INTERNAL
    Sets the position of the cross in all strips of spectrum display."""
    for strip in self.strips:
      strip._setCrossHairPosition(axisPositionDict)
  #
  # def _setActionIconColour(self, apiDataSource):
  #   action = self.spectrumActionDict.get(apiDataSource)
  #   if action:
  #     pix=QtGui.QPixmap(QtCore.QSize(60, 10))
  #     if apiDataSource.numDim < 2:
  #       pix.fill(QtGui.QColor(apiDataSource.sliceColour))
  #     else:
  #       pix.fill(QtGui.QColor(apiDataSource.positiveContourColour))
  #     action.setIcon(QtGui.QIcon(pix))

  def _deletedPeak(self, peak):
    apiPeak = peak._wrappedData
    # NBNB TBD FIXME rewrite this to not use API peaks
    # ALSO move this machinery from subclasses to this class.
    for peakListView in self.activePeakItemDict:
      peakItemDict = self.activePeakItemDict[peakListView]
      peakItem = peakItemDict.get(apiPeak)
      if peakItem:
        peakListView.spectrumView.strip.plotWidget.scene().removeItem(peakItem)
        del peakItemDict[apiPeak]
        inactivePeakItems = self.inactivePeakItemDict.get(peakListView)
        if inactivePeakItems:
          inactivePeakItems.add(peakItem)

  def _resetRemoveStripAction(self):
    """
    # CCPN INTERNAL - called from GuiMainWindow and from GuiStrip to manage removeStrip button enabling,
    and from Framework to set up initial state
    """
    strips = set(self._appBase.current.strips)
    if not strips.intersection(self.strips) or len(self.strips) == 1:
      # no strip in display is in current.strips, or only 1 strip in display, so disable removeStrip button
      enabled = False
    else:
      enabled = True
    self.removeStripAction.setEnabled(enabled)

def _deletedPeak(peak:Peak):
  """Function for notifiers.
  #CCPNINTERNAL """

  for spectrumView in peak.peakList.spectrum.spectrumViews:
    spectrumView.strip.spectrumDisplay._deletedPeak(peak)

def _deletedSpectrumView(project:Project, apiSpectrumView):
  """tear down SpectrumDisplay when new SpectrumView is deleted - for notifiers"""
  spectrumDisplay = project._data2Obj[apiSpectrumView.spectrumDisplay]
  apiDataSource = apiSpectrumView.dataSource

  # remove toolbar action (button)
  # NBNB TBD FIXME get rid of API object from code
  action = spectrumDisplay.spectrumActionDict.get(apiDataSource)  # should always be not None
  if action:
    spectrumDisplay.spectrumToolBar.removeAction(action)
    del spectrumDisplay.spectrumActionDict[apiDataSource]
