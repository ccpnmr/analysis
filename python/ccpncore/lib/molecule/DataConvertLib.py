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
"""Utility functions for data conversion"""

# NBNB TBD Rewrite/replace COMPLETELY based on residueType/sequenceCode



#
# import copy
# from ccpncore.lib.chemComp.ChemCompOverview import chemCompOverview
# from ccpncore.lib.chemComp import Io as chemCompIo
#from ccp.general.Io import getChemComp, getStdChemComps

# # priority order of naming systems
# namingSystemPriorityOrder = ['PDB','IUPAC','PDB_REMED','BMRB','XPLOR',
#                              'CYANA2.1','DIANA', 'GROMOS','MSD','SYBYL',
#                              'UCSF','AQUA','DISGEO','DISMAN', 'MOLMOL','MSI']

# # molType priority order
# molTypeOrder = ('protein', 'DNA', 'RNA', 'carbohydrate', 'other')
    
###################################################################
#
### Input data conversion
#
####################################################################
#
#
# def getBestNamingSystem(residues, atomNamesList):
#
#   """
#   Descrn: Determine best naming system from residues and matching atom names
#   Inputs:
#     residues: list of residues
#     atomNamesList: list of list of atom names, matching residues 1:1
#
#   Output: name of best namingSystem
#   """
#
#   # Make dict of chemComp:merged atom name sets
#   atomsDict = {}
#   for ii, residue in enumerate(residues):
#     if residue:
#       # NB residue could be None in some contexts
#       names = atomNamesList[ii]
#       chemComp = residue.molResidue.chemComp
#       if chemComp in atomsDict:
#         atomsDict[chemComp].update(names)
#       else:
#         atomsDict[chemComp]= set(names)
#
#   # Make parallel lists of chemcomps and their atomnames
#   chemComps,atomNames = zip(*atomsDict.items())
#
#   # get naming system
#   return getBestNamingSystemCC(chemComps, atomNames)
#
#
# def getBestNamingSystemCC(chemComps, atomNamesList, prefNamingSystemName=None):
#
#   """
#   Descrn: Determine best naming system from ChemComps and matching atom names
#           Does not check for duplicate ChemComps.
#   Inputs: chemComps: list of ChemComps
#           atomNamesList: list of collections of atom names, matching chemComps 1:1
#
#   Output: name of best namingSystem
#   """
#
#   # Weights for a hit in sysname:
#   fullHit = 10
#   # Weights for a hit in altSysNames:
#   altHit = 5
#
#   # Calculate namingSystem score from atomName hits
#   scoreDict = {}
#   for ii,chemComp in enumerate(chemComps):
#     atomNames = atomNamesList[ii]
#
#     for namingSystem in chemComp.namingSystems:
#       ns = namingSystem.name
#       score = scoreDict.get(ns, 0)
#
#       for atomName in atomNames:
#
#         refNamingSystem = namingSystem
#         done = False
#
#         while refNamingSystem:
#           # First choice plain mapping
#           if refNamingSystem.findFirstAtomSysName(sysName=atomName):
#             score += fullHit
#             break
#
#           # Otherwise try alternative sys names
#           else:
#             for atomSysName0 in refNamingSystem.atomSysNames:
#               if atomName in atomSysName0.altSysNames:
#                 score += altHit
#                 done = True
#                 break
#
#             if done:
#               break
#
#             else:
#               #  no luck, try again with reference naming system
#               refNamingSystem = refNamingSystem.atomReference
#
#       scoreDict[ns] = score
#
#   bestSc = -1
#   bestNs = None
#   # read naming systems in priority order (in case of ties)
#   sortOrder = list(namingSystemPriorityOrder)
#   if prefNamingSystemName:
#     if prefNamingSystemName in sortOrder:
#       sortOrder.remove(prefNamingSystemName)
#     sortOrder.insert(0,prefNamingSystemName)
#   for ns in sortOrder:
#     if ns in scoreDict:
#       score = scoreDict.pop(ns)
#       if score > bestSc:
#         bestSc = score
#         bestNs = ns
#
#   # read remaining systems, if any (in alphabetical order, for reproducability)
#   for ns in sorted(scoreDict):
#     score = scoreDict.pop(ns)
#     if score > bestSc:
#       bestSc = score
#       bestNs = ns
#
#   #
#   return bestNs
#
#
# def getBestChemComp(project, resName, atomNames, molType=None, download=True):
#   """Find the best matching ChemComp for the resName,  using atomNames for determining molType
#   .. describe:: Input
#
#   Implementation.Project, Word (imported residue name),
#              List of Words (imported atom names)
#
#   .. describe:: Output
#
#   Word (Molecule.MolResidue.ccpCodes)
#   """
#
#   # TODO NBNB Refactor. Now non-proteins also have names of form 'Xyz'
#
#   # chemComp = None
#
#   # get molType
#   if not molType:
#     molType  = getBestMolType(atomNames)
#
#   if molType in ('DNA','RNA','DNA/RNA'):
#     if len(resName) == 1:
#       if 'PD' in atomNames:
#         resName += '11'
#
#   # reset character case depending on molType
#   if molType == 'protein':
#     resName = resName[0] + resName[1:].lower()
#
#   chemComp = project.findFirstChemComp(ccpCode=resName.upper(), molType=molType) or \
#              project.findFirstChemComp(ccpCode=resName, molType=molType)
#
#   if chemComp:
#     return chemComp
#
#   ccpCodeDict = {}
#   chemComps = chemCompIo.getStdChemComps(project, molTypes=[molType,])
#
#   for chemComp0 in chemComps:
#     ccpCodeDict[chemComp0.ccpCode] = chemComp0
#     ccpCodeDict[chemComp0.code3Letter] = chemComp0
#
#   # Get ChemComp from std dict
#   chemComp = ccpCodeDict.get(resName)
#
#   # Get ChemComp from std dict using alternative naming systems
#   if chemComp is None:
#     for chemCompTest in chemComps:
#       for namingSystem in chemCompTest.namingSystems:
#         for sysName in namingSystem.chemCompSysNames:
#           if sysName.sysName == resName:
#             #ccpCodeDict[resName] = chemCompTest
#             chemComp = chemCompTest
#             break
#
#         else:
#           continue
#         break
#
#       else:
#         continue
#       break
#
#     # get ChemComp outside std ChemComps,
#     if not chemComp:
#       chemComp = chemCompIo.getChemComp(project, molType, resName, download=download)
#
#     # get ChemComp outside std ChemComp - try with type Other
#     if not chemComp and molType != 'other':
#       chemComp = chemCompIo.getChemComp(project, 'other', resName, download=download)
#       if not chemComp:
#         resName = resName[0] + resName[1:].lower()
#         chemComp = chemCompIo.getChemComp(project, 'other', resName)
#
#   return chemComp
#
#
# def getBestMolType(atomNames, ccpCodes=None):
#   """Determine the best molecule type (protein, DNA, RNA, carbohydrate or
#              nonpolymer) given the input atom names and residue ccpCodes
#
#   .. describe:: Input
#
#   List of Words (imported atom names),
#   List of Words (Molecule.MolResidue.ccpCodes)
#
#   .. describe:: Output
#
#   Word (Molecule.Molecule.molType)
#   """
#
#   molType = 'other'
#
#   if ("C3'" in atomNames) and ("C5'" in atomNames) and ("C2" in atomNames):
#     molType = 'DNA'
#     if "O2'" in atomNames:
#       molType = 'RNA'
#
#   elif ("C3*" in atomNames) and ("C5*" in atomNames) and ("C2" in atomNames):
#     # PDB Naming system different from others
#     molType = 'DNA'
#     if "O2*" in atomNames:
#       molType = 'RNA'
#
#   elif 'CA' in atomNames:
#     molType = 'protein'
#
#   elif ("C1" in atomNames) and ("C2" in atomNames) and ("C3" in atomNames) and ("C4" in atomNames) \
#        and ( ("O2" in atomNames) or ("O3" in atomNames) or ("O4" in atomNames)):
#     molType = 'carbohydrate'
#
#   return molType
  
