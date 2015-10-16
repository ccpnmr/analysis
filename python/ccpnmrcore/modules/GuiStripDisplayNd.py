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
# from ccpn.lib._wrapper import Spectrum as LibSpectrum

__author__ = 'simon'
from PyQt4 import QtCore, QtGui

from ccpn import Project

from ccpncore.api.ccp.nmr.Nmr import DataSource as ApiDataSource
from ccpncore.api.ccp.nmr.Nmr import Peak as ApiPeak
from ccpncore.api.ccpnmr.gui.Task import SpectrumView as ApiSpectrumView
from ccpncore.api.ccpnmr.gui.Task import FreeStrip as ApiFreeStrip
from ccpncore.api.ccpnmr.gui.Task import BoundDisplay as ApiBoundDisplay
from ccpncore.api.ccpnmr.gui.Task import StripSpectrumView as ApiStripSpectrumView
from ccpncore.api.ccpnmr.gui.Task import StripPeakListView as ApiStripPeakListView

#from ccpncore.memops import Notifiers

from ccpncore.gui.Icon import Icon
from ccpncore.gui.VerticalLabel import VerticalLabel

from ccpnmrcore.modules.GuiSpectrumDisplay import GuiSpectrumDisplay
from ccpnmrcore.modules.GuiStripNd import GuiStripNd

from ccpnmrcore.modules.spectrumItems.GuiPeakListView import PeakNd

