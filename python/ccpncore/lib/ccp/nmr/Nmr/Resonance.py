"""Additional methods for Resonance class

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

from ccpncore.util import MergeObjects
from ccpncore.memops.ApiError import ApiError
from ccpncore.api.ccp.nmr import Nmr


def absorbResonance(resonanceA:Nmr.Resonance, resonanceB:Nmr.Resonance) -> None:
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
    shiftA.recalculateShiftValue()
  
  # AssognNames ar no longer used in new model
  # Assign names will be merged, but if assigned we only want the correct ones
  # if resonanceA.resonanceSet:
  #   assignNames = []
  #   for atomSet in resonanceA.resonanceSet.atomSets:
  #     assignNames.append( atomSet.name )
  #
  #   resonanceA.setAssignNames(assignNames)
  
  return resonanceA


def getBoundResonances(resonance:Nmr.Resonance) -> tuple:
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
      result = [x for x in partners if _doNamesMatchBound(resonanceName, x.name)]
    else:
      partners = [x for x in unassigned if x.isotopeCode not in singleCodes]
      result = [x for x in partners if _doNamesMatchBound(x.name, resonanceName)]

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

def _boundNamesfromType(chemCompVar, atomName):
  """get names of atoms bound to atom names atomName within chemComp"""