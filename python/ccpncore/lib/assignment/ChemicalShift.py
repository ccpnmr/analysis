"""Module Documentation here

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

import os
from math import exp
from ccpncore.lib.assignment.ChemicalShiftRef import REFDB_SD_MEAN

# TBD DNA/RNA residue probs
#
# Sanity checks:
#   Only on amide
#   Gly CA - ignore CB
#

ROOT_TWO_PI = 2.506628274631
PROTEIN_MOLTYPE = 'protein'
REF_STORE_DICT = {}
CHEM_ATOM_REF_DICT = {}
#
# def makeRandomCoilShiftList(molSystems):
#   """
#   Make a synthetic chemical shift list using random coil values,
#   adjusting protein backbone values for sequence where approprate.
#
#   .. describe:: Input
#
#   MolSystem.MolSystem
#
#   .. describe:: Output
#
#   Nmr.ShiftList
#   """
#
#   from ccpnmr.analysis.core.AssignmentBasic import assignAtomsToRes
#   from ccpnmr.analysis.core.MoleculeBasic import DEFAULT_ISOTOPES, getRandomCoilShift
#
#   project = list(molSystems)[0].root
#   done = set()
#   nmr = project.currentNmrProject
#   shiftList = nmr.newShiftList(isSimulated=True, unit='ppm', name='Random coil')
#   resonanceDict = {}
#
#   for molSystem in molSystems:
#     for chain in molSystem.sortedChains():
#       if chain.molecule in done:
#         continue
#
#       done.add(chain.molecule)
#       residues = chain.sortedResidues()
#       n = len(residues)
#
#       for i, residue in enumerate(residues):
#         context = [None] * 5
#         for k, j in enumerate(range(i-2, i+3)):
#           if 0 <= j < n:
#             context[k] = residues[j]
#
#         atomSets = set()
#         for atom in residue.atoms:
#           atomSet = atom.atomSet
#
#           if atomSet:
#             atomSets.add(atomSet)
#
#         for atomSet in atomSets:
#           atom = atomSet.findFirstAtom()
#           chemAtom = atom.chemAtom
#           value = getRandomCoilShift(chemAtom, context)
#
#           if value is not None:
#             resonanceSet = atomSet.findFirstResonanceSet()
#
#             if resonanceSet:
#               resonances = list(resonanceSet.resonances)
#               index = list(resonanceSet.atomSets).index(atomSet)
#               resonance = resonances[min(index, len(resonances)-1)]
#
#             else:
#               isotope = DEFAULT_ISOTOPES.get(atom.chemAtom.elementSymbol)
#
#               if isotope is None:
#                 continue
#
#               resonance = nmr.newResonance(isotopeCode=isotope)
#               resonanceSet = assignAtomsToRes((atomSet,), resonance)
#
#             resonanceDict[resonance] = value
#
#   for resonance in resonanceDict:
#     value = resonanceDict[resonance]
#     shift = shiftList.newShift(value=value, resonance=resonance)
#
#   return shiftList
#
# def chemShiftBasicMacro(argServer):
#
#   shiftValues = [8.21, 121.4, 53.9, 38.2]
#   elements = ['H','N','C','C']
#   atomTypes = None
#
#   print (shiftValues, 'Asp', elements, atomTypes)
#
# def getAtomProbability(ccpCode, atomName, shiftValue, molType=PROTEIN_MOLTYPE):
#
#   shiftRefs = REFDB_SD_MEAN.get((molType, ccpCode))
#
#   if not shiftRefs:
#     return
#
#   stats = shiftRefs.get(atomName)
#   if not stats:
#     return
#
#   mean, sd, pMissing, bound = stats
#   d = shiftValue-mean
#   e = d/sd
#   p = exp(-0.5*e*e)/(sd*ROOT_TWO_PI)
#
#   return p
#
# def lookupAtomProbability(project, ccpCode, atomName, shiftValue,
#                           molType=PROTEIN_MOLTYPE):
#
#   if molType == PROTEIN_MOLTYPE:
#     if (ccpCode == 'Gly') and (atomName == 'HA'):
#       atomName = 'HA2'
#
#     value = getAtomProbability(ccpCode, atomName, shiftValue)
#
#   if value is None:
#     chemAtomNmrRef = getChemAtomNmrRef(project, atomName, ccpCode, molType)
#
#     if not chemAtomNmrRef:
#       return
#
#     value = getAtomRefLikelihood(chemAtomNmrRef, shiftValue)
#
#   return value


