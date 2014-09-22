"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
"""Data conversion function"""


# OLD TODO 1 make maximum independent of installed ccpn

# OLD TODO 2 port code for reading coordinates to this file.

# NEW TODO Dat conversion functionality (commented out0 TO REUSE OR REMOVE

import os
#import copy
#from collections import namedtuple, defaultdict

#from ccp.general import Io as genIO

#from ccpnmr.analysis.core import AssignmentBasic, ConstraintBasic
#from ccp.lib import MoleculeAlign
from ccpncore.lib import DataConvertLib
from ccpncore.lib import MoleculeQuery

emptyTuple = ()

# constraintListData = {
#  'distanceConstraints':{'ccpnName':'DistanceConstraint','nResonances':2},
#  'rdcConstraints':{'ccpnName':'RdcConstraint','nResonances':2},
#  'jcouplingConstraints':{'ccpnName':'JCouplingConstraints','nResonances':2},
#  'hbondConstraints':{'ccpnName':'HBondConstraint','nResonances':2},
#  'dihedralConstraints':{'ccpnName':'DihedralConstraint','nResonances':4},
#  'shiftConstraints':{'ccpnName':'ChemShiftConstraint','nResonances':1},
# }


########################################################################
#
# Data classes - develped from FormatExchaange data structure
#

# Atom Record. NBNB all four elements assumed to be STRING (or None)
# AtomRecord = namedtuple('AtomRecord', ("chainId", "resId", "resName", "atName"))
#
# # Assignment record. NBNB seqCode can be an Int (residue number) OR a string (Spin System name)
# # Otherwise all fields are assumed to be String or None.
#
# Assignment = namedtuple('Assignment', ("chainCode", "seqCode", "molType",
#                                        "resCode", "atomCode", "offset"))
#
# class Constraint:
#   """ Generic restraint
#   atomRecords is a list of tuples of AtomRecord; Other fields are floats
#   """
#   fields = ('targetValue', 'upperLimit', 'lowerLimit', 'error',
#             'weight', 'origData', 'atomRecords')
#
#   def __init__(self, **kw):
#
#     for tag in fields:
#       setattr(self, tag, kw.get(tag))
#     if self.atomRecords is None:
#       self.atomRecords = []
#     else:
#       self.atomRecords = list(self.atomRecords)


