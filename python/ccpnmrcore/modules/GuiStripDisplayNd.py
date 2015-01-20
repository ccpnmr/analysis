__author__ = 'simon'

from PySide import QtGui, QtCore

from ccpnmrcore.modules.GuiSpectrumDisplay import GuiSpectrumDisplay
from ccpnmrcore.modules.spectrumItems.GuiSpectrumViewNd import GuiSpectrumViewNd
from ccpnmrcore.modules.GuiStripNd import GuiStripNd

class GuiStripDisplayNd(GuiSpectrumDisplay):

  def __init__(self, dockArea, apiSpectrumDisplayNd):
    if not apiSpectrumDisplayNd.strips:
      apiSpectrumDisplayNd.newStripNd()
    GuiSpectrumDisplay.__init__(self, dockArea, apiSpectrumDisplayNd)
    self.fillToolBar()

  def addSpectrum(self, spectrum):

    apiDataSource = spectrum._wrappedData
    apiSpectrumView = self.apiSpectrumDisplay.findFirstSpectrumView(dataSource=apiDataSource)
    if not apiSpectrumView:
      ##axisCodes=spectrum.axisCodes
      axisCodes = ('H', 'N')  # TEMP
      apiSpectrumView = self.apiSpectrumDisplay.newSpectrumView(dataSourceSerial=apiDataSource.serial,
                          experimentName=apiDataSource.experiment.name, axisCodes=axisCodes)
    guiSpectrumView = GuiSpectrumViewNd(self, apiSpectrumView)

    for guiStrip in self.guiStrips:
      guiStrip.addSpectrum(spectrum, guiSpectrumView)


  def addStrip(self):

    apiStrip = self.apiSpectrumDisplay.newStripNd()
    print('HERE221')
    n = len(self.apiSpectrumDisplay.strips) - 1
    guiStrip = GuiStripNd(self.stripFrame, apiStrip, grid=(1, n), stretch=(0, 1))
    if n > 0:
      prevGuiStrip = self.guiStrips[n-1]
      prevGuiStrip.axes['right']['item'].hide()
      guiStrip.setYLink(prevGuiStrip)

    print('HERE222')

  def fillToolBar(self):
    GuiSpectrumDisplay.fillToolBar(self)