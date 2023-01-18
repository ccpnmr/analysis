"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2023-01-18 12:43:42 +0000 (Wed, January 18, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-02-15 14:34:15 +0000 (Tue, February 15, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.Logging import getLogger
from ccpn.core.lib.ContextManagers import inactivity

def updateProject_fromV2(project):
    """Update actions for a V2 project
    """

    if project._isUpgradedFromV2:
        # Regrettably this V2 upgrade operation must be done at the V3 level.
        # No good place except here
        for structureEnsemble in project.structureEnsembles:
            data = structureEnsemble.data
            if data is None:
                getLogger().warning("%s has no data. This should never happen")
            else:
                data._containingObject = structureEnsemble

        getLogger().debug('initialising v2 noise and contour levels')
        with inactivity():
            for spectrum in project.spectra:
                # calculate the new noise level
                spectrum.noiseLevel = spectrum.estimateNoise()

                # Check  contourLevels, contourColours
                spectrum._setDefaultContourValues()

                # set the initial contour colours
                (spectrum.positiveContourColour, spectrum.negativeContourColour) = getDefaultSpectrumColours(spectrum)
                spectrum.sliceColour = spectrum.positiveContourColour

                # set the initial axis ordering
                _getDefaultOrdering(spectrum)


    project._objectVersion = '3.0.4'