class DataMapper:
  """ Format-independent and importer-independent class for 
  importing, mapping and converting input data to CCPN.
  """

  
  # def __init__(self, ccpnProject=None, molSystem=None, nmrProject=None,
  #              nmrConstaintStore=None, **kw):
  #   """
  #   """
  #
  #   kwAtttributes = ('prefMolType', 'prefNamingSystemName')
  #
  #   if molSystem is None:
  #     raise ImplementationError(
  #           "Not yet implemented DataMapper without input MolSystem")
  #   else:
  #     self.molSystem = molSystem
  #     self.ccpnProject = molSystem.ccpnProject
  #
  #   if nmrConstraintStore is None:
  #     if nmrProject is None:
  #       self.nmrProject = self.ccpnProject.currentNmrProject
  #
  #     if not self.nmrProject:
  #       self.nmrProject = self.ccpnProject.newNmrProject(name='DataMapperAuto')
  #
  #     self.nmrConstraintStore = self.ccpnProject.newNmrConstraintStore(
  #                                                nmrProject=self.nmrProject)
  #   else:
  #     self.nmrConstraintStore = nmrConstraintStore
  #     self.nmrproject = nmrConstraintStore.nmrProject
  #
  #   # Needed for atom set mappings - simpler to have a separate one
  #   self.analysisProject = self.ccpnProject.newAnalysisProject(
  #       name='DataMapperAuto', nmrProject=self.nmrProject)
  #   AssignmentBasic.initAtomSetMappings()
  #
  #
  #   for tag in kwAtttributes:
  #     setattr(self, tag, kw.get(tag))
  #
  #   # Main mapping dicts
  #
  #   #   from AtomRecord to Assignment
  #   self.record2Assign = {}
  #   # from Assignment to list(AtomRecords)
  #   self.assign2Records = defaultdict(list)
  #   #from Assignment to AtomSetMapping
  #   self.assign2AtomSetMapping = {}
  #
  #
  #   # Auxiliiary dictionaries:
  #
  #   # (resName:bestChemCompId} dictionary for resNames present.
  #   # None if no ChemComps match
  #   self.resName2ChemCompId = {}
  #   # NBNB consider using (molType,ccpCode) instead!?!
  #
  #   # {(chainId,resId):resnames} dictionary
  #   self.chainResId2ResNames = defaultdict(list)
  #
  #   # {(chainId,resId):(chainCode,seqCode)}  dictionary
  #   self.seqMapping = {}
  #
  #   # {resName:{atName:normAtomName}} dictionary
  #   self.resAtomNames = defaultdict(dict)
  #
  #   # {chemComp:normAtomName}} dictionary
  #   self.chemCompIdAtomCodes = defaultdict(dict)
  #
  #   # NBNB no offset handling yet TODO
  #
  #   # Standard dict: {resName:(tuple of (molType,ccpCode) tuples
  #   # Initialise once and for all here)
  #   self.resName2AllChemCompId = DataConvertLib.getStdResNameMap(
  #                                  self.ccpnProject.sortedChemComps())
  #
  # def validateMappings(self):
  #   """ check mappings for consisency and warnings
  #   """
  #
  #   # mapping consistency
  #   unmatchRecords = []
  #   unmatchAssignRecs = []
  #   for record,assign  in sorted(self.record2Assign.items()):
  #     if assign and record not in self.assign2Records[assign]:
  #       unmatchRecords.append((record,assign))
  #
  #   if unmatchRecords:
  #     for record,assign in unmatchRecords:
  #       print 'ERROR unreciprocted mapping from %s to %s' % (record, assign)
  #
  #   for assign.records in (self.assign2Records[assign]):
  #     for record in records:
  #       if assign is not self.record2Assign[record]:
  #         unmatchAssignRecs.append((assign, record))
  #
  #   if unmatchAssigns:
  #     for assign,record in unmatchAssigns:
  #       print 'ERROR unreciprocated mapping from %s to %s' % (assign, records)
  #
  #   # resNames for residue identifiers
  #   for tt,ll in (self.chainResId2ResNames):
  #     if not ll:
  #       print 'WARNING residue ID %s has no resNames' % tt
  #     elif len(ll) > 1:
  #       print 'WARNING resiude ID %s has multiple resNames %s' % (tt,ll)
  #
  #   # atNames for resNames
  #   for resName, dd in sorted(self.resAtomNames.items()):
  #     if not dd:
  #       print 'WARNING resName %s has no atoms' % resName
  #
  #   # resName to ChemComps:
  #   for resName,chemCompId in sorted(self.resName2ChemCompId.items()):
  #     if not chemCompId:
  #       print 'WARNING resName %s matches no ChemComp' % resName
  #
  #   # check residue mapping
  #   unmapped = []
  #   mismatched = []
  #   mappedRes = {}
  #   for tt in (self.chainResId2ResNames):
  #     tt2 = self.seqMapping.get(tt)
  #     if tt2:
  #
  #       res = self.molSystem.getByNavigation(('chain', t2[0], ('residue',tt2[1])))
  #       if res:
  #         cc = res.molResidue.chemComp
  #         ccId = (cc.molType,cc.ccpCode)
  #         mappedRes[res] = tt
  #
  #         ll = chainResId2ResNames.get(tt)
  #         if len(ll) == 1:
  #           chemCompId = resName2ChemCompId.get(ll[0])
  #           if chemCompId and chemCompId is not ccId:
  #             mismatched.append(tt, ll[0], chemCompId, tt2, ccId)
  #       else:
  #         print 'ERROR %s maps to %s, which has no ChemComp' % (tt,tt2)
  #     else:
  #       unmapped.append(tt)
  #
  #   for tt in unmapped:
  #     print 'WARNING no Molsystem residue mapped to %s' % tt
  #
  #   for tt in mismatched:
  #     print ('ERROR Mismatch beween %s %s ChemComp %s and sequence position %s %s'
  #            % tt)
  #
  #   for chain in molSystem.chains:
  #     residues = chain.sortedResidues()
  #     mappedResidues = [x for x in residues if x in mappedRes]
  #     if mappedResidues:
  #       nMissing = len(residues) - len(mappedResidues)
  #       if nMissing:
  #         nTrunc1 = residues.index(mappedResidues[0])
  #         nTrunc2 = len(residues) - residues.index(mappedResidues[-1]) -1
  #         if nTrunc1:
  #           print 'WARNING first %s residues of %s not in data' % (nTrunc1, chain)
  #         if nTrunc2:
  #           print 'WARNING last %s residues of %s not in data' % (nTrunc2, chain)
  #         nn = nMissing > nTrunc1 + nTrunc2
  #         if nn:
  #           print 'WARNING %s non-terminal residues of %s not in data' % (nn, chain)
  #
  #     else:
  #       print 'WARNING chain %s has no matching data' % chain
  #
  #
  #
  # def makeAssignmentMapping(self, reset=True):
  #   """ Make Assignments corresponding to AtomRecords
  #   and set up two-way hashmaps betwen them   """
  #
  #   if reset:
  #     self.assign2Records.clear()
  #     self.record2Assign = dict.fromkeys(self.record2Assign.keys())
  #
  #   record2Assign = self.record2Assign
  #   assign2Records = self.assign2Records
  #   assign2AtomSetMapping = self.assign2AtomSetMapping
  #
  #   for atomRecord, prevAssign in self.record2Assign.items():
  #     if prevAssign is None:
  #       assignment = self.newAssignment(atomRecord)
  #       record2Assign[atomRecord] = assignment
  #       assign2Records[assignment].append(atomRecord)
  #       atomSetMapping = getAtomSetMapping(self.analysisProject, assignment,
  #                                          self.molSystem.code)
  #       if atomSetMapping:
  #         assign2AtomSetMapping[assignment] = atomSetMapping
  #
  #
  # def addAtomRecord(self, atomRecord):
  #   """Add new atomRecord and update main maps. Does nothing if atomRecord already exists
  #   """
  #   if atomRecord not in self.record2Assign:
  #     assignment = self.newAssignment(atomRecord)
  #     self.record2Assign[atomRecord] = assignment
  #     self.assign2Records[assignment].append(atomRecord)
  #
  #
  # def removeAtomRecordFromMaps(self, atomRecord):
  #   """Remove atomRecord and update maps. Does nothing if atomRecord is not in maps.
  #   WARNING. this will NOT affect AtomRecords in restraints, peak assignments etc.
  #   """
  #   if atomRecord in self.record2Assign:
  #     assignment = self.record2Assign.pop(atomRecord)
  #     self.assign2Records[assignment].remove(atomRecord)
  #
  #
  # def removeAssignment(self, assignment):
  #   """Remove assignment and update maps. Does nothing if assignment is not in maps.
  #   """
  #   atomRecords = self.assign2Records.pop(assignment, ())
  #   for atomRecord in atomRecords:
  #     self.record2Assign[atomRecord] = None
  #
  #
  # def newAssignment(self, atomRecord):
  #   """ get Assignment record matching atomRecord, If none exists, make one
  #   """
  #   chainId, resId, resName, atName = atomRecord
  #
  #   # get chainCode and seqCode
  #   mapResId = self.seqMapping.get((chainId, resId))
  #   if mapResId:
  #     chainCode,seqCode = mapResId
  #   else:
  #     chainCode, seqCode = chainId, resId
  #
  #   # get molType, ccpCode
  #   if not resName:
  #     ll = self.chainResId2ResNames.get((chainId, resId))
  #     if len(ll) == 1:
  #       resName = ll[0]
  #
  #   chemCompId = None
  #   if resName:
  #     chemCompId = self.resName2chemCompId.get(resName)
  #   elif mapResId and self.molSystem:
  #     cc = self.molSystem.getByNavigation(('chain', mapResId[0]),
  #                                         ('residue', mapResId[1]),
  #                                         'molResidue', 'chemComp')
  #     if cc:
  #       chemCompId = (cc.molType, cc.ccpCode)
  #
  #   if not chemCompId:
  #     chemCompId = (None, resName)
  #
  #   # get atomCode
  #   dd = self.chemCompIdAtomCodes[chemCompId]
  #   atomCode = dd.get(atName)
  #
  #   # get offset - NBNB not in use yet. TODO
  #   offset = None
  #
  #   #
  #   return Assignment(chainCode, seqCode, chemCompId[0], chemCompId[1], atomCode,
  #                     offset)
  #
  #
  #
  # def loadAtomRecords(self, atomRecords, reset=False):
  #   """ Generate mapping files as necessary.
  #   input: list of DataMapper.AtomRecord namedtuples.
  #   If 'reset' mappings are reset and regenerated, otherwise expanded.
  #   NB, seqMapping cannot be expanded, but is recalculated.
  #   It is preferable to load all atomRecords in one go.
  #   """
  #   if reset:
  #     self.chainResId2ResNames.clear()
  #     self.resName2ChemCompId.clear()
  #     self.seqMapping.clear()
  #     self.resAtomNames.clear()
  #     self.chemCompIdAtomCodes.clear()
  #     self.record2Assign.clear()
  #
  #   # First set chainResId2ResNames and resAtomNames
  #   noResName = []
  #   for atomRecord in set(atomRecords):
  #     chainId, resId, resName, atName = atomRecord
  #
  #     # if atomRecord not in already, put it in with value None
  #     self.record2Assign.setdefault(atomRecord)
  #
  #     if resName:
  #
  #       # {(chainId,resId):resnames} dictionary
  #       ll = self.chainResId2ResNames[(chainId, resId)]
  #       if resName not in ll:
  #         ll.append(resName)
  #
  #       # {resName:{atName:normAtomName}} dictionary
  #       dd = self.resAtomNames[resName]
  #       if atName not in dd:
  #         dd[atName] = DataMapper.normalisedAtomName(atName)
  #
  #     else:
  #       noResNames.append(atomRecord)
  #
  #   # do fill-in round for resAtomNames using chainResId2ResNames
  #   for atomRecord in noResNames:
  #     chainId, resId, resName, atName = atomRecord
  #     ll = self.chainResId2ResNames.get((chainId, resId), emptyTuple)
  #     if len(ll) == 1:
  #       resName = ll[0]
  #
  #       # {resName:{atName:normAtomName}} dictionary
  #       dd = self.resAtomNames[resName]
  #       if atName not in dd:
  #         dd[atName] = DataMapper.normalisedAtomName(atName)
  #
  #   # set resName:chemCompId dictionary
  #   chemCompAtNames = defaultdict(dict)
  #   for resName,dd in self.resAtomNames.items():
  #     if resName and resName not in self.resName2ChemCompId:
  #       ccIds = (self.resName2AllChemCompId.get(resName) or
  #                self.resName2AllChemCompId.get(resName.upper()))
  #       chemCompId = self.selectChemCompId(ccIds, atomNames=dd.values(),
  #                                       prefMolType=self.prefMolType)
  #       self.resName2ChemCompId[resName] = chemCompId
  #       if chemCompId:
  #         chemComp = genIo.getChemComp(self.ccpnProject,
  #                                      molType=ccId[0], ccpCode=ccId[1])
  #       else:
  #         chemComp = None
  #
  #       # set up for next block:
  #       chemCompAtNames[chemComp].update(dd)
  #
  #   # fill chemCompIdAtomCodes dictionary
  #   self.prefNamingSystemName = DataConvertLib.getBestNamingSystemCC(
  #                                   chemCompAtNames.keys(),
  #                                   chemCompAtNames.values(),
  #                                   prefNamingSystemName=self.prefNamingSystemName
  #                                  )
  #
  #   for chemComp, atNameDict in chemCompAtNames.items():
  #     sysNameDict = DataMapper.chemCompGetAtomSysNames(chemComp, atNameDict,
  #                                       namingSystemName=self.prefNamingSystemName)
  #
  #     atCodes = self.chemCompIdAtomCodes[(chemComp.molType,chemComp.ccpCode)]
  #     excludeAtomNames = set()
  #     for atName, atomSysName in sorted(sysNameDict.items()):
  #       # NBNB TODO all atoms assumed NON-stereospecific. FIX!
  #       dd = DataMapper.getAtomData(atomSysName, excludeAtomNames=excludeAtomNames)
  #       atCode = dd.get('name')
  #       excludeAtomNames.add(atCode)
  #       atCodes[atName] = atCode
  #
  #   # set sequence mapping
  #   self.seqMapping = DataMapper.makeSeqMapping(self.molSystem,
  #                                                 self.chainResId2ResNames,
  #                                                 self.resName2ChemCompId)
  #
  #
  # def constraintList2Ccpn(self, listType, name, constraints):
  #   """ make new constraintList in current nmrConstraintStore using current mappings
  #
  #   Input ...
  #        Word (name of List type (CCPN constraint class name, e.g. DistanceConstraint)
  #        List of Constraint objects
  #
  #   Output ...
  #        New ccp.nmr.NmrConstraint.AbstractCOnstraintList
  #   """
  #
  #   # set up, for speed
  #   record2Assign = self.record2Assign
  #   assign2AtomSetMapping = self.assign2AtomSetMapping
  #
  #   # tags for creating constraints and items
  #   if listType == 'DihedralConstraint':
  #     # tags for constraint
  #     tagsc = ('weight', 'origData')
  #     # tags for constraint item
  #     tagsi = ('targetValue', 'upperLimit', 'lowerLimit', 'error')
  #   else:
  #     # tags for constraint
  #     tagsc = ('targetValue', 'upperLimit', 'lowerLimit', 'error',
  #             'weight', 'origData')
  #     # tags for constraint item
  #     tagsi = ()
  #
  #   dd = constraintListData.get(listType)
  #   if dd:
  #     ccpnName = dd['ccpnName']
  #     nResonances = dd['nResonances']
  #
  #   else:
  #     print ("ERROR '%s' is not a recognized  constraint list type" % listType)
  #     return None
  #
  #   try:
  #     ConstraintClass = __import__('ccp.api.nmr.NmrConstraint', {}, {}, [ccpnName])
  #     ListClass = __import__('ccp.api.nmr.NmrConstraint', {}, {},
  #                            [ccpnName + 'List'])
  #     ItemClass = __import__('ccp.api.nmr.NmrConstraint', {}, {},
  #                            [ccpnName + 'Item'])
  #   except ImportError:
  #     print 'ERROR (non-existent?) class %s could not be imported' % listType
  #     return None
  #
  #   # NBNB TODO check what else might be needed (name?)
  #   constraintList = ListClass(self.nmrConstraintStore, name=name)
  #
  #
  #   if ccpnName == 'DihedralConstraint' or nResonances == 1:
  #     # constraints with only a singel item.
  #     # NB Two-item dihedral constraints NOT supported for now
  #
  #     for indx,constraint in enumerate(constraints):
  #       atomRecords = constraint.atomRecords
  #
  #       # check validity
  #       if len(atomRecords) != 1:
  #         print ("ERROR - %s constraint %s: must have exactly one item, %s found"
  #                         % (ccpnName, indx+1, len(atomRecords)))
  #         continue
  #
  #       if len(atomRecords[0]) != nResonances:
  #         print ("ERROR - %s constraint %s: must connect %s atoms: %s "
  #                         % (ccpnName, indx+1, nResonances, atomRecords))
  #         continue
  #
  #       # from record to AtomSetMap to resonances to FixedResonances
  #       fresonances = []
  #       for record in atomRecords[0]:
  #         amap = assign2AtomSetMapping.get(record2Assign.get(x))
  #
  #         if amap is None:
  #           print ('WARNING unassigned AtomRecord in %s constraint %s : %s'
  #                    (ccpnName, indx+1,record))
  #           break
  #
  #         rs = amap.sortedResonances()
  #         if len(rs) != 1:
  #           print ('WARNING ambiguous AtomRecord in %s constraint %s : %s'
  #                    (ccpnName, indx+1,record))
  #           break
  #
  #         fresonances.append(ConstraintBasic.getFixedResonance(self.nmrConstraintStore,
  #                                                              rs[0]))
  #
  #       else:
  #         # If we did not break, this is an OK set of resonances. Make constraint
  #
  #         ccpnConstraint = ConstraintClass(constraintList,
  #                                 **dict((x,getattr(constraint, x))
  #                                                 for x in tagsc))
  #         if ccpnName == 'DihedralConstraint':
  #           ccpnItem = ItemClass(ccpnConstraint, **dict((x,getattr(constraint, x))
  #                                                       for x in tagsi))
  #           # Add atomRecords
  #           ccpnConstraint.resonances = fresonances
  #
  #         else:
  #           # single-resonance no-item restraint (Csa or ChemShift
  #           # Add atomRecords
  #           ccpnConstraint.resonance = fresonances[0]
  #
  #   else:
  #     # Generic constraint (Pairwise constraint in practice)
  #
  #     for indx, constraint in enumerate(constraints):
  #       atomRecords = constraint.atomRecords
  #
  #       resonances = []
  #       for ar in atomRecords:
  #
  #         if len(ar) == nResonances:
  #           # Get resonances through AtomSetMaps
  #           amaps = tuple(assign2AtomSetMapping.get(record2Assign.get(x))
  #                       for x in ar)
  #           if None in amaps:
  #             print ('WARNING unassigned AtomRecord 1 in %s constraint %s : %s'
  #                    (ccpnName, indx+1,ar))
  #           else:
  #             # NB a map may correspond to one or two (or more) resonances)
  #             tt = tuple(x.resonances or None for x in amaps)
  #             if None in ll:
  #               print ('WARNING unassigned AtomRecord 2 in %s constraint %s : %s'
  #                      (ccpnName, indx+1,ar))
  #
  #             else:
  #               resonances.append(tt)
  #
  #         else:
  #           print ("ERROR - %s constraint %s: must connect %s atoms: %s "
  #                           % (ccpnName, indx+1, nResonances, atomRecords))
  #
  #       if resonances:
  #
  #         # Make Constraint
  #         ccpnConstraint = ConstraintClass(constraintList,
  #                                 **dict((x,getattr(constraint, x)) for x in tagsc))
  #
  #         # Convert to FixedResonances and expand to tuples of single resonances
  #         fresonances = []
  #         for tt in resonances:
  #           ll = []
  #           length = 1
  #           for ii,rr in tt:
  #             #
  #             frr = tuple(ConstraintBasic.getFixedResonance(self.nmrConstraintStore, x)
  #                         for x in rr)
  #             length *= len(frr)
  #             ll.append(frr)
  #           if length >= 1:
  #             ll = [xx * (len(xx)/length) for xx in ll]
  #           fresonances.extend(zip(*ll))
  #
  #         # make ConstraintItems
  #         for tt in fresonances:
  #           ItemClass(ccpnConstraint, resonances=tt)
  #
  #       else:
  #         # Skip if no valid resonances
  #         print ("atomSetMaps - %s Constraint %s has no valid atomRecords"
  #                % (ccpnName, indx + 1))
  #
  
  ########################################################################
  #
  #  Static functions
  #
  
  @staticmethod
  def getAtomSetMapping(analysisProject, assignment, molSystemCode=None):
    """ Get ccpnmr.Analysis.AtomSetMaping for Assignment
    """
    if molSystemCode is None:
      molSystems = analysisProject.root.sortedMolSystems()
      if len(molSystems) == 1:
        molSystemCode = molSystems[0].code
      else:
        raise Exception("No molSystemCode passed in and no unique MolSystem")
      
    chainCode, seqCode, molType, resCode, atomCode, offset = assignment
    chainMapping = analysisProject.findFirstChainMapping(molSystemCode=molSystemCode,
                                                         chainCode=chainCode)
    if chainMapping:
      residueMapping = chainMapping.findFirstResidueMapping(seqId=seqCode)
      
      if residueMapping:
        return residueMapping.findFirstAtomSetMapping(name=atomCode)
    #
    return None
  
  @staticmethod
  def selectChemCompId(ccIds, atomNames=None, prefMolType=None):
    """Get the best matching ccId ((molType,ccpCode) tuple) from the presented list
    using (optional) atomNames and prefMolType to resolve ambiguity if necessary
    .. describe:: Input
 
               List of tuples (molType,ccpCode),
               List of Words (normalised atom names)
               Word (referred molType)

    .. describe:: Output

    (molType,ccpCode) tuple
    """
  
    ccId = None
    
    if ccIds:
      if len(ccIds) == 1:
        # Only one ChemComp matches. Use it
        ccId = ccIds[0]
      else:
        # more than one match, choose by type
        
        if prefMolType:
          #Use preferred molType,if given
          ll = [tt for tt in ccIds if prefMolType == tt[0]]
          if len(ll) == 1:
            ccId = ll[0]
            
        if ccId is None and atomNames:
          # match on basis of atom names
          # NB the expression for ll ensures that molType 'DNA/RNA'
          # will select either 'DNA' or 'RNA' if present
          molType = DataMapper.getBestMolType(atomNames)
          ll = [tt for tt in sorted(ccIds) if tt[0] in molType]
          if ll:
            ccId = ll[0]
        
        if ccId is None:
          # try in priority order:
          for molType in DataConvertLib.molTypeOrder:
            ll = [tt for tt in ccIds if molType == tt[0]]
            if len(ll) == 1:
              ccId = ll[0]
              break
    #
    return ccId
  
  
  # NBNB modified interface and behaviour rel to analysis/core
  #def getBestMolType(atomNames, ccpCodes=None):
  @staticmethod
  def getBestMolType(atomNames):
    """ Use heuristics to get best molType from molTypes using atomNames
    returns 'protein', 'DNA', 'RNA', 'carbohydrate', 'DNA/RNA' or 'other'(default)
    
  .. describe:: Input
  
  List of Words (imported atom names)
  
  .. describe:: Output
  
  Word (Molecule.Molecule.molType)
    """
  
    proteinNames = {'HA', 'CO', 'C', 'N', 'H', 'HN'}
    nuclNames = {"H1'", "H2'", "H3'", "H4'", "C3'", "C5'", "C2", "C3*", "C5*", "H5", "H6", "H8"}
    
    
    molType = 'other'
    
    # first try with more reliable heavy atom names
    if ("C3'" in atomNames) and ("C5'" in atomNames) and ("C2" in atomNames):
      molType = 'DNA'
      if "O2'" in atomNames:
        molType = 'RNA'
  
    elif ("C3*" in atomNames) and ("C5*" in atomNames) and ("C2" in atomNames):
      # PDB Naming system different from others
      molType = 'DNA'
      if "O2*" in atomNames:
        molType = 'RNA'
  
    elif 'CA' in atomNames:
      molType = 'protein'
  
    elif (("C1" in atomNames) and ("C2" in atomNames) and ("C3" in atomNames) and
          ("C4" in atomNames)and
          ( ("O2" in atomNames) or ("O3" in atomNames) or ("O4" in atomNames))):
      molType = 'carbohydrate'
    
    else:
      # try looser heuristics
      protMatch = len(proteinNames.intersection(atomNames))
      nucMatch = len(nuclNames.intersection(atomNames))
  
      if protMatch or nucMatch:
        if protMatch >= nucMatch:
          # prefer protein if equal match
          molType = 'protein'
  
        else:
          molType = 'DNA/RNA'
    #
    return molType
    


  #@staticmethod
  # def makeSeqMapping(molSystem, chainResId2ResNames, resName2ChemCompId):
  #   """ make sequence mapping, using several alternative methods
  #   .. input:
  #   ccp.molecule.Molsystem.MolSystem
  #   {(chainId,resId):resName} dictionary
  #   {resName:chemComp} dictionary
  #
  #   ... output
  #   result {(chainId,resId):(chainCode,seqId)} dictionary
  #   """
  #
  #   result = {}
  #
  #   numChains = len(molSystem.chains)
  #
  #   # first get chain2Res2ChemComp mapping
  #   chain2Res2ChemComp = dict()
  #   for tt,resNames in chainResId2ResNames.items():
  #
  #     chainId, resId = tt
  #     # Convert string resId to integer
  #     try:
  #       intResId = int(resId)
  #     except ValueError:
  #       print ("WARNING, chain '%s': non-integer resId '%s'. Skipping in seq mapping"
  #              % (chainId, resId))
  #       continue
  #
  #     # Check that resId is equal to its int representation
  #     if str(intResId) == resId:
  #       resId = intResId
  #     else:
  #       print ("WARNING, chain '%s': non-standard integer resId '%%' (should have been '%s'"
  #              " Skipping in seq mapping" % (chainId, resId))
  #
  #     if len(resNames) == 1:
  #       resName= resNames[0]
  #       dd = chain2Res2ChemComp.get(chainId)
  #       if dd is None:
  #         dd = chain2Res2ChemComp[chainId] = {}
  #       ccId = resName2ChemCompId.get(resName)
  #       if ccId:
  #         chemComp = molSystem.getByNavigation(('chain', ccId[0]),
  #                                              ('residue', ccId[1]),
  #                                              'molResidue', 'chemComp')
  #         dd[intResId] = chemComp
  #
  #   # set test order and check length
  #   ll = list(chain2Res2ChemComp.keys())
  #   # Move empty chain ID to the end.
  #   for ii,ss in ll:
  #     if ss and ss.strip():
  #       break
  #   useChainIds = ll[ii:] + ll[:ii]
  #
  #   if len(useChainIds) > numChains:
  #     print ('WARNING %s chains, %s chainCodes: %s - allowing duplicate mapping'
  #            % (numChains, len(useChainIds), useChainIds))
  #
  #   # make mapping using ChemComps
  #   chains = []
  #   retry = []
  #   for chainId in useChainIds:
  #     seqDict = chain2Res2ChemComp.get(chainId)
  #     if seqDict is None:
  #       seqDict = chain2Res2ChemComp[chainId] = {}
  #     # NBNB reversed order, so that None, '', or space chainCodes are tried LAST
  #     chain = None
  #
  #     if len(chains) < numChains:
  #       excludeChains = chains
  #     else:
  #       # If all chains are taken allow duplicate mapping
  #       excludeChains = None
  #
  #     if seqDict:
  #
  #       # Try matching using seqCodes
  #       chain, resIdMap = MoleculeAlign.matchBySeqCode(molSystem, seqDict,
  #                                                      excludeChains)
  #       if chain:
  #         print('---> Matched to chain %s using seqCodes' % chain.code)
  #
  #       else:
  #         # try matching using uniform offset
  #         chain, resIdMap = MoleculeAlign.matchByOffset(molSystem, seqDict,
  #                                                       excludeChains)
  #         if chain:
  #           pair = list(resIdMap.items())[0]
  #           print ('---> Matched to chain %s with offset %s'
  #                  % (chain.code, (pair[1] - pair[0])))
  #
  #         else:
  #           # try full alignment. NB unlikely to work well for very sparse data
  #          chain, resIdMap = MoleculeAlign.matchSequences(molSystem, seqDict,
  #                                                         excludeChains)
  #
  #     if chain is None:
  #       # no ChemComps to use. Put on retry list
  #       retry.append(chainId)
  #
  #     else:
  #       chains.append(chain)
  #       chainCode = chain.code
  #       for resId,seqId in resIdMap.items():
  #         result[(chainId, resId)] = (chainCode, seqId)
  #
  #   #
  #   for chainId in retry:
  #     # these chainIds had no matches - likely because there were no resNames
  #     # Try simply matching resId numbers to seqCodes or seqIds
  #     chain = None
  #
  #     if len(chains) < numChains:
  #       excludeChains = chains
  #     else:
  #       # If all chains are taken allow duplicate mapping
  #       excludeChains = None
  #
  #     seqDict = chain2Res2ChemComp.get(chainId)
  #     if seqDict is None:
  #       seqDict = chain2Res2ChemComp[chainId] = {}
  #     chain,resIdMap  = MoleculeAlign.matchResidueNumbers(molSystem, seqDict.keys(),
  #                                                         excludeChains)
  #     if chain is None:
  #       print('ERROR, no possible match for chain %s' % chainId)
  #
  #     else:
  #       if any((tt[0] != tt[1]) for tt in resIdMap.items()):
  #         print('WARNING, no match on resNames - chain %s assumed matching seqCodes' % chainCode)
  #       else:
  #         print('WARNING, no match on resNames - chain %s assumd matching seqIds' % chainCode)
  #
  #       chains.append(chain)
  #       chainCode = chain.code
  #       for resId,seqId in resIdMap.items():
  #         result[(chainId, str(resId))] = (chainCode, seqId)
    
    

  @staticmethod
  def normalisedAtomName(name):
    """ Get normalized atom name: Upper case, with common offset-indicating
        suffixes removed 
        COPY from FormatExchange.CcpnUtil
 
    .. describe:: Input
 
    atom name (Word)

    .. describe:: Output

    normalisedatom name (Word)
    """
 
    stripSuffixes = ('I+1', 'I-1', '+1', '-1', '+', '-', 'I' )
 
    result = name.upper()
 
    for ss in stripSuffixes:
      if result.endswith(ss):
        result = result[:-len(ss)]
        break
    #
    return result
  
  

  @staticmethod
  def getAtomData(atomSysName, excludeAtomNames=None, useStereospecific=False):
    """ Get atom data (name, isProchiral, isEquivalent) for AtomSysName object.
  Rules for name match:
  - If match is an atom and is part of an equivalent atomset, use atomset
    - unless name is H: in this case use single atom
  - If match is an AtomSet (or as above), use AtomSet name. Duplicate hits allowed
  - If match is an atom and is part of a prochiral atomset, and stereospecific
     is false, use a/b names. Duplicates prohibited
  - Otherwise use atom name. Duplicates prohibited
    
    .. describe:: Input
    
    ChemComp.AtomSysName (object to get data from)
    
    List of (Word)  (atom names already found in same contect) 
  
    .. describe:: Output
  
    Dictionary of ('name':Word, 'isProchiral':Boolean, 'isEquivalent':Boolean 
                   (all optional))
    """                                         
    
    # set up
    result = {}
    chemComp = atomSysName.namingSystem.chemComp
    atomName = atomSysName.atomName
    
    # set ChemAtom and chemAtomSet
    matchAtom = chemComp.findFirstChemAtom(name=atomName)
    if matchAtom is None:
      matchAtomSet = chemComp.findFirstChemAtomSet(name=atomName)
      matchObject = matchAtomSet
    elif atomName == 'H':
      # special case - necessary to map protein backbone H to H rather than H*
      matchObject = matchAtom
      matchAtomSet = None
    else:
      matchObject = matchAtom
      matchAtomSet = matchAtom.chemAtomSet
    
    
    if matchObject is None:
      # Nothing found
      chemComp.root._logger.warning('Bad ref data? No ChemAtomSet found for %s' % atomSysName)
    
    elif matchAtomSet is None:
        # Single atom
        result['name'] = MoleculeQuery.makeGuiName(atomName, matchObject.elementSymbol)
    
    else:
      # We have a matching atom set
      
      # Look for highest equivalent atomSet
      equivObj = None
      ms = matchAtomSet
      while ms is not None:
        if ms.isEquivalent == False: # NB, deliberate. 
          # Value can be None, which means 'sometimes equivalent'
          break
        else:
          # Possibly equivalent. Treat as equivalent
          equivObj = ms
        #
        ms = ms.chemAtomSet
      
      # set isEquivalent 
      if equivObj:
        result['isEquivalent'] = True
        matchObject = equivObj
        
      name = matchObject.name
      
      # set isProchiral and modify name if necessary
      xx = matchObject.chemAtomSet
      if xx and xx.isProchiral:
        result['isProchiral'] = True
        if not useStereospecific:
          name = DataMapper.nonStereoName(matchObject, excludeAtomNames=excludeAtomNames)
      
      result['name'] = MoleculeQuery.makeGuiName(name, matchObject.elementSymbol)
    #
    return result
      
      

  @staticmethod
  def nonStereoName(matchObj, excludeAtomNames=None):
    """ Make non-stereospecific name for ChemAtom or ChematomSet
    Assumes that matchObj is part of a prochiral ChemAtomSet
    Replaces first non-shared character in prochiral name pair with 'a' or 'b'
    
    .. describe:: Input
    
    ChemComp.ChemAtom or ChemComp.ChemAtomSet
  
    .. describe:: Output
  
    Word (nonstereospecific name)
    
    
    """
    
    assert matchObj.className in ('ChemAtom','ChemAtomSet'), \
           "%s must is neither a ChemAtom nor a ChemAtomSet" % matchObj
    
    prochSet = matchObj.chemAtomSet
    assert prochSet is not None, \
           "%s must be part of a prochiral ChematomSet" % matchObj
    
    name = matchObj.name
    chars = list(name)
    objs = prochSet.chemAtoms or prochSet.chemAtomSets
    names = sorted(x.name for x in objs)
    commonChars = os.path.commonprefix(names)
    newchar = 'ab'[names.index(name)]
    chars[len(commonChars)] = newchar
    name = ''.join(chars)
    
    if excludeAtomNames and name in excludeAtomNames:
      # Should not happen, but just in case
      if newchar == 'a':
        chars[len(commonChars)] = 'b'
      else:
        chars[len(commonChars)] = 'a'
      name = ''.join(chars)
        
    #
    return name
  
    
    
  @staticmethod
  def chemCompGetAtomSysNames(chemComp, atNameDict, prefNamingSystemName=None):
    """ Get atomName:AtomSysName dictionary
    
    .. describe:: Input
    
    chemComp matching atoms
    atnameDict, {atomName:normalisedName} dictionary
    preferred naming system name
    
  
    .. describe:: Output
    
    dictionary {atomName:atomSysName
    """
    
    atomSysNames = {}
    usedAtomSysNames = set()
    
    # Get naming systems in priority order
    systems = DataConvertLib.priorityOrderedNamingSystems(chemComp,
                                        prefNamingSystemName=prefNamingSystemName)
       
    for namingSystem in systems:
      # First loop - check against AtomSysName.sysName
    
      if len(atomSysNames) >= len(atNameDict):
        # We have found matches for all
        return atomSysNames
      
      # looping over namingSystem and its referenceNamingSystems
      namingSystemR = namingSystem
      while namingSystemR:
        
        # Check match with original names
        for atomName in sorted(atNameDict):
          if atomName not in atomSysNames:
            hit = namingSystemR.findFirstAtomSysName(sysName=atomName)
            if hit is not None and hit not in usedAtomSysNames:
              if not (atomName == 'H' and hit.atomName == 'H*'):
                atomSysNames[atomName] = hit
                usedAtomSysNames.add(hit)
    
        if len(atomSysNames) >= len(atNameDict):
          # We have found matches for all
          return atomSysNames
        
        # Check match with normalised names
        for atomName in sorted(atNameDict):
          if atomName not in atomSysNames:
            hit = namingSystemR.findFirstAtomSysName(
                                 sysName=atNameDict[atomName])
            if hit is not None and hit not in usedAtomSysNames:
              if not (atomName == 'H' and hit.atomName == 'H*'):
                atomSysNames[atomName] = hit
                usedAtomSysNames.add(hit)
    
        if len(atomSysNames) >= len(atNameDict):
          # We have found matches for all
          return atomSysNames
        
        #  no luck, try again with reference naming system
        namingSystemR = namingSystemR.atomReference
            
    
    for namingSystem in systems:
      # Second loop - check against AtomSysName.altSysNames
    
      if len(atomSysNames) >= len(atNameDict):
        # We have found matches for all
        break
      
      # check against AtomSysName.altSysNames
      # looping over namingSystem and its referenceNamingSystems
      namingSystemR = namingSystem
      while namingSystemR:
        
        # Check match with original names
        for atomName in sorted(atNameDict):
          if atomName not in atomSysNames:
            for atomSysName0 in namingSystemR.sortedAtomSysNames():
              if (atomSysName0 not in usedAtomSysNames and 
                  atomName in atomSysName0.altSysNames):
                atomSysNames[atomName] = atomSysName0
                usedAtomSysNames.add(atomSysName0)
                break
              
        if len(atomSysNames) >= len(atNameDict):
          # We have found matches for all
          return atomSysNames
        
        # Check match with normalised names
        for key in sorted(atNameDict):
          atomName = atNameDict[key]
          if atomName not in atomSysNames:
            for atomSysName0 in namingSystemR.sortedAtomSysNames():
              if (atomSysName0 not in usedAtomSysNames and 
                  atomName in atomSysName0.altSysNames):
                atomSysNames[atomName] = atomSysName0
                usedAtomSysNames.add(atomSysName0)
                break
    
        if len(atomSysNames) >= len(atNameDict):
          # We have found matches for all
          return atomSysNames
        
        #  no luck, try again with reference naming system
        namingSystemR = namingSystemR.atomReference
          
    #
    return atomSysNames
    
    