#
# def findMatchingMolSystemAtom(atomName, residue, namingSystem, excludeAtoms,
#                               fixAtomNames=False):
#   """
#   Find the best matching CCPN atom name in a residue for the input
#   atom name in the input naming system.
#   Will try other naming systems if the input one doesn't work
#
#   .. describe:: Input
#
#   Word (imported atom name), MolSystem.Residue,
#   Word (ChemComp.NamingSystem.name), List of MolSystem.Atoms
#
#   .. describe:: Output
#
#   Word (MolSystem.Atom.name)
#   """
#   #nucleic = ('DNA','RNA','DNA/RNA')
#   #weirdos = {'O1P':'OP1','O2P':'OP2','C5A':'C7'}
#   #if weirdos.get(atomName) and residue.molResidue.molType in nulciec:
#   #  atomName = weirdos[atomName]
#
#   # TODO NBNB refaotor signature, and move to lib.ccp.molecule.Molecule.Residue
#
#   # If desired change (e.g.) '2HB' to 'HB2'
#   if fixAtomNames and atomName[0] in '123':
#     # move leading indices to end of name
#     atomName = atomName[1:] + atomName[0]
#
#   # get list of atomSysNames for preferred NamingSystem and its reference systems
#   # First by sysName, then by altSysNames
#   # atom = None
#   chemComp = residue.chemCompVar.chemComp
#   namingSystem0 = chemComp.findFirstNamingSystem(name=namingSystem)
#   atomSysNames = []
#   atomSysNamesAlt = []
#
#   usedNamingSystems = set()
#
#   if namingSystem0:
#     namingSystemR = namingSystem0
#
#     while namingSystemR:
#
#       usedNamingSystems.add(namingSystemR)
#
#       # First choice plain mapping
#       for atomSysName in namingSystemR.findAllAtomSysNames(sysName=atomName):
#         atomSysNames.append(atomSysName)
#
#       # Otherwise try alternative sys names
#       for atomSysName0 in namingSystemR.atomSysNames:
#         if atomName in atomSysName0.altSysNames:
#           atomSysNamesAlt.append(atomSysName0)
#           #break
#
#       namingSystemR = namingSystemR.atomReference
#
#   atomSysNames.extend(atomSysNamesAlt)
#
#   moreNamingSystems = [x for x in priorityOrderedNamingSystems(chemComp)
#                        if x not in usedNamingSystems]
#
#   # Next chance any naming system plain mapping
#   for namingSystem0 in moreNamingSystems:
#     for atomSysName in namingSystem0.findAllAtomSysNames(sysName=atomName):
#       atomSysNames.append(atomSysName)
#
#   # Final chance any naming system alt name
#   for namingSystem0 in moreNamingSystems:
#     for atomSysName in namingSystem0.atomSysNames:
#       if atomName in atomSysName.altSysNames:
#         atomSysNames.append(atomSysName)
#
#   # Find the molSystem atom
#   for atomSysName in atomSysNames:
#     atom = residue.findFirstAtom(name=atomSysName.atomName)
#     if atom and atom not in excludeAtoms:
#       return atom
#   #
#   return None

