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

from ccpncore.util import Logging
from ccpncore.memops.ApiError import ApiError
from ccpncore.api.ccp.molecule import Molecule
from ccpncore.util import CopyData
from ccpncore.lib.chemComp import Io as chemCompIo

###from ccp.general.Io import getChemComp

#################################################################
#
# Molecule creation
#
##################################################################

def makeMolecule(project, molType, sequence, molName=None, startNum=1, isCyclic=False):

  """Descrn: Makes Molecule for a given sequence

     Inputs: Project, Word (ChemComp.molType), List of Words (ChemComp.CcpCode),
     String ( Ccp.Molecule.Molecule.name) Int (first MolResidue.seqCode)

     Output: Molecule
  """

  if not molName:
    i = 1
    molName = 'Molecule %d' % i
    while project.findFirstMolecule(name=molName):
      i += 1
      molName = 'Molecule %d' % i
 
  molecule =  project.newMolecule(name=molName)

  try:
    addMolResidues(molecule, molType, sequence, startNum, isCyclic)
  except ApiError as e:
    try:
      molecule.delete()
    except:
      pass
    raise e

  return molecule

def addMolResidues(molecule, molType, sequence, startNum=1, isCyclic=False):
  """Descrn: Makes MolResidues for a given sequence in a new or specified Molecule
     Inputs: Ccp.Molecule.Molecule, Word (ChemComp.molType), List of Words (ChemComp.CcpCode),
             Ccp.Moleule.Molecule, String ( Ccp.Molecule.Molecule.name)
             Int (first MolResidue.seqCode)
     Output: List of Ccp.Molecule.MolResidues
  """
  
  if not sequence:
    return []
  
  oldMolResidues = molecule.molResidues
  if oldMolResidues:
    nn = max([x.seqCode for x in oldMolResidues]) + 1
    startNum = max(startNum, nn)
  
  if len(sequence) > 1 and molType in ('protein','DNA','RNA'):
    # linear polymer
    
    seqInput = zip([molType]*len(sequence),sequence)
    molResidues = makeLinearSequence(molecule, seqInput, seqCodeStart=startNum, isCyclic=isCyclic)
  
  else:
    # not linear polymer
  
    molResidues = []
    
    project = molecule.root
    for i in range(len(sequence)):
      chemComp = chemCompIo.getChemComp(project, molType, sequence[i])
      if chemComp:
        chemCompVar  = chemComp.findFirstChemCompVar(linking='none') or chemComp.findFirstChemCompVar() # just a default
        descriptor   = chemCompVar.descriptor
        linking      = chemCompVar.linking

        molResidue   = molecule.newMolResidue(seqCode=i+startNum, chemComp=chemComp, linking=linking, descriptor=descriptor)
        molResidues.append(molResidue)

      else:
        # TBD: should be logging
        project._logger.warning('Warning: Residue code %s cannot be found for molecule type %s.'
                                % (sequence[i],molType))
  
  return molResidues
  
  