class GuiStripDisplayNd(GuiSpectrumDisplay):




  def __init__(self):
    # if not apiSpectrumDisplayNd.strips:
    #   apiSpectrumDisplayNd.newStripNd()
    
    ##self.viewportDict = {} # maps QGLWidget to GuiStripNd

    # below are so we can reuse PeakItems and only create them as needed
    self.activePeakItemDict = {}  # maps peakListView to apiPeak to peakItem for peaks which are being displayed
    # cannot use (wrapper) peak as key because project._data2Obj dict invalidates mapping before deleted callback is called
    # TBD: this might change so that we can use wrapper peak (which would make nicer code in showPeaks and deletedPeak below)
    self.inactivePeakItems = set() # contains unused peakItems
    
    GuiSpectrumDisplay.__init__(self)
    
    #Notifiers.registerNotify(self._deletedPeak, 'ccp.nmr.Nmr.Peak', 'delete')
    # Notifiers.registerNotify(self._addedStripSpectrumView, 'ccpnmr.gui.Task.StripSpectrumView', '__init__')
    # Notifiers.registerNotify(self._removedStripSpectrumView, 'ccpnmr.gui.Task.StripSpectrumView', 'delete')
    # for func in ('setPositiveContourColour', 'setSliceColour'):
    #   Notifiers.registerNotify(self._setActionIconColour, 'ccp.nmr.Nmr.DataSource', func)
    
    self.spectrumActionDict = {}  # apiDataSource --> toolbar action (i.e. button)
    # self._apiStripSpectrumViews = set()  # set of apiStripSpectrumViews seen so far

    self.fillToolBar()
    self.setAcceptDrops(True)
    if self._appBase.preferences.general.toolbarHidden:
      GuiSpectrumDisplay.hideUtilToolBar(self)
    # self.addSpinSystemSideLabel()
    # self._appBase.current.pane = self

  # def addSpectrum(self, spectrum):
  #
  #   apiSpectrumDisplay = self._apiSpectrumDisplay
  #
  #   #axisCodes = spectrum.axisCodes
  #   axisCodes = LibSpectrum.getAxisCodes(spectrum)
  #   if axisCodes != self._apiSpectrumDisplay.axisCodes:
  #     raise Exception('Cannot overlay that spectrum on this display')
  #
  #   apiDataSource = spectrum._wrappedData
  #   apiSpectrumView = apiSpectrumDisplay.findFirstSpectrumView(dataSource=apiDataSource)
  #   if apiSpectrumView:
  #     raise Exception('Spectrum already in display')
  #
  #   dimensionCount = spectrum.dimensionCount
  #   dimensionOrdering = range(1, dimensionCount+1)
  #   apiSpectrumView = apiSpectrumDisplay.newSpectrumView(spectrumName=apiDataSource.name,
  #                         dimensionOrdering=dimensionOrdering)
  #   guiSpectrumView = GuiSpectrumViewNd(self, apiSpectrumView)
  #
  #   # at this point likely there is only one guiStrip???
  #   if not apiSpectrumDisplay.axes: # need to create these since not done automatically
  #     # TBD: assume all strips the same and the strip direction is the Y direction
  #     for m, axisCode in enumerate(apiSpectrumDisplay.axisCodes):
  #       position, width = _findPpmRegion(spectrum, m, dimensionOrdering[m]-1) # -1 because dimensionOrdering starts at 1
  #       for n, guiStrip in enumerate(self.guiStrips):
  #         if m == 1: # Y direction
  #           if n == 0:
  #             apiSpectrumDisplay.newFrequencyAxis(code=axisCode, position=position, width=width, stripSerial=1)
  #         else: # other directions
  #           apiSpectrumDisplay.newFrequencyAxis(code=axisCode, position=position, width=width, stripSerial=1) # TBD: non-frequency axis; TBD: should have stripSerial=0 but that not working
  #
  #         viewBox = guiStrip.viewBox
  #         region = (position-0.5*width, position+0.5*width)
  #         if m == 0:
  #           viewBox.setXRange(*region)
  #         elif m == 1:
  #           viewBox.setYRange(*region)
  #
  #   for guiStrip in self.guiStrips:
  #     guiStrip.addSpectrum(guiSpectrumView)
  #
  def addStrip(self):
    newStrip = self.strips[0].clone()
    return newStrip
  # print('addNewStrip')
  #   print(self.stripFrame.layout())
  #   axisCodes = self.strips[0].axisCodes
  #   print(axisCodes)
  #   # print(newStrip)

    # self.stripFrame.layout().addWidget(newGuiStrip)
  #
  #   apiStrip = self._apiSpectrumDisplay.newStripNd()
  #   n = len(self._apiSpectrumDisplay.strips) - 1
  #   guiStrip = GuiStripNd(self.stripFrame, apiStrip, grid=(1, n), stretch=(0, 1))
  #   guiStrip.addPlaneToolbar(self.stripFrame, n)
  #   guiStrip.addSpinSystemLabel(self.stripFrame, n)
  #   if n > 0:
  #     prevGuiStrip = self.guiStrips[n-1]
  #     prevGuiStrip.axes['right']['item'].hide()
  #     guiStrip.setYLink(prevGuiStrip)

  # def fillToolBar(self):
  #   GuiSpectrumDisplay.fillToolBar(self)
    # self.spectrumUtilToolBar.addAction(QtGui.QAction('HS', self, triggered=self.hideSpinSystemLabel))
    # self.spectrumUtilToolBar.addAction(QtGui.QAction("SS", self, triggered=self.showSpinSystemLabel))

  def showSpinSystemLabel(self):
    self.spinSystemSideLabel.show()

  def hideSpinSystemLabel(self):
    self.hideSystemSideLabel.show()

  def addSpinSystemSideLabel(self):

    dock = self.dock
    self.spinSystemSideLabel = VerticalLabel(self.dock, text='test', grid=(1, 0), gridSpan=(1, 1))
    self.spinSystemSideLabel.setFixedWidth(30)

  def fillToolBar(self):

    GuiSpectrumDisplay.fillToolBar(self)
    
    spectrumUtilToolBar = self.spectrumUtilToolBar
    
    plusOneAction = spectrumUtilToolBar.addAction("+1", self.addOne)
    plusOneIcon = Icon('iconsNew/contour-add')
    plusOneAction.setIcon(plusOneIcon)
    plusOneAction.setToolTip('Add One Level')
    minusOneAction = spectrumUtilToolBar.addAction("+1", self.subtractOne)
    minusOneIcon = Icon('iconsNew/contour-remove')
    minusOneAction.setIcon(minusOneIcon)
    minusOneAction.setToolTip('Remove One Level ')
    upBy2Action = spectrumUtilToolBar.addAction("*1.4", self.upBy2)
    upBy2Icon = Icon('iconsNew/contour-base-up')
    upBy2Action.setIcon(upBy2Icon)
    upBy2Action.setToolTip('Raise Contour Base Level')
    downBy2Action = spectrumUtilToolBar.addAction("/1.4", self.downBy2)
    downBy2Icon = Icon('iconsNew/contour-base-down')
    downBy2Action.setIcon(downBy2Icon)
    downBy2Action.setToolTip('Lower Contour Base Level')
    storeZoomAction = spectrumUtilToolBar.addAction("Store Zoom", self.storeZoom)
    storeZoomIcon = Icon('iconsNew/zoom-store')
    storeZoomAction.setIcon(storeZoomIcon)
    storeZoomAction.setToolTip('Store Zoom')
    restoreZoomAction = spectrumUtilToolBar.addAction("Restore Zoom", self.restoreZoom)
    restoreZoomIcon = Icon('iconsNew/zoom-restore')
    restoreZoomAction.setIcon(restoreZoomIcon)
    restoreZoomAction.setToolTip('Restore Zoom')


  def upBy2(self):

    for spectrumView in self.spectrumViews:
      if spectrumView.isVisible():
        apiDataSource = spectrumView._wrappedData.spectrumView.dataSource
        apiDataSource.positiveContourBase *= apiDataSource.positiveContourFactor
        apiDataSource.negativeContourBase *= apiDataSource.negativeContourFactor
        spectrumView.update()

  def downBy2(self):

    for spectrumView in self.spectrumViews:
      if spectrumView.isVisible():
        apiDataSource = spectrumView._wrappedData.spectrumView.dataSource
        apiDataSource.positiveContourBase /= apiDataSource.positiveContourFactor
        apiDataSource.negativeContourBase /= apiDataSource.negativeContourFactor
        spectrumView.update()
  def addOne(self):

    for spectrumView in self.spectrumViews:
      if spectrumView.isVisible():
        apiDataSource = spectrumView._wrappedData.spectrumView.dataSource
        apiDataSource.positiveContourCount += 1
        apiDataSource.negativeContourCount += 1

  def subtractOne(self):

    for spectrumView in self.spectrumViews:
      if spectrumView.isVisible():
        apiDataSource = spectrumView._wrappedData.spectrumView.dataSource
        if apiDataSource.positiveContourCount > 0:
          apiDataSource.positiveContourCount -= 1
        if apiDataSource.negativeContourCount > 0:
          apiDataSource.negativeContourCount -= 1

  def showPeaks(self, peakListView, peaks):
  
    viewBox = peakListView.spectrumView.strip.viewBox
    activePeakItemDict = self.activePeakItemDict
    peakItemDict = activePeakItemDict.setdefault(peakListView, {})
    inactivePeakItems = self.inactivePeakItems
    existingApiPeaks = set(peakItemDict.keys())
    unusedApiPeaks = existingApiPeaks - set([peak._wrappedData for peak in peaks])
    for apiPeak in unusedApiPeaks:
      peakItem = peakItemDict.pop(apiPeak)
      viewBox.removeItem(peakItem)
      inactivePeakItems.add(peakItem)
    for peak in peaks:
      apiPeak = peak._wrappedData
      if apiPeak in existingApiPeaks:
        continue
      if inactivePeakItems:
        peakItem = inactivePeakItems.pop()
        peakItem.setupPeakItem(peakListView, peak)
        viewBox.addItem(peakItem)
      else:
        peakItem = PeakNd(peakListView, peak)
      peakItemDict[apiPeak] = peakItem
    
  def _deletedPeak(self, apiPeak):
    for peakListView in self.activePeakItemDict:
      peakItemDict = self.activePeakItemDict[peakListView]
      peakItem = peakItemDict.get(apiPeak)
      if peakItem:
        peakListView.spectrumView.strip.plotWidget.scene().removeItem(peakItem)
        del peakItemDict[apiPeak]
        self.inactivePeakItems.add(peakItem)
      


  # def wheelEvent(self, event):
  #   event.accept()
  #   print(event)
  #   if event.modifiers() & QtCore.Qt.ShiftModifier:
  #     if event.delta() > 0:
  #         self.upBy2()
  #     else:
  #       self.downBy2()
  #         # spectrumItem.update()
  #   elif not event.modifiers():
  #     QtGui.QGraphicsView.wheelEvent(self, event)
  #     sc = 1.001 ** event.delta()
  #     #self.scale *= sc
  #     #self.updateMatrix()
  #     self.scale(sc, sc)
    # elif event.modifiers() & QtCore.Qt.ControlModifier:
    #   if event.delta() > 0:
    #      self.increaseTraceScale()
    #   else:
    #     self.decreaseTraceScale()
    # else:
    #   event.ignore

  # def _addedStripSpectrumView(self, apiStripSpectrumView):
  #   apiSpectrumDisplay = self._wrappedData
  #   if apiSpectrumDisplay is not apiStripSpectrumView.strip.spectrumDisplay:
  #     return
  #
  #   # cannot deal with wrapper spectrum object because that not ready yet when this notifier is called
  #   apiDataSource = apiStripSpectrumView.spectrumView.dataSource
  #   action = self.spectrumActionDict.get(apiDataSource)
  #   if not action:
  #     # add toolbar action (button)
  #     action = self.spectrumToolBar.addAction(apiDataSource.name)
  #     action.setCheckable(True)
  #     action.setChecked(True)
  #     widget = self.spectrumToolBar.widgetForAction(action)
  #     widget.setFixedSize(60, 30)
  #     self.spectrumActionDict[apiDataSource] = action  # have to use wrappedData because wrapper object disappears before delete notifier is called
  #     self._setActionIconColour(apiDataSource)
  #   if apiStripSpectrumView not in self._apiStripSpectrumViews:
  #     spectrumView = self._project._data2Obj[apiStripSpectrumView]
  #     action.toggled.connect(spectrumView.setVisible)
  #     self._apiStripSpectrumViews.add(apiStripSpectrumView)
  #
  #   return action
  #
  # def _apiDataSourcesInDisplay(self):
  #   apiDataSources = set()
  #   for strip in self.strips:
  #     for spectrumView in strip.spectrumViews:
  #       apiDataSources.add(spectrumView.spectrum._wrappedData)
  #   return apiDataSources
  #
  # def _removedStripSpectrumView(self, apiStripSpectrumView):
  #   # cannot deal with wrapper spectrum object because already disappears when this notifier is called
  #   apiDataSources = self._apiDataSourcesInDisplay()
  #   apiDataSource = apiStripSpectrumView.spectrumView.dataSource
  #   if apiDataSource not in apiDataSources:
  #     # remove toolbar action (button)
  #     action = self.spectrumActionDict.get(apiDataSource)  # should always be not None (correct??)
  #     if action:
  #       self.spectrumToolBar.removeAction(action)
  #       del self.spectrumActionDict[apiDataSource]
  #     if apiStripSpectrumView in self._apiStripSpectrumViews:  # should always be the case
  #       self._apiStripSpectrumViews.remove(apiStripSpectrumView)
          

  # def raiseContextMenu(self, event):
  #   print('event',event)
  #   # from ccpncore.gui.Menu import Menu
  #   # contextMenu = Menu('', self, isFloatWidget=True)
  #   # from functools import partial
  #   # contextMenu.addAction('Delete', partial(self.removeSpectrum, action))
  #   # return contextMenu
  #
  # def removeSpectrum(self, action):
  #   self.spectrumToolBar.removeAction(action)
  #
  #   # print(self, widget)

  def _setActionIconColour(self, apiDataSource):
    action = self.spectrumActionDict.get(apiDataSource)
    if action:
      pix=QtGui.QPixmap(QtCore.QSize(60, 10))
      if apiDataSource.numDim < 2: # irrelevant here, but need if this code moves to GuiSpectrumDisplay
        pix.fill(QtGui.QColor(apiDataSource.sliceColour))
      else:
        pix.fill(QtGui.QColor(apiDataSource.positiveContourColour))
      action.setIcon(QtGui.QIcon(pix))

  # def _spectrumViewsInDisplay(self):
  #   spectrumViews = set()
  #   for strip in self.strips:
  #     spectrumViews.update(strip.spectrumViews)
  #   return spectrumViews


