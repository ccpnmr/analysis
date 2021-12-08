"""
Patch code for 3.0.4
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
__dateModified__ = "$dateModified: 2021-11-15 12:08:45 +0000 (Mon, November 15, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2021-11-10 10:28:41 +0000 (Wed, November 10, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from nmrglue.fileio.bruker import read_jcamp
from ccpn.util.Logging import getLogger


NC_PROC = 'NC_proc'

def getNCprocDataScale(spectrum):

    "Read the procs file"
    procs = spectrum.path.parent  / 'procs'
    if not procs.exists():
        raise RuntimeError('Invalid acqus file "%s"' % procs)
    params = read_jcamp(procs)

    if 'NC_proc' in params:
        dataScale = pow(2, float(params['NC_proc']))
    else:
        dataScale = 1.0

    return dataScale


def scaleBrukerSpectrum(spectrum):
    """Adjust the scaling in a Bruker spectrum; store it in the internal store for later
    """
    dataScale = getNCprocDataScale(spectrum)

    spectrum.scale *= dataScale
    if spectrum.dimensionCount >= 2:
        spectrum.positiveContourBase *= dataScale
        spectrum.negativeContourBase *= dataScale

    spectrum._setInternalParameter(NC_PROC, dataScale)
    getLogger().debug('Multiplied scale with NC_proc derived value (%s)' % dataScale)
