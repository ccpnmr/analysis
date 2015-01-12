__author__ = 'simon'

from PySide import QtGui, QtCore
import os

from ccpnmrcore.modules.GuiSpectrumDisplay import GuiSpectrumDisplay
from ccpnmrcore.modules.spectrumItems.GuiSpectrumView1d import GuiSpectrumView1d


class GuiStripDisplay1d(GuiSpectrumDisplay):

  def __init__(self, dockArea, apiSpectrumDisplay1d):
    if not apiSpectrumDisplay1d.strips:
      apiSpectrumDisplay1d.newStrip1d()
    GuiSpectrumDisplay.__init__(self, dockArea, apiSpectrumDisplay1d)

  def addSpectrum(self, spectrum):

    guiSpectrumView = GuiSpectrumView1d(self, spectrum)
    guiSpectrumView.name = spectrum.name

    for guiStrip in self.guiStrips:
      guiStrip.addSpectrum(spectrum, guiSpectrumView)

