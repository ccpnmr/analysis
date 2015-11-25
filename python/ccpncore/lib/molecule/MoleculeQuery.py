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
"""Code for querying Molecules and MolSystems"""

import re
from ccpncore.lib.chemComp import ChemCompOverview
from ccpncore.lib.chemComp import ObsoleteChemComps
from ccpncore.util import Logging


###from ccp.util.LabeledMolecule import getIsotopomerSingleAtomFractions, getIsotopomerAtomPairFractions
###from ccp.util.LabeledMolecule import singleAtomFractions, atomPairFractions

###from ccp.util.NmrExpPrototype import longRangeTransfers

molTypeOrder = ('protein', 'DNA', 'RNA', 'carbohydrate', 'other')

LINEAR_POLYMER_TYPES = ('protein', 'DNA', 'RNA')


# CifCode map - preset to ensure it is not overridden by obsolete ChemComps in list
cifCodeRemap = {}
# # Std DNA - keep one-letter ccpCode
cifCodeRemap['DA'] = cifCodeRemap['Da'] = ('DNA', 'Da')
cifCodeRemap['DC'] = cifCodeRemap['Dc'] = ('DNA', 'Dc')
cifCodeRemap['DG'] = cifCodeRemap['Dg'] = ('DNA', 'Dg')
cifCodeRemap['DI'] = cifCodeRemap['Di'] = ('DNA', 'Di')
cifCodeRemap['DU'] = cifCodeRemap['Du'] = ('DNA', 'Du')
cifCodeRemap['DT'] = cifCodeRemap['Dt'] = ('DNA', 'Dt')

# # Std RNA - keep one-letter ccpCode
cifCodeRemap['5MU'] = cifCodeRemap['5mu'] = cifCodeRemap['RT'] =  cifCodeRemap['Rt'] = ('RNA','5mu')
#
# Set as RNA or other, to override DNA with similar name
for tag in ('2at', '2bt', '2gt', '2nt', '2ot', '3me', 'Ap7', 'Atl', 'Boe', 'Car',
            'Eit', 'Fnu', 'Gmu', 'Lcc', 'Lcg', 'P2t', 'S2m', 'T2t', 'Tfe', 'Tln'):
  cifCodeRemap[tag] = cifCodeRemap[tag.upper()] = ['RNA', tag]

cifCodeRemap['Hob'] = cifCodeRemap['HOB'] = ('other', 'Hob')
cifCodeRemap['Xxx'] = cifCodeRemap['XXX'] = ('other', 'Xxx')

# ccpCode remaps - for upgrade convresion of 'inventive' ChemComps
ccpCodeRemap = {
  'DNA':{
    'Xxx':('DNA','Dn'),
    'A00':('DNA','Da'),
    'A11':('DNA','Da'),
    'C00':('DNA','Dc'),
    'C11':('DNA','Dc'),
    'G00':('DNA','Dg'),
    'G11':('DNA','Dg'),
    'I00':('DNA','Di'),
    'I11':('DNA','Di'),
    'U00':('DNA','Du'),
    'U11':('DNA','Du'),
  },
  'protein':{
    'Xxx':('protein','Unk'),
  },
  'RNA':{
    'Xxx':('RNA','N'),
    'A00':('RNA','A'),
    'A11':('RNA','A'),
    'C00':('RNA','C'),
    'C11':('RNA','C'),
    'G00':('RNA','G'),
    'G11':('RNA','G'),
    'I00':('RNA','I'),
    'I11':('RNA','I'),
    'U00':('RNA','U'),
    'U11':('RNA','U'),
  },
  'other':{
    'Acy':('other','Ace'),
    'Nh3':('other','Nh2'),
    'A01_dna':('DNA','Da'),
    'C01_dna':('DNA','Dc'),
    'G01_dna':('DNA','Dg'),
    'I01_dna':('DNA','Di'),
    'T01_dna':('DNA','Dt'),
    'U01_dna':('DNA','Du'),
    'A01_rna':('RNA','A'),
    'C01_rna':('RNA','C'),
    'G01_rna':('RNA','G'),
    'I01_rna':('RNA','I'),
    'T01_rna':('RNA','T'),
    'U01_rna':('RNA','U'),
  },
}



