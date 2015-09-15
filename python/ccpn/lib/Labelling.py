"""molecule labelling library functions

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

from ccpncore.lib.molecule import Labelling
from ccpn import Project
from ccpn import Atom
from ccpn import NmrAtom
from ccpn import Sample
from ccpncore.util.Pid import Pid
from ccpncore.util.typing import Sequence


def atomLabellingFractions(project:Project, atom:(Atom,NmrAtom,str), labelling:str) -> dict:
  """get {isotopeCode:labellingFraction} in given sample for atom/nmrAtom or ID string"""

  atomId = atom if isinstance(atom, str) else atom.id

  useAtom = project.getAtom(atomId)
  if useAtom is None:
    fields = Pid(atomId).fields
    if len(fields) == 4:
      atomName = fields[3]
      residueType = fields[2]
      return Labelling.chemAtomLabelFractions(project, labelling, residueType, atomName)

    else:
      # No valid parameters found, return empty dict
      return {}

  else:
    return Labelling.molAtomLabelFractions(labelling, useAtom._wrappedData.residue.molResidue,
                                          useAtom.name)



def atomPairLabellingFractions(project:Project, atomPair:Sequence, labelling:str) -> dict:
  """get {(isotopeCode1,isotopeCode2):labellingFraction with given labelling for atom pair
  each atom in atomPair may be an Atom, an NmrAtom, or an atom ID string """
  atomIds = tuple(x if isinstance(x, str) else x.id for x in atomPair)

  useAtoms = tuple(project.getAtom(x) for x in atomIds)
  if None in useAtoms:
    residueTypes = set()
    atomNames = []
    for atomId in atomIds:
      fields = Pid(atomId).fields
      if len(fields) == 4:
        atomNames.append(fields[3])
        residueTypes.add(fields[2])
      else:
        break
    else:
      if len(residueTypes) == 1:
        return Labelling.chemAtomPairLabelFractions(project, labelling, residueTypes.pop(), atomNames)

  else:
    residues = tuple(x._wrappedData.residue.molResidue for x in useAtoms)
    atomNames = tuple(x.name for x in useAtoms)
    return Labelling.molAtomLabelPairFractions(labelling, residues, atomNames)

  # no valid return - return empty
  return {}


def sampleChainLabelling(sample:Sample, chainCode:str) -> str:
  """Get labelling string for chain chainCode in sample
  If chainCode does not match a SampleComponent, look for unambiguous global labelling:
  Heuristics: If there is only one SampleComponent, use that labelling
  If all SAmpleComponents with explicit chainCodes have the same labeliing, use that labelling"""

  labelling = Labelling.NULL_LABELLING

  sampleComponents = sample.sortedSampleComponents()
  if len(sampleComponents) == 1:
    labelling = sampleComponents[0].labelling

  else:
    for sampleComponent in sampleComponents:
      if chainCode in sampleComponent.chainCodes:
        labelling = sampleComponent.labelling
        break

    else:
      labellings = [x.labelling for x in sample.sampleComponents if x.chainCodes]
      if len(labellings) == 1:
        # Only one labelling in use in sample - use it
        labelling = labellings.pop()
  #
  return labelling


def sampleLabellingFractions(sample:Sample, atom:(Atom,NmrAtom,str)) -> dict:
  """get {isotopeCode:labellingFraction} with given labelling for atom/nmrAtom or ID string"""

  atomId = atom if isinstance(atom, str) else atom.id
  fields = Pid(atomId).fields
  if len(fields) == 4:
    chainCode, dummy, residueType, atomName = fields
    labelling = sampleChainLabelling(sample, chainCode)
    if labelling == Labelling.NULL_LABELLING:
      # No labelling found - return empty
      return {}
    else:
      return atomLabellingFractions(sample._project, atomId, labelling)
  else:
    # Not a valid atom ID - return empty
    return {}


def samplePairLabellingFractions(sample:Sample, atomPair:Sequence) -> dict:
  """get {(isotopeCode1,isotopeCode2):labellingFraction in given sample for atom pair
  each atom in atomPair may be an Atom, an NmrAtom, or an atom ID string """
  atomIds = tuple(x if isinstance(x, str) else x.id for x in atomPair)

  labellings = set()
  residueTypes = set()
  atomNames = []
  for atomId in atomIds:
    fields = Pid(atomId).fields
    if len(fields) == 4:
      atomNames.append(fields[3])
      residueTypes.add(fields[2])
      labellings.add(sampleChainLabelling(sample, fields[0]))
    else:
      break

  else:
    if len(labellings) == 1:
      labelling = labellings.pop()
      useAtoms = tuple(sample._project.getAtom(x) for x in atomIds)
      if None in useAtoms:
        if len(residueTypes) == 1:
          return Labelling.chemAtomPairLabelFractions(sample._project, labelling, residueTypes.pop(),
                                                     atomNames)

      else:
        residues = tuple(x._wrappedData.residue.molResidue for x in useAtoms)
        return Labelling.molAtomLabelPairFractions(labelling, residues, atomNames)

  # No valid return found, return empty dict
  return {}
