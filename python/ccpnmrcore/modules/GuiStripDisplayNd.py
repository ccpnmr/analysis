__author__ = 'simon'

from PySide import QtGui, QtCore

from ccpnmrcore.modules.GuiSpectrumDisplay import GuiSpectrumDisplay
from ccpnmrcore.modules.spectrumItems.GuiSpectrumViewNd import GuiSpectrumViewNd


class GuiStripDisplayNd(GuiSpectrumDisplay):

  def __init__(self, dockArea, apiSpectrumDisplayNd):
    if not apiSpectrumDisplayNd.strips:
      apiSpectrumDisplayNd.newStripNd()
    GuiSpectrumDisplay.__init__(self, dockArea, apiSpectrumDisplayNd)

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