#
# def priorityOrderedNamingSystems(chemComp, prefNamingSystemName=None):
#   """
#   Give naming systems for chemComp in reproducible priority order
#
#   .. describe:: Input
#
#   ChemComp (ChemComp being named)
#
#   .. describe:: Output
#
#   List of (ChemComp.NamingSystem)
#   """
#
#   # NBNB TODO move to lib.ccp.molecule.ChemComp.ChemComp
#
#   result = []
#
#   # set up name:NamingSystem dict
#   dd = {}
#   for ns in chemComp.namingSystems:
#     dd[ns.name] = ns
#
#   # Put naming systems on list in priority order
#   sortOrder = list(namingSystemPriorityOrder)
#   if prefNamingSystemName:
#     if prefNamingSystemName in sortOrder:
#       sortOrder.remove(prefNamingSystemName)
#     sortOrder.insert(0,prefNamingSystemName)
#   for name in sortOrder:
#     if name in dd:
#       result.append(dd.pop(name))
#
#   # Put remaining NamingSystems on in alphabetical order
#   for name in sorted(dd):
#     result.append(dd[name])
#
#   #
#   return result

#
# def getStdResNameMap(chemComps=None):
#   """
#   """
#
#   result = {}
#
#   # Get stdChemComps first - avoids certain name clash error loading ChemComps
#   chemComps = (   [x for x in chemComps if x.className == 'StdChemComp']
#                 + [x for x in chemComps if x.className != 'StdChemComp'])
#
#   for molType in molTypeOrder:
#
#     tmpResult = {}
#
#     # add data from entered ChemComps
#     for chemComp in chemComps:
#       if molType == chemComp.molType:
#
#         ccpCode = chemComp.ccpCode
#
#         # Add ccpCode and main names
#         # NBNB TBD remove the tag,upper() after checking
#         tags = {ccpCode, chemComp.code3Letter}
#         tag = chemComp.code1Letter
#         if tag and chemComp.className == 'StdChemComp':
#           tags.add(tag)
#
#         # also sysNames
#         for namingSystem in chemComp.namingSystems:
#           for sysName in namingSystem.chemCompSysNames:
#             tags.add(sysName.sysName)
#
#         if None in tags:
#           tags.remove(None)
#         if '' in tags:
#           tags.remove('')
#
#         # TEMP HACK:
#         tags = {str(chemComp.code3Letter)}
#
#         # put in mapping
#         ccId = (molType, ccpCode)
#         for tag in tags:
#
#           aSet = tmpResult.get(tag)
#           if aSet is None:
#             tmpResult[tag] = {ccId}
#           else:
#             aSet.add(ccId)
#
#     # Add data for all chemComps from overview
#     data = copy.deepcopy(chemCompOverview[molType])
#
#     for ccpCode,tt in sorted(data.items()):
#
#       # get tags to add
#       ccId = (molType, ccpCode)
#       tags = {ccpCode, tt[1], tt[0]}
#
#       if None in tags:
#         tags.remove(None)
#       if '' in tags:
#         tags.remove('')
#
#         # TEMP HACK:
#       tags = {str(tt[1])}
#
#       for tag in tags:
#         aSet = tmpResult.get(tag)
#         if aSet is None:
#           tmpResult[tag] = {ccId}
#         else:
#           aSet.add(ccId)
#
#     # merge tempResult into global result
#     for tag, val in tmpResult.items():
#       oldval = result.get(tag)
#       if oldval is None:
#         result[tag] = val
#       else:
#         result[tag] = oldval | val
#   #
#   return result
#
#
#
# def getOldStdResNameMap(chemComps=None):
#   """ Generate map of possible string resNames to tuple of (molType, ccpCode)
#   tuples.
#   All ccpCodes, code1Letter, code3Letter are used for ChemCompOverview list;
#   for passed-in ChemComps also chemCompSysNames are used. 'other' chemcomp
#   names are ignored if clashing, unless the ChemComp is passed in.
#   NEW code
#
#   NBNB TODO change so that D-Ala is preferred over Dal (etc.)
#
#   Input: List of ChemComps
#
#   Output:
#    Dictionary {Word:(Word,Word)}
#   """
#
#   result = {}
#
#   for molType in molTypeOrder:
#
#     tmpResult = {}
#
#     data = copy.deepcopy(chemCompOverview[molType])
#
#     # add data from entered ChemComps
#     ccpCodesCC = set()
#
#     # Get stdChemComps first - avoids certain name clash error loading ChemComps
#     chemComps = (   [x for x in chemComps if x.className == 'StdChemComp']
#                   + [x for x in chemComps if x.className != 'StdChemComp'])
#     for chemComp in chemComps:
#       if molType == chemComp.molType:
#
#         ccpCode = chemComp.ccpCode
#         ccpCodesCC.add(ccpCode)
#
#         # Add ccpCode and main names
#         tags = {ccpCode, ccpCode.upper(), chemComp.code3Letter}
#         tag = chemComp.code1Letter
#         if tag and chemComp.className == 'StdChemComp':
#           tags.add(tag)
#         if None in tags:
#           tags.remove(None)
#
#         # also sysNames
#         for namingSystem in chemComp.namingSystems:
#           for sysName in namingSystem.chemCompSysNames:
#             tags.add(sysName.sysName)
#
#         # put in mapping
#         ccId = (molType, ccpCode)
#         for tag in tags:
#           prevId = tmpResult.get(tag)
#           if prevId is None:
#             tmpResult[tag] = ccId
#           elif prevId != ccId:
#             # Clash. resolve in favour of shortest ccpCode, if any
#             # Heuristic- facvours standard bases over phosphorylation states
#             if len(prevId[1]) == 1 and len(ccId[1]) > 1:
#               continue
#             elif len(prevId[1]) > 1 and len(ccId[1]) == 1:
#               tmpResult[tag] = ccId
#             else:
#               raise Exception(
#                "Residue name conflict for %s between ChemComps %s and %s"
#                % (tag, ccId, prevId))
#
#     # Add data for all chemComps from overview
#     for ccpCode,tt in sorted(data.items()):
#
#       if ccpCode in ccpCodesCC:
#         # We have this one already, from chemComps. Skip
#         continue
#
#       if ccpCode == ccpCode.upper():
#         truCode = ccpCode[0].upper() + ccpCode[1:].lower()
#
#         if ccpCode != truCode and truCode in data:
#           # We have this one in correct casing elsewhere. Skip it.
#           continue
#
#       # get tags to add
#       ccId = (molType, ccpCode)
#       tags = {ccpCode}
#       cifCode = tt[1]
#       if cifCode:
#         truCif = cifCode[0].upper() + cifCode[1:].lower()
#         if cifCode not in data and truCif not in data:
#           # Skip cifCodes dealt with elsewhere
#           tags.add(cifCode)
#       if ccpCode.upper() != cifCode:
#         tags.add(ccpCode.upper())
#       code1L = tt[0]
#       if code1L and code1L not in tmpResult:
#         tags.add(code1L)
#
#       # put values in result
#       for tag in tags:
#         prevId = tmpResult.get(tag)
#         if prevId is None:
#           tmpResult[tag] = ccId
#         elif prevId != ccId:
#           raise Exception(
#            "Residue name conflict for %s between Entries %s and %s"
#            % (tag, ccId, prevId), tags)
#
#     # merge tempResult into global result
#     for tag, val in tmpResult.items():
#       oldval = result.get(tag)
#       if oldval is None:
#         result[tag] = (val,)
#       else:
#         # clash between types
#         if molType != 'other':
#           # Ignore clashes with 'other. NB 'other' must be last in loop.
#           result[tag] = oldval + (val,)
#   #
#   return result
#
#
# def getNewStdResNameMap(chemComps=None):
#   """
#   """
#
#   result = {}
#   excluded = []
#   pending = []
#
#   # # Get stdChemComps first - avoids certain name clash error loading ChemComps
#   # chemComps = (   [x for x in chemComps if x.className == 'StdChemComp']
#   #               + [x for x in chemComps if x.className != 'StdChemComp'])
#
#   nFound = 0
#   for molType in molTypeOrder:
#
#     # Add data for all chemComps from overview
#     data = copy.deepcopy(chemCompOverview[molType])
#
#     for ccpCode,tt in sorted(data.items()):
#
#       # get tags to add
#       ccId = (molType, ccpCode)#
#       cifCode = tt[1]
#       if not cifCode:
#         excluded.append(['NONE     ', molType, ccpCode, cifCode, tt[0], tt[2]])
#       elif cifCode == ccpCode:
#         if cifCode in result:
#           excluded.append(['DUPL-CIF1',  molType, ccpCode, result[cifCode][0], tt[0], tt[2]])
#         else:
#           result[cifCode] = ccId
#       else:
#         pending.append([molType, ccpCode, cifCode, tt[0], tt[2]])
#     #
#     nn = len(result)
#     print ("Found %s %s ccpCode == cifCode" % (nn-nFound, molType))
#     nFound = nn
#
#   pending2 = []
#   counter = {}
#   for (molType, ccpCode, cifCode, code1Letter, info) in pending:
#     if ccpCode.upper() == cifCode:
#       if cifCode in result:
#         excluded.append(['DUPL-CIF2',  molType, ccpCode, result[cifCode][0], code1Letter, info])
#       else:
#         result[cifCode] = (molType, ccpCode)
#         ii = counter.get(molType, 0)
#         counter[molType] = ii +1
#         if ccpCode in result:
#           excluded.append(['DUPL-CCP1',  molType, ccpCode, cifCode, code1Letter, info])
#         else:
#           result[ccpCode] = (molType, ccpCode)
#     else:
#       if cifCode in result:
#         excluded.append(['DUPL-CIF3',  molType, ccpCode, cifCode, code1Letter, info])
#       else:
#         pending2.append([molType, ccpCode, cifCode, code1Letter, info])
#   pending = pending2
#
#   for typ,count in sorted(counter.items()):
#     print("Found %s %s ccpUpper = cifCode" % (count, typ))
#
#   #
#   return result, excluded, pending