def makeLinearSequence(molecule, sequence, seqCodeStart=1, isCyclic=False):
  """Descrn: Add residues to molecule. Fast method, which uses 'override' mode.
             sequence is a list of (molType,ccpCode) tuples - so can make mixed-type
             linear polymers; All ChemComps must have next and prev links to fit a 
             linear polymer seqCodes start from seqCodeStart, serial from next 
             free serial (or 1)
     Inputs: Molecule.molecule, List of Tuples of Strings (molType, ccpCode), Int, Boolean
     Output: List of Molecule.MolResidues
  """
  logger = molecule.root._logger
  
  if len(sequence) < 2:
    raise ApiError("Sequence %s too short for function" % sequence)
  
  # set up
  project = molecule.root
  chemCompData = {}
  
  molResidues = []
  molResLinkEnds = []
  molResLinks = []
  
  # get starting serial
  serialDict = molecule.__dict__.setdefault('_serialDict', {})
  serial = serialDict.get('molResidues', 0)
  
  root = molecule.root
  root.__dict__['override'] = True
  
  ###if 1:
  try:
    # first residue
    if isCyclic:
      seqCode = seqCodeStart - 1
      doSequence = sequence
    else:
      seqCode = seqCodeStart
      serial += 1
      doSequence = sequence[1:-1]
 
      molType, ccpCode = sequence[0]
      molResData, otherLinkCodes = _getLinearChemCompData(project, molType,
                                                        ccpCode, 'start')
      
      molResidue = molecule.newMolResidue(seqCode=seqCode, serial=serial,
                                          **molResData)                                         
      molResidues.append(molResidue)
      
      if otherLinkCodes:
        for linkCode in otherLinkCodes:
          # TBC these mostly seem to exist already...
          if not molResidue.findFirstMolResLinkEnd(linkCode=linkCode):
            linkEnd = molResidue.newMolResLinkEnd(linkCode=linkCode)
            molResLinkEnds.append(linkEnd)

    # middle residues
    for seqTuple in doSequence:
      molType,ccpCode = seqTuple
      seqCode += 1
      serial += 1
      if seqTuple in chemCompData:
        molResData,otherLinkCodes = chemCompData[seqTuple]
      else:
        molResData,otherLinkCodes = _getLinearChemCompData(project, molType,
                                                          ccpCode, 'middle')
        chemCompData[seqTuple] = (molResData,otherLinkCodes)
              
      molResidue = molecule.newMolResidue(seqCode=seqCode, serial=serial,
                                          **molResData)                                         
      molResidues.append(molResidue)
      
      if otherLinkCodes:
        for linkCode in otherLinkCodes:
          # TBC these mostly seem to exist already...
          if not molResidue.findFirstMolResLinkEnd(linkCode=linkCode):
            linkEnd = molResidue.newMolResLinkEnd(linkCode=linkCode)
            molResLinkEnds.append(linkEnd)
 
    # last residue
    if not isCyclic:
      seqCode += 1
      serial += 1
      (molType,ccpCode) = sequence[-1]
      molResData,otherLinkCodes = _getLinearChemCompData(project, molType,
                                                        ccpCode, 'end')
                                                        
      molResidue = molecule.newMolResidue(seqCode=seqCode, serial=serial,
                                          **molResData)                                         
      molResidues.append(molResidue)
      
      if otherLinkCodes:
        for linkCode in otherLinkCodes:
          # TBC these mostly seem to exist already...
          if molResidue.findFirstMolResLinkEnd(linkCode=linkCode):
            continue
          
          linkEnd = molResidue.newMolResLinkEnd(linkCode=linkCode)
          molResLinkEnds.append(linkEnd)
 
    # make links
    for second in range(1,len(sequence)):
      first = second -1
      nextLinkEnd = molResidues[first].findFirstMolResLinkEnd(linkCode='next')
      molResLinkEnds.append(nextLinkEnd)
      prevLinkEnd = molResidues[second].findFirstMolResLinkEnd(linkCode='prev')
      molResLinkEnds.append(prevLinkEnd)
      molResLinks.append(
       molecule.newMolResLink(molResLinkEnds=[nextLinkEnd,prevLinkEnd])
      )
 
    if isCyclic:
      # cyclising link
      nextLinkEnd = molResidues[-1].findFirstMolResLinkEnd(linkCode='next')
      molResLinkEnds.append(nextLinkEnd)
      prevLinkEnd = molResidues[0].findFirstMolResLinkEnd(linkCode='prev')
      molResLinkEnds.append(prevLinkEnd)
      molResLinks.append(
       molecule.newMolResLink(molResLinkEnds=[nextLinkEnd,prevLinkEnd])
      )
    
    # final validity check
    molecule.checkAllValid()

  except:
    # clean up
    try:
      while molResLinks:
        molResLink = molResLinks.pop()
        molResLink.delete()
      while molResidues:
        molResidue = molResidues.pop()
        molResidue.delete()
    except:
      logger.error("Error in clean-up after precious error")

  finally:
    # reset override and set isModified
    root.__dict__['override'] = False
    molecule.__dict__['isModified'] = True

    
  # call notifiers:
  for clazz, objs in (
   (Molecule.MolResidue, molResidues),
   (Molecule.MolResLinkEnd, molResLinkEnds),
   (Molecule.MolResLink, molResLinks),
  ):
    notifiers = clazz._notifies.get('__init__')
    if notifiers:
      for notify in notifiers:
        for obj in objs:
          notify(obj)
 
  return molResidues
  
  
