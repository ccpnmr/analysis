#TODO:GEERTEN: Move to other places, like SpectrumDisplay or Strip

from ccpn.core.NmrAtom import NmrAtom
from ccpn.core.Peak import Peak
from ccpn.core.Project import Project
from typing import List
from ccpn.ui.gui.lib.GuiSpectrumDisplay import GuiSpectrumDisplay
from ccpn.ui.gui.lib.Strip import navigateToPositionInStrip, navigateToNmrAtomsInStrip
from ccpn.core.lib.ContextManagers import undoBlockManager
from ccpn.util.Logging import getLogger


def navigateToCurrentPeakPosition(application):
    """

    Takes the current peak position and navigates (centres) to that position all strips and spectrum displays of the project.
    Called by shortcut. For a more generic usage refer to:  "navigateToPositionInStrip"
    instead
    """

    project = application.project
    displays = project.spectrumDisplays
    peak = application.current.peak

    if len(application.current.peaks) > 1:
        getLogger().warning('More than one peak selected. Select only one for the "navigateToCurrentPeakPosition" command.')
        return

    if len(displays) < 1:
        getLogger().warning('No Displays where to navigate.')
        return

    if peak is None:
        getLogger().warning('No peak selected.')
        return

    for display in displays:
        for strip in display.strips:
            if strip:
                navigateToPositionInStrip(strip, peak.position, peak.axisCodes)


def makeStripPlot(spectrumDisplay: GuiSpectrumDisplay, nmrAtomPairs: List[List[NmrAtom]], autoWidth=True, widths=None):
    if not nmrAtomPairs:
        return

    with undoBlockManager():
        numberOfStrips = len(spectrumDisplay.strips)

        # Make sure there are enough strips to display nmrAtomPairs
        if numberOfStrips < len(nmrAtomPairs):
            for ii in range(numberOfStrips, len(nmrAtomPairs)):
                # spectrumDisplay.strips[-1].clone()
                spectrumDisplay.addStrip()
        else:  # numberOfStrips >= len(nmrAtomPairs):  # too many strips if >
            for ii in range(len(nmrAtomPairs), numberOfStrips):
                spectrumDisplay.deleteStrip(spectrumDisplay.strips[-1])
                # spectrumDisplay.removeLastStrip()

        # loop through strips and navigate to appropriate position in strip
        for ii, strip in enumerate(spectrumDisplay.strips):
            if autoWidth:
                widths = ['default'] * len(strip.axisCodes)
            elif not widths:
                widths = None
            navigateToNmrAtomsInStrip(strip, nmrAtomPairs[ii], widths=widths)


def makeStripPlotFromSingles(spectrumDisplay: GuiSpectrumDisplay, nmrAtoms: List[NmrAtom], autoWidth=True):
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