# STEREO_PREFIX = 'stereo_'
# CARBOHYDRATE_MOLTYPE = 'carbohydrate'
# PROTEIN_MOLTYPE = 'protein'
# OTHER_MOLTYPE = 'other'
# DNA_MOLTYPE = 'DNA'
# RNA_MOLTYPE = 'RNA'
# DNARNA_MOLTYPE = 'DNA/RNA'


# userResidueCodesDict = {DNA_MOLTYPE:{'A':'Ade','T':'Thy','G':'Gua','C':'Cyt','U':'Ura'},
#                         RNA_MOLTYPE:{'A':'Ade','T':'Thy','G':'Gua','C':'Cyt','U':'Ura','I':'Ino'},
#                         PROTEIN_MOLTYPE:{},
#                         CARBOHYDRATE_MOLTYPE:{}
#                         }

#
# # Should really be derived or modelled attrs
# PROTEIN_RESIDUE_CLASS_DICT = {'Acidic'       :['Asp','Glu'],
#                               'Basic'        :['Arg','Lys','His'],
#                               'Charged'      :['Asp','Glu','Arg','Lys','His'],
#                               'Polar'        :['Asn','Gln','Asp','Glu','Arg','Lys','His','Ser','Thr','Tyr'],
#                               'Non-polar'    :['Ala','Phe','Gly','Ile','Leu','Met','Pro','Val','Trp','Cys'],
#                               'Hydrophilic'  :['Ser','Asp','Glu','Arg','Lys','His','Asp','Glu','Pro','Tyr'],
#                               'Hydrophobic'  :['Phe','Met','Ile','Leu','Val','Cys','Trp','Ala','Thr','Gly'],
#                               'Amide'        :['Asn','Gln'],
#                               'Hydroxyl'     :['Ser','Thr','Tyr'],
#                               'Aromatic'     :['Phe','Ptr','Tyr','Trp'],
#                               'Beta-branched':['Thr','Val','Ile'],
#                               'Small'        :['Cys','Ala','Ser','Asp','Thr','Gly','Asn'],
#                               'Neutral'      :['Ala','Asn','Cys','Gln','Gly','Ile','Leu','Met',
#                                                'Phe','Pro','Ser','Thr','Trp','Tyr','Val'],
#                               'Methyl'       :['Ala','Met','Ile','Leu','Thr','Val'],
#                              }

# X is an unusual base, not ambiguiuty

####################################################################
#
# ChemComps and ccpCodes
#

# def getMolTypeCcpCodes(molType='all', project=None):
#   """Gives ccpCodes for chemComps according to molecule type: e.g. DNA
#              Project can be input to search for non-standard types.
#   .. describe:: Input
#
#   Implementation.Project, String (ChemComp.molType or 'all')
#
#   .. describe:: Output
#
#   List of Words (ChemComp.CcpCodes)
#   """
#
#   ccpCodes = []
#   if molType == 'all':
#     molTypes = [PROTEIN_MOLTYPE, DNA_MOLTYPE, RNA_MOLTYPE,
#                 CARBOHYDRATE_MOLTYPE, OTHER_MOLTYPE]
#   else:
#     molTypes = [molType,]
#
#   for molType in molTypes:
#     chemCompDict = getChemCompOverview(molType, project)
#
#     if chemCompDict:
#       ccpCodes.extend( chemCompDict.keys() )
#
#   if ccpCodes:
#     ccpCodes.sort()
#
#   return ccpCodes

