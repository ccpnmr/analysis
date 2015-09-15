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
"""Code for generating and modifying Molecules and MolSystems"""

from ccpncore.memops.ApiError import ApiError
from ccpncore.lib.chemComp import Io as chemCompIo


###from ccp.general.Io import getChemComp

#################################################################
#
# Molecule creation
#
##################################################################

def createMolecule(project, sequence:(list,str), molType:str='protein', name:str="Molecule",
                 startNumber:int=1, isCyclic=False):

  """Descrn: Makes Molecule for a given sequence

     Inputs: Project,List of Words (ChemComp.CcpCode), Word (ChemComp.molType), 
     String ( Ccp.Molecule.Molecule.name) Int (first MolResidue.seqCode)

     Output: Molecule
  """

  # ensure name is unique
  i = 0
  ss = name
  while project.findFirstMolecule(name=ss):
    i += 1
    ss = '%s%d' % (name,i)
  if ss != name:
    project._logger.warning(
    "CCPN molecule named %s already exists. New molecule has been named %s" %
    (name,ss))
  name = ss
 
  molecule =  project.newMolecule(name=name)

  try:
    if isinstance(sequence, str):
      molecule.extendOneLetterMolResidues(sequence, molType, startNumber, isCyclic)
    else:
      molecule.extendMolResidues(sequence, startNumber, isCyclic)
  except Exception as e:
    try:
      molecule.delete()
    except:
      pass
    raise e

  return molecule

  
  
def _getLinearChemCompData(project, molType, ccpCode, linking):
  """Descrn: Implementation function, specific for addLinearSequence()
     Inputs: Project object, and desired molType, ccpCode, linking (all strings)
     Output: (dd,ll) tuple where dd is a dictionary for passing to the 
              MolResidue creation (as **dd), and ll is a list of the linkCodes
              that are different from 'next' and 'prev'
  """
  
  seqLinks = []
  otherLinkCodes = []
  
  chemComp = project.findFirstChemComp(molType=molType, ccpCode=ccpCode)
  
  isOther = False
  if chemComp is None:
    isOther = True
    chemComp = project.findFirstChemComp(molType='other', ccpCode=ccpCode)

  if chemComp is None:
    chemComp = chemCompIo.getChemComp(project, molType, ccpCode)

  if chemComp is None:
    raise ApiError("No chemComp for %s residue %s" % (molType, ccpCode))
    
  chemCompVar = chemComp.findFirstChemCompVar(linking=linking, isDefaultVar=True) or \
                chemComp.findFirstChemCompVar(linking=linking)
  # Note requiring a default var is too strict - not always set for
  # imports from mol2/PDB etc

  if isOther and (chemCompVar is None):
    if linking == 'start':
      linkEnd = chemComp.findFirstLinkEnd(linkCode='next')
     
    elif linking == 'end':
      linkEnd = chemComp.findFirstLinkEnd(linkCode='prev')
    
    else:
      linkEnd = None
      
    if linkEnd:
      otherLinkCodes.append(linkEnd.linkCode)
      chemCompVar = chemComp.findFirstChemCompVar(isDefaultVar=True) or \
                    chemComp.findFirstChemCompVar()            
                
  if chemCompVar is None:
    raise ApiError("No ChemCompVar found for %s:%s linking %s" % (molType, ccpCode, linking))
  
  molResData = {'chemComp':chemComp, 'linking':chemCompVar.linking,
                'descriptor':chemCompVar.descriptor}
  
  for linkEnd in chemCompVar.linkEnds:
    code = linkEnd.linkCode
    
    if code in ('next','prev'):
      seqLinks.append(code)
    else:
      otherLinkCodes.append(code)
  
  if linking == 'start':
    if seqLinks and seqLinks != ['next']:
      raise ApiError("Linking 'start' must have just 'next' linkEnd")
      
  elif linking == 'end':
    if seqLinks and seqLinks != ['prev']:
      raise ApiError("Linking 'end' must have just 'prev' linkEnd ")
      
  elif linking != 'middle' or seqLinks not in (['next','prev'],['prev','next']):
    raise ApiError("Illegal linking %s with seqLinks %s" % (linking,seqLinks))
  
  return molResData, otherLinkCodes


#################################################################
#
# Molecule modification
#
##################################################################



# def setMolResidueCcpCode(molResidue,ccpCode):
#   """Descrn: Replaces a molResidue with an equivalently connected one (if possible) with a different ccpCode
#      Inputs: Ccp.Molecule.MolResidue, Word (Ccp.Molecule.MolResidue.ccpCode)
#      Output: Ccp.Molecule.MolResidue
#   """
#
#   if molResidue.ccpCode == ccpCode:
#     return molResidue
#
#   chemComp = molResidue.root.findFirstChemComp(ccpCode=ccpCode)
#   if not chemComp:
#     return
#
#   chemCompVar = chemComp.findFirstChemCompVar(descriptor=molResidue.descriptor,
#                                               linking=molResidue.linking)
#   if not chemCompVar:
#     chemCompVar = chemComp.findFirstChemCompVar(linking=molResidue.linking)
#
#   if chemCompVar:
#     molResidue = setMolResidueChemCompVar(molResidue,chemCompVar)
#
#   return molResidue
#
# def setMolResidueChemCompVar(molResidue,chemCompVar):
#   """Descrn: Replaces a molResidue with an equivalently connected one (if possible)
#              with a different chemChemCompVar. This is a very naughty function
#              which bypasses the API - but it does check molecule validity at the end.
#
#      Inputs: Ccp.Molecule.MolResidue, Ccp.ChemComp.ChemCompVar
#
#      Output: Ccp.Molecule.MolResidue
#
#      NBNB TBD looks broken
#   """
#
#   if molResidue.chemCompVar is chemCompVar:
#     return molResidue
#
#   molecule     = molResidue.molecule
#   # seqCode      = molResidue.seqCode
#   linking      = chemCompVar.linking
#   descriptor   = chemCompVar.descriptor
#   chemComp = chemCompVar.chemComp
#
#   links = []
#   for linkEnd in molResidue.molResLinkEnds:
#     if linkEnd.molResLink:
#       # codes = [linkEnd.linkCode]
#       for linkEnd2 in linkEnd.molResLink.molResLinkEnds:
#         if linkEnd2 is not linkEnd:
#           links.append( [linkEnd.linkCode, linkEnd2] )
#           linkEnd.molResLink.delete()
#
#   if molResidue.chemComp is not chemComp:
#     molResidue.__dict__['chemComp'] = chemComp
#
#   molResidue.__dict__['descriptor'] = descriptor
#   molResidue.__dict__['linking'] = linking
#
#   linkCodes = []
#   for linkEnd in chemCompVar.linkEnds:
#     linkCode = linkEnd.linkCode
#     linkCodes.append(linkCode)
#     if not molResidue.findFirstMolResLinkEnd(linkCode=linkCode):
#       molResidue.newMolResLinkEnd(linkCode=linkCode)
#
#   for linkEnd in molResidue.molResLinkEnds:
#     if linkEnd.linkCode not in linkCodes:
#       link = linkEnd.molResLink
#       if link:
#         link.delete()
#       linkEnd.delete()
#
#   for (linkCodeA,linkEndB) in links:
#     linkEndA = molResidue.findFirstMolResLinkEnd(linkCode=linkCodeA)
#     if linkEndA and linkEndB:
#       molecule.newMolResLink(molResLinkEnds=(linkEndA,linkEndB))
#
#   molecule.checkAllValid(complete=True)
#
#   return molResidue



  
  

  


