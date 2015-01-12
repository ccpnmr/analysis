__author__ = 'simon'

from PySide import QtGui, QtCore

from ccpnmrcore.modules.GuiSpectrumDisplay import GuiSpectrumDisplay
from ccpnmrcore.modules.spectrumItems.GuiSpectrumView1d import GuiSpectrumView1d


class GuiStripDisplay1d(GuiSpectrumDisplay):

  def __init__(self, dockArea, apiSpectrumDisplay1d):
    if not apiSpectrumDisplay1d.strips:
      apiSpectrumDisplay1d.newStrip1d()
    GuiSpectrumDisplay.__init__(self, dockArea, apiSpectrumDisplay1d)

  def addSpectrum(self, spectrum):

    guiSpectrumView = GuiSpectrumView1d(self, spectrum)

    for guiStrip in self.guiStrips:
      guiStrip.addSpectrum(spectrum, guiSpectrumView)