# def getChemCompOverview(molType, project=None):
#   """Get a dictionary containing details of all available chemical compounds
#              for a given molecule type. Project can be input to search for loaded,
#              but non standard chem comps.
#   .. describe:: Input
#
#   Word (Molecule.MolResidue.MolType), Implementation.Project
#
#   .. describe:: Output
#
#   Dict of ChemComp.ccpCode:[Word, Word, Line, Word]
#              (1-letter Code, 3-letter Code, name, mol formula)
#   """
#
#   if molType == OTHER_MOLTYPE:
#     chemCompDict = ChemCompOverview.chemCompOverview.get(molType, {})
#
#   else:
#     chemCompDict = ChemCompOverview.chemCompStdDict.get(molType, {})
#
#   if project:
#     for chemComp in project.findAllChemComps(molType=molType):
#       ccpCode  = chemComp.ccpCode
#
#       if chemCompDict.get(ccpCode) is None:
#         chemCompVar = chemComp.findFirstChemCompVar(linking=None, isDefaultVar=True) \
#                       or chemComp.findFirstChemCompVar(isDefaultVar=True) \
#                       or chemComp.findFirstChemCompVar()
#
#         if chemCompVar:
#           molFormula = chemCompVar.formula
#         else:
#           molFormula = ''
#           # NBNB TBD fixme
#
#         chemCompDict[ccpCode] = [chemComp.code1Letter,
#                                  chemComp.code3Letter,
#                                  chemComp.name,
#                                  None]   # Added RHF 1/7/10 for bug fix.
#
#   return  chemCompDict



####################################################################
#
# Bonds between atoms
#

# def getNumConnectingBonds(atom1, atom2, limit=5):
#   """
#   Get the minimum number of binds that connect two atoms.
#   Stops at a specified limit (and returns None if not within it)
#
#   .. describe:: Input
#
#   MolSystem.Atom, MolSystem.atom, Int
#
#   .. describe:: Output
#
#   Int
#   """
#
#   num = 0
#   atoms = {atom1}
#
#   while atom2 not in atoms:
#     if num > limit:
#       return None
#
#     atoms2 = atoms.copy()
#
#     for atom in atoms2:
#       atoms.update(getBoundAtoms(atom))
#
#     num += 1
#
#   return num

# def areAtomsTocsyLinked(atom1, atom2):
#   """
#   Determine if two atoms have a connectivity that may be observable in a TOCSY experiment
#
#   .. describe:: Input
#
#   MolSystem.Atom, MolSystem.atom
#
#   .. describe:: Output
#
#   Boolean
#   """
#
#   if not hasattr(atom1, 'tocsyDict'):
#     atom1.tocsyDict = {}
#   elif atom2 in atom1.tocsyDict:
#     return atom1.tocsyDict[atom2]
#
#   if not hasattr(atom2, 'tocsyDict'):
#     atom2.tocsyDict = {}
#   elif atom2 in atom2.tocsyDict:
#     return atom2.tocsyDict[atom1]
#
#   chemAtom1 = atom1.chemAtom
#   chemAtom2 = atom2.chemAtom
#   element1  = chemAtom1.elementSymbol
#   element2  = chemAtom2.elementSymbol
#
#   if element1 != element2:
#     boolean = False
#
#   elif areAtomsBound(atom1, atom2):
#     boolean = True
#
#   else:
#
#     residue1 = atom1.residue
#     residue2 = atom2.residue
#
#     if residue1 is not residue2:
#       boolean = False
#
#     else:
#       atomsA = {atom1}
#       boolean = True
#       while atom2 not in atomsA:
#         atomsB = atomsA.copy()
#
#         for atomB in atomsB:
#           for atom3 in getBoundAtoms(atomB):
#             if atom3.residue is not residue1:
#               continue
#
#             if element1 == 'H':
#               if atom3.chemAtom.elementSymbol != 'H':
#                 for atom4 in getBoundAtoms(atom3):
#                   if atom4.chemAtom.elementSymbol == 'H':
#                     break
#                 else:
#                   continue
#
#             if atom3.chemAtom.elementSymbol == element1:
#               if not hasattr(atom3, 'tocsyDict'):
#                 atom3.tocsyDict = {}
#
#               atom1.tocsyDict[atom3] = True
#               atom3.tocsyDict[atom1] = True
#
#             atomsA.add(atom3)
#
#         if atomsA == atomsB: # Nothing more to add and atom2 not in linked set
#           boolean = False
#           break
#
#   atom1.tocsyDict[atom2] = boolean
#   atom2.tocsyDict[atom1] = boolean
#   return boolean


