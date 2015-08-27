"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
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


def _doNamesMatchBound(lightName:str, heavyName:str) -> bool:
  """checks if lightName matches a hydrogen atom or fluorine bound to atom named heavyName
  NB, a name like H11 would match both C1 or C11 - cannot be helped"""

  # possible names for 'light' atoms or pseudoatoms
  lightFirstChars = 'HDTFMQ'
  lightAppendixChars = '123XY#'

  if ((lightName == "H" and heavyName == "N") or
      (lightName == "H#" and heavyName == "N") or
      (lightName == "H2''" and heavyName == "C2'") or
      (lightName == "H5''" and heavyName == "C5'")):
    # special cases for protein and DNA/RNA
    return True

  elif not lightName or len(heavyName) < 2:
    # lightName empty or heavyName too short
    # Single-char heavyName is only allowed in special cases above
    return False

  elif lightName[0] not in lightFirstChars or heavyName[0] in lightFirstChars:
    # incorrect nucleus code
    return False

  elif lightName[1:] == heavyName[1:]:
    # names match except for first character.
    return True

  elif lightName[1:-1] == heavyName[1:] and lightName[-1] in lightAppendixChars:
    # names match except for first character, with single suffix character
    return True

  else:
    return False

# def _boundNamesfromType(chemCompVar, atomName):
#   """get names of atoms bound to atom names atomName within chemComp"""
# NBNB TBD What is this for?