def _getResidueProbability(ppms, ccpCode, elements, shiftNames=None, ppmsBound=None,
                          prior=0.05, molType=PROTEIN_MOLTYPE, cutoff=1e-10):
  """Probability that data match a given ccpCode and molType
  NBNB unassigned (unnamed) resonances make no differences, but named resonances
  that do not fit a residue type WILL GIVE PROBABILITY ZERO!"""

  # Use refExperiment info
  # Use bound resonances info

  shiftRefs = REFDB_SD_MEAN.get((molType, ccpCode))
    
  if not shiftRefs:
    return None
  
  if not shiftNames:
    shiftNames = [None] * len(ppms)
  
  if not ppmsBound:
    ppmsBound = [None] * len(ppms)
    
  
  atomData = [(x, shiftRefs[x]) for x in shiftRefs.keys()]

  data = []
  dataAppend = data.append
  for i, ppm in enumerate(ppms):
    element = elements[i]
    shiftName = shiftNames[i]
    ppmB = ppmsBound[i]
    n = 0
    
    for j, (atomName, stats) in enumerate(atomData):
      if not atomName.startswith(element):
        continue 
      
      if shiftName and not _isAssignmentCompatible(shiftName, atomName):
        continue
      
      mean, sd, pMissing, bound = stats
      d = ppm-mean
      
      if (not shiftName) and (abs(d) > 5*sd):
        continue
      
      e = d/sd   
      p = exp(-0.5*e*e)/(sd*ROOT_TWO_PI)
      
      if bound and (ppmB is not None):
        boundData = shiftRefs.get(bound)
	
        if boundData:
          meanB, sdB, pMissingB, boundB = boundData
          dB = ppmB-meanB
          eB = dB/sdB
          pB = exp(-0.5*eB*eB)/(sdB*ROOT_TWO_PI)
      
          p = (p*pB) ** 0.5
      
      if (not shiftName) and (p < cutoff):
        continue
      
      
      dataAppend((i,j,p))
      n += 1
    
    if n == 0:
      return 0.0  
  
  groups = [set([node,]) for node in data if node[0] == 0]
  
  while data:
    node = data.pop()
    i, j, p = node
    
    for group in groups[:]:
      for node2 in group:
        i2, j2, p2 = node2
       
        if (i == i2) or (j == j2):
          break
      
      else:
        newGroup = group.copy()
        newGroup.add(node)
        groups.append(newGroup)
 
  probTot = 0.0
  for group in groups:
  
    if len(group) != len(ppms):
      continue
    
    found = set([])
    prob = 1.0
    for i,j, p in group:
      found.add(j)  
      prob *= p
    
    #for k, datum in enumerate(atomData):
    #  atomName, stats = datum
    #  pMissing = stats[2]
    #  
    #  if k in found:
    #    prob *= 1-pMissing
    #  else:
    #    prob *= pMissing
    
    if found:
      probTot += prob
      
  return probTot
