# from ccpn.lib.wrapper import Spectrum as LibSpectrum

__author__ = 'simon'

from ccpncore.gui.Icon import Icon
from ccpncore.gui.VerticalLabel import VerticalLabel
from ccpnmrcore.modules.GuiSpectrumDisplay import GuiSpectrumDisplay
# from ccpnmrcore.modules.GuiSpectrumViewNd import GuiSpectrumViewNd
from ccpnmrcore.modules.GuiStripNd import GuiStripNd



class GuiStripDisplayNd(GuiSpectrumDisplay):

  def __init__(self):
    # if not apiSpectrumDisplayNd.strips:
    #   apiSpectrumDisplayNd.newStripNd()
    
    self.viewportDict = {} # maps QGLWidget to GuiStripNd

    GuiSpectrumDisplay.__init__(self)
    self.fillToolBar()
    # self.setAcceptDrops(True)
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
  # def addStrip(self):
  #
  #   print('addNewStrip')
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
    # spinSystemSideLabel.setText()
    # print(dir(spinSystemSideLabel))
    # print(spinSystemSideLabel.paintEvent())
    self.spinSystemSideLabel.setFixedWidth(30)
    # spinSystemSideLabel.setAlignment(QtCore.Qt.AlignVCenter)
    # spinSystemSideLabel.setFrameStyle(QtGui.QFrame.Box | QtGui.QFrame.Plain)

  def fillToolBar(self):
    spectrumUtilToolBar =  self.spectrumUtilToolBar
    spectrumUtilToolBar.addAction('+', self.addAStrip)
    spectrumUtilToolBar.addAction('-', self.removeStrip)
    plusOneAction = spectrumUtilToolBar.addAction("+1", self.addOne)
    plusOneIcon = Icon('icons/contourAdd')
    plusOneAction.setIcon(plusOneIcon)
    plusOneAction.setToolTip('Add One Level')
    minusOneAction = spectrumUtilToolBar.addAction("+1", self.subtractOne)
    minusOneIcon = Icon('icons/contourRemove')
    minusOneAction.setIcon(minusOneIcon)
    minusOneAction.setToolTip('Remove One Level ')
    upBy2Action = spectrumUtilToolBar.addAction("*1.4", self.upBy2)
    upBy2Icon = Icon('icons/contourBaseUp')
    upBy2Action.setIcon(upBy2Icon)
    upBy2Action.setToolTip('Raise Contour Base Level')
    downBy2Action = spectrumUtilToolBar.addAction("*1.4", self.downBy2)
    downBy2Icon = Icon('icons/contourBaseDown')
    downBy2Action.setIcon(downBy2Icon)
    downBy2Action.setToolTip('Lower Contour Base Level')
    storeZoomAction = spectrumUtilToolBar.addAction("Store Zoom", self.storeZoom)
    storeZoomIcon = Icon('icons/zoom-store')
    storeZoomAction.setIcon(storeZoomIcon)
    storeZoomAction.setToolTip('Store Zoom')
    restoreZoomAction = spectrumUtilToolBar.addAction("Restore Zoom", self.restoreZoom)
    restoreZoomIcon = Icon('icons/zoom-restore')
    restoreZoomAction.setIcon(restoreZoomIcon)
    restoreZoomAction.setToolTip('Restore Zoom')


  def upBy2(self):
    for spectrumItem in self.spectrumItems:
      spectrumItem.baseLevel*=1.4
      spectrumItem.levels = spectrumItem.getLevels()

  def downBy2(self):
    for spectrumItem in self.spectrumItems:
      spectrumItem.baseLevel/=1.4
      spectrumItem.levels = spectrumItem.getLevels()

  def addOne(self):
    self.current.spectrum.spectrumItem.numberOfLevels +=1
    self.current.spectrum.spectrumItem.levels = self.current.spectrum.spectrumItem.getLevels()


  def subtractOne(self):
    self.current.spectrum.spectrumItem.numberOfLevels -=1
    self.current.spectrum.spectrumItem.levels = self.current.spectrum.spectrumItem.getLevels()

  def addAStrip(self):

    newStrip = self.strips[0].clone()
    newStrip.setMinimumWidth(200)
    # self.stripFrame.layout().addWidget(newStrip)
    # self.stripNumber+=1
    # # self.stripFrame.layout().addWidget(self, 2, 0, 1, 1)

  def removeStrip(self):
    pass




