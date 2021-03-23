"""
CcpNmr ChemBuild is a tool to create chemical compound descriptions.

Copyright Tim Stevens, University of Cambridge December 2010
"""

from ccpnmr.chemBuild.general.Constants import AROMATIC

class AtomGroup:

  def __init__(self, compound, varAtoms, groupType):
    
    self.compound = compound
    self.varAtoms = set(varAtoms)
    self.groupType = groupType
    self.subGroups = set()
    self.variant = list(varAtoms)[0].variant
    self._name = None

    compound = self.compound
    compound.isModified = True
    
    existing = set()
    orphaned = set()
    for varAtom in varAtoms:
      if varAtom.atomGroups:
        existing.update(varAtom.atomGroups)
      else:
        orphaned.add(varAtom)
    
    if groupType == AROMATIC:
      if existing:
        for group in existing:
          if group.groupType == AROMATIC:
            varAtoms2 = set(group.varAtoms)
 
            if len(varAtoms) > len(varAtoms2):
              if not varAtoms2 - varAtoms:
                group.delete()
 
            else:
              if not varAtoms - varAtoms2:
                group.delete()
      
    elif existing:
      # Check union with single other group; replace any
      if len(existing) == 1:
        group = existing.pop()
        if group.groupType != AROMATIC:
          group.delete()
      
      # Subgroups only allowed if fill current completely
      # Subgroups must be defined first
      elif orphaned:
        for group in existing:
          if group.groupType != AROMATIC:
            group.delete()
      
      else:
        self.subGroups = existing
    
    for varAtom in varAtoms:
      varAtom.atomGroups.add(self)
    
    
    self.variant.atomGroups.add(self)
    compound.atomGroups.add(self)
    
    if self.groupType == AROMATIC:
      for varAtom in self.varAtoms:
        for bond in varAtom.bonds:
          varAtomA, varAtomB = bond.varAtoms
          
          if (varAtomA in self.varAtoms) and (varAtomB in self.varAtoms):
            bond.bondType = 'aromatic'
  
        varAtom.updateValences()

  def _getName(self, suffix ='%'):

    varAtoms = list(self.varAtoms)


    names = set([va.name for va in varAtoms])
    while len(names) > 1:
      names = set([x[:-1] for x in names])

    baseName = str(names.pop() or varAtoms[0].name)
    name = baseName + suffix

    return name

  @property
  def name(self):
    return self._name

  @name.getter
  def name(self):
    if not self._name:
      _name = self._getName()
    else:
     _name = self._name
    return _name

  @name.setter
  def name(self, value):
    if value is None:
      raise ValueError('Value cannot be None')
    self._name = str(value)

  def delete(self):
  
    compound = self.compound
    compound.isModified = True

    for varAtom in self.varAtoms:
      varAtom.atomGroups.remove(self)
   
    self.variant.atomGroups.remove(self)
    compound.atomGroups.remove(self)

    if self.groupType == AROMATIC:
      for bond in varAtom.bonds:
        varAtomA, varAtomB = bond.varAtoms
        
        if (varAtomA in self.varAtoms) and (varAtomB in self.varAtoms):
          bond.bondType = 'single'
          
      for varAtom in self.varAtoms:
        varAtom.updateValences()
    del self
      
