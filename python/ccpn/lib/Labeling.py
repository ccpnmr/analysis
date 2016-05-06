"""molecule labeling library functions

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

from ccpncore.lib.molecule import Labeling
from ccpn import Project
from ccpn import Atom
from ccpn import NmrAtom
from ccpn import Sample
from ccpncore.util.Pid import Pid
from typing import Sequence


def atomLabelingFractions(project:Project, atom:(Atom,NmrAtom,str), labeling:str) -> dict:
  """get {isotopeCode:labelingFraction} in given sample for atom/nmrAtom or ID string"""

  atomId = atom if isinstance(atom, str) else atom.id

  useAtom = project.getAtom(atomId)
  if useAtom is None:
    fields = Pid(atomId).fields
    if len(fields) == 4:
      atomName = fields[3]
      residueType = fields[2]
      return Labeling.chemAtomLabelFractions(project, labeling, residueType, atomName)

    else:
      # No valid parameters found, return empty dict
      return {}

  else:
    return Labeling.molAtomLabelFractions(labeling, useAtom._wrappedData.residue.molResidue,
                                          useAtom.name)



def atomPairLabelingFractions(project:Project, atomPair:Sequence, labeling:str) -> dict:
  """get {(isotopeCode1,isotopeCode2):labelingFraction with given labeling for atom pair
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
        return Labeling.chemAtomPairLabelFractions(project, labeling, residueTypes.pop(), atomNames)

  else:
    residues = tuple(x._wrappedData.residue.molResidue for x in useAtoms)
    atomNames = tuple(x.name for x in useAtoms)
    return Labeling.molAtomLabelPairFractions(labeling, residues, atomNames)

  # no valid return - return empty
  return {}


def sampleChainLabeling(sample:Sample, chainCode:str) -> str:
  """Get labeling string for chain chainCode in sample
  If chainCode does not match a SampleComponent, look for unambiguous global labeling:
  Heuristics: If there is only one SampleComponent, use that labeling
  If all SampleComponents with explicit chainCodes have the same labeling, use that labeling"""

  labeling = Labeling.NULL_LABELING

  sampleComponents = sample.sortedSampleComponents()
  if len(sampleComponents) == 1:
    labeling = sampleComponents[0].labeling

  else:
    for sampleComponent in sampleComponents:
      if chainCode in sampleComponent.chainCodes:
        labeling = sampleComponent.labeling
        break

    else:
      labelings = [x.labeling for x in sample.sampleComponents if x.chainCodes]
      if len(labelings) == 1:
        # Only one labeling in use in sample - use it
        labeling = labelings.pop()
  #
  return labeling


def sampleLabelingFractions(sample:Sample, atom:(Atom,NmrAtom,str)) -> dict:
  """get {isotopeCode:labelingFraction} with given labeling for atom/nmrAtom or ID string"""

  atomId = atom if isinstance(atom, str) else atom.id
  fields = Pid(atomId).fields
  if len(fields) == 4:
    chainCode, dummy, residueType, atomName = fields
    labeling = sampleChainLabeling(sample, chainCode)
    if labeling == Labeling.NULL_LABELING:
      # No labeling found - return empty
      return {}
    else:
      return atomLabelingFractions(sample._project, atomId, labeling)
  else:
    # Not a valid atom ID - return empty
    return {}


def samplePairLabelingFractions(sample:Sample, atomPair:Sequence) -> dict:
  """get {(isotopeCode1,isotopeCode2):labelingFraction in given sample for atom pair
  each atom in atomPair may be an Atom, an NmrAtom, or an atom ID string """
  atomIds = tuple(x if isinstance(x, str) else x.id for x in atomPair)

  labelings = set()
  residueTypes = set()
  atomNames = []
  for atomId in atomIds:
    fields = Pid(atomId).fields
    if len(fields) == 4:
      atomNames.append(fields[3])
      residueTypes.add(fields[2])
      labelings.add(sampleChainLabeling(sample, fields[0]))
    else:
      break

  else:
    if len(labelings) == 1:
      labeling = labelings.pop()
      useAtoms = tuple(sample._project.getAtom(x) for x in atomIds)
      if None in useAtoms:
        if len(residueTypes) == 1:
          return Labeling.chemAtomPairLabelFractions(sample._project, labeling, residueTypes.pop(),
                                                     atomNames)

      else:
        residues = tuple(x._wrappedData.residue.molResidue for x in useAtoms)
        return Labeling.molAtomLabelPairFractions(labeling, residues, atomNames)

  # No valid return found, return empty dict
  return {}
