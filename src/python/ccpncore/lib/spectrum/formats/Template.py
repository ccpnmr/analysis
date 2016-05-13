"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================
import os, sys

from ccpncore.lib.spectrum.Spectrum import checkIsotope
# from memops.qtgui.MessageDialog import showError

FILE_TYPE = 'None'

def readParams(paramFileName):

  dataFile = None
  wordSize = 4
  isBigEndian = sys.byteorder == 'big'
  isFloatData = True
  headerSize = 0
  blockHeaderSize = 0
  sampledValues = []
  sampledSigmas = []
  pulseProgram = None
  dataScale = 1.0
  
  ndim = 2

  numPoints = [0] * ndim
  blockSizes = [0] * ndim
  refPpms = [0] * ndim
  refPoints = [0] * ndim
  specWidths = [0] * ndim
  specFreqs = [0] * ndim
  isotopes = [0] * ndim

  data = (FILE_TYPE, dataFile, numPoints, blockSizes,
          wordSize, isBigEndian, isFloatData,
          headerSize, blockHeaderSize,
          isotopes, specFreqs,
          specWidths, refPoints, refPpms,
          sampledValues, sampledSigmas,
          pulseProgram, dataScale)

  return data
