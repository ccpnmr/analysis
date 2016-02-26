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
from ccpn import Peak


from ccpncore.api.ccpnmr.gui.Task import SpectrumView as ApiSpectrumView
from ccpncore.api.ccpnmr.gui.Task import FreeStrip as ApiFreeStrip
from ccpncore.api.ccpnmr.gui.Task import BoundDisplay as ApiBoundDisplay
from ccpncore.api.ccpnmr.gui.Task import StripSpectrumView as ApiStripSpectrumView
from ccpncore.api.ccpnmr.gui.Task import StripPeakListView as ApiStripPeakListView

from ccpncore.gui.Icon import Icon

from ccpncore.util import Types

from application.core.modules.GuiSpectrumDisplay import GuiSpectrumDisplay
from application.core.modules.GuiStripNd import GuiStripNd
from application.core.modules.spectrumItems import GuiPeakListView

class GuiStripDisplayNd(GuiSpectrumDisplay):

  def __init__(self):

    # below are so we can reuse PeakItems and only create them as needed
    self.activePeakItemDict = {}  # maps peakListView to apiPeak to peakItem for peaks which are being displayed
    # cannot use (wrapper) peak as key because project._data2Obj dict invalidates mapping before deleted callback is called
    # TBD: this might change so that we can use wrapper peak (which would make nicer code in showPeaks and deletedPeak below)
    ###self.inactivePeakItems = set() # contains unused peakItems
    self.inactivePeakItemDict = {}  # maps peakListView to apiPeak to set of peaks which are not being displayed
    
    GuiSpectrumDisplay.__init__(self)

    self.isGrouped = False
    
    self.spectrumActionDict = {}  # apiDataSource --> toolbar action (i.e. button)

    self.fillToolBar()
    self.setAcceptDrops(True)
    if self._appBase.preferences.general.toolbarHidden:
      GuiSpectrumDisplay.hideUtilToolBar(self)

  #
  def addStrip(self) -> GuiStripNd:
    """
    Creates a new strip by duplicating the first strip in the display.
    """
    newStrip = self.strips[0].clone()
    return newStrip


  def showSpinSystemLabel(self):
    """NBNB do we still need this?"""
    self.spinSystemSideLabel.show()

  def hideSpinSystemLabel(self):
    """NBNB do we still need this?"""
    self.hideSystemSideLabel.show()

  def fillToolBar(self):
    """
    Adds specific icons for Nd spectra to the spectrum utility toolbar.
    """
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
    """
    Increases contour base level for all spectra visible in the display.
    """
    for spectrumView in self.spectrumViews:
      if spectrumView.isVisible():
        apiDataSource = spectrumView._wrappedData.spectrumView.dataSource
        apiDataSource.positiveContourBase *= apiDataSource.positiveContourFactor
        apiDataSource.negativeContourBase *= apiDataSource.negativeContourFactor
        spectrumView.update()

  def downBy2(self):
    """
    Decreases contour base level for all spectra visible in the display.
    """
    for spectrumView in self.spectrumViews:
      if spectrumView.isVisible():
        apiDataSource = spectrumView._wrappedData.spectrumView.dataSource
        apiDataSource.positiveContourBase /= apiDataSource.positiveContourFactor
        apiDataSource.negativeContourBase /= apiDataSource.negativeContourFactor
        spectrumView.update()
  def addOne(self):
    """
    Increases number of contours by 1 for all spectra visible in the display.
    """
    for spectrumView in self.spectrumViews:
      if spectrumView.isVisible():
        apiDataSource = spectrumView._wrappedData.spectrumView.dataSource
        apiDataSource.positiveContourCount += 1
        apiDataSource.negativeContourCount += 1

  def subtractOne(self):
    """
    Decreases number of contours by 1 for all spectra visible in the display.
    """
    for spectrumView in self.spectrumViews:
      if spectrumView.isVisible():
        apiDataSource = spectrumView._wrappedData.spectrumView.dataSource
        if apiDataSource.positiveContourCount > 0:
          apiDataSource.positiveContourCount -= 1
        if apiDataSource.negativeContourCount > 0:
          apiDataSource.negativeContourCount -= 1
    
  def showPeaks(self, peakListView:GuiPeakListView.GuiPeakListView, peaks:Types.List[Peak]):
    """
    Displays specified peaks in all strips of the display using peakListView
    """
    viewBox = peakListView.spectrumView.strip.viewBox
    activePeakItemDict = self.activePeakItemDict
    peakItemDict = activePeakItemDict.setdefault(peakListView, {})
    inactivePeakItemDict = self.inactivePeakItemDict
    inactivePeakItems = inactivePeakItemDict.setdefault(peakListView, set())
    ##inactivePeakItems = self.inactivePeakItems
    existingApiPeaks = set(peakItemDict.keys())
    unusedApiPeaks = existingApiPeaks - set([peak._wrappedData for peak in peaks])
    for apiPeak in unusedApiPeaks:
      peakItem = peakItemDict.pop(apiPeak)
      #viewBox.removeItem(peakItem)
      inactivePeakItems.add(peakItem)
      peakItem.setVisible(False)
    for peak in peaks:
      apiPeak = peak._wrappedData
      if apiPeak in existingApiPeaks:
        continue
      if inactivePeakItems:
        peakItem = inactivePeakItems.pop()
        peakItem.setupPeakItem(peakListView, peak)
        #viewBox.addItem(peakItem)
        peakItem.setVisible(True)
      else:
        peakItem = GuiPeakListView.PeakNd(peakListView, peak)
      peakItemDict[apiPeak] = peakItem
    
  def _deletedPeak(self, apiPeak):
    for peakListView in self.activePeakItemDict:
      peakItemDict = self.activePeakItemDict[peakListView]
      peakItem = peakItemDict.get(apiPeak)
      if peakItem:
        peakListView.spectrumView.strip.plotWidget.scene().removeItem(peakItem)
        del peakItemDict[apiPeak]
        inactivePeakItems = self.inactivePeakItemDict.get(peakListView)
        if inactivePeakItems:
          inactivePeakItems.add(peakItem)

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
  
def _deletedStripPeakListView(project:Project, apiStripPeakListView:ApiStripPeakListView):
  
  getDataObj = project._data2Obj.get
  peakListView = getDataObj(apiStripPeakListView)
  spectrumView = peakListView.spectrumView
  strip = spectrumView.strip
  spectrumDisplay = strip.spectrumDisplay
 
  if not isinstance(spectrumDisplay, GuiStripDisplayNd):
    return
    
  peakItemDict = spectrumDisplay.activePeakItemDict[peakListView]
  peakItems = set(spectrumDisplay.inactivePeakItemDict[peakListView])
  for apiPeak in peakItemDict:
    peakItem = peakItemDict[apiPeak]
    peakItems.add(peakItem)
    
  scene = strip.plotWidget.scene()
  for peakItem in peakItems:
    scene.removeItem(peakItem.annotation)
    scene.removeItem(peakItem)
  scene.removeItem(peakListView)
  
  del spectrumDisplay.activePeakItemDict[peakListView]
  del spectrumDisplay.inactivePeakItemDict[peakListView]
  
Project._setupNotifier(_deletedStripPeakListView, ApiStripPeakListView, 'preDelete')

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
