#TODO:GEERTEN: Move to other places, like SpectrumDisplay or Strip

from ccpn.core.NmrAtom import NmrAtom
from ccpn.core.Peak import Peak
from ccpn.core.Project import Project
from typing import List
from ccpn.ui.gui.modules.GuiStrip import GuiStrip
from ccpn.ui.gui.modules.GuiSpectrumDisplay import GuiSpectrumDisplay
from ccpn.ui.gui.lib.Strip import navigateToPositionInStrip, navigateToNmrAtomsInStrip
from ccpn.util.Logging import getLogger


def navigateToPeakPosition(project:Project, peak:Peak=None,
   selectedDisplays:List[GuiSpectrumDisplay]=None, strip:GuiStrip=None):
  """
  Takes a peak and optional spectrum displays and strips and navigates the strips and spectrum displays
  to the positions specified by the peak.
  """

  if selectedDisplays is None and not strip:
    selectedDisplays = [display.pid for display in project.spectrumDisplays]

  if peak is None:
    peak = project._appBase.current.peak
    if peak is None:
      getLogger().warning('No peak selected.')
      return

  positions = peak.position
  axisCodes = peak.axisCodes

  if not strip:
    for displayPid in selectedDisplays:
      display = project.getByPid(displayPid)
      for strip in display.strips:
        navigateToPositionInStrip(strip, positions, axisCodes)
  else:
    navigateToPositionInStrip(strip, positions, axisCodes)


def makeStripPlot(spectrumDisplay:GuiSpectrumDisplay, nmrAtomPairs:List[List[NmrAtom]], autoWidth=True, widths=None):

  if not nmrAtomPairs:
    return

  project = spectrumDisplay.project
  project._startCommandEchoBlock('makeStripPlot', spectrumDisplay, nmrAtomPairs, autoWidth, widths)
  try:

    numberOfStrips = len(spectrumDisplay.strips)

    # Make sure there are enough strips to display nmrAtomPairs
    if numberOfStrips < len(nmrAtomPairs):
      for ii in range(numberOfStrips, len(nmrAtomPairs)):
        # spectrumDisplay.strips[-1].clone()
        spectrumDisplay.addStrip()
    else:  # numberOfStrips >= len(nmrAtomPairs):  # too many strips if >
      for ii in range(len(nmrAtomPairs), numberOfStrips):
        spectrumDisplay.removeStrip(spectrumDisplay.strips[-1])
        # spectrumDisplay.removeLastStrip()

    # loop through strips and navigate to appropriate position in strip
    for ii, strip in enumerate(spectrumDisplay.strips):
      if autoWidth:
        widths = ['default'] * len(strip.axisCodes)
      elif not widths:
        widths = None
      navigateToNmrAtomsInStrip(strip, nmrAtomPairs[ii], widths=widths)
  finally:
    project._endCommandEchoBlock()


def makeStripPlotFromSingles(spectrumDisplay:GuiSpectrumDisplay, nmrAtoms:List[NmrAtom], autoWidth=True):

  numberOfStrips = len(spectrumDisplay.strips)

  # Make sure there are enough strips to display nmrAtomPairs
  if numberOfStrips < len(nmrAtoms):
    for ii in range(numberOfStrips, len(nmrAtoms)):
      spectrumDisplay.strips[-1].clone()

  # print(spectrumDisplay, nmrAtomPairs, len(nmrAtomPairs), len(spectrumDisplay.strips))
  # loop through strips and navigate to appropriate position in strip
  for ii, strip in enumerate(spectrumDisplay.strips):
    if autoWidth:
      widths = ['default'] * len(strip.axisCodes)
    else:
      widths = None
    navigateToNmrAtomsInStrip(strip, [nmrAtoms[ii]], widths=widths)