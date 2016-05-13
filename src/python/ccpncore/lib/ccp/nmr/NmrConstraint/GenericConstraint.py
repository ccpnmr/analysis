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

def newGenericContribution(self:'GenericConstraint', *params, **kwds) -> 'GenericContribution':
  """Create Contribution of type appropriate for the List type"""
  itemLength = self.parentList.itemLength
  if itemLength == 1:
    return self.newSingleAtomContribution(*params, **kwds)
  elif itemLength == 4:
    return self.newFourAtomContribution(*params, **kwds)
  else:
    # assert itemLength == 2
    return self.newAtomPairContribution(*params, **kwds)