def _createdSpectrumView(project:Project, apiSpectrumView:ApiSpectrumView):
  """Set up SpectrumDisplay when new SpectrumView is created - for notifiers"""
  
  getDataObj = project._data2Obj.get
  spectrumDisplay = getDataObj(apiSpectrumView.spectrumDisplay)
  if not isinstance(spectrumDisplay, GuiStripDisplayNd):
    return

  apiDataSource = apiSpectrumView.dataSource
  action = spectrumDisplay.spectrumActionDict.get(apiDataSource)  # should always be None
  if not action:
    # add toolbar action (button)
    if len(apiDataSource.name) <= 12:
      spectrumName = apiDataSource.name
    elif len(apiDataSource.name) > 12:
      spectrumName = apiDataSource.name[:12]+'.....'
    action = spectrumDisplay.spectrumToolBar.addAction(spectrumName)
    action.setCheckable(True)
    action.setChecked(True)
    action.setToolTip(apiDataSource.name)
    widget = spectrumDisplay.spectrumToolBar.widgetForAction(action)
    widget.setIconSize(QtCore.QSize(120, 10))
    widget.setFixedSize(100, 30)
    widget.spectrumView = apiSpectrumView
    spectrumDisplay.spectrumActionDict[apiDataSource] = action
    spectrumDisplay._setActionIconColour(apiDataSource)

  return action

