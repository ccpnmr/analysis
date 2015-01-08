__author__ = 'simon'

from PySide import QtGui, QtCore

from ccpnmrcore.modules.GuiSpectrumDisplay import GuiSpectrumDisplay
from ccpnmrcore.modules.spectrumItems.GuiSpectrumViewNd import GuiSpectrumViewNd


class GuiStripDisplayNd(GuiSpectrumDisplay):

  def __init__(self, dockArea, apiSpectrumDisplay):
    if not apiSpectrumDisplay.strips:
      apiSpectrumDisplay.newStripNd()
    GuiSpectrumDisplay.__init__(self, dockArea, apiSpectrumDisplay)

  def addSpectrum(self, spectrum):

    guiSpectrumView = GuiSpectrumViewNd(self, spectrum)

    for guiStrip in self.guiStrips:
      guiStrip.addSpectrum(spectrum, guiSpectrumView)
