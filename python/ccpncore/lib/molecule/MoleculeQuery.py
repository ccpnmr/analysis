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
from ccpncore.util import Logging


###from ccp.util.LabeledMolecule import getIsotopomerSingleAtomFractions, getIsotopomerAtomPairFractions
###from ccp.util.LabeledMolecule import singleAtomFractions, atomPairFractions

###from ccp.util.NmrExpPrototype import longRangeTransfers

STANDARD_ISOTOPES = ['1H','13C','15N','31P','2H','29Si','19F','17O']

DEFAULT_ISOTOPES = {'H':'1H','C':'13C','N':'15N','P':'31P','Si':'29Si',
                    'F':'19F','O':'16O'}

molTypeOrder = ('protein', 'DNA', 'RNA', 'carbohydrate', 'other')

LINEAR_POLYMER_TYPES = ('protein', 'DNA', 'RNA')

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
  

def getBoundAtoms(atom):
  """Get a list of atoms bound to a given atom..
  .. describe:: Input

  MolSystem.Atom

  .. describe:: Output

  List of MolSystem.Atoms
  """

  if hasattr(atom, 'boundAtoms'):
    return atom.boundAtoms

  atoms    = []
  chemAtom = atom.chemAtom
  residue  = atom.residue

  chemAtomDict = {}
  for atom2 in residue.atoms:
    # Only atoms specific to ChemCompVar :-)
    chemAtomDict[atom2.chemAtom] = atom2

  for chemBond in chemAtom.chemBonds:
    for chemAtom2 in chemBond.chemAtoms:
      if chemAtom2 is not chemAtom:
        atom2 = chemAtomDict.get(chemAtom2)
        if atom2:
          atoms.append(atom2)

  linkEnd = residue.chemCompVar.findFirstLinkEnd(boundChemAtom=chemAtom)
  if linkEnd:
    molResLinkEnd = residue.molResidue.findFirstMolResLinkEnd(linkEnd=linkEnd)

    if molResLinkEnd:
      molResLink = molResLinkEnd.molResLink

      if molResLink:
        for molResLinkEnd2 in molResLink.molResLinkEnds:
          if molResLinkEnd2 is not molResLinkEnd:
            residue2 = residue.chain.findFirstResidue(molResidue=molResLinkEnd2.molResidue)

            if residue2:
              chemAtom2 = molResLinkEnd2.linkEnd.boundChemAtom
              atom2 = residue2.findFirstAtom(chemAtom=chemAtom2)

              if atom2:
                atoms.append(atom2)

            break

  atom.boundAtoms = atoms
  return atoms


