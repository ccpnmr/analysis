"""
CcpNmr ChemBuild is a tool to create chemical compound descriptions.

Copyright Tim Stevens, University of Cambridge December 2010
"""

from ccpnmr.chemBuild.model.Variant import Variant

from ccpnmr.chemBuild.general.Constants import LINK, ELEMENT_DATA, ELEMENT_DEFAULT
from ccpnmr.chemBuild.general.Constants import EQUIVALENT, NONSTEREO

class Atom:
  
  def __init__(self, compound, element, name, isVariable=False):
    
    self.compound = compound
    self.element = element
    self.isVariable = isVariable
    self.varAtoms = set()
    self.isDeleted = False
    self.baseValences = ELEMENT_DATA.get(element,  ELEMENT_DEFAULT)[0]
    
    if not name:
      self.defaultName()
    
    else:
      self.name = name
    
    compound.isModified = True
    compound.atoms.add(self)
    compound.atomDict[self.name] = self
    
    if isVariable:
      for varAtom in self.varAtoms:
        var = varAtom.variant
        var.updateDescriptor()
      
      
  def __repr__(self):
    
    return '<Atom %s %s>' % (self.element, self.name)
  
  def isLink(self):
  
    return self.element == LINK
  
  def setName(self, name):
    
    if name == self.name:
      return
    
    compound = self.compound
    compound.isModified = True
    prevName = self.name

    used = set(compound.atomDict.keys())
    if name in used:
      name = self.defaultName()
      #raise Exception('Atom name "%s" already in use' % name)
      #return
    
    self.name = name
    
    neighbours = set()
    for varAtom in self.varAtoms:
      varAtom.name = name
      var = varAtom.variant
          
      if self.element == LINK:
        var.updatePolyLink()
      else:
        neighbours.update([va.atom for va in varAtom.neighbours])
        
    if self.isVariable:
      for var in compound.variants:
        var.updateDescriptor()
    
    if prevName not in compound.atomDict:
      print("Atom Dict missing", prevName)
      nn = list(compound.atomDict.keys())
      nn.sort()
      print(', '.join(nn))
    else:
      del compound.atomDict[prevName]
    
    compound.atomDict[name] = self
    
    for atom in neighbours:
      if atom.element == LINK:
        if ('prev' not in atom.name) and ('next' not in atom.name):
          atom.setName('link_%s' % name)
         
  def defaultName(self):
  
    atoms = self.compound.atoms
    used = set([a.name for a in atoms])
    
    elem = self.element
  
    i = 1
    name = '%s%d' % (elem, i)
    
    while name in used:
      i += 1
      name = '%s%d' % (elem, i)
    
    self.name = name
    
    return name
  
  def setBaseValences(self, n):
  
    self.baseValences = n
    for varAtom in self.varAtoms:
      varAtom.updateValences()
  
  def setVariable(self, value=True):
    
    
    compound = self.compound
    compound.isModified = True
    variants = list(compound.variants)
    
    for varAtom in self.varAtoms:
      varAtom.isVariable = value
    
    if value and not self.isVariable:
      self.isVariable = value
      # if it is variable need duplicate vars +/- this atom
    
      if self.element == 'H':
        for varAtom in self.varAtoms:
          varAtom.isLabile = True
      
      for varA in variants:
        # If a var has this atom
        if self not in varA.atomDict:
          continue
        
        varAtomA = varA.atomDict[self]
        bound = [va.atom for va in varAtomA.neighbours if va.element != 'H']
        
        # make a copy without this atom
        atomsA = set(varA.varAtoms)
        atomsA.remove(varAtomA)
        
        
        var = Variant(self.compound, atomsA)

        for atomB in bound:
          varAtomB = var.atomDict.get(atomB)
          
          if varAtomB:
            varAtomB.setCharge(varAtomB.charge-1, autoVar=False)
    
    elif not value:
      self.isVariable = value
      # If it is not variable only need the one eqiv var with this atom
              
      for varA in variants:
        # If a var has this atom
        if self not in varA.atomDict:
          continue
        
        
        # Remove other vars that are the same, save this atom
        atomsA = set([va.atom for va in varA.varAtoms])
        atomsA.remove(self)
        
        for varB in variants:
          if varB is varA:
            continue
          
          atomsB = set([va.atom for va in varB.varAtoms])

          if atomsA == atomsB:
            varB.delete()
     
    for var in self.compound.variants:
      var.updatePolyLink()
      var.updateDescriptor()
      names = [a.name for a in var.varAtoms]
      names.sort()
      
  def delete(self):

    self.isDeleted = True
    compound = self.compound
    compound.isModified = True
    varAtoms = list(self.varAtoms)
    
    if self.element == LINK:
      # Delete all vars with same link
    
      for varAtom in varAtoms:
        if len(self.compound.variants) == 1:
          break
        else:
          varAtom.variant.delete()
             
    for varAtom in varAtoms:
      varAtom.delete()  # deletes bonds and updates any neighbours
    
    compound.atoms.remove(self)
    del compound.atomDict[self.name]
        
    for var in self.compound.variants:
      var.updatePolyLink()
      var.updateDescriptor()
    
    del self
