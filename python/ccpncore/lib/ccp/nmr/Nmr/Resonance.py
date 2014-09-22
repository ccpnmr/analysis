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



def mergeResonances(resonanceB, resonanceA):
  """
  Merge two resonances and their shifts into one

  .. describe:: Input
  
  Nmr.Resonance, Nmr.Resonance
  
  .. describe:: Output
  
  Nmr.Resonance
  """

  from ccpnmr.analysis.core.MoleculeBasic import getResidueMapping
  
  if resonanceB is resonanceA:
    return resonanceA

  if resonanceB.isDeleted:
    return resonanceA

  if resonanceA.isDeleted:
    return resonanceB
  
  removeAssignmentNotifiers()
  
  isotopeA = resonanceA.isotopeCode
  isotopeB = resonanceB.isotopeCode
  
  if isotopeA and isotopeB:
    if isotopeA != isotopeB:
      showWarning('Resonance Merge Failure',
                  'Attempt to merge resonances with different isotope codes')
      setupAssignmentNotifiers()
      return 
  
  mappings = []
  resonanceSet = resonanceB.resonanceSet
  if resonanceSet:
    atomSets = resonanceSet.atomSets
    residue  = resonanceSet.findFirstAtomSet().findFirstAtom().residue
    serials  = [atomSet.serial for atomSet in atomSets]
    serials.sort()
    residueMapping = getResidueMapping(residue)
    for atomSetMapping in residueMapping.atomSetMappings:
      serials2 = list(atomSetMapping.atomSetSerials)
      serials2.sort()
      if serials2 == serials:
        mappings.append([atomSetMapping, atomSets])
  
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
          objectA = mergeObjects(objectB, objectA)
  
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
          objectA = mergeObjects(objectB, objectA)
  
  resonanceA.setCovalentlyBound([])
  resonanceB.setCovalentlyBound([])
        
  # merge shifts in the same shiftlist
  # NB must be done after other measurements 
  for shiftA in resonanceA.shifts:
    for shiftB in resonanceB.shifts:
      if shiftA.parentList is shiftB.parentList:
        shiftA = mergeObjects(shiftB,shiftA)

  # Get rid of duplicate appData
  for appData in resonanceA.applicationData:
    matchAppData = resonanceB.findFirstApplicationData(application=appData.application,
                                                       keyword=appData.keyword)
    if matchAppData:
      resonanceB.removeApplicationData(matchAppData)
  
  mergeObjects(resonanceB, resonanceA)
  
  # Must be after resonance merge, so that links to peaks are properly set
  for shiftA in resonanceA.shifts:
    averageShiftValue(shiftA)
  
  # Assign names will be merged, but if assigned we only want the correct ones 
  if resonanceA.resonanceSet:
    assignNames = []
    for atomSet in resonanceA.resonanceSet.atomSets:
      assignNames.append( atomSet.name )
      
    resonanceA.setAssignNames(assignNames)  
  
  for atomSetMapping, atomSets in mappings:
    updateAtomSetMapping(atomSetMapping, atomSets)
  
  getBoundResonances(resonanceA, recalculate=True)
  updateResonanceAnnotation(resonanceA)
  
  setupAssignmentNotifiers()
  
  return resonanceA