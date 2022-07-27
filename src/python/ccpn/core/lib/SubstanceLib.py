"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-07-27 15:41:00 +0100 (Wed, July 27, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author:  $"
__date__ = "$Date:  $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.decorators import singleton
from collections import defaultdict

@singleton
class SpectrumSubstancesDict(defaultdict):
    """
    Class to contain spectra and their linked referenceSubstances
    """
    def __init__(self):
        super(SpectrumSubstancesDict, self).__init__(list)

    def get(self, item):
        """
        return values if item is found or an empty list
        :param item: dictionary key
        :return: list
        """
        return super().get(item) or []

@singleton
class SubstanceSpectraDict(defaultdict):
    """
    Class to contain substances and their linked referenceSpectra
    """

    def __init__(self):
        super(SubstanceSpectraDict, self).__init__(list)

    def get(self, item):
        """
        return values if item is found or an empty list
        :param item: dictionary key
        :return: list
        """
        return super().get(item) or []


def _addSubstancesToSpectrum(spectrum, substances):
    pointer = SpectrumSubstancesDict()
    pointer[spectrum].extend(substances)

def _addSpectraToSubstance(substance, spectra):
    pointer = SubstanceSpectraDict()
    pointer[substance].extend(spectra)

def _initSubstanceSpectraDict():
    from ccpn.framework.Application import getProject
    project = getProject()
    if not project:
        return
    dd = SubstanceSpectraDict()
    for sp in project.spectra:
        dd[sp].extend(sp.referenceSubstances)

def _updateSubstanceDicts4Spectrum(spectrum, substances):
    dd = SpectrumSubstancesDict()
    if not spectrum in dd:
        _addSubstancesToSpectrum(spectrum, substances)
        for substance in substances:
            _addSpectraToSubstance(substance, [spectrum])