def _getLinearChemCompData(project, molType, ccpCode, linking):
  """Descrn: Implementation function, specific for makeLinearSequence()
     Inputs: Project object, and desired molType, ccpCode, linking (all strings)
     Output: (dd,ll) tuple where dd is a dictionary for passing to the 
              MolResidue crreation (as **dd), and ll is a list of the linkCodes
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



def setMolResidueCcpCode(molResidue,ccpCode):
  """Descrn: Replaces a molResidue with an equivalently connected one (if possible) with a different ccpCode
     Inputs: Ccp.Molecule.MolResidue, Word (Ccp.Molecule.MolResidue.ccpCode)
     Output: Ccp.Molecule.MolResidue
  """
  
  if molResidue.ccpCode == ccpCode:
    return molResidue

  chemComp = molResidue.root.findFirstChemComp(ccpCode=ccpCode)
  if not chemComp:
    return
  
  chemCompVar = chemComp.findFirstChemCompVar(descriptor=molResidue.descriptor,
                                              linking=molResidue.linking)
  if not chemCompVar:
    chemCompVar = chemComp.findFirstChemCompVar(linking=molResidue.linking)
    
  if chemCompVar:
    molResidue = setMolResidueChemCompVar(molResidue,chemCompVar)
  
  return molResidue

def setMolResidueChemCompVar(molResidue,chemCompVar):
  """Descrn: Replaces a molResidue with an equivalently connected one (if possible) 
             with a different chemChemCompVar. This is a very naughty function 
             which bypasses the API - but it does check molecule validity at the end.

     Inputs: Ccp.Molecule.MolResidue, Ccp.ChemComp.ChemCompVar

     Output: Ccp.Molecule.MolResidue

     NBNB TBD looks broken
  """
  
  if molResidue.chemCompVar is chemCompVar:
    return molResidue
  
  molecule     = molResidue.molecule
  # seqCode      = molResidue.seqCode
  linking      = chemCompVar.linking
  descriptor   = chemCompVar.descriptor 
  chemComp = chemCompVar.chemComp
    
  links = []
  for linkEnd in molResidue.molResLinkEnds:
    if linkEnd.molResLink:
      # codes = [linkEnd.linkCode]
      for linkEnd2 in linkEnd.molResLink.molResLinkEnds:
        if linkEnd2 is not linkEnd:
          links.append( [linkEnd.linkCode, linkEnd2] )
          linkEnd.molResLink.delete()

  if molResidue.chemComp is not chemComp:
    molResidue.__dict__['chemComp'] = chemComp

  molResidue.__dict__['descriptor'] = descriptor
  molResidue.__dict__['linking'] = linking

  linkCodes = [] 
  for linkEnd in chemCompVar.linkEnds:
    linkCode = linkEnd.linkCode
    linkCodes.append(linkCode)
    if not molResidue.findFirstMolResLinkEnd(linkCode=linkCode):
      molResidue.newMolResLinkEnd(linkCode=linkCode)
  
  for linkEnd in molResidue.molResLinkEnds:
    if linkEnd.linkCode not in linkCodes:
      link = linkEnd.molResLink
      if link:
        link.delete()
      linkEnd.delete()  
  
  for (linkCodeA,linkEndB) in links:
    linkEndA = molResidue.findFirstMolResLinkEnd(linkCode=linkCodeA)
    if linkEndA and linkEndB:
      molecule.newMolResLink(molResLinkEnds=(linkEndA,linkEndB))
    
  molecule.checkAllValid(complete=True)
 
  return molResidue



#################################################################
#
# Chain modification
#
##################################################################

def nextChainCode(molSystem):
  """Descrn: Gives the first unused chain code for a molSystem, starting as close to 'A' as possible 
     Inputs: Ccp.MolSystem.MolSystem
     Output: Word (Ccp.MolSystem.Chain.code)
  """

  chains = molSystem.sortedChains()
       
  if not chains:
    return 'A'
    
  codes = []
  for chain in chains:
    codes.append(chain.code)
    
  code = 'A'
  while code in codes:
    i = ord(code)
    i += 1
    j = i - ord('A')
    if j  >= 26:
      code = chr(ord('A')+int(j/26)) + chr(ord('A')+int(j % 26))
    else:
      code = chr(i)

  return code
  
  
def makeChain(molSystem,molecule,code=None):
  """Descrn: Make a molSystem chain based upon an input molecule template
     Inputs: Ccp.MolSystem.MolSystem, Ccp.Molecule.Molecule, Word
     Output: Ccp.MolSystem.Chain
  """

  if code is None:
    code = nextChainCode(molSystem)
  
  chain = molSystem.newChain(code=code, molecule=molecule)
    
  if len(molecule.molResidues) == 1:
    details = molecule.findFirstMolResidue().chemComp.name
  else:
    details = molecule.seqString
  
  if details:
    if len(details) > 10:
      details = details[:10] + '...'
 
    chain.setDetails(details)
  
  return chain
  

def renumberChainSeqCodes(chain, firstSeqCode=1, skipZeroSeqCode=False):

  seqCode = firstSeqCode
  for residue in chain.sortedResidues():
    if seqCode == 0 and skipZeroSeqCode:
      seqCode = 1
    residue.seqCode = seqCode
    seqCode += 1
    
    
def copyMolecule(molecule, newName=None):
  """Make a new molecule based upon the sequence of an existing one
  .. describe:: Input
  
  Molecule.Molecule

  .. describe:: Output
  
  Molecule.Molecule
  """
  
  project = molecule.root
  i = len(project.molecules) + 1
  newName = newName or 'Molecule %d' % i
  newMolecule = CopyData.copySubTree(molecule, project, topObjectParameters={'name':newName,},
                                     maySkipCrosslinks=1 )
  
  return newMolecule


def expandMolSystemAtoms(chain):
  """Add extra atoms to chain corresponding to AtomSets
  Called on V2 upgrade, or on finalisation of chain."""

  # Set elementSymbol and add missing atoms (lest something breaks lower down)
  for residue in chain.sortedResidues():
    chemCompVar = residue.chemCompVar
    for chemAtom in chemCompVar.findAllChemAtoms(className='ChemAtom'):
      atom = residue.findFirstAtom(name=chemAtom.name)
      if atom is None:
        residue.newAtom(name=chemAtom.name, atomType='single',
                        elementSymbol=chemAtom.elementSymbol)
      else:
        atom.elementSymbol = chemAtom.elementSymbol

  # Set boundAtoms for existing atoms within residue
  for residue in chain.sortedResidues():
    chemCompVar = residue.chemCompVar
    for atom in residue.atoms:
      chemAtom = chemCompVar.findFirstChemAtom(name=atom.name, className='ChemAtom')
      if chemAtom is not None:
        boundChemAtoms = set(x for y in chemAtom.chemBonds for x in y.chemAtoms)
        for boundChemAtom in boundChemAtoms:
          if boundChemAtom is not chemAtom and boundChemAtom.className == 'ChemAtom':
            boundAtom = residue.findFirstAtom(name=boundChemAtom.name)
            if boundAtom is not None and boundAtom not in atom.boundAtoms:
              atom.addBoundAtom(boundAtom)

    # Add boundAtoms for MolResLinks
      for molResLink in chain.molecule.molResLinks:
        ff = chain.findFirstResidue
        atoms = [ff(seqId=x.molResidue.serial).findFirstAtom(name=x.linkEnd.boundChemAtom.name)
                 for x in molResLink.molResLinkEnds]
        if atoms[1] not in atoms[0].boundAtoms:
          atoms[0].addBoundAtom(atoms[1])

    # Add boundAtoms for MolSystemLinks
    for linkEnd in residue.sortedMolSystemLinkEnds():
      molSystemLink = linkEnd.molSystemLink
      atoms = [x.residue.findFirstAtom(name=x.linkEnd.boundChemAtom.name)
               for x in molSystemLink.molSystemLinkEnds]
      if atoms[1] not in  atoms[0].boundAtoms:
        atoms[0].addBoundAtom(atoms[1])

    # NB we do NOT add boundAtoms for NonCovalentBonds

    # Add extra atoms corresponding to ChemAtomSets
    chemCompVar = residue.chemCompVar
    # AQUA is good on pseudoatom names
    pseudoNamingSystem = chemCompVar.chemComp.findFirstNamingSystem(name='AQUA')

    # Map from chemAtomSet to equivalent Atom
    casMap = {}

    # map from chemAtomSet.name to nonStereo names
    nonStereoNames = {}

    for chemAtomSet in chemCompVar.chemAtomSets:

      # get nests of connected chemAtomSets
      if not chemAtomSet.chemAtomSet:
        # get nested chemAtomSets, starting at topmost set
        localSets = [chemAtomSet]
        for cas in localSets:
          localSets.extend(cas.chemAtomSets)

        # Process in reverse order, guaranteeing that contained sets are always ready
        for cas in reversed(localSets):
          chemContents = cas.sortedChemAtoms()
          # NB the fact that chemAtoms and chemAtomSets are sorted (by name) is used lower down
          if chemContents:
            # contents are real atoms
            components = [residue.findFirstAtom(name=x.name) for x in chemContents]
          else:
            chemContents = cas.sortedChemAtomSets()
            components = [casMap[x] for x in chemContents]
          elementSymbol = chemContents[0].elementSymbol

          commonBound = frozenset.intersection(*(x.boundAtoms for x in components))

          # Add 'equivalent' atom
          newName = cas.name.replace('*', '%')
          newAtom = residue.newAtom(name=newName, atomType='equivalent',
                                    elementSymbol=elementSymbol,atomSetName=cas.name,
                                    components=components, boundAtoms=commonBound)
          casMap[cas] = newAtom

          # NBNB the test on '#' count is a hack to exclude Tyr/Phe HD#|HE#
          hackExclude = newName.count('%') >= 2

          # Add 'pseudo' atom for proton
          if elementSymbol == 'H':
            newName = None
            if pseudoNamingSystem:
              atomSysName = pseudoNamingSystem.findFirstAtomSysName(atomName=cas.name,
                                                                    atomSubType=cas.subType)
              if atomSysName:
                newName = atomSysName.sysName

            if newName is None:
              # No systematic pseudoatom name found - make one.
              # NBNB this will give names like MD1, QG1, MD2 for cases like Ile delta,
              # where the standard says MD, QG, MG.
              # But all the standard cases are covered by the pseudoNamingSystem ('AQUA')
              # Can we get away with this, or do we have to rename on a per-residue basis
              # for the special cases?
              startChar = 'Q'
              if (len(cas.chemAtoms) == 3 and cas.isEquivalent
                  and components[0].findFirstBoundAtom().elementSymbol == 'C'):
                if len(set(x.findFirstBoundAtom() for x in components)) == 1:
                  # This is a methyl group
                  # The second 'if' is likely unnecessary in practice, but let us be correct here
                  startChar = 'M'

              newName = startChar + cas.name.strip('*')[1:]

            if len(newName) > 1:
              # Make pseudoatom, except for 'H*'
              residue.newAtom(name=newName, atomType='pseudo', elementSymbol=elementSymbol,
                              atomSetName=cas.name, components=components, boundAtoms=commonBound)

          # Add 'nonstereo atoms
          if not cas.isEquivalent and len(components) == 2 and not hackExclude:
            # NB excludes cases with more than two non-equivalent components
            # But then I do not think there are any in practice.
            # and anyway we do not have a convention for them.
            nonStereoNames[cas.name] = newNames = []
            starpos = cas.name.find('*')
            for ii,component in enumerate(components):
              # NB components are sorted by key, which means by name
              newChar = 'XY'[ii]
              ll = list(component.name)
              ll[starpos] = newChar
              newName = ''.join(ll)
              newNames.append(newName)
              if residue.findFirstAtom(name=newName) is not None:
                print ("WARNING, new atom already exists: %s %s %s %s"
                       % (residue.chain.code, residue.seqId, residue.ccpCode, newName))
              else:
                residue.newAtom(name=newName, atomType='nonstereo', elementSymbol=elementSymbol,
                                atomSetName=cas.name, components=components, boundAtoms=commonBound)


    # NBNB Now we need to set boundAtoms for non-single Atoms.
    # We need to set:
    # HG*-CG* etc.
    # HGX*-CGX etc. - can be done from previous by char substitution
    eqvTypeAtoms = [x for x in residue.sortedAtoms() if x.atomType == 'equivalent']
    for ii,eqvAtom in enumerate(eqvTypeAtoms):
      components = eqvAtom.sortedComponents()
      for eqvAtom2 in eqvTypeAtoms[ii+1:]:
        components2 = eqvAtom2.sortedComponents()
        if len(components) == len(components2):
          if all((x in components2[jj].boundAtoms) for jj,x in enumerate(components)):
            # All components of one are bound to a component of the other
            # NB this relies on the sorted components being ordered to match the bonds
            # but you should expect that both cases are sorted by branch index
            # CG1,CG2 matching HG1*,HG2* etc.

            # Add bond between equivalent atoms
            eqvAtom.addBoundAtom(eqvAtom2)

            nsNames1 = nonStereoNames.get(eqvAtom.atomSetName)
            nsNames2 = nonStereoNames.get(eqvAtom2.atomSetName)
            if nsNames1 and nsNames2:
              # Non-stereoAtoms are defined for both - add X,Y bonds
              # NB We rely on names being sorted (X then Y in both cases)
              for kk,name in enumerate(nsNames1):
                atom2 = residue.findFirstAtom(name=nsNames2[kk])
                residue.findFirstAtom(name=name).addBoundAtom(atom2)

            break
