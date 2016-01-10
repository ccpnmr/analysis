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

from ccpncore.lib import Constants
from ccpncore.lib.molecule import MoleculeQuery

def resetResidueType(self, value:str=None):
  """Reset residue type. NB this renames the NmrResidue"""
  self.residueType = value
  if value is None:
    self.molType = None
    self.ccpCode = None
  else:
    # get chem comp ID strings from residue type
    tt = MoleculeQuery.fetchStdResNameMap(self.root).get(value)
    if tt is not None:
      self.molType, self.ccpCode = tt

def resetNmrChain(self, newNmrChain:'NmrChain'=None):
  """Remove ResonanceGroup from NmrChain, breaking up connected NmrChain if necessary
  and move to newNmrChain (or default NmrChain if not set)"""

  nmrChain = self.nmrChain
  defaultNmrChain = self.nmrProject.findFirstNmrChain(code=Constants.defaultNmrChainCode)
  newNmrChain = newNmrChain or defaultNmrChain

  if newNmrChain is nmrChain:
    return

  elif self.mainResonanceGroup is not self:
    raise ValueError("Cannot disconnect nmrChain for satellite ResonanceGroup")


  elif nmrChain.isConnected:
    stretch = nmrChain.mainResonanceGroups
    if self is stretch[-2]:
      stretch[-1].directNmrChain = defaultNmrChain
    elif self is stretch[1]:
      stretch[0].directNmrChain = defaultNmrChain
    elif self not in (stretch[0], stretch[-1]):
      index = stretch.index(self)
      # The tricky case - we have to make a new NmrChain
      extraNmrChain = self.nmrProject.newNmrChain(isConnected=True)
      dummyNmrChain = self.nmrProject.newNmrChain()
      ll = stretch[index+1:]
      # NB We have to do this in two steps in order to avoid 1) breaking the connect chain
      # 2) overriding the API and having to do independent undo handling
      for resonanceGroup in reversed(ll):
        resonanceGroup.directNmrChain = dummyNmrChain
      for resonanceGroup in ll:
        resonanceGroup.directNmrChain = extraNmrChain
      dummyNmrChain.delete()

  #
  self.directNmrChain = newNmrChain

  # clean out single-residue connected stretches and delete empty ones
  if nmrChain.isConnected:
    ll = nmrChain.mainResonanceGroups
    if len(ll) == 1:
      ll[0].directNmrChain = defaultNmrChain
    if not nmrChain.mainResonanceGroups:
      nmrChain.delete()

def resetAssignment(self, nmrChain:'NmrChain', sequenceCode:str):
  """Reset nmrChain and sequenceCode at the same time, while avoiding name clashes"""
  oldNmrChain = self.nmrChain
  oldSequenceCode = self.sequenceCode
  previous = nmrChain.findFirstResonanceGroup(sequenceCode=sequenceCode)
  if previous is self:
    return
  elif previous is None:
    self.sequenceCode = None
    self.directNmrChain = nmrChain
    try:
      self.sequenceCode = sequenceCode
    except:
      # error - probably to do with offset. Set back to initial state
      self.directNmrChain = oldNmrChain
      self.sequenceCode = oldSequenceCode
      raise ValueError("Could not set to sequenceCode %s in nmrChain %s" % (sequenceCode, nmrChain))
