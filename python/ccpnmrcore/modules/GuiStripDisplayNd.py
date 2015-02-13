__author__ = 'simon'

from ccpncore.gui.VerticalLabel import VerticalLabel
from ccpn.lib import Spectrum as LibSpectrum
from ccpnmrcore.modules.GuiSpectrumDisplay import GuiSpectrumDisplay
<<<<<<< .mine
=======
from ccpnmrcore.modules.GuiSpectrumViewNd import GuiSpectrumViewNd
from ccpnmrcore.modules.GuiStripNd import GuiStripNd
>>>>>>> .r8045


def _findPpmRegion(spectrum, axisDim, spectrumDim):
  
  pointCount = spectrum.pointCounts[spectrumDim]
  if axisDim < 2: # want entire region
    region = (0, pointCount)
  else:
    n = pointCount // 2
    region = (n, n+1)
    
  firstPpm, lastPpm = LibSpectrum.getDimValueFromPoint(spectrum, spectrumDim, region)
  
  return 0.5*(firstPpm+lastPpm), abs(lastPpm-firstPpm)
  
class GuiStripDisplayNd(GuiSpectrumDisplay):

  def __init__(self):
    # if not apiSpectrumDisplayNd.strips:
    #   apiSpectrumDisplayNd.newStripNd()
    
    self.viewportDict = {} # maps QGLWidget to GuiStripNd

    GuiSpectrumDisplay.__init__(self)
    self.fillToolBar()
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

  def addSpinSystemSideLabel(self):
    self.spinSystemSideLabel = VerticalLabel(self, text=None)
    self.spinSystemSideLabel = VerticalLabel(self, text=None)
    self.spinSystemSideLabel.setText('A.147.ALA.HA')
    # spinSystemSideLabel.setText()
    self.addWidget(self.spinSystemSideLabel, 1, 0, 1, 1)
    # print(dir(spinSystemSideLabel))
    # print(spinSystemSideLabel.paintEvent())
    self.spinSystemSideLabel.setFixedWidth(30)
    # spinSystemSideLabel.setAlignment(QtCore.Qt.AlignVCenter)
    # spinSystemSideLabel.setFrameStyle(QtGui.QFrame.Box | QtGui.QFrame.Plain)




