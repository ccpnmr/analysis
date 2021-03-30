import os
from os import path

from ccpnmr.chemBuild.general.Constants import LINK, ELEMENT_DATA, ELEMENT_DEFAULT
from ccpnmr.chemBuild.general.Constants import EQUIVALENT, NONSTEREO, VAR_TAG_ORDER

from ccpnmr.chemBuild.model.Compound import Compound
from ccpnmr.chemBuild.model.Variant import Variant
from ccpnmr.chemBuild.model.VarAtom import VarAtom
from ccpnmr.chemBuild.model.Atom import Atom
from ccpnmr.chemBuild.model.Bond import Bond, BOND_TYPE_VALENCES
from ccpnmr.chemBuild.model.AtomGroup import AtomGroup

def makeChemComp(compound,  ccpCode,  molType, hasStdChirality=None, rootProject=None):

  # Mol type is editable but guessed
  try:
    import getpass
    user = getpass.getuser()
    
  except Exception():
    import pwd
    user = pwd.getpwuid(os.getuid())[0]
  
  user = ''.join([a for a in user if a.isalnum()])
  
  if not rootProject:
    from memops.api.Implementation import MemopsRoot
    rootProject = MemopsRoot(name='ChemBuild', currentUserId=user)
    rootProject.__dict__['override'] = True
  
  # Make ChemComp
  keywords = [str(x) for x in compound.keywords]
  chemComp = rootProject.newNonStdChemComp(molType=molType,
                                           ccpCode=ccpCode, 
                                           name=str(compound.name), 
                                           details=str(compound.details) or None,
                                           hasStdChirality=hasStdChirality,
                                           keywords=keywords)
  
  # TBD aromatic
  # TBD paramagnetic
  
  variants = compound.variants
  mainAtoms = [a for a in compound.atoms if not a.isLink()]
  linkAtoms = [a for a in compound.atoms if a.isLink()]
  chemAtomDict = {}
  
  # Make regular ChemAtoms
  for atom in mainAtoms:
  
    varAtomDict = {}
    
    for varAtom in atom.varAtoms:
      hasLink = True if varAtom.getLinks() else False
      chirality = varAtom.chirality
      subType = (hasLink, chirality)
      isLabile = varAtom.isLabile
      
      if subType in varAtomDict:
        varAtomDict[subType].append(varAtom)
      else:
        varAtomDict[subType] = [varAtom]
    
    
    subTypes = sorted(varAtomDict.keys())  
        
    for subType, key in enumerate(subTypes, 1):
      (hasLink, chirality) = key
    
      if chirality:
        if chirality in 'RS':
          chirality = str(chirality)
        else:
          chirality = 'unknown'
      
      chemAtom = chemComp.newChemAtom(elementSymbol=str(atom.element),
                                      name=str(atom.name),
                                      subType=subType,
                                      chirality=chirality,
                                      waterExchangeable=isLabile)
  
      for va in varAtomDict[key]:
        chemAtomDict[va] = chemAtom
  
  # Make LinkAtoms and corresponding link ends
  linkCodeDict = {}
  for atom in linkAtoms:

    varAtomDict = {}
    
    # Must pair with right subTypes
    for varAtom in atom.varAtoms: 
      boundVarAtom = list(varAtom.neighbours)[0]
      boundChemAtom = chemAtomDict[boundVarAtom]
  
      if boundChemAtom in varAtomDict:
        varAtomDict[boundChemAtom].append(varAtom)
      else:
        varAtomDict[boundChemAtom] = [varAtom] 
  
    boundChemAtoms = list(varAtomDict.keys())
    
    for i, boundChemAtom in enumerate(boundChemAtoms, 1):
      linkCode = boundChemAtom.name
      
      if len(boundChemAtoms) > 1:
        linkCode += '_%d' % i     
      
      if 'next' in atom.name:
        linkCode = 'next'
        
      elif 'prev' in atom.name:
        linkCode = 'prev'  
        
      name = linkCode + '_1'
      linkAtom = chemComp.newLinkAtom(name=str(name),
                                      subType=1)
      
      linkEnd = chemComp.newLinkEnd(linkCode=str(linkCode),
                                    boundChemAtom=boundChemAtom,
                                    boundLinkAtom=linkAtom)
      
      linkAtom.boundLinkEnd = linkEnd                        
 
      for varAtom in varAtomDict[boundChemAtom]:
        chemAtomDict[varAtom] = linkAtom
        
        if linkCode not in ('prev','next'):
          linkCodeDict[varAtom] = linkCode
  
  # Make ChemCompVars
  protStateDict = {}
  for var in variants:
    polyLink = var.polyLink
    
    if polyLink not in protStateDict:
      protStateDict[polyLink] = {}
    
    for varAtom in var.elementDict.get('H', []):
      if varAtom.isVariable:
        name = varAtom.name
        
        if name not in protStateDict[polyLink]:
          protStateDict[polyLink][name] = set([var])
          
        else:
          protStateDict[polyLink][name].add(var)
  
  neutral = 'neutral'
  for var in variants:
    
    # Get chemCompVar linking
    linkCodes = [linkCodeDict[va] for va in linkCodeDict if va.variant is var]
    linkCodes.sort()
    linking = str(var.polyLink)
    
    if molType in ('protein','DNA','RNA'):
      if linking in ('free','linked'):
        linking = 'none'
     
    elif linking == 'free':
      linking = 'none'
    
    elif linking == 'linked':
      tagsLink = ','.join(linkCodes)
      linking = 'link:%s' % tagsLink
    
    
    # Get chemCompVar descriptor
    descriptorDict = {}
    
    # link
    if linkCodes and molType in ('protein','DNA','RNA'):
      descriptorDict['link'] = linkCodes
    
    
    # prot, deprot
    hAtomVars = protStateDict[var.polyLink]
    for name in hAtomVars:
      if var in hAtomVars[name]: # var is vars that have this hydrogen
        label = 'prot'
      else:
        label = 'deprot'
      
      if label in descriptorDict:
        descriptorDict[label].append(name)
      else:
        descriptorDict[label] = [name]


    # stereo
    for varAtom in var.varAtoms:
      if varAtom.chirality:
        chemAtom = chemAtomDict[varAtom]
        label = 'stereo_%s' % chemAtom.subType

        if label in descriptorDict:
          descriptorDict[label].append(varAtom.name)
        else:
          descriptorDict[label] = [varAtom.name]

    
    tagNames = []
    for label in VAR_TAG_ORDER:
      if label in descriptorDict:
        atomNames = ','.join(sorted(descriptorDict[label]))
        tagNames.append('%s:%s' % (label,atomNames))
 
 
    descriptor = str(';'.join(tagNames)) or neutral
    charge = sum([a.charge for a in var.varAtoms])
    isDefaultVar = var in compound.defaultVars  
    chemCompVar = chemComp.newChemCompVar(linking=str(linking),
                                          descriptor=descriptor,
                                          formalCharge=charge, 
                                          isDefaultVar=isDefaultVar,
                                          isAromatic=False, 
                                          isParamagnetic=False)

    chemAtoms = [chemAtomDict[va] for va in var.varAtoms] 
    chemCompVar.setChemAtoms(chemAtoms)
                          
  
  # Make ChemBonds
  done = set()
  for var in variants:
    for bond in var.bonds:
      chemAtoms = [chemAtomDict[va] for va in bond.varAtoms]
      key = frozenset(chemAtoms)
      
      if key in done:
        continue
      else:
        done.add(key)
        chemComp.newChemBond(chemAtoms=chemAtoms,
                             bondType=bond.bondType)
    
  # Make ChemAtomSets
  done = {}
  groupMapping = {}
  for group in compound.atomGroups:
    if group.subGroups:
      continue
    
    varAtoms = list(group.varAtoms)
    atoms = [va.atom for va in varAtoms]
    
    # CCPN groups are per chem comp not per var
    key = frozenset(atoms)
    if key in done:
      groupMapping[group] = done[key]
      continue
    
    chemAtoms = [chemAtomDict[va] for va in varAtoms]

    names = set([va.name for va in varAtoms])
    while len(names) > 1:
      names = set([x[:-1] for x in names])
    
    # name = str(names.pop() or varAtoms[0].name)
    name = group.name
    print('BEF NAME', name)

    while chemComp.findFirstChemAtomSet(name=name):
      name = name + "'"
      print('NAME', name)
    
    # name = name + "*"
 
    if group.groupType == EQUIVALENT:
      isProchiral = False
 
      if len(atoms) == 2:
        equiv = None
      else:
        equiv = True
 
    elif group.groupType == NONSTEREO:
      common = set(varAtoms[0].neighbours)
      for varAtom in varAtoms[1:]:
        common = common & varAtom.neighbours
      
      if common and len(common.pop().neighbours) < 4:
        isProchiral = False
      
      else:
        isProchiral = True
      
      equiv = False
 
    else:
      continue
   
    chemAtomSet = chemComp.newChemAtomSet(isProchiral=isProchiral,
                                          name=str(name),
                                          isEquivalent=equiv,
                                          chemAtoms=chemAtoms)
                                          
    groupMapping[group] = chemAtomSet
    done[key] = chemAtomSet

  for group in compound.atomGroups:
    if not group.subGroups:
      continue
    
    varAtoms = group.varAtoms
    atoms = [va.atom for va in varAtoms]
    chemAtomSets = [groupMapping[g] for g in group.subGroups]

    key = frozenset(atoms)
    if key in done:
      groupMapping[group] = done[key]
      continue
      
    names = set([va.name for va in varAtoms])
    while len(names) > 1:
      names = set([x[:-1] for x in names])
    
    # name = str(names.pop()) + '*'
    name = group.name

    while chemComp.findFirstChemAtomSet(name=name):

      name = name + "'"

    if group.groupType == EQUIVALENT:
      isProchiral = False
      equiv = True
 
    elif group.groupType == NONSTEREO:
      subGroups = list(group.subGroups)
      groupA = subGroups[0]
      groupB = subGroups[-1]
      stackA = set(groupA.varAtoms)
      stackB = set(groupB.varAtoms)
      
      # Graph walk to find root of symmetry
      doneSymmetry = set()
      isProchiral = True
      while stackA and stackB:
        varAtomA = stackA.pop()
        varAtomB = stackB.pop()
        doneSymmetry.add(varAtomA)
        doneSymmetry.add(varAtomB)
        neighboursA = set(varAtomA.neighbours)
        neighboursB = set(varAtomB.neighbours)
        union = neighboursA & neighboursB         
        
        if union:
          if len(union.pop().neighbours) < 4:
            isProchiral = False
          break
        
        for va in neighboursA:
          if va not in doneSymmetry:
            stackA.add(va)

        for va in neighboursB:
          if va not in doneSymmetry:
            stackB.add(va)
           
      equiv = False

    else:
      continue

    chemAtomSet = chemComp.newChemAtomSet(isProchiral=isProchiral,
                                          name=str(name),
                                          isEquivalent=equiv,
                                          chemAtomSets=chemAtomSets)
    done[key] = chemAtomSet

  
  rootProject.__dict__['override'] = False
  chemComp.__dict__['isModified'] = True
  chemComp.checkValid()
  
  for chemCompVar in chemComp.chemCompVars:
    chemCompVar.checkValid()
  
  for linkEnd in chemComp.linkEnds:
    linkEnd.checkValid()                              

  return chemComp
  #from memops.format.xml import XmlIO
  #XmlIO.save(targetDirectory, topObject)



