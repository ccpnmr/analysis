"""Additional methods for Resonance class

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

from ccpncore.util import MergeObjects
from ccpncore.lib.assignment import Assignment
from ccpncore.memops.ApiError import ApiError
# from ccpncore.lib.molecule.Labelling import _getIsotopomerSingleAtomFractions, _singleAtomFractions, \
#   _getIsotopomerAtomPairFractions, _atomPairFractions


def absorbResonance(resonanceA, resonanceB) -> None:
  """
  Transfers all information from resonanceB to resonanceA and deletes resonanceB

  .. describe:: Input
  
  Nmr.Resonance, Nmr.Resonance
  
  .. describe:: Output
  
  Nmr.Resonance
  """

  # NBNB TBD
  # This function does NOT consider what happens to other resonances
  # that are known to be directly bound to this one from peak assignments
  # E.g. the two resonances assigned to an HSQC peak
  # Merging a single resonance may make peak assignments inconsistent.
  
  if resonanceB is resonanceA:
    return resonanceA

  if resonanceB.isDeleted:
    return resonanceA

  if resonanceA.isDeleted:
    raise ApiError("function absorbResonance call on deleted resonance: @%s" % resonanceA.serial)
  
  isotopeA = resonanceA.isotopeCode
  isotopeB = resonanceB.isotopeCode
  
  if isotopeA and isotopeB:
    if isotopeA != isotopeB:
      resonanceA.root._logger.warning('Resonance Merge Failure: '
                                      'Attempt to merge resonances with different isotope codes')
      return
  
  # attributes where we have object.resonance
  controlData = {'findFirstMeasurement':('shiftDifferences', 'hExchRates',
                                         'hExchProtections', 'shiftAnisotropies',
                                         't1s', 't1Rhos', 't2s'),
                 'findFirstDerivedData':('pkas',),
                 'findFirstPeakDimContrib':('peakDimContribs',)
                }
  for funcName in controlData:
    for attrName in controlData[funcName]:
      for objectA in list(resonanceA.__dict__.get(attrName)):
        objectB = getattr(objectA.parent, funcName)(resonance=resonanceB)
        if objectB is not None:
          MergeObjects.mergeObjects(objectB, objectA)
  
  # attributes where we have object.resonances
  controlData = {'findFirstMeasurement':('jCouplings',
                                         'noes', 'rdcs', 'dipolarRelaxations'),
                 'findFirstDerivedData':('isotropicS2s', 'spectralDensities',
                                         'datums'),
                 'findFirstPeakDimContribN':('peakDimContribNs',)
                }
  for funcName in controlData:
    for attrName in controlData[funcName]:
      for objectA in list(resonanceA.__dict__.get(attrName)):
        testKey = set(objectA.__dict__['resonances'])
        testKey.remove(resonanceA)
        testKey.add(resonanceB)
        testKey = frozenset(testKey)
        objectB = getattr(objectA.parent, funcName)(resonances=testKey)
    
        if objectB is not None:
          MergeObjects.mergeObjects(objectB, objectA)
  
  # We rae not using covalentlyBound any more - removeed from model
  # resonanceA.setCovalentlyBound([])
  # resonanceB.setCovalentlyBound([])
        
  # merge shifts in the same shiftlist
  # NB must be done after other measurements 
  for shiftA in resonanceA.shifts:
    for shiftB in resonanceB.shifts:
      if shiftA.parentList is shiftB.parentList:
        shiftA = MergeObjects.mergeObjects(shiftB,shiftA)

  # Get rid of duplicate appData
  for appData in resonanceA.applicationData:
    matchAppData = resonanceB.findFirstApplicationData(application=appData.application,
                                                       keyword=appData.keyword)
    if matchAppData:
      resonanceB.removeApplicationData(matchAppData)
  
  MergeObjects.mergeObjects(resonanceB, resonanceA)
  
  # Must be after resonance merge, so that links to peaks are properly set
  for shiftA in resonanceA.shifts:
    shiftA.recalculateValue()
  
  # AssignNames ar no longer used in new model
  # Assign names will be merged, but if assigned we only want the correct ones
  # if resonanceA.resonanceSet:
  #   assignNames = []
  #   for atomSet in resonanceA.resonanceSet.atomSets:
  #     assignNames.append( atomSet.name )
  #
  #   resonanceA.setAssignNames(assignNames)
  
  return resonanceA


def getBoundResonances(resonance) -> tuple:
  """get resonances that are known to be directly bound to this one, using ONLY resonance assignment
  """

  # heavy-atom intraresidue bonds to standard protein atoms
  # to be used for completely unassigned resonanceGroups
  genericProteinBound = {
    'N':('CA',),
    'C':('CA',),
    'CB':('CA',),
    'CA':('C', 'N', 'CB')
  }

  resonanceGroup = resonance.resonanceGroup
  chemComp = resonanceGroup.chemComp
  resonanceName = resonance.name
  result = None
  unassigned = None

  if chemComp is None:
    # No assignment even to type
    unassigned = resonanceGroup.resonances

  else:
    chemCompVar = resonanceGroup.chemCompVar or chemComp.findFirstChemCopmVar(isDefaultVar=True)
    residue = resonanceGroup.residue

    if residue:
      # resonanceGroup is assigned
      atom = residue.findFirstAtom(name=resonanceName)
      if atom:
        # resonance is assigned - find bound resonances only from assignment
        result = []
        names = [x.name for x in atom.boundAtoms]
        for name in sorted(names):
          rr = resonanceGroup.findFirstResonance(name=name)
          if rr is not None:
            result.append(rr)

        return tuple(result)

      else:
        # Atom is not assigned - look for bound resonances among unassigned only
        unassigned = [x for x in resonanceGroup.resonances
                      if residue.findFirstAtom(name=x.name) is None]

    elif chemCompVar:
      # Type is assigned. Use type to look for bound resonances
      unassigned = resonanceGroup.resonances  # NBNB this is TEMPORARY
      pass
      # NBNB TBD
      # NBNB this is postponed till later - it needs to be done by making a map
      # starting from the ChemCompVar and caching those, and that is not for now.
      # NBNB unassigned must be set
      # NBNB not all resonance names can be found in chemCompVar
      # NBNB add interresidue bonds if possible


  if unassigned:
    # resonance is unassigned. Look for bound atoms among other unassigned resonances

    singleCodes = ('1H', '2H', '3H', '19F')
    if resonance.isotopeCode in singleCodes:
      partners = [x for x in unassigned if x.isotopeCode in singleCodes]
      result = [x for x in partners if Assignment._doNamesMatchBound(resonanceName, x.name)]
    else:
      partners = [x for x in unassigned if x.isotopeCode not in singleCodes]
      result = [x for x in partners if Assignment._doNamesMatchBound(x.name, resonanceName)]

    if not residue:
    # if not chemCompVar:
      # This resonanceGroup is not even type assigned.
      # Special cases - add bonds for protein backbone heavy atoms
    #
    # NBNB TBD when type-assigned resonanceGroups are properly handled,
    # this shoudl say 'if not chemCompVar

      extraNames = genericProteinBound.get(resonance.name)
      resonances = [x for x in unassigned if x.name in extraNames]
      if resonances:
        if any((x.molecule.molType == 'protein') for x in resonance.nmrProject.molSystem.chains):
          # The molecule.molType call is expensive and so this 'if' should be executed last
          result.extend(resonances)

  #
  return tuple(result)
#
#
# def getLabellingFraction(resonance, labelling:str):
#   """
#   Get the fraction of labelling for a given resonance's assignment
#   or make a guess if it is atom typed and in a residue typed spin system.
#   The labelling string is teh key for a labelledMixture (if a LabelledMolecule can be found)
#   or else the name of a LabellingScheme
#   Can work with a reference isotopomer scheme or a labeled mixture.
#
#   .. describe:: Input
#
#   Nmr.Resonance, str
#
#   .. describe:: Output
#
#   Float
#   """
#
#   # Get labellingObject
#   root = resonance.root
#
#   moleculeName = None
#   resonanceGroup = resonance.resonanceGroup
#   if resonanceGroup is not None:
#     residue = resonanceGroup.assignedResidue
#     if residue is not None:
#       labelledMolecule = root.findFirstLabelledMolecule(name=residue.chain.molecule.name)
#       if labelledMolecule is not None:
#
#
#
#   fraction = 1.0 # In the absence of any assignment
#
#   resonanceSet = resonance.resonanceSet
#
#   if labellingObject.className == 'LabelingScheme':
#     if resonanceSet:
#       atomSets = list(resonanceSet.atomSets)
#       residue = atomSets[0].findFirstAtom().residue
#       ccpCode = residue.ccpCode
#       molType = residue.molType
#       chemCompLabel = labellingObject.findFirstChemCompLabel(ccpCode=ccpCode,
#                                                              molType=molType)
#
#       if not chemCompLabel:
#         natAbun = resonance.root.findFirstLabelingScheme(name='NatAbun')
#
#         if natAbun:
#           chemCompLabel = natAbun.findFirstChemCompLabel(ccpCode=ccpCode,
#                                                          molType=molType)
#
#       if chemCompLabel:
#         isotopomers = chemCompLabel.isotopomers
#         isotope = resonance.isotopeCode
#
#         fractions = []
#         for atomSet in atomSets:
#           atoms = atomSet.atoms
#           atomFrac = 0.0
#
#           for atom in atoms:
#             subType = atom.chemAtom.subType
#
#             fracDict = _getIsotopomerSingleAtomFractions(isotopomers,
#                                                         atom.name, subType)
#             atomFrac += fracDict.get(isotope, 1.0)
#
#           atomFrac /= float(len(atoms))
#
#           fractions.append(atomFrac)
#
#         fraction = max(fractions)
#
#     elif resonance.assignNames:
#       atomNames = resonance.assignNames
#       spinSystem = resonance.resonanceGroup
#
#       if spinSystem and spinSystem.ccpCode:
#         ccpCode = spinSystem.ccpCode
#         molType = spinSystem.molType or 'protein'
#         chemCompLabel = labellingObject.findFirstChemCompLabel(ccpCode=ccpCode,
#                                                          molType=molType)
#
#         if not chemCompLabel:
#           natAbun = resonance.root.findFirstLabelingScheme(name='NatAbun')
#
#           if natAbun:
#             chemCompLabel = natAbun.findFirstChemCompLabel(ccpCode=ccpCode,
#                                                            molType=molType)
#
#         if chemCompLabel:
#           isotopomers = chemCompLabel.isotopomers
#           isotope = resonance.isotopeCode
#           fraction = 0.0
#
#           for atomName in atomNames:
#             fracDict = _getIsotopomerSingleAtomFractions(isotopomers,
#                                                         atomName, 1)
#             fraction += fracDict.get(isotope, 1.0)
#
#           fraction /= float(len(atomNames))
#
#   else: # get from experiment labelled mixture
#
#     if resonanceSet:
#       atomSets = list(resonanceSet.atomSets)
#       isotope = resonance.isotopeCode
#       labelledMixtures = labellingObject.labeledMixtures
#       molResidue = atomSets[0].findFirstAtom().residue.molResidue
#       molecule = molResidue.molecule
#       resId = molResidue.serial
#
#       for mixture in labelledMixtures:
#         if mixture.labeledMolecule.molecule is molecule:
#           fractions = []
#           for atomSet in atomSets:
#             atoms = atomSet.atoms
#             atomFrac = 0.0
#
#             for atom in atoms:
#               fracDict = _singleAtomFractions(mixture, resId, atom.name)
#               atomFrac += fracDict.get(isotope, 1.0)
#
#             atomFrac /= float(len(atoms))
#
#             fractions.append(atomFrac)
#
#           fraction = max(fractions)
#           break
#
#   return fraction
#
#
# def getPairLabellingFraction(resonanceA, resonanceB, labelling:str):
#   """
#   Get the fraction of a pair of resonances both being labelled
#   given a labelling scheme. Considers individual isotopomers if
#   the resonances are bound within the same residue.
#   Can work with a reference isotopomer scheme or a labeled mixture.
#
#   .. describe:: Input
#
#   Nmr.Resonance, Nmr.Resonance, str
#
#   .. describe:: Output
#
#   Float
#   """
#
#   # from ccpnmr.analysis.core.MoleculeBasic import areResonancesBound
#
#   fraction = 1.0 # In the absence of any assignment
#
#   resonanceSetA = resonanceA.resonanceSet
#   resonanceSetB = resonanceB.resonanceSet
#
#   if resonanceSetA and resonanceSetB:
#     isotopes = (resonanceA.isotopeCode, resonanceB.isotopeCode)
#     atomA = resonanceSetA.findFirstAtomSet().findFirstAtom()
#     atomB = resonanceSetB.findFirstAtomSet().findFirstAtom()
#     residueA = atomA.residue
#     residueB = atomB.residue
#
#     if labellingObject.className == 'LabelingScheme':
#       findFirstChemCompLabel = labellingObject.findFirstChemCompLabel
#
#       subTypeA = atomA.chemAtom.subType
#       subTypeB = atomB.chemAtom.subType
#
#       if residueA is residueB:
#         chemCompLabel = findFirstChemCompLabel(ccpCode=residueA.ccpCode,
#                                                molType=residueA.molType)
#
#         if not chemCompLabel:
#           natAbun = resonanceA.root.findFirstLabelingScheme(name='NatAbun')
#
#           if natAbun:
#             chemCompLabel = natAbun.findFirstChemCompLabel(ccpCode=residueA.ccpCode,
#                                                            molType=residueA.molType)
#         if not chemCompLabel:
#           return 1.0 # Nothing can be done, no isotopomers
#
#         isotopomers  = chemCompLabel.isotopomers
#
#         fractions = []
#         for atomSetA in resonanceSetA.atomSets:
#           for atomSetB in resonanceSetB.atomSets:
#
#             n = 0.0
#             pairFrac = 0.0
#             for atomA in atomSetA.atoms:
#               nameA = atomA.name
#               subTypeA = atomA.chemAtom.subType
#
#               for atomB in atomSetB.atoms:
#                 atomNames = (nameA, atomB.name)
#                 subTypes  = (subTypeA, atomB.chemAtom.subType)
#                 pairDict  = _getIsotopomerAtomPairFractions(isotopomers, atomNames, subTypes)
#                 pairFrac += pairDict.get(isotopes, 1.0)
#                 n += 1.0
#
#             pairFrac /= n
#             fractions.append(pairFrac)
#
#         fraction = max(fractions)
#
#       else: # Assumes filly mixed
#         fractionA = getResonanceLabellingFraction(resonanceA, labelling)
#         fractionB = getResonanceLabellingFraction(resonanceB, labelling)
#         fraction = fractionA * fractionB
#
#     else: # Get Labelling mixture from experiment
#       molResidueA = residueA.molResidue
#       molResidueB = residueB.molResidue
#       resIds = (molResidueA.serial, molResidueB.serial)
#       labelledMixtures = labellingObject.labeledMixtures
#
#       moleculeA = molResidueA.molecule
#       moleculeB = molResidueA.molecule
#
#       if moleculeA is moleculeB:
#         for mixture in labelledMixtures:
#           if mixture.labeledMolecule.molecule is moleculeA:
#             fractions = []
#             for atomSetA in resonanceSetA.atomSets:
#               for atomSetB in resonanceSetB.atomSets:
#
#                 n = 0.0
#                 pairFrac = 0.0
#                 for atomA in atomSetA.atoms:
#                   nameA = atomA.name
#
#                   for atomB in atomSetB.atoms:
#                     atomNames = (nameA, atomB.name)
#
#                     pairDict  = _atomPairFractions(mixture, resIds, atomNames)
#                     pairFrac += pairDict.get(isotopes, 1.0)
#                     n += 1.0
#
#                 pairFrac /= n
#                 fractions.append(pairFrac)
#
#             fraction = max(fractions)
#             break
#       else:
#         fractionA = getResonanceLabellingFraction(resonanceA, labelling)
#         fractionB = getResonanceLabellingFraction(resonanceB, labelling)
#         fraction = fractionA * fractionB
#
#   else:
#     fractionA = getResonanceLabellingFraction(resonanceA, labelling)
#     fractionB = getResonanceLabellingFraction(resonanceB, labelling)
#     fraction = fractionA * fractionB
#
#   return fraction