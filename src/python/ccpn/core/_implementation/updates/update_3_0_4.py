"""
update 3.0.4 routines
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2021-12-20 09:30:08 +0000 (Mon, December 20, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2021-11-10 10:28:41 +0000 (Wed, November 10, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

import pandas as pd
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar


def _updateSpectrum_3_0_4_to_3_1_0(spectrum):
    """Update the _ccpnInternal settings from version 3.0.4 -> 3.1.0
    These routines are called post-project initialisation
    """
    _updateSpectrum_settings(spectrum)
    _updateSpectrum_NC_proc(spectrum)


def _updateSpectrum_NC_proc(spectrum):
    """Update spectrum from 3.1.0.alpha to 3.1.0.alpha2
    Correct Bruker NC_proc related issues
    """
    from ccpn.core._implementation.patches.patch_3_0_4 import NC_PROC, getNCprocDataScale
    from ccpn.core.lib.SpectrumDataSources.BrukerSpectrumDataSource import BrukerSpectrumDataSource

    if spectrum.dataFormat == BrukerSpectrumDataSource.dataFormat:
        if spectrum._hasInternalParameter(NC_PROC):
            # Spectrum was adjusted in 3.0.4
            scale = spectrum._getInternalParameter(NC_PROC)
            # restore the spectrum scale to its original value as it was 'misused' in 3.0.4
            spectrum.scale /= scale

        else:
            scale = spectrum._dataSource.dataScale
            if spectrum.dimensionCount >=2:
                spectrum.positiveContourBase *= scale
                spectrum.negativeContourBase *= scale

        for pk in spectrum.peaks:
            pk.height *= scale


def _updateSpectrum_settings(spectrum):
    """Update the _ccpnInternal settings from version3.0.4 -> 3.1.0.alpha2
    """
    if not isinstance(spectrum._ccpnInternalData, dict):
        raise ValueError('Invalid _ccpnInternalData')

    # deprecated ccpnInternal settings
    SPECTRUMAXES = 'spectrumAxesOrdering'
    SPECTRUMPREFERREDAXISORDERING = 'spectrumPreferredAxisOrdering'
    SPECTRUMALIASING = 'spectrumAliasing'
    SPECTRUMSERIES = 'spectrumSeries'
    SPECTRUMSERIESITEMS = 'spectrumSeriesItems'
    NEGATIVENOISELEVEL = 'negativeNoiseLevel'

    # include positive/negative contours
    if spectrum._INCLUDEPOSITIVECONTOURS in spectrum._ccpnInternalData:
        value = spectrum._ccpnInternalData.get(spectrum._INCLUDEPOSITIVECONTOURS)
        spectrum._setInternalParameter(spectrum._INCLUDEPOSITIVECONTOURS, value)
        del spectrum._ccpnInternalData[spectrum._INCLUDEPOSITIVECONTOURS]

    if spectrum._INCLUDENEGATIVECONTOURS in spectrum._ccpnInternalData:
        value = spectrum._ccpnInternalData.get(spectrum._INCLUDENEGATIVECONTOURS)
        spectrum._setInternalParameter(spectrum._INCLUDENEGATIVECONTOURS, value)
        del spectrum._ccpnInternalData[spectrum._INCLUDENEGATIVECONTOURS]

    # spectrum preferred axis order
    if spectrum.hasParameter(SPECTRUMAXES, SPECTRUMPREFERREDAXISORDERING):
        value = spectrum.getParameter(SPECTRUMAXES, SPECTRUMPREFERREDAXISORDERING)
        if value is not None:
            spectrum._setInternalParameter(spectrum._PREFERREDAXISORDERING, value)

    # spectrumGroup series items
    if spectrum.hasParameter(SPECTRUMSERIES, SPECTRUMSERIESITEMS):
        value = spectrum.getParameter(SPECTRUMSERIES, SPECTRUMSERIESITEMS)
        if value is not None:
            spectrum._setInternalParameter(spectrum._SERIESITEMS, value)

    # display folded contours
    if spectrum.hasParameter(SPECTRUMALIASING, spectrum._DISPLAYFOLDEDCONTOURS):
        value = spectrum.getParameter(SPECTRUMALIASING, spectrum._DISPLAYFOLDEDCONTOURS)
        if value is not None:
            spectrum._setInternalParameter(spectrum._DISPLAYFOLDEDCONTOURS, value)
    # visibleAliasingRange/aliasingRange should already have gone

    # remove unnecessary dict items
    if SPECTRUMAXES in spectrum._ccpnInternalData:
        del spectrum._ccpnInternalData[SPECTRUMAXES]
    if SPECTRUMSERIES in spectrum._ccpnInternalData:
        del spectrum._ccpnInternalData[SPECTRUMSERIES]
    if SPECTRUMALIASING in spectrum._ccpnInternalData:
        del spectrum._ccpnInternalData[SPECTRUMALIASING]

    # update the list of substances
    if spectrum._ReferenceSubstancesPids in spectrum._ccpnInternalData:
        value = spectrum._ccpnInternalData.get(spectrum._ReferenceSubstancesPids)
        if value:
            spectrum._setInternalParameter(spectrum._REFERENCESUBSTANCES, value)
        del spectrum._ccpnInternalData[spectrum._ReferenceSubstancesPids]

    if spectrum.hasParameter(spectrum._AdditionalAttribute, NEGATIVENOISELEVEL):
        # move the internal parameter to the correct namespace
        value = spectrum.getParameter(spectrum._AdditionalAttribute, NEGATIVENOISELEVEL)
        spectrum.deleteParameter(spectrum._AdditionalAttribute, NEGATIVENOISELEVEL)
        spectrum._setInternalParameter(spectrum._NEGATIVENOISELEVEL, value)


def _updateChemicalShiftList_3_0_4_to_3_1_0(chemicalShiftList):
    """Move chemicalShifts from model shifts to pandas dataFrame

    version 3.0.4 -> 3.1.0.alpha update
    dataframe now stored in _wrappedData.data
    CCPN Internal
    """
    from ccpn.core.ChemicalShiftList import CS_COLUMNS, CS_UNIQUEID, CS_CLASSNAME

    # skip for no shifts
    if not chemicalShiftList._oldChemicalShifts:
        return

    with undoBlockWithoutSideBar():
        # create a new dataframe
        shifts = []
        for row, oldShift in enumerate(chemicalShiftList._oldChemicalShifts):
            newRow = oldShift._getShiftAsTuple()
            if not newRow.isDeleted:
                # ignore deleted as not needed - this SHOULDN'T happen here, but just to be safe
                shifts.append(newRow)

                # get the id from the shift and update the _uniqueId dict
                _uniqueId = newRow.uniqueId
                _nextId = chemicalShiftList.project._queryNextUniqueIdValue(CS_CLASSNAME)
                chemicalShiftList.project._setNextUniqueIdValue(CS_CLASSNAME, 1 + max(_nextId, _uniqueId))

            # delete the old shift object
            oldShift.delete()

        # instantiate the dataframe
        df = pd.DataFrame(shifts, columns=CS_COLUMNS)
        df.set_index(df[CS_UNIQUEID], inplace=True, )  # drop=False)

        # set as the new subclassed DataFrameABC - not using yet, may have undo/redo issues
        chemicalShiftList._wrappedData.data = df  #_ChemicalShiftListFrame(df)

def _updateStrip_3_0_4_to_3_1_0(strip):
    """Update the strip object from 3.0.4 to 3.1.0
    """
    # move everything from stripHeaderDict in one operation - same names
    STRIPDICT = 'stripHeaderDict'
    space = strip._ccpnInternalData.pop(STRIPDICT, None)
    if space is not None:
        strip._ccpnInternalData[strip._CCPNMR_NAMESPACE].update(space)

    return strip
