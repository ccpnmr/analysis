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
__dateModified__ = "$dateModified: 2021-11-16 12:02:37 +0000 (Tue, November 16, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2021-11-10 10:28:41 +0000 (Wed, November 10, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.framework.Version import VersionString, applicationVersion

def _updateSpectrum_3_0_4(spectrum) -> VersionString:
    """Update the _ccpnInternal settings from version3.0.4 -> 3.1.0.alpha
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

    return applicationVersion