def _createdStripSpectrumView(project:Project, apiStripSpectrumView:ApiStripSpectrumView):
  """Set up SpectrumDisplay when new StripSpectrumView is created - for notifiers"""

  apiSpectrumView = apiStripSpectrumView.spectrumView
  getDataObj = project._data2Obj.get
  spectrumDisplay = getDataObj(apiSpectrumView.spectrumDisplay)
  if not isinstance(spectrumDisplay, GuiStripDisplayNd):
    return

  apiDataSource = apiSpectrumView.dataSource
  action = _createdSpectrumView(project, apiSpectrumView) # _createdStripSpectrumView is called before _createdSpectrumView so need this duplicate call here
  spectrumView = getDataObj(apiStripSpectrumView)
  action.toggled.connect(spectrumView.setVisible)

  ##strip = spectrumView.strip
  ##for apiPeakList in apiDataSource.sortedPeakLists():
  ##  strip.showPeaks(getDataObj(apiPeakList))

def _deletedSpectrumView(project:Project, apiSpectrumView:ApiSpectrumView):
  """tear down SpectrumDisplay when new SpectrumView is deleted - for notifiers"""
  spectrumDisplay = project._data2Obj[apiSpectrumView.spectrumDisplay]
  if not isinstance(spectrumDisplay, GuiStripDisplayNd):
    return

  apiDataSource = apiSpectrumView.dataSource

  # remove toolbar action (button)
  action = spectrumDisplay.spectrumActionDict.get(apiDataSource)  # should always be not None
  if action:
    spectrumDisplay.spectrumToolBar.removeAction(action)
    del spectrumDisplay.spectrumActionDict[apiDataSource]

