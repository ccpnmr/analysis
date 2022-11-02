#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-11-02 22:05:34 +0000 (Wed, November 02, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"


#=========================================================================================
# Start of code
#=========================================================================================


def make1DSpectrumFromData(project, data, isotopeCodes, axisCodes, name, path, **kwargs):
    """Create a spectrum instance from numpy data array; store at path
    """
    nPoints = data.shape[0]
    sp = project.newEmptySpectrum(isotopeCodes=isotopeCodes,
                                  name=name,
                                  pointCounts=(nPoints,),
                                  **kwargs,
                                  )
    sp.setBuffering(True, path=path)
    sp.setSliceData(data, position=[1], sliceDim=1)
    sp.axisCodes = axisCodes
    return sp

def _getSpectrumParamsFromAnother(sp, axisCode):
    dd = {}
    properties = ['pointCounts','spectralWidths','spectralWidthsHz','spectrometerFrequencies', 'referencePoints','referenceValues']
    for p in properties:
        dd[p] = sp.getByAxisCodes(p, [axisCode])
    return dd

def _createSTDSpectrum(onResonanceSpectrum, offResonanceSpectrum,
                       stdName, stdNamePrefix='STD_', stdNameSuffix='',
                       stdPath=None):
    """
    CCPN internal. Used in pipes
    Function to create a user defined CCPN object spectrum. It can be used to create STD spectrum
    """
    project = onResonanceSpectrum.project
    isotopeCodes = onResonanceSpectrum.isotopeCodes
    axisCodes = onResonanceSpectrum.axisCodes
    spProperties = _getSpectrumParamsFromAnother(onResonanceSpectrum, axisCode=axisCodes[0])
    spProperties.pop('pointCounts') #avoid duplicate
    stdData = onResonanceSpectrum.intensities - offResonanceSpectrum.intensities
    name = f'{stdNamePrefix}{stdName}{stdNameSuffix}'
    std = make1DSpectrumFromData(project, data=stdData, isotopeCodes=isotopeCodes, axisCodes=axisCodes,
                                 name=name, path=stdPath, **spProperties)
    return std

