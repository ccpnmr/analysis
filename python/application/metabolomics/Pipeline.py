"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - : 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = ": rhfogh $"
__date__ = ": 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = ": 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================

from ccpncore.util import Types


def runPipeLine(self, functions):
  pass

def alignToReference(spectrumArrays:dict, window:tuple, referencePosition:float):
  pass

def excludeRegions(spectrumArrays:dict, regions:list):
  pass

def polyBaseLine(spectrumArrays:dict, controlPoints:list):
  pass

def whittakerBaseline(spectrumArrays:dict, a:float, lam:float, controlPoints:list=None):
  pass

def segmentalAlign(spectrumArrays:dict, regions:list):
  pass

def bin(spectrumArrays:dict, binWidth:float):
  pass

def excludeSignalFreeRegions(spectrumArrays:dict, lam:float):
  pass

def whittakerSmooth(spectrumArrays:dict, a:float, lam:float, controlPoints:list=None):
  pass

def excludeBaselinePointss(spectrumArrays:dict, baselineRegion:tuple, baselineMultipler:float):
  pass

def normalise(spectrumArrays:dict, method:str, coeffs:list=None):
  pass

def autoScale(spectrumArrays:dict):
  pass

def meanCentre(spectrumArrays:dict):
  pass

def scale(spectrumArrays:dict, method:str):
  pass