def fetchStdResNameMap(project, reset:bool=False):
  """ fetch dict of {residueName:(molType,ccpCode)},
  using cached value if preeent and not resdet.
  """

  chemCompOverview = ChemCompOverview.chemCompOverview

  logger = project._logger

  if hasattr(project, '_residueName2chemCompId') and not reset:
    return project._residueName2chemCompId
  else:
    result = project._residueName2chemCompId = {}

  # Special cases:

  # Std DNA - keep one-letter ccpCode
  result['DA'] = result['Da'] = ('DNA', 'A')
  result['DC'] = result['Dc'] = ('DNA', 'C')
  result['DG'] = result['Dg'] = ('DNA', 'G')
  result['DI'] = result['Di'] = ('DNA', 'I')
  result['DU'] = result['Du'] = ('DNA', 'U')
  result['DT'] = result['Dt'] = ('DNA', 'T')

  # Std RNA - keep one-letter ccpCode
  result['5MU'] = result['5mu'] = result['RT'] =  result['Rt'] = ('RNA', 'T')

  # Set as RNA or other, to override DNA with similar name
  for tag in ('2at', '2bt', '2gt', '2nt', '2ot', '3me', 'Ap7', 'Atl', 'Boe', 'Car',
              'Eit', 'Fnu', 'Gmu', 'Lcc', 'Lcg', 'P2t', 'S2m', 'T2t', 'Tfe', 'Tln'):
    result[tag] = result[tag.upper()] = ['RNA', tag]

  result['Hob'] = result[''] = ('other', 'Hob')
  result['Xxx'] = result[''] = ('other', 'Xxx')

  # cifCodes to be replaced or skipped
  remapRemove = {
    '6CT':'T32',
    '6MC':'6ma',
    '6MT':'6ma',
    'B1P':'Aab',
    'DRT':'0dt',
    'DXN':'Dxd',
    'HDP':'Xtr',
    'I5C':'C38',
    'LCH':'Lcc',
    'CB2':'-skip',
    'DFC':'-skip',
    'DFG':'-skip',
    'LC':'-skip',
    'LG':'-skip',
    'LHU':'-skip',
    'PG7':'-skip',
    'PR5':'-skip',
  }

  nFound = 0
  print ("CIF-TOTAL %s" % sum(len(x) for x in chemCompOverview.values()))
  for molType in molTypeOrder:

    # Add data for all chemComps from overview
    for ccpCode,tt in reversed(sorted(chemCompOverview[molType].items())):
      # NB done in reversed order to ensure Xyz takes precedence over XYZ
      cifCode = tt[1]
      altCode = remapRemove.get(cifCode)

      if altCode == '-skip':
        # cifCode is obsoleted. kip it.
        print("CIF-SKIP\t%s\t%s\t%s\t%s\t%s"
              % (molType, ccpCode, tt[0] or '-', tt[1] or '-', tt[2] or '-'))
        continue

      elif altCode is not None:
        # cifCode is remapped - change to alternative code
        print("CIF-REMAP\t%s\t%s\t%s\t%s\t%s\t%s"
              % (molType, ccpCode, tt[0] or '-', tt[1] or '-', tt[2] or '-', altCode))
        cifCode = altCode.upper()
        ccpCode = altCode

      # Dummy value to allow shared diagoistics printout
      val = ('-', '-')

      if not cifCode:
        # no cifCode - skip. debug message
        message = 'CIF-NO'
      elif cifCode != cifCode.upper():
        # cifCode is not upperCase - skip. debug message
        message = 'CIF-LOW'
      else:
        locif = cifCode[0] + cifCode[1:].lower()
        val = result.get(cifCode) or result.get(locif)
        if val is None:
          # New value. Set the map
          val = result[cifCode] = result[locif] =(molType, ccpCode)
          message = 'CIF-OK'

          if ccpCode not in result:
            # ccp code not in result. Debug message
            print("\t".join( ('CCP-MISS', molType, ccpCode, val[0], val[1],
                                           tt[0] or '-', tt[1] or '-', tt[2] or '-') ))
        else:
          # Value was already set

          if val[1] == cifCode and val[1] != locif:
            # ccpCode was UPPER-CASE
            # replace UPPERCASE ccpCode with mixed-case
            if molType == val[0]:
              result[cifCode] = result[locif] = (molType, ccpCode)

              # Debug messages:
              if ccpCode.upper() == val[1].upper():
                message = 'CIF-REPL-INTRA'
              else:
                message = 'CIF-REPL-CLASH1'

            elif molType == 'other' and val[0] != 'other':
              message = 'CIF-CLASH-OTHER'

            else:
              message = 'CIF-REPL-CLASH2'

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

        # Print out debug messages
        print("\t".join((message, molType, ccpCode, val[0], val[1],
                         tt[0] or '-', tt[1] or '-', tt[2] or '-')))

        if len(ccpCode) == 5 and ccpCode.startswith('D-'):
          # D- amino acid - special case.
          # for now add ccpCode as extra alias
          print("\t".join(('CCP-D-Xyz', molType, ccpCode,val[0], val[1],
                           tt[0] or '-', tt[1] or '-', tt[2] or '-')))
          result[ccpCode] = val


  # Check for upper-case ccpCodes remaining
  for tag,val in sorted(result.items()):
    if val[1][1:] !=  val[1][1:].lower():
      print("CCP-UPPER\t%s\t%s\t%s" % (val[1], val[0], tag))

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

    if message is not None:
      print ("\t".join(str(x) for x in (message, molType, ccpCode, val[0], val[1], cifCode)))

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

    if message is not None:
      print ("\t".join(str(x) for x in (message, molType, ccpCode, val[0], val[1], cifCode)))


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
         print ("CINFO8 Rejecting one-letter synonym %s from ChemComp %s:%s"
                 % (tag, cifCode, val))

        elif ccId == val:
          print ("CINFO9 Adding new ccpCode synonym %s from ChemComp %s:%s"
                 % (tag, cifCode, ccId))

          result[tag] = val

        else:
          print ("CWARNING clash1 for %s chemComp %s v. cifCode %s:%s"
                % (tag, ccId, cifCode,  val))

      elif prevId != val:
        print ("CWARNING clash2 for %s chemComp %s, %s v. cifCode %s:%s"
              % (tag, ccId, prevId, cifCode,  val))

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


if __name__ == '__main__':
  from ccpncore.util import Io as ioUtil
  project = ioUtil.newProject('ChemCompNameTest')
  # printCcpCodeStats(project)
  fetchStdResNameMap(project, reset=True)