def fetchStdResNameMap(project:'MemopsRoot', reset:bool=False, debug:bool=False):
  """ fetch dict of {residueName:(molType,ccpCode)},
  using cached value if present and not reset.

  NBNB TBD Add naming variants from ChemComp naming systems
  """

  chemCompOverview = ChemCompOverview.chemCompOverview
  obsoleteChemComps = ObsoleteChemComps.obsoleteChemCompData

  logger = project._logger

  if hasattr(project, '_residueName2chemCompId') and not reset:
    return project._residueName2chemCompId
  else:
    result = project._residueName2chemCompId = {}
    rejected = {}
    result.update(cifCodeRemap)

  # for molType, ccpCode in (result.values()):
  #   if ccpCode in chemCompOverview[molType]:
  #     print ('\t'.join(("CPRE-FOUND", molType, ccpCode)))
  #   else:
  #     print ('\t'.join(("CPRE-MISS", molType, ccpCode)))
  #
  # for molType,dd in sorted(chemCompOverview.items()):
  #   print ("CIF-TOTAL-%s %s" % (molType, len(dd)))


  # print ("CIF-TOTAL %s" % sum(len(x) for x in chemCompOverview.values()))

  remapped = {}
  nFound = 0
  for molType in molTypeOrder:

    # Add data for all chemComps from overview
    for ccpCode,tt in reversed(sorted(chemCompOverview[molType].items())):
      nFound += 1
      # NB done in reversed order to ensure Xyz takes precedence over XYZ
      cifCode = tt[1]
      dd = obsoleteChemComps.get(cifCode)

      if dd:
        altCode = dd['cifCode']
        if altCode is None:
          # cifCode is obsoleted. Skip it.
          # print("CIF-SKIP\t%s\t%s\t%s\t%s\t%s\t%s\t%s"
          #       % (molType, dd['shortType'], dd['longType'], ccpCode, tt[0] or '-', tt[1] or '-', tt[2] or '-'))
          rejected[molType, ccpCode] = None

        else:
          # Remaps are handled in another loop
          remapped[(molType, ccpCode)] = (cifCode, altCode)
      else:

        # Dummy value to allow shared diagnostics printout
        val = ('-', '-')

        if not cifCode:
          # no cifCode - skip. debug message
          rejected[molType, ccpCode] = cifCode
          ccId = ccpCodeRemap.get(molType, {}).get(ccpCode)
          if ccId:
            val = ccId
            message = 'CIF-CCP-REMAP'
          else:
            message = 'CIF-NO'

        elif cifCode != cifCode.upper():
          # cifCode is not upperCase - skip. debug message
          message = 'CIF-LOW'
          rejected[molType, ccpCode] = cifCode
        else:
          locif = cifCode[0] + cifCode[1:].lower()
          val = result.get(cifCode) or result.get(locif)
          if val is None:
            # New value. Set the map
            val = result[cifCode] = result[locif] =(molType, ccpCode)
            message = 'CIF-OK'

            # if ccpCode not in result:
              # ccp code not in result. Debug message
              # print("\t".join ('CCP-MISS', molType, ccpCode, val[0], val[1],
              #                                tt[0] or '-', tt[1] or '-', tt[2] or '-') )
          else:
            # Value was already set

            if val[0] == molType and val[1] == ccpCode:
              # This one was set up front
              message = 'CIF-PRESET'

            elif val[1] == cifCode and val[1] != locif:
              # ccpCode was UPPER-CASE
              # replace UPPERCASE ccpCode with mixed-case
              if molType == val[0]:
                result[cifCode] = result[locif] = (molType, ccpCode)
                rejected[val[0], val[1]] = cifCode

                # Debug messages:
                if ccpCode.upper() == val[1].upper():
                  message = 'CIF-REPL-INTRA'
                else:
                  message = 'CIF-REPL-CLASH1'

              elif molType == 'other' and val[0] != 'other':
                message = 'CIF-CLASH-OTHER'
                rejected[molType, ccpCode] = cifCode

              else:
                message = 'CIF-REPL-CLASH2'
                rejected[molType, ccpCode] = cifCode

            else:
              # Simple cifCode clash. Ignore and set debug messages
              if molType == val[0]:
                if ccpCode.upper() == val[1].upper():
                  message = 'CIF-INTRA'
                else:
                  message = 'CIF-CLASH1'
              elif molType == 'other' and val[0] != 'other':
                message = 'CIF-OTHER'
              else:
                message = 'CIF-CLASH2'
              rejected[molType, ccpCode] = cifCode

        #   # Print out debug messages
        # print("\t".join((message, molType, ccpCode, val[0], val[1],
        #                  tt[0] or '-', tt[1] or '-', tt[2] or '-')))
        #
        # if len(ccpCode) == 5 and ccpCode.startswith('D-'):
        #   # D- amino acid - special case.
        #   # for now add ccpCode as extra alias
        #   print("\t".join(('CCP-D-Xyz', molType, ccpCode,val[0], val[1],
        #                    tt[0] or '-', tt[1] or '-', tt[2] or '-')))
          # result[ccpCode] = val


  # print("CIF-nFound %s" % nFound)

  for ccId, codes in sorted(remapped.items()):
    cifCode, altCode = codes
    val = result.get(altCode)
    if val is None:
      pass
      # print('\t'.join(("CIF-REMAP-ERROR1", ccId[0], ccId[1], cifCode, altCode)))
    else:
      locif = cifCode[0] + cifCode[1:].lower()
      result[cifCode] = result[locif] = val
      # print('\t'.join(("CIF-REMAP-OK", ccId[0], ccId[1], cifCode, altCode, val[0], val[1])))
    rejected[ccId] = cifCode


  if debug:
    # for tt, cifCode in sorted(rejected.items()):
    #   print("  %s:%s,  # REJECTED" % (repr(tt), repr(cifCode)))

    # Check for upper-case ccpCodes remaining
    # for tag,val in sorted(result.items()):
      # if val[1][1:] !=  val[1][1:].lower():
      #   print("CCP-UPPER\t%s\t%s\t%s" % (val[0], val[1], tag))

    # check for unused ChemComps
    for chemComp in project.sortedChemComps():
      cifCode = chemComp.code3Letter
      ccpCode = chemComp.ccpCode
      molType = chemComp.molType
      val = result.get(ccpCode)
      ccId = (chemComp.molType, ccpCode)

      # Debug output checking ccpCode
      message = None
      if not val:
        val = (chemComp.code1Letter, cifCode)
        message = "CHEM-MISS"
      elif molType != val[0]:
        message = "CHEM-TYPE-CLASH"
      elif ccpCode != val[1]:
        message = "CHEM-CODE-CLASH"
      else:
        message = "CHEM-OK"

      # if message is not None:
      #   print ("\t".join(str(x) for x in (message, molType, ccpCode, val[0], val[1], cifCode)))

      # Debug output checking ccpCode
      val = result.get(cifCode)
      message = None
      if not val:
        val = (chemComp.code1Letter, cifCode)
        message = "CCIF-MISS"
      elif molType != val[0]:
        message = "CCIF-TYPE-CLASH"
      elif ccpCode != val[1]:
        message = "CCIF-CODE-CLASH"
      else:
        message = "CCIF-OK"

      # if message is not None:
      #   print ("\t".join(str(x) for x in (message, molType, ccpCode, val[0], val[1], cifCode)))


    tags = set()
    # get sysNames
    for namingSystem in chemComp.namingSystems:
      for sysName in namingSystem.chemCompSysNames:
        tags.add(sysName.sysName)

    # set additional synonyms
    for tag in tags:
      prevId = result.get(tag)

      if prevId is None:

        if len(tag) == 1:
          pass
         # print ("CINFO8\tRejecting one-letter synonym\t%s from ChemComp %s:%s"
         #         % (tag, cifCode, val))

        elif ccId == val:
          # print ("CINFO9\tAdding new ccpCode synonym\t%s from ChemComp %s:%s"
          #        % (tag, cifCode, ccId))

          result[tag] = val
        #
        # else:
        #   print ("CWARNING\tclash1\tfor %s chemComp %s v. cifCode %s:%s"
        #         % (tag, ccId, cifCode,  val))

      # elif prevId != val:
      #   print ("CWARNING\tclash2\tfor %s chemComp %s, %s v. cifCode %s:%s"
      #         % (tag, ccId, prevId, cifCode,  val))
  #
  return result

