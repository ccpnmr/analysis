"""Library functions for molecule labeling

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

from ccpncore.util import Common as commonUtil
from ccpncore.util.typing import Sequence

# Default labeling - must be treated as 'not labeled'
NULL_LABELING = 'std'

def _getIsotopomerSingleAtomFractions(isotopomers, atomName, subType=1):
  """Descrn: Get the isotope proportions for a names atom in over a set
             of isotopomers. Fractions normalised to 1.0
     Inputs: List of ChemCompLabel.Isotopomers, Word (ChemAtom.name), Word (ChemAtom.subType)
     Output: Dict of Word:Float - IsotopeCode:fraction
  """

  fractionDict = {}
  isoWeightSum =  sum([x.weight for x in isotopomers])

  for isotopomer in isotopomers:
    atomLabels  = isotopomer.findAllAtomLabels(name=atomName,subType=subType)
    atWeightSum = sum([x.weight for x in atomLabels])
    atFactor    = isotopomer.weight  / isoWeightSum

    for atomLabel in atomLabels:
      isotopeCode = atomLabel.isotopeCode
      contrib     = atFactor * atomLabel.weight / atWeightSum
      fractionDict[isotopeCode] = fractionDict.get(isotopeCode,0.0) + contrib
  #
  return fractionDict


def _getIsotopomerAtomPairFractions(isotopomers, atomNames, subTypes=(1,1)):
  """Descrn: Get the combined isotope proportions for a given pair of named
             atoms within a set of isotopomers. Fractions normalised to 1.0
     Inputs: List of ChemCompLabel.Isotopomers, 2-Tuple of Words (ChemAtom.name), 2-Tuple of Words (ChemAtom.subType)
     Output: Dict of Tuple:Float - (IsotopeCode,IsotopeCode):fraction
  """

  fractionDict = {}

  isoWeightSum = sum([x.weight for x in isotopomers])

  atLabels   = [None, None]
  sumWeights = [None, None]

  for isotopomer in isotopomers:
    for i in (0,1):
      atLabels[i] = isotopomer.findAllAtomLabels(name=atomNames[i],
                                                 subType=subTypes[i])
      sumWeights[i] = sum([x.weight for x in atLabels[i]])

    # Done this way to guard against the divisor becoming zero
    factor  = isotopomer.weight / isoWeightSum
    divisor = sumWeights[0] * sumWeights[1]

    for atl0 in atLabels[0]:
      for atl1 in atLabels[1]:

        if atl0 is atl1:
          contrib = atl0.weight * factor / sumWeights[0]
        else:
          contrib = atl0.weight * atl1.weight * factor / divisor

        key = (atl0.isotopeCode, atl1.isotopeCode)
        fractionDict[key] = fractionDict.get(key, 0.0) + contrib
  #
  return fractionDict


def _singleAtomFractions(labeledMixture, resId, atName):
  """get the isotopeCode:fraction dictionary for a labeledMixture

  labeledMixture:  LabeledMixture object
  resid, atName, residue serial and atom name for atom
  Returns isotopeCode:fraction dictionary with fractions normalised to 1.0
  """

  # set up
  molResidue = labeledMixture.labeledMolecule.molecule.findFirstMolResidue(
               serial=resId)
  if molResidue is None:
    return None

  chemAtom = molResidue.chemCompVar.findFirstChemAtom(name=atName)
  if chemAtom is None:
    return None
  elementName = chemAtom.elementSymbol
  subType = chemAtom.subType

  # get MolLabelFractions
  useLabel = labeledMixture.averageComposition
  if not useLabel:
    molLabelFractions = list(labeledMixture.molLabelFractions)
    if len(molLabelFractions) == 1:
      useLabel = molLabelFractions[0]

  if useLabel:
    # average composition
    resLabel = useLabel.molLabel.findFirstResLabel(resId=resId)
    result = _molLabelFractionsDict(resLabel, atName, subType, elementName)

  else:
    # average over multiple molLabels
    molWeightSum = sum([x.weight for x in molLabelFractions])
    result = {}

    for mlf in molLabelFractions:
      resLabel = mlf.molLabel.findFirstResLabel(resId=resId)
      partResult = _molLabelFractionsDict(resLabel, atName, subType, elementName)
      for key, val in partResult.items():
        result[key] = result.get(key, 0.0) + val * mlf.weight / molWeightSum
  #
  return result


def _atomPairFractions(labeledMixture, resIds, atNames,):
  """get the isotope pair : fraction dictionary for a labeledMixture

  labeledMixture:  LabeledMixture object
  resIds: length-two tuple of residue serials
  atNames: length-two tuple of atom names

  Returns (isotopeCode1, isotopeCode2):fraction dictionary
  with fractions normalised to 1.0
  """

  result = {}

  if len(resIds) != 2:
    raise("Error: length of resIds %s must be 2" % resIds)
  if len(atNames) != 2:
    raise("Error: length of atNames %s must be 2"
          % atNames)

  # calculate starting parameters
  elementNames = []
  subTypes = []
  for ii in (0,1):
    molResidue = labeledMixture.labeledMolecule.molecule.findFirstMolResidue(
                 serial=resIds[ii])
    if molResidue is None:
      return None

    chemAtom = molResidue.chemCompVar.findFirstChemAtom(name=atNames[ii])
    if chemAtom is None:
      return None
    elementName = chemAtom.elementSymbol
    elementNames.append(elementName)
    subTypes.append(chemAtom.subType)

  # get MolLabelFractions
  avLabel = labeledMixture.averageComposition
  if avLabel:
    molLabelFractions = [avLabel]
  else:
    molLabelFractions = labeledMixture.molLabelFractions
  molWeightSum = sum([x.weight for x in molLabelFractions])

  # calculate result
  for mlf in molLabelFractions:
    molFactor = mlf.weight / molWeightSum
    molLabel = mlf.molLabel

    uncorrelatedAtoms = True
    if resIds[0] == resIds[1]:
      oneResLabel = molLabel.findFirstResLabel(resId=resIds[0])
      for ii in (0,1):
        if (oneResLabel.findAllAtomLabels(atomName=atNames[ii]) or
            oneResLabel.findAllAtomLabels(elementName=elementNames[ii])):
          uncorrelatedAtoms = False

    if uncorrelatedAtoms:
      # isotope frequencies are uncorrelated at the residue level
      dds = []
      for ii in (0,1):
        resLabel = molLabel.findFirstResLabel(resId=resIds[ii])
        dds.append(_molLabelFractionsDict(resLabel, atNames[ii],
                                     subTypes[ii], elementNames[ii]))

      for iso0 in dds[0]:
        for iso1 in dds[1]:
          key = (iso0, iso1)
          contrib = dds[0][iso0] * dds[1][iso1] * molFactor
          result[key] = result.get(key, 0.0) + contrib

    else:
      # isotope frequencies are correlated at the residue level
      # Only happens if both are from the same residue and neither has
      # any AtomLabels. Loop over ResLabelFractions only
      resLabelFractions = oneResLabel.resLabelFractions
      rlfWeightSum = sum([x.weight for x in resLabelFractions])
      for rlf in resLabelFractions:
        partResult = _getIsotopomerAtomPairFractions(rlf.iotopomers, atNames, subTypes)
        for key, val in partResult.items():
          contrib = val * rlf.weight * molFactor / rlfWeightSum
          result[key] = result.get(key, 0.0) + contrib
  #
  return result


def _molLabelFractionsDict(resLabel, atName, subType, elementName):
  """get the isotopeCode:fraction dictionary for a single resLabel

  resLabel: resLabel object
  resid residue serial
  atName, subType, elementName: atom name subType and element name for atom

  Returns isotopeCode:fraction dictionary with fractions normalised to 1.0
  """
  # set up
  result = {}

  # get atomLabels, if any
  atomLabels = resLabel.findAllAtomLabels(atomName=atName)
  if not atomLabels:
    atomLabels = resLabel.findAllAtomLabels(elementName=elementName)

  # calculate fractions for AtomLabels
  if atomLabels:
    atWeightSum = sum([x.weight for x in atomLabels])
    for atomLabel in atomLabels:
      isotopeCode = '%s%s' % (atomLabel.massNumber, elementName)
      result[isotopeCode] = (result.get(isotopeCode, 0.0) +
                             atomLabel.weight / atWeightSum)

  else:
    # calculate fractions for ResLabelFractions
    resLabelFractions = resLabel.resLabelFractions
    rlfWeightSum = sum([x.weight for x in resLabelFractions])

    for rlf in resLabelFractions:
      isotopomers = rlf.isotopomers
      isoFactor = rlf.weight  / rlfWeightSum

      fractionDict = _getIsotopomerSingleAtomFractions(isotopomers, atName, subType)

      for isotopeCode in fractionDict.keys():
        contrib = fractionDict[isotopeCode]
        result[isotopeCode] = result.get(isotopeCode,0.0) + (isoFactor * contrib)
  #
  return result

def molAtomLabelFractions(labeling:str, molResidue, atomName:str) -> dict:
  """get isotopeCode:percentage mapping for atom in molResidue, with given labeling
  Will use molecule specific labeling if one exists, otherwise general labeling scheme."""
  result = {}
  labeledMolecule = molResidue.root.findFirstLabeledMolecule(name=molResidue.molecule.name)
  if labeledMolecule:
    labeledMixture = labeledMolecule.findFirstLabeledMixture(name=labeling)
    if labeledMixture:
      result =  _singleAtomFractions(labeledMixture, molResidue.serial, atomName)

  if not result:
    result = chemAtomLabelFractions(molResidue.root, labeling, molResidue.ccpCode, atomName)
  #
  return result

def molAtomLabelPairFractions(labeling:str, molResiduePair:Sequence, atomNamePair:Sequence) -> dict:
  """get isotopeCode:percentage mapping for atom (molResidue, atomName) pair with given labeling
  Will use molecule specific labeling if one exists, otherwise general labeling scheme."""

  assert len(molResiduePair) == 2, "molAtomLabelPairFractions: length of molResidues must be 2"
  assert len(atomNamePair) == 2, "molAtomLabelPairFractions: length of atomNames must be 2"
  if molResiduePair[0].molecule is not molResiduePair[1].molecule:
    raise ValueError("molResidues must belong to the same molecule")

  result = {}
  molResidue0 = molResiduePair[0]
  labeledMolecule = molResidue0.root.findFirstLabeledMolecule(name=molResidue0.molecule.name)
  if labeledMolecule:
    # There is a specifically labeled molecule - use corresponding function
    labeledMixture = labeledMolecule.findFirstLabeledMixture(name=labeling)
    if labeledMixture:
      result =  _atomPairFractions(labeledMixture, [x.serial for x in molResiduePair], atomNamePair)

  if not result:
    # No specific labeled molecule
    if molResidue0 is molResiduePair[1]:
      # intraresidue = use labeling scheme, if any
      result = chemAtomPairLabelFractions(molResiduePair[0].root, labeling, molResidue0.ccpCode,
                                          atomNamePair)
    else:
      # Uncorrelated atoms - use product of fractions for each atom
      result = commonUtil.dictionaryProduct(
        chemAtomLabelFractions(molResidue0.root, labeling, molResidue0.ccpCode, atomNamePair[0]),
        chemAtomLabelFractions(molResidue0.root, labeling, molResiduePair[1].ccpCode, atomNamePair[1])
      )
  #
  return result

def chemAtomLabelFractions(project, labeling:str, ccpCode:str, atomName:str) -> dict:
  """get isotopeCode:percentage mapping for atom in ChemComp with given labeling"""
  result = {}
  labelingScheme = project.findFirstLabelingScheme(name=labeling)
  if labelingScheme:
    chemCompLabel = labelingScheme.findFirstChemCompLabel(ccpCode=ccpCode)
    if chemCompLabel:
      result =  _getIsotopomerSingleAtomFractions(chemCompLabel.isotopomers, atomName)
  #
  return result

def chemAtomPairLabelFractions(project, labeling:str, ccpCode:str, atomNamePair:Sequence) -> dict:
  """get isotopeCode:percentage mapping for atom pair in ChemComp with given labeling
  Assumes that atoms are in the same residue"""
  result = {}
  labelingScheme = project.findFirstLabelingScheme(name=labeling)
  if labelingScheme:
    chemCompLabel = labelingScheme.findFirstChemCompLabel(ccpCode=ccpCode)
    if chemCompLabel:
      result =  _getIsotopomerAtomPairFractions(chemCompLabel.isotopomers, atomNamePair)
  #
  return result

