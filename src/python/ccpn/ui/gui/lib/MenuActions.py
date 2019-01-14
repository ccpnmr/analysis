"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.MessageDialog import showInfo
from ccpn.util.Logging import getLogger
from ccpn.core.MultipletList import MultipletList
from ccpn.core.Spectrum import Spectrum
from ccpn.core.PeakList import PeakList
from ccpn.core.ChemicalShiftList import ChemicalShiftList
from ccpn.core.SpectrumGroup import SpectrumGroup
from ccpn.core.Note import Note
from ccpn.core.Sample import Sample
from ccpn.core.IntegralList import IntegralList
from ccpn.core.NmrChain import NmrChain
from ccpn.core.Chain import Chain
from ccpn.core.StructureEnsemble import StructureEnsemble
from ccpn.core.RestraintList import RestraintList

# OPEN_ITEM_DICT = {
#     Spectrum.className         : _openSpectrumDisplay,
#     PeakList.className         : showPeakTable,
#     IntegralList.className     : showIntegralTable,
#     MultipletList.className    : showMultipletTable,
#     NmrChain.className         : showNmrResidueTable,
#     Chain.className            : showResidueTable,
#     SpectrumGroup.className    : _openSpectrumGroup,
#     Sample.className           : _openSampleSpectra,
#     ChemicalShiftList.className: showChemicalShiftTable,
#     RestraintList.className    : showRestraintTable,
#     Note.lastModified          : showNotesEditor,
#     StructureEnsemble.className: showStructureTable
#     }


def _openNote(mainWindow, note, position=None, relativeTo=None):
    application = mainWindow.application
    application.showNotesEditor(note=note, position=position, relativeTo=relativeTo)


def _openIntegralList(mainWindow, integralList, position=None, relativeTo=None):
    application = mainWindow.application
    application.showIntegralTable(integralList=integralList, position=position, relativeTo=relativeTo)


def _openPeakList(mainWindow, peakList, position=None, relativeTo=None):
    application = mainWindow.application
    application.showPeakTable(peakList=peakList, position=position, relativeTo=relativeTo)


def _openMultipletList(mainWindow, multipletList, position=None, relativeTo=None):
    application = mainWindow.application
    application.showMultipletTable(multipletList=multipletList, position=position, relativeTo=relativeTo)


def _openChemicalShiftList(mainWindow, chemicalShiftList, position=None, relativeTo=None):
    application = mainWindow.application
    application.showChemicalShiftTable(chemicalShiftList=chemicalShiftList, position=position, relativeTo=relativeTo)


def _openRestraintList(mainWindow, restraintList, position=None, relativeTo=None):
    application = mainWindow.application
    application.showRestraintTable(restraintList=restraintList, position=position, relativeTo=relativeTo)


def _openStructureTable(mainWindow, structureEnsemble, position=None, relativeTo=None):
    application = mainWindow.application
    application.showStructureTable(structureEnsemble=structureEnsemble, position=position, relativeTo=relativeTo)


def _openNmrResidueTable(mainWindow, nmrChain, position=None, relativeTo=None):
    application = mainWindow.application
    application.showNmrResidueTable(nmrChain=nmrChain, position=position, relativeTo=relativeTo)


def _openResidueTable(mainWindow, chain, position=None, relativeTo=None):
    application = mainWindow.application
    application.showResidueTable(chain=chain, position=position, relativeTo=relativeTo)


def _openItemObject(mainWindow, objs, **kwds):
    """
    Abstract routine to activate a module to display objs
    Builds on OpenObjAction dict, generated below, which defines the handling for the various
    obj classes
    """
    spectrumDisplay = None

    for obj in objs:
        if obj:
            try:
                if obj.__class__ in OpenObjAction:

                    # if a spectrum object has already been opened then attach to that spectrumDisplay
                    if isinstance(obj, Spectrum) and spectrumDisplay:
                        spectrumDisplay.displaySpectrum(obj)

                    else:

                        # process objects to open
                        returnObj = OpenObjAction[obj.__class__](mainWindow, obj, **kwds)

                        # if the first spectrum then set the spectrumDisplay
                        if isinstance(obj, Spectrum):
                            spectrumDisplay = returnObj

                else:
                    info = showInfo('Not implemented yet!',
                                    'This function has not been implemented in the current version')
            except Exception as e:
                getLogger().warning('Error: %s' % e)
                # raise e