#
# def printCcpCodeStats(project):
#
#   chemCompOverview = ChemCompOverview.chemCompOverview
#
#   for molType in molTypeOrder:
#
#     current = chemCompOverview[molType]
#
#     # Add data for all chemComps from overview
#     for ccpCode,tt in sorted(current.items()):
#
#       code1Letter, cifCode, info = tt[:3]
#       code1Letter = code1Letter or '-'
#       ccpUpper = ccpCode.upper()
#       # cifCode test
#       if not cifCode:
#         print ("CIF NONE  %s %s %s %s %s" % (molType, ccpCode, code1Letter, cifCode, info))
#         continue
#       elif cifCode != cifCode.upper():
#         print ("CIF LOWER %s %s %s %s %s" % (molType, ccpCode, code1Letter, cifCode, info))
#         continue
#       else:
#         print ("CIF UPPER %s %s %s %s %s" % (molType, ccpCode, code1Letter, cifCode, info))
#
#       cifMixed = cifCode[0] + cifCode[1:].lower()
#
#       if ccpUpper == cifMixed:
#         ss1 = 'CCP BOTH'
#         ss2 = 'THESAME'
#       elif ccpCode == cifCode:
#         ss1 = 'CCP UPPER'
#         ss2 = (cifMixed in current and 'DOUBLE') or 'SINGLE'
#       elif ccpCode == cifMixed:
#         ss1 = 'CCP MIXED'
#         ss2 = (ccpUpper in current and 'DOUBLE') or 'SINGLE'
#       else:
#         ss1 = 'CCP OTHER'
#         ss2 = (cifCode in current and 'HASCIF') or 'NOTCIF'
#
#       cifclash = '-' + ','.join(x for x,dd in sorted(chemCompOverview.items())
#                           if x != molType  and cifCode in dd)
#       mixClash = '-'
#       if cifMixed != cifCode:
#         mixClash += ','.join(x for x,dd in sorted(chemCompOverview.items())
#                              if x != molType  and cifMixed in dd)
#       ccpClash = '-'
#       if ccpCode != cifCode:
#         ccpClash += ','.join(x for x,dd in sorted(chemCompOverview.items())
#                              if x != molType  and ccpCode in dd)
#
#       print(ss1, ss2,molType, ccpCode, code1Letter, cifCode, cifclash, mixClash, ccpClash, info )

# def _parseObsoleteChemCompTable(stream):
#   result = {}
#   for line in stream:
#     ll = line.split()
#     ll = [ll[0], ll[1], ' '.join(ll[2:-2]), ll[-2], ll[-1]]
#     ll = [x if x != 'NONE' else None for x in ll]
#     result[ll[0]] = {'cifCode':ll[-1], 'shortType':ll[1], 'typeCode':ll[-2],  'longType':ll[2]}
#   return result


if __name__ == '__main__':
  from ccpncore.util import Io as ioUtil
  project = ioUtil.newProject('ChemCompNameTest')
  # printCcpCodeStats(project)
  dd = fetchStdResNameMap(project, reset=True, debug=True)
  for key,val in sorted(dd.items()):
    print ("%s  %s  %s" % (key, val[0], val[1]))
  # import json
  # data = _parseObsoleteChemCompTable(open('/home/rhf22/rhf22/Dropbox/RHFnotes/ChemComp/ResidueNameMap3.txt'))
  # print(json.dumps(data, sort_keys=True, indent=4))
