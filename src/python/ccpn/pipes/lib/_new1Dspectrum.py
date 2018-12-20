#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:39 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"


#=========================================================================================
# Start of code
#=========================================================================================


def _create1DSpectrum(project, name, intensities, positions, expType, axisCodes):
    '''
     CCPN internal. Used in pipes
    Function to create a user defined CCPN object spectrum. It can be used to create STD spectrum
    '''

    spectrum = project.createDummySpectrum(axisCodes, name)
    spectrum.positions = positions
    spectrum.intensities = intensities
    spectrum.totalPointCounts = (len(intensities),)
    # lims = (float(min(positions[0], positions[-1])),
    #         float(max(positions[0], positions[-1])))
    # spectrum.aliasingLimits = (lims,)
    # spectrum.referenceValues = [lims[0]]

    if expType is not None:
        spectrum.experimentType = expType

    return spectrum
