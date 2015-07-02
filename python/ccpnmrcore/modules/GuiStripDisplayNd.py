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
    self.inactivePeakItems = set() # containus unused peakItems
    
    Notifiers.registerNotify(self.deletedPeak, 'ccp.nmr.Nmr.Peak', 'delete')
    
    GuiSpectrumDisplay.__init__(self)
    
    self.fillToolBar()
    self.setAcceptDrops(True)
    self.addSpinSystemSideLabel()
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

    for spectrumView in self._wrappedData.spectrumViews:
      spectrumView.positiveContourBase *= spectrumView.positiveContourFactor
      spectrumView.negativeContourBase *= spectrumView.negativeContourFactor

  def downBy2(self):

    for spectrumView in self.spectrumViews:
      spectrumView._wrappedData.findFirstSpectrumView().positiveContourBase /= spectrumView.spectrum.positiveContourFactor
      spectrumView._wrappedData.findFirstSpectrumView().negativeContourBase /= spectrumView.spectrum.negativeContourFactor

  def addOne(self):

    for spectrumView in self.spectrumViews:
      spectrumView.spectrum.positiveContourCount +=1
      spectrumView.spectrum.negativeContourCount +=1

  def subtractOne(self):

    for spectrumView in self.spectrumViews:
      spectrumView.spectrum.positiveContourCount -=1
      spectrumView.spectrum.negativeContourCount -=1

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
      
  def deletedPeak(self, apiPeak):
    
    for peakLayer in self.activePeakItemDict:
      peakItemDict = self.activePeakItemDict[peakLayer]
      peakItem = peakItemDict.get(apiPeak)
      if peakItem:
        print('111')
        peakLayer.strip.plotWidget.scene().removeItem(peakItem)
        print('222')
        del peakItemDict[apiPeak]
        self.inactivePeakItems.add(peakItem)
      