# # def getNew2StdResNameMap(project):
# def fetchStdResNameMap(project, reset:bool=False):
#   """ fetch dict of {residueName:(molType,ccpCode)},
#   using cached value if preeent and not resdet.
#   """
#
#   logger = project._logger
#
#   if hasattr(project, '_residueName2chemCompId') and not reset:
#     return project._residueName2chemCompId
#   else:
#     result = project._residueName2chemCompId = {}
#
#   # Special cases:
#   result['6MA'] = ('DNA', '6ma')
#
#   for molType in molTypeOrder:
#     for chemComp in project.findAllChemComps(molType=molType, className='StdChemComp'):
#       cifCode = chemComp.code3Letter
#       ccpCode = chemComp.ccpCode
#       val = (chemComp.molType, ccpCode)
#       if cifCode and cifCode != ccpCode:
#         # Make sure std ChemComps are given preference.
#         # NB cifCode == ccpCode is handled correctly in next loop.
#         # NB ccpCode entry is handled below.
#         vv = result.get(cifCode)
#         if vv is None:
#           result[cifCode] = val
#         else:
#           logger.debug("WARNING cifCode % clash in stdChemComps %s - %s" % (cifCode, val, vv))
#
#   nFound = 0
#   for molType in molTypeOrder:
#
#     # Add data for all chemComps from overview
#     for ccpCode,tt in sorted(chemCompOverview[molType].items()):
#       val = (molType, ccpCode)
#       cifCode = tt[1]
#
#       if cifCode == ccpCode:
#         # First round: only ccpCode == cifCode
#
#         vv = result.get(cifCode)
#         if vv is None:
#           result[cifCode] = val
#         else:
#           if molType == 'other':
#             pass
#             logger.debug ("INFO1 cifCode clash: %s v. %s : %s - 'other' chemComp discarded"
#                    % (vv, val, tt))
#           else:
#             logger.debug ("WARNING duplicate cifCode  %s for %s and %s : %s" %
#                    ( cifCode, vv, val, tt))
#
#   for molType in molTypeOrder:
#     for ccpCode,tt in sorted(chemCompOverview[molType].items()):
#       val = (molType, ccpCode)
#       cifCode = tt[1]
#       if (cifCode != ccpCode and cifCode == ccpCode.upper()):
#         # Second round: only ccpCode.upper() == cifCode
#
#         vv = result.get(cifCode)
#         if vv is None:
#           result[cifCode] = val
#           vv = result.get(ccpCode)
#           if vv is None:
#             result[ccpCode] = val
#           else:
#             logger.debug("WARNING ccpCode already in map %s v. %s  %s" %
#                   (vv, val, tt))
#         else:
#           if molType == 'other':
#             pass
#             logger.debug ("INFO2 cifCode clash: %s v. %s - %s 'other' chemComp discarded"
#                    % (vv, val, tt))
#           else:
#             if molType == vv[0]:
#               # OK, different casing (or std ChemCOmp), same molType. Use previous entry
#               if ccpCode in result:
#                 logger.debug("WARNING ccpCode already in map %s v. %s  %s" %
#                       (vv, val, tt))
#               else:
#                 result[ccpCode] = vv
#             else:
#               # cifCodes clash for non-other, different molTypes. PROBLEM
#               logger.debug("WARNING molType clash for %s v. %s - %s"
#                     % (vv, val, tt))
#
#   for molType in molTypeOrder:
#     for ccpCode,tt in sorted(chemCompOverview[molType].items()):
#       val = (molType, ccpCode)
#       cifCode = tt[1]
#       if cifCode != ccpCode.upper():
#         # Last round: cifCode and ccpCode differ in more than casing
#
#         vv = result.get(cifCode)
#
#         if not cifCode:
#           pass
#           logger.debug("INFO3 Entry with no cifCode discarded %s : %s" % val, tt)
#
#         elif vv is None:
#           logger.debug("WARNING unused cifCode: ccpCode: %s - %s" % (val, tt))
#
#         else:
#           if len(ccpCode) == 5 and ccpCode.startswith('D-') and len(cifCode) == 3:
#             result[ccpCode] = vv
#             logger.debug ("INFO4 added 'D-' synonym for %s : %s - %s" % (vv, val, tt))
#
#           elif molType == 'other':
#             pass
#             logger.debug ("INFO5 cifCode clash: %s v. %s - %s 'other' chemComp discarded"
#                   % (vv, val, tt))
#
#           elif ccpCode == vv[1] and cifCode == 'D' + ccpCode and molType == 'DNA':
#             # Std DNA residue. OK
#             pass
#             logger.debug("INFO6 Added Std DNA residue %s - %s" % (val, tt))
#
#           else:
#             # ss = "%s,%s" % (vv[0] == val[0], vv[-1] == val[-1])
#             # print ("CIF7 %s %s %s %s %s" % (ss, vv[0], vv[1], val, vv[-1]))
#             logger.debug ("WARNING clashing cifCode unused ccpCode%s v. %s  - %s" % (vv, val, tt))
#
#
#   for chemComp in project.sortedChemComps():
#
#     cifCode = chemComp.code3Letter
#     ccpCode = chemComp.ccpCode
#     ccId = (chemComp.molType, ccpCode)
#
#     tags = {ccpCode}
#
#     # sysNames
#     for namingSystem in chemComp.namingSystems:
#       for sysName in namingSystem.chemCompSysNames:
#         tags.add(sysName.sysName)
#
#     # info output for standard CHemCOmps
#     if chemComp.className == 'StdChemComp':
#       logger.debug ("STD ChemComp %s %s %s %s" % (ccId, chemComp.code1Letter, cifCode, tags))
#
#     # put in mapping
#     val = result.get(cifCode)
#
#     if val is None:
#       # New ChemComp - add it in
#
#       if cifCode is not None:
#         logger.debug ("INFO7 Adding new cifCode %s from ChemComp %s"
#                % (cifCode, ccId))
#         result[cifCode] = val = ccId
#
#     elif ccId[0] != val[0]:
#       logger.debug("WARNING cifCode %s molType clash chemComp %s v. map %s" % (cifCode, ccId, val))
#
#     else:
#       # We have the cifCode in the mapping already
#       for tag in tags:
#         prevId = result.get(tag)
#
#         if prevId is None:
#
#           if len(tag) == 1:
#             logger.debug ("INFO8 Rejecting one-letter synonym %s from ChemComp %s:%s"
#                    % (tag, cifCode, val))
#
#           elif (ccId == val or
#                 (val[0] == ccId[0] and ccpCode.startswith('D-') and len(ccpCode) == 5)):
#             logger.debug ("INFO9 Adding new ccpCode synonym %s from ChemComp %s:%s"
#                    % (tag, cifCode, ccId))
#             result[tag] = val
#
#           else:
#             logger.debug ("WARNING clash1 for %s chemComp %s v. cifCode %s:%s"
#                   % (tag, ccId, cifCode,  val))
#
#         elif prevId != val:
#           logger.debug ("WARNING clash2 for %s chemComp %s, %s v. cifCode %s:%s"
#                 % (tag, ccId, prevId, cifCode,  val))
#
#

#
#
#
# if __name__ == '__main__':
#   from ccpncore.util import Io as ioUtil
#   project = ioUtil.newProject('ChemCompNameTest')
#   fetchStdResNameMap(project)
  # result, excluded, pending = getNewStdResNameMap(chemComps=project.chemComps)
  #
  # print ("TOTAL mapped: %s" % len(result))
  # print ("TOTAL excluded: %s" % len(excluded))
  # print ("TOTAL pending: %s" % len(pending))
  #
  # for ll in excluded:
  #   print(*ll)
  #
  # for ll in pending:
  #   print("PENDING", *ll)