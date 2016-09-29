"""
CcpNmr ChemBuild is a tool to create chemical compound descriptions.

Copyright Tim Stevens, University of Cambridge December 2010
"""


from ccpnmr.chemBuild.general.Constants import LINK, AROMATIC

    
BOND_TYPE_VALENCES = {'single':1, 'double':2, 'aromatic':1, 'quadruple':4,
                      'triple':3, 'singleplanar':1, 'dative':1}
                      
BOND_STEREO_DICT = {4:(0,-1, 0,1), # tetrahedral
                    5:(0,-1, 0,1,0), # trigonal bipyramidal
                    6:(0,-1,-1,1,1,0), # octahedral
                    7:(0,-1,-1,1,1,0, 0), # pentagonal bipyramidal
                    }
class Bond:

  def __init__(self, varAtoms, bondType='single', autoVar=True):
    
    varAtomA, varAtomB = varAtoms
     
    if varAtomA.variant is not varAtomB.variant:
      raise Exception('VarAtom mismatch in bond formation %s-%s' % (varAtomA.name, varAtomB.name))
     
     
    self.varAtoms = set(varAtoms)
    
    self.variant = variant = varAtomA.variant
    self.compound = self.variant.compound
    self.compound.isModified = True
    self.direction = varAtomA if bondType == 'dative' else None
    
    varAtomA.bonds.add(self)   
    varAtomB.bonds.add(self)
    
    self.bondType = bondType
    self.removeDuplicates()
    
    varAtomA.updateValences() # Need this before auto varing
    varAtomB.updateValences()
     
    variant.bonds.add(self)
    varAtomA.updateNeighbours()
    varAtomB.updateNeighbours()
    
    nameA = varAtomA.name
    nameB = varAtomB.name
    atomA = varAtomA.atom
    atomB = varAtomB.atom
    
    elementA = varAtomA.element
    elementB = varAtomB.element

    nameLink = None
    nameH = None
    if (elementA == LINK) and (nameA == LINK):
      nameLink = (varAtomA, varAtomB)
    elif (elementB == LINK) and (nameB == LINK):
      nameLink = (varAtomB, varAtomA)
    elif (elementA == 'H') and nameB:
      nameH = (varAtomA, varAtomB)
    elif (elementB == 'H') and nameA:
      nameH = (varAtomB, varAtomA)
 
    if nameLink:
      varAtom1, varAtom2 = nameLink  
      name = varAtom2.name or varAtom2.element
      varAtom1.atom.setName( '%s_%s' % (LINK, name) )
      
    elif nameH and autoVar:
      varAtom1, varAtom2 = nameH
      name = varAtom2.name
      if name.startswith(varAtom2.element):
        name = name[len(varAtom2.element):]
      
      if name:
        firstName = 'H' + name
        hydrogens = [a for a in varAtom2.neighbours if a.element == 'H']
        
        if len(hydrogens) > 1:
          variant.autoNameAtoms(hydrogens)
    
     
    if autoVar:
      failedVars = set()
      for var in list(self.compound.variants):
        if var is not variant:
          atomDict = var.atomDict
          varAtomC = atomDict.get(atomA)
          varAtomD = atomDict.get(atomB)
          
          if varAtomC and varAtomD: # Both exist in this var
            getBond = var.getBond(varAtomC, varAtomD, autoVar=False)
 
            if not getBond:
              if varAtomC not in varAtomD.neighbours:
                failedVars.add(var)
          
          elif varAtomC and not varAtomC.neighbours:
            varAtomC.delete() # E.g. proton not in this link var

          elif varAtomD and not varAtomD.neighbours:
            varAtomD.delete() # E.g. proton not in this link var
           
      for var in failedVars:
        var.delete()
      
      if elementA == 'O' and elementB == 'H':
        self.checkCarboxylVar(varAtomA, varAtomB)
        
      elif elementB == 'O' and elementA == 'H':
        self.checkCarboxylVar(varAtomB, varAtomA)
        
      elif elementA == 'N' and elementB == 'H':
        self.checkAmineVar(varAtomA, varAtomB)
        
      elif elementB == 'N' and elementA == 'H':
        self.checkAmineVar(varAtomB, varAtomA)
    
    varAtomA.updateValences()
    varAtomB.updateValences()
  
  
  def __repr__(self):
  
    aNames = [a.name for a in self.varAtoms]
    aNames.sort()
    aName = '-'.join(aNames)
    
    return '<Bond %s %s>' % (aName, self.bondType)
    
  def checkCarboxylVar(self, oAtom, hAtom):
    
    neighbours = set(oAtom.neighbours)
    neighbours.remove(hAtom)
    
    if not neighbours:
      return
    
    other = neighbours.pop()
    
    if other.element == 'C':
      neighbours2 = set(other.neighbours)
      neighbours2.remove(oAtom)
      variant = oAtom.variant
      compound = variant.compound
      bondsC = set(other.bonds)
      
      for atom in neighbours2:
        if atom.element == 'O':
          bondsO = set(atom.bonds)
          common = bondsO & bondsC
          if not common:
            continue
         
          if common.pop().bondType != 'double':
            continue
         
          hAtom.atom.setVariable(True)
          
          for varAtom in oAtom.atom.varAtoms:
            if varAtom.freeValences:
              varAtom.setCharge(-1)
          
          for var in compound.variants:
            var.updatePolyLink()
            var.updateDescriptor()
            
  def checkAmineVar(self, nAtom, hAtom):
      
    neighbours = nAtom.neighbours
    hydrogens = [a for a in neighbours if a.element == 'H']

    if len(hydrogens) > 2 and len(neighbours) == 4:
      compound = nAtom.variant.compound
      hAtom.setVariable(True)
      
      for varAtom in nAtom.atom.varAtoms:
        if varAtom.freeValences:
          varAtom.setCharge(0)
        
      for var in compound.variants:
        var.updatePolyLink()
        var.updateDescriptor()
      
  def setBondType(self, bondType):
    
    if bondType != self.bondType:
      compound = self.compound
      compound.isModified = True
      
      varAtomA, varAtomB = self.varAtoms
      nValPrev = BOND_TYPE_VALENCES[self.bondType]
      nValNext = BOND_TYPE_VALENCES[bondType]
      added = nValNext - nValPrev
      
      while added > 0:
        if varAtomA.freeValences:
          varAtomA.freeValences.pop()

        if varAtomB.freeValences:
          varAtomB.freeValences.pop()
        
        added -= 1
      
      while added < 0:
        varAtomA.freeValences.append(0.0)
        varAtomB.freeValences.append(0.0)
        added += 1
    
      if bondType == 'dative':      
        if self.direction is varAtomA:
          self.direction = varAtomB
        else:
          self.direction = varAtomA
      
      if added:
        varAtomA.updateValences()
        varAtomB.updateValences()
      
      self.bondType = bondType
                 
  def removeDuplicates(self):

    varAtomA, varAtomB = self.varAtoms
    
    nVals = int(BOND_TYPE_VALENCES[self.bondType])
    
    # Could trap errors here
    
    commonBonds = varAtomA.bonds & varAtomB.bonds
    n = len(commonBonds)
    
    if n > 1:
      for bond in commonBonds:
        if bond is not self:
          bond.delete()
       
  def delete(self):

    compound = self.compound
    compound.isModified = True
    
    varAtomA, varAtomB = self.varAtoms
    varAtomA.variant.bonds.remove(self)
    
    varAtomA.bonds.remove(self)
    varAtomB.bonds.remove(self)  
        
    varAtomA.stereo = []
    varAtomB.stereo = []
    
    varAtomA.freeValences.append(0.0)     
    varAtomB.freeValences.append(0.0)     
    
    groups = varAtomA.atomGroups | varAtomB.atomGroups
    for group in groups:
      if group.groupType == AROMATIC:
        if self.bondType == AROMATIC:
          group.delete()
      else:
        group.delete()
    
    varAtomA.updateValences()
    varAtomB.updateValences()      
 
    varAtomA.updateNeighbours()
    varAtomB.updateNeighbours()

    del self
    

  def deleteAll(self):
  
    atoms = set([va.atom for va in self.varAtoms])
    
    delBonds = []
    for var in self.compound.variants:
      for bond in var.bonds:
        atoms2 = set([va.atom for va in bond.varAtoms])
        
        if atoms == atoms2:
          delBonds.append(bond)
    
    for bond in delBonds:

      bond.delete()

