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
__author__ = "$Author: CCPN $"
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:39 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"

#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: simon $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

# import importlib, os

from PyQt4 import QtGui, QtCore

from ccpn.core.Project import Project
from ccpn.core.Peak import Peak
from ccpn.core.Spectrum import Spectrum

from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.ToolBar import ToolBar

import typing

from ccpn.ui.gui.widgets.Frame import Frame as Frame
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.PhasingFrame import PhasingFrame
from ccpn.ui.gui.widgets.SpectrumToolBar import SpectrumToolBar

from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier

# suppress messages
#TODO:WAYNE: fix the root cause of this HACK!!!
QtCore.qInstallMsgHandler(lambda *args: None)


class GuiSpectrumDisplay(CcpnModule):

  def __init__(self, parent, name, application):

    super(GuiSpectrumDisplay, self).__init__(parent=parent,
                                             name=name, closeFunc=self._closeModule,
                                             size=(1100, 1300), autoOrientation=False
                                             )
    self.module = self
    self.application = application

    #TODO:GEERTEN; remove this once it has been established that GuiSpectrumDisplay can safely be subcalssed from CcpnModule
    #self.module = CcpnModule(parent=self.window.moduleArea,
    #                         name=self._wrappedData.name, closeFunc=self._closeModule,
    #                         size=(1100,1300), autoOrientation=False)
    #self.window.moduleArea.addModule(self.module, position='right')

    # hack for now
    # inherit application from wrapper insertion
    # self.application = self.module.application
    # derive current and mainWindow from application
    self.mainWindow = self.application.ui.mainWindow
    self.current = self.application.current
    # cannot set self.project because self is a wrapper object
    # self.project = self.application.project

    self.spectrumToolBar = SpectrumToolBar(self.module, widget=self)#, grid=(0, 0), gridSpan=(1, 2))
    self.module.addWidget(self.spectrumToolBar, 0, 0, 1, 2)#, grid=(0, 0), gridSpan=(1, 2))
    self.spectrumToolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
    # screenWidth = QtGui.QApplication.desktop().screenGeometry().width()
    # self.spectrumToolBar.setFixedWidth(screenWidth*0.5)
    #self.resize(self.sizeHint())

    # Utilities Toolbar
    self.spectrumUtilToolBar = ToolBar(self.module)#, grid=(0, 2), gridSpan=(1, 2))
    # self.spectrumUtilToolBar.setFixedWidth(screenWidth*0.4)
    self.spectrumUtilToolBar.setFixedHeight(self.spectrumToolBar.height())
    # grid=(0, 2), gridSpan=(1, 1))
    self.module.addWidget(self.spectrumUtilToolBar, 0, 2)
    if self.application.preferences.general.showToolbar:
      self.spectrumUtilToolBar.show()
    else:
      self.spectrumUtilToolBar.hide()
    # toolBarColour = QtGui.QColor(214,215,213)

    # position box
    self.positionBox = Label(self.module)
    self.module.addWidget(self.positionBox, 0, 3)

    # scroll area
    self.scrollArea = ScrollArea(self.module, grid=(1, 0), gridSpan=(1, 4))
    self.scrollArea.setWidgetResizable(True)
    self.stripFrame = Frame(self.scrollArea, grid=(0, 0))
    self.stripFrame.guiSpectrumDisplay = self
    self.scrollArea.setWidget(self.stripFrame)
    
    #self.setEnabled(True)

    includeDirection = not self.is1D
    self.phasingFrame = PhasingFrame(self.module, includeDirection=includeDirection, callback=self._updatePhasing, returnCallback=self._updatePivot,
                                     directionCallback=self._changedPhasingDirection, grid=(2, 0), gridSpan=(1, 3))
    self.phasingFrame.setVisible(False)

    self.stripFrame.setAcceptDrops(True)
    self.droppedNotifier = GuiNotifier(self.stripFrame,
                                       [GuiNotifier.DROPEVENT], [DropBase.PIDS],
                                       self._processDroppedItems)

    # GWV: this came from previous code, but I am not sure why it was there
    # commented for now
    # self.hoverEvent = self._hoverEvent

  # def _hoverEvent(self, event):
  #   event.accept()

  #def getName(self):
  #  return super(GuiSpectrumDisplay, self).name()
  #name = getName

  def _processDroppedItems(self, data):
    "Process the pids"
    for ii, pid in enumerate(data.get('pids',[])):
      print('GuiSpectrumDisplay._processDroppedItems>>> dropped:', pid)
      self._handlePid(pid)

  #TODO:LUCA: add handling for SpectrumGroup Pids; also do so in BlankDisplay
  def _handlePid(self, pid):
    "handle a; return True in case it is a Spectrum or a SpectrumGroup"
    success = False
    obj = self.project.getByPid(pid)
    if obj is not None and isinstance(obj, Spectrum):
      self.displaySpectrum(obj)
      success = True
    return success

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
    for strip in self.strips:
      strip._unregisterStrip()
    if len(self.application.project.spectrumDisplays) == 1:
      # if self.application.ui.mainWindow is not None:
      #   mainWindow = self.application.ui.mainWindow
      # else:
      #   mainWindow = self.application._mainWindow
      # mainWindow.addBlankDisplay()
      self.mainWindow.addBlankDisplay()
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


  def removeStrip(self, strip=None):
    # changed 6 Jul 2016
    #self.orderedStrips[-1]._unregisterStrip()
    #self.orderedStrips[-1].delete()
    if len(self.orderedStrips) > 1:
      if not strip:
        strip = self.current.strip
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
    self.current.strip._restoreZoom()

  def _storeZoom(self):
    """Saves zoomed region of current strip."""
    self.current.strip._storeZoom()
    
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
    # CCPNINTERNAL - called from GuiMainWindow and from GuiStrip to manage removeStrip button enabling,
    and from Framework to set up initial state
    """
    #TODO:WAYNE: FrameWork should not have anything to do with this
    strip = self.current.strip
    # # Rasmus HACK!
    # # This code broke because it got triggered (via a current notifier) when strips
    # # were deleted but self was not. A bigger fix is needed (TODO), but for now try this
    myStrips = [self.project._data2Obj.get(x) for x in self._wrappedData.strips]
    if len(myStrips) <= 1 or not strip in myStrips:
      # current.strip not in display, or only 1 strip in display, so disable removeStrip button
      enabled = False
    else:
      enabled = True
    self.removeStripAction.setEnabled(enabled)

    # strips = set(self._appBase.current.strips)
    # # Rasmus HACK!
    # # This code broke because it got triggered (via a current notifier) when strips
    # # were deleted but self was not. A bigger fix is needed, but for now try this
    # myStrips = [self._project._data2Obj.get(x) for x in self._wrappedData.strips]
    # myStrips = [x for x in myStrips if x is not None]
    # if len(myStrips) <= 1 or not strips.intersection(myStrips):
    # # if not strips.intersection(self.strips) or len(self.strips) == 1:
    #   # no strip in display is in current.strips, or only 1 strip in display, so disable removeStrip button
    #   enabled = False
    # else:
    #   enabled = True
    # self.removeStripAction.setEnabled(enabled)

def _deletedPeak(peak:Peak):
  """Function for notifiers.
  #CCPNINTERNAL """

  for spectrumView in peak.peakList.spectrum.spectrumViews:
    spectrumView.strip.spectrumDisplay._deletedPeak(peak)

def _spectrumHasChanged(spectrum:Spectrum):
  project = spectrum.project
  apiDataSource = spectrum._wrappedData
  for spectrumDisplay in project.spectrumDisplays:
    action = spectrumDisplay.spectrumActionDict.get(apiDataSource)
    if action: # spectrum might not be in all displays
      # update toolbar button name
      action.setText(spectrum.name)

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