def _openSpectrumDisplay(mainWindow, spectrum, position=None, relativeTo=None):
    spectrumDisplay = mainWindow.createSpectrumDisplay(spectrum)

    if len(spectrumDisplay.strips) > 0:
        mainWindow.current.strip = spectrumDisplay.strips[0]
        # if spectrum.dimensionCount == 1:
        spectrumDisplay._maximiseRegions()
        # mainWindow.current.strip.plotWidget.autoRange()

    mainWindow.moduleArea.addModule(spectrumDisplay, position=position, relativeTo=relativeTo)

    # TODO:LUCA: the mainWindow.createSpectrumDisplay should do the reporting to console and log
    # This routine can then be ommitted and the call above replaced by the one remaining line
    mainWindow.pythonConsole.writeConsoleCommand(
            "application.createSpectrumDisplay(spectrum)", spectrum=spectrum)
    getLogger().info('spectrum = project.getByPid(%r)' % spectrum.id)
    getLogger().info('application.createSpectrumDisplay(spectrum)')

    return spectrumDisplay


def _openSpectrumGroup(mainWindow, spectrumGroup, position=None, relativeTo=None):
    '''displays spectrumGroup on spectrumDisplay. It creates the display based on the first spectrum of the group.
    Also hides the spectrumToolBar and shows spectrumGroupToolBar '''

    if len(spectrumGroup.spectra) > 0:
        spectrumDisplay = mainWindow.createSpectrumDisplay(spectrumGroup.spectra[0])
        mainWindow.moduleArea.addModule(spectrumDisplay, position=position, relativeTo=relativeTo)
        for spectrum in spectrumGroup.spectra:  # Add the other spectra
            spectrumDisplay.displaySpectrum(spectrum)

        spectrumDisplay.isGrouped = True
        spectrumDisplay.spectrumToolBar.hide()
        spectrumDisplay.spectrumGroupToolBar.show()
        spectrumDisplay.spectrumGroupToolBar._addAction(spectrumGroup)
        mainWindow.application.current.strip = spectrumDisplay.strips[0]
        # if any([sp.dimensionCount for sp in spectrumGroup.spectra]) == 1:
        spectrumDisplay._maximiseRegions()


def _openSampleSpectra(mainWindow, sample, position=None, relativeTo=None):
    """
    Add spectra linked to sample and sampleComponent. Particularly used for screening
    """
    if len(sample.spectra) > 0:
        spectrumDisplay = mainWindow.createSpectrumDisplay(sample.spectra[0])
        mainWindow.moduleArea.addModule(spectrumDisplay, position=position, relativeTo=relativeTo)
        for spectrum in sample.spectra:
            spectrumDisplay.displaySpectrum(spectrum)
        for sampleComponent in sample.sampleComponents:
            if sampleComponent.substance is not None:
                for spectrum in sampleComponent.substance.referenceSpectra:
                    spectrumDisplay.displaySpectrum(spectrum)
        mainWindow.application.current.strip = spectrumDisplay.strips[0]
        if all(sample.spectra[0].dimensionCount) == 1:
            mainWindow.application.current.strip.autoRange()

OpenObjAction = {
    Spectrum         : _openSpectrumDisplay,
    PeakList         : _openPeakList,
    MultipletList    : _openMultipletList,
    NmrChain         : _openNmrResidueTable,
    Chain            : _openResidueTable,
    SpectrumGroup    : _openSpectrumGroup,
    Sample           : _openSampleSpectra,
    ChemicalShiftList: _openChemicalShiftList,
    RestraintList    : _openRestraintList,
    Note             : _openNote,
    IntegralList     : _openIntegralList,
    StructureEnsemble: _openStructureTable
    }