#
# def getShiftsChainProbabilities(shifts, chain):
#
#   probDict = {}
#   getProb = getShiftsResidueProbability
#   priors = getChainResTypesPriors(chain)
#
#   ccpCodes = set(getChainResidueCodes(chain))
#
#   total = 0.0
#   for ccpCode, molType in ccpCodes:
#     prob = getProb(shifts, ccpCode, priors[ccpCode], molType)
#     probDict[ccpCode] = prob
#
#     if prob is not None:
#       total += prob
#
#   if not total:
#     total = 1.0
#
#   for ccpCode, molType in ccpCodes:
#     if probDict[ccpCode] is None:
#       probDict[ccpCode] = 1.0 / len(chain.residues)
#     else:
#       probDict[ccpCode] /= total
#
#   # Have to do this until have stats at var level
#   if 'Cyss' in probDict:
#     if 'Cys' in probDict:
#       if probDict['Cyss'] > probDict['Cys']:
#         probDict['Cys'] = probDict['Cyss']
#
#     else:
#       probDict['Cys'] = probDict['Cyss']
#
#     del probDict['Cyss']
#
#   return probDict
#
# def getSpinSystemChainProbabilities(spinSystem, chain, shiftList):
#
#   probDict = {}
#   getProb = getSpinSystemResidueProbability
#   priors = getChainResTypesPriors(chain)
#
#   ccpCodes = set(getChainResidueCodes(chain))
#
#   for ccpCode, molType in ccpCodes:
#     probDict[ccpCode] = getProb(spinSystem, shiftList, ccpCode,
#                                 priors[ccpCode], molType)
#
#   return probDict
#
# def getChainResidueCodes(chain):
#
#   ccpCodes = []
#   for residue in chain.residues:
#     ccpCode = residue.ccpCode
#     if (ccpCode == 'Cys') and (residue.descriptor == 'link:SG'):
#       ccpCode = 'Cyss'
#
#     ccpCodes.append((ccpCode, residue.molType))
#
#   return ccpCodes
#
# def getChainResTypesPriors(chain):
#
#   priors = {}
#
#   ccpCodes = [x[0] for x in getChainResidueCodes(chain)]
#   n = float(len(ccpCodes))
#
#   for ccpCode in set(ccpCodes):
#     priors[ccpCode] = ccpCodes.count(ccpCode)/n
#
#   return priors
#
# def getShiftsResidueProbability(shifts, ccpCode, prior=0.05, molType=PROTEIN_MOLTYPE):
#
#   ppms = []
#   boundPpms = []
#   elements = []
#   atomTypes = []
#   ppmsAppend = ppms.append
#   boundPpmsAppend = boundPpms.append
#   elementsAppend = elements.append
#   atomTypesAppend = atomTypes.append
#
#   betaBranch = set(['Val','Ile','Thr'])
#
#   for shift in shifts:
#     resonance = shift.resonance
#     isotope = resonance.isotope
#
#     if isotope:
#       element = isotope.chemElement.symbol
#
#       if element == 'H':
#         bound = resonance.findFirstCovalentlyBound()
#       else:
#         bound = resonance.findFirstCovalentlyBound(isotopeCode='1H')
#
#       if bound:
#         shift2 = bound.findFirstShift(parentList=shift.parentList)
# 	if shift2:
# 	  ppm2 = shift2.value
# 	else:
# 	  ppm2 = None
#       else:
#         ppm2 = None
#
#
#       assignNames = resonance.assignNames or set([])
#
#       if (not assignNames) and resonance.peakDimContribs:
# 	refExpDimRefs = set([])
#
# 	for contrib in resonance.peakDimContribs:
# 	  refExpDimRef = contrib.peakDim.dataDimRef.expDimRef.refExpDimRef
#   	  if refExpDimRef:
# 	    refExpDimRefs.add(refExpDimRef)
#
# 	for refExpDimRef in refExpDimRefs:
#   	  expMeasurement = refExpDimRef.expMeasurement
#   	  atomSites = expMeasurement.atomSites
#
#   	  for atomSite in atomSites:
#   	    name = atomSite.name
#
#   	    if name == 'CO':
#   	      name == 'C'
#
#   	    elif name in ('H','N',): # Not specific sites
#   	      continue
#
#   	    elif (name == 'HA') and (ccpCode == 'Gly'):
#   	      name = 'HA2'
#
#   	    elif (name == 'HB') and (ccpCode not in betaBranch):
#   	      name = 'HB2'
#
#   	    elif name in ('C','Cali'):
#   	      for expTransfer in atomSite.expTransfers:
#   	        if expTransfer.transferType in ('onebond','CP'):
#   	          atomSites2 = list(expTransfer.atomSites)
#   	          atomSites2.remove(atomSite)
#   	          name2 = atomSites2[0].name
#
#   	          if (name2 == 'CA') and (ccpCode != 'Gly'):
#   	            name = 'CB'
#   	            break
#   	          elif name2 == 'CO':
#   	            name = 'CA'
#   	            break
#
#   	      else:
#   	        continue
#
#             assignNames.add(name)
#
#       boundPpmsAppend(ppm2)
#       ppmsAppend(shift.value)
#       elementsAppend(element)
#       atomTypesAppend(assignNames)
#
#   prob = getResidueProbability(ppms, ccpCode, elements, atomTypes,
#                                boundPpms, prior, molType)
#
#   return prob

def getSpinSystemResidueProbability(spinSystem, shiftList, ccpCode,
                                    prior=0.05, molType=PROTEIN_MOLTYPE):
  """Get probability that Spin system matches molType and ccpCode
  NB to avoid rejection all atom names must be either unassigned (default) or correct!"""

  ppms = []
  elements = []
  atomNames = []
  ppmsAppend = ppms.append
  elementsAppend = elements.append
  atomNamesAppend = atomNames.append

  for resonance in spinSystem.resonances:

    isotope = resonance.isotope
    if isotope:

      shift = resonance.findFirstShift(parentList=shiftList)
      if shift:
        ppmsAppend(shift.value)
        elementsAppend(isotope.chemElement.symbol)
        # NB, use implName to avoid default (unassigned) names.
        atomNamesAppend(resonance.implName)


  prob = _getResidueProbability(ppms, ccpCode, elements,
                               atomNames, prior=prior, molType=molType)

  return prob

