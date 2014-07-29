"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
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

from array import array

NDIM_INDEX = 9
NPTS_INDEX = (99, 219, 15, 32)
COMPLEX_INDEX = (55, 56, 51, 54)
ORDER_INDEX = (24, 25, 26, 27)
SW_INDEX = (229, 100, 11, 29)
SF_INDEX = (218, 119, 10, 28)
ORIGIN_INDEX = (249, 101, 12, 30)
ISOTOPE_INDEX = (18, 16, 20, 22)
VALUE_INDEX = 199

def readParams(filePath):

  dataFile = filePath
  wordSize = 4
  isFloatData = True
  headerSize = 4*512
  blockHeaderSize = 0
  sampledValues = []
  sampledSigmas = []
  pulseProgram = None
  dataScale = 1.0
  
  fileObj = open(filePath, 'rb')

  headData = fileObj.read(headerSize)
  fileObj.close()

  if len(headData) < headerSize:
    msg = 'NMRPipe file %s appears to be truncated'
    # showError('Error', msg % filePath)
    return

  floatVals = array('f')
  floatVals.fromstring(headData)

  if floatVals[0] != 0.0:
    msg = 'NMRPipe file %s appears to be corrupted'
    # showError('Error', msg % filePath)
    return

  byte_order = [ 0x40, 0x16, 0x14, 0x7b ]
  t = [ ord(chr(c)) for c in headData[8:12] ]
  if t == byte_order:
    isBigEndian = True
    
  else:
    t.reverse()
    if t == byte_order:
      isBigEndian = False
      
    else:
      msg = 'NMRPipe file %s appears to be corrupted'
      # showError('Error', msg % filePath)
      return

  if isBigEndian is not (sys.byteorder == 'big'):
    floatVals.byteswap()

  ndim = int(floatVals[NDIM_INDEX])
  
  if not (0 < ndim < 5):
    msg = 'Can only handle NMRPipe files with between 1 and 4 dimensions'
    # showError('Error', msg)
    return

  numPoints = [0] * ndim
  blockSizes = [0] * ndim
  refPpms = [0.0] * ndim
  refPoints = [0.0] * ndim
  specWidths = [1000.0] * ndim
  specFreqs = [500.0] * ndim
  isotopes = [None] * ndim
  
  for i in range(ndim):
    j = int(floatVals[ORDER_INDEX[i]]) - 1
    c = int(floatVals[COMPLEX_INDEX[i]])
    if c == 0:
      msg = 'NMRPipe data is complex in dim %d, can only cope with real data at present'
      # showError('Error', msg % (i+1))
      return
      
    numPoints[i] = int(floatVals[NPTS_INDEX[i]])
    
    if i == 0:
      blockSizes[i] = numPoints[i]
    else:
      blockSizes[i] = 1
      
    specWidths[i] = sw = floatVals[SW_INDEX[j]]
    if sw == 0:
      specWidths[i] = sw  = 1000 # ?
      
    specFreqs[i] = sf = floatVals[SF_INDEX[j]]
    o = floatVals[ORIGIN_INDEX[j]]
    
    refPpms[i] = (sw + o) / sf
    refPoints[i] = 0
    n = 4 * ISOTOPE_INDEX[j]
    isotope = headData[n:n+4].strip()

    # get rid of null termination
    m = isotope.find(0)
    if m >= 0:
      isotope = (isotope[:n])
    isotopes.append( checkIsotope(isotope.decode("utf-8")) )
      
    if isotope == 'ID': # ?
      isotopes[i] = None
    else:
      isotopes[i] = checkIsotope(isotope.decode("utf-8"))

  data = (dataFile, numPoints, blockSizes,
          wordSize, isBigEndian, isFloatData,
          headerSize, blockHeaderSize,
          isotopes, specFreqs,
          specWidths, refPoints, refPpms,
          sampledValues, sampledSigmas,
          pulseProgram, dataScale)

  return data
