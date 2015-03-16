"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
import os, sys

from ccpncore.lib.spectrum.Util import checkIsotope
# from memops.qtgui.MessageDialog import showError

XEASY_PARAM_DICT = {
  'ndim': 'Number of dimensions', 
  'nbits': '16 or 8 bit file type', 
  'sf': 'Spectrometer frequency in w',
  'sw': 'Spectral sweep width in w',
  'maxppm': 'Maximum chemical shift in w',
  'npts': 'Size of spectrum in w',
  'block': 'Submatrix size in w',
  'order': 'Permutation for w',
  'fold': 'Folding in w',  # not used
  'type': 'Type of spectrum',  # not used
  'nuc': 'Identifier for dimension w',
}

FILE_TYPE = 'Xeasy'

def readParams(paramFileName):

  # Format invariant
  
  headerSize = 0
  blockHeaderSize = 0
  isFloatData = True
  isBigEndian = sys.byteorder == 'big'
  sampledValues = []
  sampledSigmas = []
  pulseProgram = None
  dataScale = 1.0

  # Params

  fileObj = open(paramFileName, 'rU')

  firstLine = 'Version ....................... '
  line = fileObj.readline().strip()
  if line[:32] != firstLine:
    msg = 'The file %s does not look like an XEASY param file because the first line does not start "%s"'
    # showError('Error', msg % (paramFileName, firstLine))
    return

  if line[-1] != '1':
    print('Warning: this XEASY param file version is not 1 so might not be interpreted correctly')

  lines = fileObj.readlines()

  dd = {}
  for line in lines:
    key = line[:32].replace('.', '').strip()
    value = line[32:].strip()
    dd[key] = value
  
  fileObj.close()
  
  ndim = int(dd[XEASY_PARAM_DICT['ndim']])

  numPoints = [0] * ndim
  blockSizes = [0] * ndim
  refPpms = [0] * ndim
  refPoints = [0] * ndim
  specWidths = [0] * ndim
  specFreqs = [0] * ndim
  isotopes = [0] * ndim

  nbits = int(dd[XEASY_PARAM_DICT['nbits']])
  wordSize = nbits / 8
  dataFile = paramFileName[:-5] + str(nbits)

  for i in range(ndim):
    ss = str(i+1)
    j = int(dd[XEASY_PARAM_DICT['order']+ss]) - 1
    numPoints[j] = int(dd[XEASY_PARAM_DICT['npts']+ss])
    blockSizes[j] = int(dd[XEASY_PARAM_DICT['block']+ss])
    specFreqs[j] = float(dd[XEASY_PARAM_DICT['sf']+ss])
    specWidths[j] = float(dd[XEASY_PARAM_DICT['sw']+ss])
    specWidths[j] *= specFreqs[j]  # convert from ppm to Hz
    refPpms[j] = float(dd[XEASY_PARAM_DICT['maxppm']+ss])
    refPoints[j] = 1.0
    isotopes[j] = checkIsotope(dd[XEASY_PARAM_DICT['nuc']+ss])

  data = (FILE_TYPE, dataFile, numPoints, blockSizes,
          wordSize, isBigEndian, isFloatData,
          headerSize, blockHeaderSize,
          isotopes, specFreqs,
          specWidths, refPoints, refPpms,
          sampledValues, sampledSigmas,
          pulseProgram, dataScale)

  return data