def convertCcpnProject(memopsRoot, savePath='./chemGroups/ccpn'):

  if not path.exists(savePath):
    os.mkdir(savePath)
    
  molTypeDirs = {}
    
  for chemComp in memopsRoot.chemComps:
    ccpCode = chemComp.ccpCode
    molType = chemComp.molType
    
    if molType not in molTypeDirs:
      dirPath = path.join(savePath, molType)
      molTypeDirs[molType] = dirPath
      if not path.exists(dirPath):
        os.mkdir(dirPath)
        
    else:
      dirPath = molTypeDirs[molType]

    fileName = path.join(dirPath, ccpCode)

    compound = importChemComp(chemComp)
    
    if compound:
      compound.save(fileName)
      print("Imported %s:%s" % (molType,ccpCode))

def importChemComp(chemComp):
  
  # Main Compound
  
  ccpCode = chemComp.ccpCode
  molType = chemComp.molType
  memopsRoot = chemComp.root
  chemCompCoord = memopsRoot.findFirstChemCompCoord(molType=molType, ccpCode=ccpCode)
  
  name = chemComp.name or '%s:%s' % (molType, ccpCode)

  compound = Compound(name)
  compound.ccpCode = ccpCode
  compound.ccpMolType = molType
  
  # Main Atoms
  
  atomMap = {}
  aromaticAtoms = set()
  for chemAtom in chemComp.chemAtoms:

    if chemAtom.className == 'LinkAtom':
      element = LINK
      
      if ('prev' in chemAtom.name) or ('next' in chemAtom.name):
        name = chemAtom.name
      
      else:
        linkEnd = chemAtom.boundLinkEnd
        name = 'link_' + linkEnd.boundChemAtom.name
      
    else:
      element = chemAtom.chemElement.symbol
      name = chemAtom.name
    
    if name not in atomMap:
      atom = Atom(compound, element, name)
      atomMap[name] = atom
  
  # Vars and VarAtoms
  if chemCompCoord:
    getVarCoord = chemCompCoord.findFirstChemCompVarCoord
  
  for chemCompVar in chemComp.chemCompVars:
    varAtomMap = {}
    variant = Variant(compound)
    variant.polyLink = chemCompVar.linking
    
    if chemCompVar.isDefaultVar:
      variant.setDefault(True)
    
    descriptor = chemCompVar.descriptor
    descs = descriptor.split(';')
    
    varProts = set()
    for desc in descs:
      if 'prot' in desc:
        hNames = desc.split(':')[1]
        varProts.update(hNames.split(','))
       
    if chemCompCoord:
      chemCompVarCoord = getVarCoord(linking=chemCompVar.linking,
                                     descriptor=chemCompVar.descriptor)
      if not chemCompVarCoord:
        chemCompVarCoord = getVarCoord(linking=chemCompVar.linking)

      if not chemCompVarCoord:
        chemCompVarCoord = getVarCoord()
        
    else:
      chemCompVarCoord = None
        
    chemAtoms = chemCompVar.chemAtoms
    for chemAtom in chemAtoms:
      if chemAtom.className == 'LinkAtom':
        labile = None
        chirality = None
        
        if ('prev' in chemAtom.name) or ('next' in chemAtom.name):
          name = chemAtom.name
        else:
          linkEnd = chemAtom.boundLinkEnd
          name = 'link_' + linkEnd.boundChemAtom.name

      else:
        name = chemAtom.name
        labile = chemAtom.waterExchangeable
        chirality = chemAtom.chirality
        
        if chirality == 'unknown':
          chirality = None
        
        if not chirality:
          subTypes = chemComp.findAllChemAtoms(name=chemAtom.name)
          
          if len(subTypes) > 1:
            stereoTag = 'stereo_%d' % chemAtom.subType
            
            
            for tag in descs:
              if tag.startswith(stereoTag):
                
                if chemAtom.name in tag:
                  
                  if (chemAtom.subType-1) % 2 == 0:
                    chirality = 'a'
                  else:
                    chirality = 'b' 
                
                break
                
 
      coords = (0.0, 0.0, 0.0)
      if chemCompVarCoord:
        chemAtomCoord = chemCompVarCoord.findFirstChemAtomCoord(chemAtom=chemAtom)
 
        if chemAtomCoord:
          coords = (chemAtomCoord.x*50,
                    chemAtomCoord.y*50,
                    chemAtomCoord.z*50)
                    
      atom = atomMap[name]
      if not atom.isVariable:
        atom.isVariable = atom.name in varProts
              
      varAtom = VarAtom(variant, atom, chirality=chirality,
                        coords=coords, isLabile=labile)
      varAtomMap[chemAtom] = varAtom
 
    # Make bond for each var
    
    for chemBond in chemComp.chemBonds:
      varAtoms = [varAtomMap.get(a) for a in chemBond.chemAtoms]
 
      if None in varAtoms:
        # Bond only in different var
        continue
 
      bond = Bond(varAtoms, chemBond.bondType, autoVar=False)
      
      if chemBond.bondType == 'aromatic':
        atomsA = [atomMap[a.name] for a in  chemBond.chemAtoms]
        aromaticAtoms.update(atomsA)

      if chemBond.bondType == 'dative':
        if varAtoms[1].element in 'CNPOSFClI':
          bond.direction = varAtoms[0]
        else:
          bond.direction = varAtoms[1]
          
    variant.updateDescriptor()
  
  # AtomGroups
  
  # Simple first
  
  for chemAtomSet in chemComp.chemAtomSets:
    if chemAtomSet.chemAtomSets:
      continue
  
    chemAtomsB = chemAtomSet.chemAtoms
    atoms = set([atomMap[ca.name] for ca in chemAtomsB])

    for var in compound.variants:
      varAtoms = set([var.atomDict.get(a) for a in atoms])
      
      if None in varAtoms:
        # This var cannot hold the group
        continue
      
      if chemAtomSet.isEquivalent is True:
        groupType = EQUIVALENT
      elif chemAtomSet.isProchiral:
        groupType = NONSTEREO
      elif chemAtomSet.isEquivalent is None:
        groupType = EQUIVALENT  
      else:
        continue
      
      ag = AtomGroup(compound, varAtoms, groupType)
      ag.name = chemAtomSet.name
  
  # Compound second
  
  for chemAtomSet in chemComp.chemAtomSets:
    if not chemAtomSet.chemAtomSets:
      continue
    
    chemAtomsB = set()
    for chemAtomSetB in chemAtomSet.chemAtomSets:
      chemAtomsB.update(chemAtomSetB.chemAtoms)
    atoms = set([atomMap[ca.name] for ca in chemAtomsB])
    
    for var in compound.variants:
      varAtoms = set([var.atomDict.get(a) for a in atoms])
      
      if None in varAtoms:
        # This var cannot hold the group
        continue
      
      if chemAtomSet.isEquivalent is True:
        groupType = EQUIVALENT
      elif chemAtomSet.isProchiral:
        groupType = NONSTEREO
      elif chemAtomSet.isEquivalent is None:
        groupType = EQUIVALENT  
      else:
        continue
      
      # Automatically fills subGroups that were defined first
      ag = AtomGroup(compound, varAtoms, groupType)
      ag.name = chemAtomSet.name
  
  # Curate charges and link names
  
  for atom in compound.atoms:
    elem = atom.element
    
    if elem in (LINK, 'C', 'H'):
      name = atom.name
      if elem == LINK and 'prev' not in name and 'next' not in name:
        if atom.varAtoms:
          varAtom = list(atom.varAtoms)[0]
          
          if varAtom.neighbours:
            bound = list(varAtom.neighbours)[0]
            atom.setName('link_' + bound.name)
    
      continue
    
    defaultVal = ELEMENT_DATA.get(elem,  ELEMENT_DEFAULT)[0]
    
    for varAtom in atom.varAtoms:
    
      for varAtomB in varAtom.neighbours:
        if varAtomB.freeValences:
          break
 
      else:
        nVal = sum([BOND_TYPE_VALENCES[b.bondType] for b in varAtom.bonds])
        charge = nVal - defaultVal
 
        if charge:
          varAtom.setCharge(charge, autoVar=False)
 
  # Aromatics
  
  if aromaticAtoms:
    compound.setAromatic(aromaticAtoms)
    
  compound.center((0.0, 0.0, 0.0))
  for var in compound.variants:
    var.checkBaseValences()
   
  return compound
