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
# from ccpn.lib.wrapper import Spectrum as LibSpectrum

__author__ = 'simon'
from PyQt4 import QtCore, QtGui

from ccpncore.gui.Icon import Icon
from ccpncore.gui.VerticalLabel import VerticalLabel

from ccpncore.memops import Notifiers

from ccpnmrcore.modules.GuiSpectrumDisplay import GuiSpectrumDisplay

from ccpnmrcore.modules.spectrumItems.GuiPeakListView import PeakNd

class GuiStripDisplayNd(GuiSpectrumDisplay):

  # def wheelEvent(self, event):
  #   if event.modifiers() & QtCore.Qt.ShiftModifier:
  #     for spectrumItem in self.spectrumItems:
  #       if event.delta() > 0:
  #           spectrumItem.raiseBaseLevel()
  #           spectrumItem.update()
  #       else:
  #         spectrumItem.lowerBaseLevel()
  #         spectrumItem.update()
  #   elif not event.modifiers():
  #     QtGui.QGraphicsView.wheelEvent(self, event)
  #     sc = 1.001 ** event.delta()
  #     #self.scale *= sc
  #     #self.updateMatrix()
  #     self.scale(sc, sc)
  #   elif event.modifiers() & QtCore.Qt.ControlModifier:
  #     if event.delta() > 0:
  #        self.increaseTraceScale()
  #     else:
  #       self.decreaseTraceScale()
  #   else:
  #     event.ignore


  def __init__(self):
    # if not apiSpectrumDisplayNd.strips:
    #   apiSpectrumDisplayNd.newStripNd()
    
    ##self.viewportDict = {} # maps QGLWidget to GuiStripNd

    # below are so we can reuse PeakItems and only create them as needed
    self.activePeakItemDict = {}  # maps peakLayer to apiPeak to peakItem for peaks which are being displayed
    # cannot use (wrapper) peak as key because project._data2Obj dict invalidates mapping before deleted callback is called
    # TBD: this might change so that we can use wrapper peak (which would make nicer code in showPeaks and deletedPeak below)
    self.inactivePeakItems = set() # contains unused peakItems
    
    GuiSpectrumDisplay.__init__(self)
    
    Notifiers.registerNotify(self._deletedPeak, 'ccp.nmr.Nmr.Peak', 'delete')
    Notifiers.registerNotify(self._addedStripSpectrumView, 'ccpnmr.gui.Task.StripSpectrumView', '__init__')
    Notifiers.registerNotify(self._removedStripSpectrumView, 'ccpnmr.gui.Task.StripSpectrumView', 'delete')
    for func in ('setPositiveContourColour', 'setSliceColour'):
      Notifiers.registerNotify(self._setActionIconColour, 'ccp.nmr.Nmr.DataSource', func)
    
    self.spectrumActionDict = {}  # apiDataSource --> toolbar action (i.e. button)
    self.apiStripSpectrumViews = set()  # set of apiStripSpectrumViews seen so far
    
    self.fillToolBar()
    self.setAcceptDrops(True)
    # self.addSpinSystemSideLabel()
    # self._appBase.current.pane = self

  # def addSpectrum(self, spectrum):
  #
  #   apiSpectrumDisplay = self.apiSpectrumDisplay
  #
  #   #axisCodes = spectrum.axisCodes
  #   axisCodes = LibSpectrum.getAxisCodes(spectrum)
  #   if axisCodes != self.apiSpectrumDisplay.axisCodes:
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
  #   apiStrip = self.apiSpectrumDisplay.newStripNd()
  #   n = len(self.apiSpectrumDisplay.strips) - 1
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

    for apiSpectrumView in self._wrappedData.spectrumViews:
      apiDataSource = apiSpectrumView.dataSource
      apiDataSource.positiveContourBase *= apiDataSource.positiveContourFactor
      apiDataSource.negativeContourBase *= apiDataSource.negativeContourFactor

  def downBy2(self):

    for apiSpectrumView in self._wrappedData.spectrumViews:
      apiDataSource = apiSpectrumView.dataSource
      apiDataSource.positiveContourBase /= apiDataSource.positiveContourFactor
      apiDataSource.negativeContourBase /= apiDataSource.negativeContourFactor

  def addOne(self):

    for apiSpectrumView in self._wrappedData.spectrumViews:
      apiDataSource = apiSpectrumView.dataSource
      apiDataSource.positiveContourCount += 1
      apiDataSource.negativeContourCount += 1

  def subtractOne(self):

    for apiSpectrumView in self._wrappedData.spectrumViews:
      apiDataSource = apiSpectrumView.dataSource
      if apiDataSource.positiveContourCount > 0:
        apiDataSource.positiveContourCount -= 1
      if apiDataSource.negativeContourCount > 0:
        apiDataSource.negativeContourCount -= 1

  def showPeaks(self, peakLayer, peaks):
  
    viewBox = peakLayer.strip.viewBox
    activePeakItemDict = self.activePeakItemDict
    peakItemDict = activePeakItemDict.setdefault(peakLayer, {})
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
        peakItem.setupPeakItem(peakLayer, peak)
        viewBox.addItem(peakItem)
      else:
        peakItem = PeakNd(peakLayer, peak)
      peakItemDict[apiPeak] = peakItem
    
  def _deletedPeak(self, apiPeak):
    for peakLayer in self.activePeakItemDict:
      peakItemDict = self.activePeakItemDict[peakLayer]
      peakItem = peakItemDict.get(apiPeak)
      if peakItem:
        peakLayer.strip.plotWidget.scene().removeItem(peakItem)
        del peakItemDict[apiPeak]
        self.inactivePeakItems.add(peakItem)
      
  def _addedStripSpectrumView(self, apiStripSpectrumView):
    apiSpectrumDisplay = self._wrappedData
    if apiSpectrumDisplay is not apiStripSpectrumView.strip.spectrumDisplay:
      return
      
    # cannot deal with wrapper spectrum object because that not ready yet when this notifier is called
    apiDataSource = apiStripSpectrumView.spectrumView.dataSource
    action = self.spectrumActionDict.get(apiDataSource)
    if not action:
      # add toolbar action (button)
      action = self.spectrumToolBar.addAction(apiDataSource.name)
      action.setCheckable(True)
      action.setChecked(True)
      widget = self.spectrumToolBar.widgetForAction(action)
      widget.setFixedSize(60, 30)
      self.spectrumActionDict[apiDataSource] = action  # have to use wrappedData because wrapper object disappears before delete notifier is called
      self._setActionIconColour(apiDataSource)
    if apiStripSpectrumView not in self.apiStripSpectrumViews:
      spectrumView = self._appBase.project._data2Obj[apiStripSpectrumView]
      action.toggled.connect(spectrumView.setVisible)
      self.apiStripSpectrumViews.add(apiStripSpectrumView)
      
    return action
  
  def _apiDataSourcesInDisplay(self):
    apiDataSources = set()
    for strip in self.strips:
      for spectrumView in strip.spectrumViews:
        apiDataSources.add(spectrumView.spectrum._wrappedData)
    return apiDataSources
    
  def _removedStripSpectrumView(self, apiStripSpectrumView):
    # cannot deal with wrapper spectrum object because already disappears when this notifier is called
    apiDataSources = self._apiDataSourcesInDisplay()
    apiDataSource = apiStripSpectrumView.spectrumView.dataSource
    if apiDataSource not in apiDataSources:
      # remove toolbar action (button)
      action = self.spectrumActionDict.get(apiDataSource)  # should always be not None (correct??)
      if action:
        self.spectrumToolBar.removeAction(action)
        del self.spectrumActionDict[apiDataSource]
      if apiStripSpectrumView in self.apiStripSpectrumViews:  # should always be the case
        self.apiStripSpectrumViews.remove(apiStripSpectrumView)
          
  def _setActionIconColour(self, apiDataSource):
    action = self.spectrumActionDict.get(apiDataSource)
    if action:
      pix=QtGui.QPixmap(60, 10)
      if apiDataSource.numDim < 2: # irrelevant here, but need if this code moves to GuiSpectrumDisplay
        pix.fill(QtGui.QColor(apiDataSource.sliceColour))
      else:
        pix.fill(QtGui.QColor(apiDataSource.positiveContourColour))
      action.setIcon(QtGui.QIcon(pix))

  def _spectrumViewsInDisplay(self):
    spectrumViews = set()
    for strip in self.strips:
      spectrumViews.update(strip.spectrumViews)
    return spectrumViews
    
  def _connectPeakLayerVisibility(self, spectrumView, peakLayer):
    spectrumViews = self._spectrumViewsInDisplay()
    if spectrumView in spectrumViews:
      apiStripSpectrumView = spectrumView._wrappedData
      action = self._addedStripSpectrumView(apiStripSpectrumView)  # have to do it this way because peakLayer can be set up before spectrum
      action.toggled.connect(peakLayer.setVisible) # TBD: need to undo this if peakLayer removed   