Project._setupNotifier(_createdSpectrumView, ApiSpectrumView, 'postInit')
Project._setupNotifier(_deletedSpectrumView, ApiSpectrumView, 'preDelete')
Project._setupNotifier(_createdStripSpectrumView, ApiStripSpectrumView, 'postInit')

def _createdStripPeakListView(project:Project, apiStripPeakListView:ApiStripPeakListView):
  apiDataSource = apiStripPeakListView.stripSpectrumView.spectrumView.dataSource
  getDataObj = project._data2Obj.get
  peakListView = getDataObj(apiStripPeakListView)
  spectrumView = peakListView.spectrumView
  spectrumDisplay = spectrumView.strip.spectrumDisplay
  if isinstance(spectrumDisplay, GuiStripDisplayNd):
    action = spectrumDisplay.spectrumActionDict.get(apiDataSource)
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
        if isinstance(spectrumDisplay, GuiStripDisplayNd):
          spectrumDisplay._setActionIconColour(apiDataSource)

for apiFuncName in ('setPositiveContourColour', 'setSliceColour'):
  Project._setupNotifier(_setActionIconColour, ApiDataSource, apiFuncName)

def _deletedPeak(project:Project, apiPeak:ApiPeak):
  
  # TBD: the below might not be the best way to get hold of the spectrumDisplays
  for task in project.tasks:
    if task.status == 'active':
      for spectrumDisplay in task.spectrumDisplays:
        if isinstance(spectrumDisplay, GuiStripDisplayNd):
          spectrumDisplay._deletedPeak(apiPeak)

Project._setupNotifier(_deletedPeak, ApiPeak, 'delete')

# Unnecessary - dimensionOrdering is frozen
# def _changedDimensionOrderingSpectrumView(project:Project, apiSpectrumView:ApiSpectrumView):
#
#   for apiStrip in apiSpectrumView.strips:
#     strip = project._data2Obj[apiStrip]
#     if isinstance(strip, GuiStripNd):
#       strip.setZWidgets()
#
# Project._setupNotifier(_changedDimensionOrderingSpectrumView, ApiSpectrumView, 'dimensionOrdering')

# Supreseded
# def _changedAxisOrdering(project:Project, apiStrip:ApiStrip):
#
#   strip = project._data2Obj[apiStrip]
#   if isinstance(strip, GuiStripNd):
#     strip.setZWidgets()
#
# Project._setupNotifier(_changedDimensionOrderingSpectrumView, ApiStrip, 'axisOrder')


def _changedFreeStripAxisOrdering(project:Project, apiStrip:ApiFreeStrip):
  """Used (and works) for either BoundDisplay of FreeStrip"""

  project._data2Obj[apiStrip].setZWidgets()

Project._setupNotifier(_changedFreeStripAxisOrdering, ApiFreeStrip, 'axisOrder')

def _changedBoundDisplayAxisOrdering(project:Project, apiDisplay:ApiBoundDisplay):
  """Used (and works) for either BoundDisplay of FreeStrip"""

  for strip in project._data2Obj[apiDisplay].strips:
    strip.setZWidgets()

Project._setupNotifier(_changedBoundDisplayAxisOrdering, ApiBoundDisplay, 'axisOrder')