def _isAssignmentCompatible(assignName:str, atomName:str) -> bool:
  """Is assignName compatible with assignment to atomName?
  NB allows for non-standard assignment strings
  NB does NOT do case conversions - upcse both parameters if you wish case-insensitive behaviour.
  NB does NOT accept 'x' a,d 'y' as wildcards, only 'X' and 'Y'"""

  # convert pseudoAtom names to proton wildcard names
  if assignName[0] in 'QM':
    assignName = 'H' + assignName[1:] + '%'

  if assignName == atomName:
    return True

  lenPrefix = len(os.path.commonprefix((assignName, atomName)))
  lenAtomName = len(atomName)

  if lenAtomName == lenPrefix:
    if assignName[lenPrefix:] in ('*', '%'):
      # E.g. assign HG* v. HG
      return True

  elif lenAtomName - lenPrefix == 1:
    if atomName[-1] in '123%*':
      if assignName[lenPrefix:] in ('', 'X', 'Y', '*', '%'):
        # assigned wildcard v. wildcard or single digit, e.g. HGX v. HG* or HG1
        return True

  elif lenAtomName - lenPrefix == 2:
    if atomName[-2] in '123' and atomName[-1] in '123*%':
      if assignName[lenPrefix:] in ('', 'X', 'Y', '*', '%', 'X%', 'Y%', 'X*', 'Y*'):
        # E.g. HG, HG%, or HGY* v. HG21 or HG1*
        return True

  #
  return False


#
# def getChemAtomNmrRef(project, atomName, ccpCode, molType=PROTEIN_MOLTYPE,
#                       sourceName='RefDB'):
#
#   atomKey = molType + ccpCode + atomName
#   chemAtomNmrRef  = CHEM_ATOM_REF_DICT.get(atomKey)
#
#
#   if not chemAtomNmrRef:
#     key = molType + ccpCode
#     getRefStore = project.findFirstNmrReferenceStore
#     nmrRefStore = REF_STORE_DICT.get(key, getRefStore(molType=molType,ccpCode=ccpCode))
#
#     if nmrRefStore:
#       REF_STORE_DICT[key] = nmrRefStore
#       chemCompNmrRef = nmrRefStore.findFirstChemCompNmrRef(sourceName=sourceName)
#       if chemCompNmrRef:
#         chemCompVarNmrRef = chemCompNmrRef.findFirstChemCompVarNmrRef(linking='any',descriptor='any')
#
#         if chemCompVarNmrRef:
#           for chemAtomNmrRef1 in chemCompVarNmrRef.chemAtomNmrRefs:
#             if atomName == chemAtomNmrRef1.name:
#               chemAtomNmrRef = chemAtomNmrRef1
#               CHEM_ATOM_REF_DICT[atomKey] = chemAtomNmrRef
#               break
#         else:
#           return
#       else:
#         return
#     else:
#       return
#
#   if not chemAtomNmrRef:
#     atomName2 = atomName[:-1]
#     for chemAtomNmrRef1 in chemCompVarNmrRef.chemAtomNmrRefs:
#       if atomName2 == chemAtomNmrRef1.name:
#         chemAtomNmrRef = chemAtomNmrRef1
#         CHEM_ATOM_REF_DICT[atomKey] = chemAtomNmrRef
#         break
#
#   return chemAtomNmrRef
#
# def getAtomRefLikelihood(chemAtomNmrRef, shiftValue):
#
#   distribution  = chemAtomNmrRef.distribution
#   refPoint      = chemAtomNmrRef.refPoint
#   refValue      = chemAtomNmrRef.refValue
#   valuePerPoint = chemAtomNmrRef.valuePerPoint
#   N = len(distribution)
#   f = 1/3.0
#
#   refDelta = shiftValue-refValue
#   point    = int(refPoint + (refDelta/valuePerPoint))
#
#   if point < 0:
#     return 0.0
#
#   elif point >= N:
#     return 0.0
#
#   else:
#     #return distribution[int(point)]
#     return (distribution[max(point-1,0)] + distribution[point] + distribution[min(point+1,N-1)]) * f
#
#
# if __name__ == '__main__':
#
#   shiftValues =  [8.868, 112.28, 46.065, 3.982, 4.408]
#
#   elements = ['H','N','C','H','H']
#   #atomTypes = [('CB',), ('CA',), ('N',), ('H',)]
#   atomTypes = [ 'H', 'N', 'CA', None, None]
#   vals = {}
#   ccpCodes = ['Ala','Cys','Asp','Glu',
# 	      'Phe','Gly','His','Ile',
# 	      'Lys','Leu','Met','Asn',
# 	      'Pro','Gln','Arg','Ser',
# 	      'Thr','Val','Trp','Tyr',]
#
#   for ccpCode in ccpCodes:
#     vals[ccpCode] = _getResidueProbability(shiftValues, ccpCode, elements, atomTypes, prior=0.0578512396694)
#                                           # ppmsBound=[112.28, 8.868, None, None, None])
#
#
#   tot = sum(vals.values())
#   for ccpCode in ccpCodes:
#     v = vals[ccpCode] / tot
#     print (ccpCode, '%.3f' % v)
#
#
# 

