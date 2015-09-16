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

from ccpncore.lib.spectrum.Spectrum import checkIsotope
from ccpncore.util import Common as commonUtil
# from memops.qtgui.MessageDialog import showError

FILE_TYPE = 'Azara'

def readParams(filePath):
  
  # Check we didn't get a binary file
  
  fileObj = open(filePath, 'rb')
  firstData = fileObj.read(1024)
  
  testData = set([c for c in firstData]) - commonUtil.WHITESPACE_AND_NULL
  if min([ord(chr(c)) for c in testData]) < 32:
    dataFile = filePath
    dirName, fileName = os.path.split(filePath)
    
    for otherFile in os.listdir(dirName):
      if otherFile == fileName:
        continue
    
      if ('.par' in otherFile) and otherFile.startswith(fileName):
        filePath = os.path.join(dirName, otherFile)
        break
    
    else:
      msg = "Cannot find AZARA parameter file to go with binary file %s"
      # showError('Error', msg % filePath)
      return
     
  else:
    dataFile = None
      
    
  fileObj.close()
  
  # Format invariant

  wordSize = 4
  headerSize = 0
  blockHeaderSize = 0
  pulseProgram = None
  dataScale = 1.0

  # Params

  numPoints = []
  blockSizes = []
  refPpms = []
  refPoints = []
  specWidths = []
  specFreqs = []
  isotopes = []
  sampledValues = []
  sampledSigmas = []

  isFloatData = True
  isBigEndian = sys.byteorder == 'big'

  fileObj = open(filePath, 'rU')

  dim = 0
  for line in fileObj:
    line = line.strip()

    if not line:
      continue

    if line.startswith('!'):
      continue

    if '!' in line:
      line = line.split('!')[0]

    data = line.split()
    keyword = data[0]

    if keyword == 'file':
      if not dataFile:
        dataFile = data[1]

    elif keyword == 'int':
      isFloatData = False

    elif keyword == 'swap':
      isBigEndian = not isBigEndian

    elif keyword == 'big_endian':
      isBigEndian = True

    elif keyword == 'little_endian':
      isBigEndian = False

    elif keyword == 'ndim':
      nDim = int(data[1])
      numPoints = [None] * nDim
      blockSizes = [1] * nDim
      refPpms = [1.0] * nDim
      refPoints = [1.0] * nDim
      specWidths = [1000.0] * nDim
      specFreqs = [500.0] * nDim
      isotopes = ['1H'] * nDim
      sampledSigmas = [[]] * nDim
      sampledValues = [[]] * nDim

    elif keyword == 'dim':
      dim = int(data[1]) - 1

    elif keyword == 'npts':
      numPoints[dim] = int(data[1])

    elif keyword == 'block':
      blockSizes[dim] = int(data[1])

    elif keyword == 'sw':
      specWidths[dim] = float(data[1])

    elif keyword == 'sf':
      specFreqs[dim] = float(data[1])

    elif keyword == 'refppm':
      refPpms[dim] = float(data[1])

    elif keyword == 'refpt':
      refPoints[dim] = float(data[1])

    elif keyword == 'nuc':
      isotopes[dim] = checkIsotope(data[1])

    elif keyword == 'params':
      sampledValues[dim] = [float(x) for x in data[1:]]

    elif keyword == 'sigmas':
      sampledSigmas[dim] = [float(x) for x in data[1:]]

  fileObj.close()

  if dataFile is None:
    msg = "AZARA spectrum file not set in parameters"
    # showError('Error', msg)
    return

  if not os.path.exists(dataFile):
    dirPath, parFile = os.path.split(filePath)
    null, specFile = os.path.split(dataFile)
    dataFile = os.path.join(dirPath, specFile)
    
  if not os.path.exists(dataFile):
    msg = "AZARA spectrum data file %s does not exist"
    # showError('Error', msg % dataFile)
    return

  data = (FILE_TYPE, dataFile, numPoints, blockSizes,
          wordSize, isBigEndian, isFloatData,
          headerSize, blockHeaderSize,
          isotopes, specFreqs,
          specWidths, refPoints, refPpms,
          sampledValues, sampledSigmas,
          pulseProgram, dataScale)

  return data
