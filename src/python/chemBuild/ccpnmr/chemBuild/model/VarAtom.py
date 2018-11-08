"""
CcpNmr ChemBuild is a tool to create chemical compound descriptions.

Copyright Tim Stevens and Magnus Lundborg, University of Cambridge 2010-2012
"""
from math import atan2, cos, sin, radians, degrees, hypot

from ccpnmr.chemBuild.general.Constants import ELEMENT_DATA, ELEMENT_DEFAULT, ELEMENT_ISO_ABUN
from ccpnmr.chemBuild.general.Constants import COVALENT_ELEMENTS, LINK, PI, AROMATIC
from ccpnmr.chemBuild.model.Bond import BOND_TYPE_VALENCES
    

class VarAtom:

  def __init__(self, variantA, atom, freeValences=None, chirality=None,
               coords=(0.0,0.0,0.0), isLabile=False, charge=0):
    
    if variantA is None: # Means all vars
      variants = list(atom.compound.variants)
      variant = variants[0]
      otherVars = variants[1:]
    else:
      variant = variantA
      otherVars = []
    
    
    self.variant = variant
    self.atom = atom
    self.element = element = atom.element
    self.name = atom.name
    self.isVariable = atom.isVariable
    self.stereo = []
    
    compound = variant.compound
    compound.isModified = True
    self.compound = compound
      
    self.isDeleted = False
    self.coords = tuple(coords)
    self.chirality = chirality
    self.isLabile = isLabile
    self.charge = charge
    
    self.bonds = set()
    self.neighbours = set()
    self.atomGroups = set()

    if element not in variant.elementDict:
      variant.elementDict[element] = set()
    
    variant.elementDict[element].add(self)
    variant.varAtoms.add(self)
    variant.atomDict[atom] = self
    atom.varAtoms.add(self)
    
    if freeValences is None:
      self.freeValences = None
      self.updateValences()
    else:
      self.freeValences = list(freeValences)
      
    self.updateNeighbours()
    
    for var in otherVars:
      VarAtom(var, atom, freeValences, chirality,
              coords,  isLabile, charge)
    
      var.updatePolyLink()
    
    variant.updatePolyLink()
    
    if atom.isVariable:
      for var in self.compound.variants:
        var.updatePolyLink()
        var.updateDescriptor()

  def __lt__(self, other):
    return id(self) < id(other)

  def __repr__(self):
  
    aName = self.name
    return '<VarAtom %s>' % (aName)
  
  def setStereo(self, stereoVarAtoms):
    # Clockwise rule relative to first
    
    nStereo = len(self.neighbours)
    if nStereo < 4:
      stereoVarAtoms = []
    
    if stereoVarAtoms:
      if set(stereoVarAtoms) != set(self.neighbours):
        # print "Attempt to set stereo set to non-neighbours"
        return
    
    atom = self.atom
    for varAtom in atom.varAtoms:
      
      if len(varAtom.neighbours) != nStereo:
        varAtom.stereo = []
      
      elif varAtom is self:
        self.stereo = stereoVarAtoms
        
      else: # all vars same, as far as possible, respecting a/b forms
        var = varAtom.variant
        stereoVarAtoms2 = [var.atomDict.get(va.atom) for va in stereoVarAtoms]
        
        if None in stereoVarAtoms2:
          continue
        
        if len(stereoVarAtoms2) == nStereo:
          stereo = stereoVarAtoms2

          if varAtom.chirality == self.chirality:
            varAtom.stereo = stereo
          else:
            a = stereo[0]
            rest = stereo[1:]
            rest.reverse()
            varAtom.stereo = [a,] + rest
        
  def toggleAromatic(self):
  
    if self.isAromatic():
      self.compound.unsetAromatic([self.atom,])
        
    else:
      self.compound.setAromatic([self.atom,])
  
  def isLink(self):
  
    return self.element == LINK
  
  def getLinks(self):
    
    links = []
    for varAtom in self.neighbours:
      if varAtom.element == LINK:
        links.append(varAtom)
  
    return links
  
  def isHydrogen(self):
  
    return self.element == 'H'
  
  def isAromatic(self):
  
    for group in self.atomGroups:
      if group.groupType == AROMATIC:
        return True
    
    return False  
  
  def getRings(self):
  
    stack = []
    rings = set()
    
    for varAtom in self.neighbours:
      if varAtom.element != 'H':
        stack.append( [self, varAtom] )
    
    while stack:
      
      prev = stack.pop()
      if len(prev) > 8:
        continue
      
      prevSet = set(prev)
      
      nextAtoms = set([va for va in prev[-1].neighbours if va.element != 'H'])
      if prev[-2] in nextAtoms:
        nextAtoms.remove(prev[-2])
      
      for varAtom in nextAtoms:
        if varAtom.element == 'C':
          if not varAtom.freeValences:
            if not varAtom.isAromatic:
              continue
        
        if varAtom is self:
          rings.add( frozenset(prev) )
      
        elif varAtom not in prevSet:
          nextSet = prev[:] + [varAtom,]
          stack.append(nextSet)
    
    filteredRings = set()
    
    if rings:
      rings = sorted(rings, key=lambda ring: len(ring))
      minSz = len(rings[0])
      minRing = rings[0]
      filteredRings.add(minRing)

      uniqueAtoms = set()
      for ring in rings[1:]:
        unique = ring
        for ring2 in filteredRings:
          unique = unique - ring2
          nUnique = len(unique)
        if nUnique > 0 and unique not in uniqueAtoms:
          for ua in unique:
            if ua in self.neighbours:
              break
          else:
            continue
          uniqueAtoms.add(unique)
          filteredRings.add(ring)
 
#      for ring in rings:
#        if len(ring) < minSz+2:
#        filteredRings.add(ring)
 
    return filteredRings
      
      
  def setLabile(self, value=True):
  
    if (self.element == 'H') and (self.isLabile != value):
      neighbourhood = self.getContext()
      
      compound = self.compound
      compound.isModified = True
      
      # Set as labile only if the neighbours are the same as this var atom's
      # automatically includes its self
      
      for var in self.compound.variants:
        varAtom = var.atomDict.get(self.atom)
 
        if not varAtom:
          continue
        
        neighbourhoodB = varAtom.getContext()
        if neighbourhoodB!= neighbourhood:
          continue
        
        varAtom.isLabile = value
  
  def setCoords(self, x, y, z):
    
    # Compound wide for now
    
    for varAtom in self.atom.varAtoms:
      varAtom.coords = (x,y,z)

    compound = self.compound
    compound.isModified = True
  
  def setName(self, name):
  
    self.atom.setName(name)
 
  def setChirality(self, chirality, autoVar=True):
    from ccpnmr.chemBuild.model.Variant import Variant
  
    if self.element == LINK:
      return

    if self.element == 'H':
      return
      
    compound = self.compound
    variant = self.variant
    atom = self.atom
    compound.isModified = True
  
    if chirality is not None:
      nVal = len(self.freeValences) + len(self.bonds)
      nNei = len(self.neighbours)
      if nVal < 3:
        chirality = None

      if nVal > nNei:
        chirality = None
      
      hydrogens = [a for a in self.neighbours if a.element == 'H']
      if len(hydrogens) > 1:
        chirality = None
    
    if autoVar:
      variants = list(compound.variants)
      variants.remove(variant)
      variants = [variant,] + variants
      # this one must be first - so it is not deleted
    else:
      variants = [variant,]
    
    if chirality in ('R', 'S'):
      for var in variants:
        varAtom = var.atomDict[atom]
        varAtom.chirality = chirality
    
      varDict = {}
      for var in variants:
        key = frozenset(list(var.atomDict.keys()))
 
        if key not in varDict:
          varDict[key] = []
 
        varDict[key].append(var)
 
      for key in varDict:
        vars2 = varDict[key]
 
        while len(vars2) > 1:
          var = vars2.pop()
          var.delete()
          
    elif chirality in ('a','b'):
      
      varDict = {}
      for var in variants:
        key = frozenset(list(var.atomDict.keys()))
        
        if key not in varDict:
          varDict[key] = []
        
        varDict[key].append(var)
      
      for key in varDict:
        vars2 = varDict[key]
        
        while len(vars2) > 2:
          var = vars2.pop()
          var.delete()
        
        while len(vars2) < 2:
          var = Variant(compound, vars2[0].varAtoms)
          vars2.append(var)
          variants.append(var)
        
        varA, varB = vars2  
      
        if variant is varA:
          if chirality == 'b':
            varA, varB = varB, varA
            
        elif variant is varB:
          if chirality == 'a':
            varA, varB = varB, varA
           
        varAtomA = varA.atomDict[atom]
        varAtomB = varB.atomDict[atom]
        
        varAtomA.chirality = 'a'
        varAtomB.chirality = 'b'
        
        if self.stereo:
          a, b, c, d = self.stereo
          
          if chirality == 'a':
            stereoA = [varA.atomDict[va.atom] for va in [a,b,c,d]]
            stereoB = [varB.atomDict[va.atom] for va in [a,d,c,b]]
          else:
            stereoA = [varA.atomDict[va.atom] for va in [a,d,c,b]]
            stereoB = [varB.atomDict[va.atom] for va in [a,b,c,d]]
          
          varAtomA.stereo = stereoA
          varAtomB.stereo = stereoB
         
    elif not chirality:
      for var in variants:
        varAtom = var.atomDict[atom]
        varAtom.chirality = chirality
        varAtom.stereo = []
    
      varDict = {}
      for var in variants:
        key = frozenset(list(var.atomDict.keys()))
 
        if key not in varDict:
          varDict[key] = []
 
        varDict[key].append(var)
 
      for key in varDict:
        vars2 = varDict[key]
 
        while len(vars2) > 1:
          var = vars2.pop()
          var.delete()
          
    # Once all set  
    for var in variants:
      var.updateDescriptor()
    
  def getContext(self):
  
    # Get all of the (master) atoms surrounding this one
    
    return set([va.atom for va in self.neighbours])
  
  def setCharge(self, charge, autoVar=True):
    
    elem = self.element
    if elem == LINK:
      return

    if elem == 'H':
      return
      
    compound = self.compound
    compound.isModified = True
  
    defaultVal = self.atom.baseValences
    
    neighbourhood = self.getContext()
    
    if autoVar:
      variants = compound.variants
    else:
      variants = [self.variant,]
    
    for var in variants:
      varAtom = var.atomDict.get(self.atom)
      
      if not varAtom:
        continue
      
      if varAtom.getContext() != neighbourhood:
        continue

      nVal = len(varAtom.bonds) + len(varAtom.freeValences)
      if (elem in COVALENT_ELEMENTS) and (charge < 0):
        charge = max(-nVal, charge)
        targetVal = defaultVal+charge
 
      elif (elem in COVALENT_ELEMENTS) and (charge > 0):
        targetVal = defaultVal+charge
  
      else:
        targetVal = defaultVal
      
      # add any extra
      while nVal < targetVal:
        varAtom.freeValences.append(0.0)
        nVal += 1
        
      # remove exess unbound
      while nVal > targetVal:
        if varAtom.freeValences:
          varAtom.freeValences.pop()
          nVal -= 1
        else:
          break
         
      # otherwise remove extra H
      if nVal > targetVal:
        for bond in list(varAtom.bonds):
          atomA, atomB = bond.varAtoms
 
          if (atomA is not varAtom) and (atomA.element == LINK):
            bond.delete()
            nVal -= 1

          if (atomB is not varAtom) and (atomB.element == LINK):
            bond.delete()
            nVal -= 1
          
          if (atomA is not varAtom) and (atomA.element == 'H'):
            bond.delete()
            nVal -= 1

          if (atomB is not varAtom) and (atomB.element == 'H'):
            bond.delete()
            nVal -= 1
          
          if nVal == targetVal:
            break
 
      # otherwise remove anything
      if nVal > targetVal:
        for bond in list(varAtom.bonds):
          bond.delete()
          nVal -= 1
 
          if nVal == targetVal:
            break
 
      varAtom.charge = charge
      varAtom.updateValences()
    
      var.updateDescriptor()
  
  def getBondAngles(self):
  
    x1, y1, z1 = self.coords
    angles = []
    
    for bond in self.bonds:
      varAtoms = set(bond.varAtoms)
      varAtoms.remove(self)
       
      varAtom = varAtoms.pop()
       
      x2, y2, z2 = varAtom.coords
       
      dx = x2-x1
      dy = y2-y1
      
      angle = atan2(dx, dy) % (2.0*PI)
      angles.append(angle)
    
    return angles
    
  def getBondAngle(self, varAtom):
    
    x1, y1, z1 = self.coords
    x2, y2, z2 = varAtom.coords
    
    dx = x2-x1
    dy = y2-y1
      
    angle = atan2(dy, dx) % (2.0*PI)
    
    return angle
    
  def getBondToAtom(self, varAtom):
    
    for bond in self.bonds:
      if self in bond.varAtoms and varAtom in bond.varAtoms:
        return bond
        
    return None
    
  def getAtomDist(self, varAtom):
    
    x1, y1, z1 = self.coords
    x2, y2, z2 = varAtom.coords

    dx = x2-x1
    dy = y2-y1
    
    return hypot(dx, dy)
    
  def setVariable(self, boolean):
  
    self.atom.setVariable(boolean)
          
  def updateValences(self):

    defaultVal = self.atom.baseValences
    
    if self.freeValences is None:
      if defaultVal:
        gap = 2.0*PI/defaultVal
        self.freeValences = [gap*i for i in range(defaultVal)]
      else:
        self.freeValences = []
        
    else:
      bound = self.getBondAngles()
      
      numVal = defaultVal
      for bond in self.bonds:
        numVal -= BOND_TYPE_VALENCES[bond.bondType]
      
      if self.element in COVALENT_ELEMENTS:
        numVal += self.charge
      
      if numVal and self.isAromatic():
        numVal -= 1
      
      self.freeValences = [0.0] * numVal
      
      if bound:
        bound.sort()
        bound.append(bound[0] + (2.0*PI))
        gaps = [(bound[i+1]-x, x, bound[i+1], []) for i, x in enumerate(bound[:-1])]
        gaps.sort()
        for i in range(numVal):
          size, begin, end, indices = gaps[-1]
          indices.append(i)
          sizeB = (end-begin)/(len(indices)+1.0)
          
          for k, j in enumerate(indices):
            delta = (1.0+k) * sizeB
            self.freeValences[j] = (begin+delta) % (2*PI)
          
          gaps[-1] = (sizeB, begin, end, indices)
          gaps.sort()  

      elif self.freeValences:
        gap = 2.0*PI/len(self.freeValences)
        self.freeValences = [gap*i for i in range(numVal)]
        
    
  def updateNeighbours(self):
  
    atoms = set()
    for bond in self.bonds:
      atoms.update(bond.varAtoms)

    if atoms:
      atoms.remove(self)  
    
    if self.neighbours != atoms:
      hydrogens = [a for a in atoms if a.element == 'H']
      changed = atoms ^ self.neighbours

      for atom in changed:
        if (atom.element == 'H') and self.element == 'O':
          atom.setLabile(True)
            
        elif (atom.element == 'H') and self.element == 'N':
          
          if self.charge and len(hydrogens) > 2:
            for h in hydrogens:
              h.setLabile(True)
          else:
            for h in hydrogens:
              h.setLabile(False)
                
    
      if (self.element == 'C') and hydrogens:
        hydrogens = [h.atom for h in hydrogens]
      
        self.compound.unsetAtomsProchiral(hydrogens)
        self.compound.unsetAtomsEquivalent(hydrogens)
        
        if len(hydrogens) == 2:
          self.compound.setAtomsProchiral(hydrogens)
        elif len(hydrogens) == 3:
          self.compound.setAtomsEquivalent(hydrogens)
    
      self.neighbours = atoms       

  def delete(self):
    
    variant = self.variant
    if self not in variant.varAtoms:
      return
      
    compound = self.compound
    compound.isModified = True
    
    atom = self.atom
    
    for bond in list(self.bonds):
      bond.delete()
    
    if self.element in variant.elementDict:
      variant.elementDict[self.element].remove(self)
      
    variant.varAtoms.remove(self)
    del variant.atomDict[atom]
    atom.varAtoms.remove(self)
    
    # Remove any vars that have identical atoms
    
    atoms = set([(va.atom, va.chirality) for va in variant.varAtoms])
    
    for var in list(self.compound.variants):
      if var is variant:
        continue
      
      atoms2 = set([(va.atom, va.chirality) for va in var.varAtoms])
      
      if atoms2 == atoms:
        var.delete()
    
    for group in list(self.atomGroups):
      group.delete()
    
    if not atom.varAtoms:
      if not atom.isDeleted:
        atom.delete()
        
    if not variant.varAtoms:
      variant.delete()
  
  # Snap the atom to one of the specified angles. The angle is chosen based on collisions with already placed atoms.
  def snapToGrid(self, prevAtom, bondLength = 50.0, prevAngle = None, angles = [], remainingAtoms = [], ignoreHydrogens = True):
    
    prevX = prevAtom.coords[0]
    prevY =prevAtom.coords[1]
      
    oldX, oldY, oldZ = self.coords
      
    if len(angles) == 0:
      angles = [120, -120]
    if prevAngle == None:
      prevAngle = 210
    for i in range(len(angles)):
      angles[i] = radians((prevAngle + angles[i]) % 360)

    minD = None
    minI = None
    minPen = None
    
    allAtoms = self.variant.varAtoms - set(remainingAtoms)

    for i, angle in enumerate(angles):
      x = prevX + bondLength * cos(angle)
      y = prevY + bondLength * sin(angle)
      pen = 1
      for atom in allAtoms:
        if atom == self or atom in self.neighbours or (ignoreHydrogens and atom.element == 'H'):
          continue
        atomDist = hypot(x - atom.coords[0], y - atom.coords[1])
        if atomDist < bondLength:
          if atomDist < 1:
            pen *= 100
            if atomDist < 0.000001:
              atomDist = 0.000001
          pen *= 2*bondLength/atomDist
      if not minPen or pen < minPen:
        minPen = pen
        minI = i
        bestX = x
        bestY = y
      if pen == 1:
        break
     
    self.coords = (bestX, bestY, oldZ)
    
    return degrees(angles[minI])
    
  def getPreferredBondAngles(self, prevAngle, neighbours=None, ignoredAtoms = [], ignoreHydrogens=True):
    
    bonds = self.bonds
    nBonds = len(bonds)
    angles = []
    ringAtoms = []
    nHydrogens = 0
    
    if neighbours == None:
      neighbours = sorted(self.neighbours, key=lambda atom: atom.name)
      
    for neighbour in neighbours:
      if neighbour.element == 'H':
        nHydrogens += 1
        
    if ignoreHydrogens:
      nBonds -= nHydrogens
    
    rings = set(self.getRings())
    
    if len(rings) > 0:
      for ring in rings:
        # Hydrogens receive a special treatment.
        #if not ignoreHydrogens:
          #if nBonds == 4:
            #if nHydrogens == 2:
              #angles = [70, 160, -70, -160]
            #if nHydrogens == 1:
              #angles = [180]
          #return angles
        ringSize = len(ring)
        ringAngle = ((ringSize-2) * 180)/ringSize
        angle = (180 - 0.5 * ringAngle)
        if nBonds > 3:
          angle /= nBonds - 2
        if not ignoreHydrogens and abs(360-angle-2*angle) > 0.1:
          for a in [angle, -angle, 2*angle, -2*angle]:
            angles.append(a)
        else:
          for a in [angle, -angle]:
            angles.append(a)
        if angle < 120:
          angles.append(3*angle)
      return angles
    else:
      # Triple bonds or two double bonds have a 180 degrees angle.
      nDouble = 0
      for bond in bonds:
        if bond.bondType == 'triple':
          angles = [180]
        if bond.bondType == 'double':
          nDouble += 1
      if nDouble == len(bonds):
        angles = [180]
    if len(angles) == 0:
      angles = [120, -120]
      
    if prevAngle != None and (90 <= prevAngle < 180 or 270 <= prevAngle < 360):
      for i in range(len(angles)):
        angles[i] = -angles[i]
        
    if nBonds > 2:
      neighbourAngles = []
      for neighbour in neighbours:
        if not neighbour in ignoredAtoms:# and (not ignoreHydrogens or neighbour.element != 'H'):
          neighbourAngle = round(degrees(self.getBondAngle(neighbour)), 0)
          neighbourAngle -= prevAngle
          neighbourAngles.append(neighbourAngle)
      if nBonds == 4:
        if len(neighbourAngles) > 1:
          angles = [67.5, 172.5, 120, -120]
        else:
          angles = [120, -120, 67.5, 172.5]
      elif nBonds >= 4:
        angles = []
        for i in range(1, nBonds):
          angles.append(i * 360/nBonds)
          
      for neighbourAngle in neighbourAngles:
        if abs(neighbourAngle-120) < 1 or abs(neighbourAngle+240) < 1:
          for i in range(len(angles)):
            angles[i] = -angles[i]
          break
          
    return angles

  def findAtomsInBranch(self, firstAtomInBranch, atoms=None):
    
    if not atoms:
      atoms = set([firstAtomInBranch])
    
    if not self in atoms:
      temporarySelfAdd = True
      atoms.add(self)
    else:
      temporarySelfAdd = False
    
    neighbours = set(firstAtomInBranch.neighbours)
    if len(neighbours):

      while neighbours:
        neighbour = neighbours.pop()
        if neighbour == self or neighbour in atoms:
          continue

        atoms.add(neighbour)

        if neighbour.element == 'H':
          continue

        for neighbour2 in neighbour.neighbours:
          if neighbour2 in atoms:
            continue

          atoms.add(neighbour2)
          if neighbour2.element == 'H':
            continue

          atoms.update(neighbour.findAtomsInBranch(neighbour2, atoms))

    if temporarySelfAdd:
      atoms.remove(self)

    return atoms
    
  # Returns a list of atoms sorted by their respective branch lengths, shortest first.
  def getBranchesSortedByLength(self):
    branchLens = []
    for a in self.neighbours:
      branchLens.append([len(self.findAtomsInBranch(a)), a])
    branchLens.sort()
    
    branches = [b[1] for b in branchLens]
    
    return branches
  
  def atomInSameRing(self, atom):
    
    selfRings = self.getRings()
    atomRings = atom.getRings()
    if len(selfRings) > 0 and len(atomRings) > 0:
      for ring in atomRings:
        if ring in selfRings:
          return True
    return False
    
  def snapRings(self, rings, neighbours, atoms, prevAngle, bondLength):
    
    skippedAtoms = set([])
    for ring in rings:
      if len(atoms) == 0:
        return
      for ringAtom in ring:
        if ringAtom in atoms:
          if ringAtom in neighbours:
            neighbours.remove(ringAtom)
          atoms.remove(ringAtom)
        else:
          skippedAtoms.add(ringAtom)
          if ringAtom != self:
            prevAngle = None
      self.variant.snapRingToGrid(ring, self, prevAngle, bondLength, skippedAtoms)
      skippedAtoms.add(self)
      
    for ring in rings:
      for ringAtom in ring:
        if ringAtom in skippedAtoms:
          continue
        ringAtomRings = ringAtom.getRings()
        if ring in ringAtomRings:
          ringAtomRings.remove(ring)
        for ringAtomRing in set(ringAtomRings):
          for atom in atoms:
            if atom in ringAtomRing:
              break
          else:
            ringAtomRings.remove(ringAtomRing)
        if len(ringAtomRings) > 0:
          ringAtomRings = sorted(ringAtomRings, key=lambda ring: len(ring), reverse=True)
          ringAtomNeighbours = sorted(ringAtom.neighbours, key=lambda atom: atom.name)
          ringAtom.snapRings(ringAtomRings, ringAtomNeighbours, atoms, None, bondLength)
          
  def autoSetChirality(self):
    
    variants = self.compound.variants
    atom = self.atom
    stereo = None
    
    if self.chirality in ['a', 'b']:
      return

    chirality = self.getStereochemistry()
    # Make the automatically set chirality lower case to be able to distinguish it from user specified chirality.
    if chirality:
      chirality = chirality.lower()
      
    if self.chirality and self.chirality.isupper():
      branches = self.getBranchesSortedByLength()
      if len(branches) == 4:
        stereo = [branches[3], branches[0], branches[2], branches[1]]
      elif len(branches) >= 4:
        stereo = [branches[3], branches[0], branches[2], branches[1], branches[4:]]
        
        if stereo:
          self.setStereo(stereo)
        
    for var in variants:
      varAtom = var.atomDict.get(atom)
      if not varAtom:
        continue
        
      vAChirality = varAtom.chirality
      if stereo and not varAtom.stereo:
        for a in stereo:
          varAtom.stereo.append(var.atomDict.get(a.atom))
          
      chirality = varAtom.getStereochemistry()
      if chirality:
        chirality = chirality.lower()
        
      if vAChirality and vAChirality.isupper():
        if vAChirality in ('R', 'S'):
          if chirality and vAChirality.lower() != chirality:
            temp = varAtom.stereo[3]
            varAtom.stereo[3] = varAtom.stereo[1]
            varAtom.stereo[1] = temp
            chirality = varAtom.getStereochemistry()
            chirality = chirality.lower()
            if vAChirality.lower() != chirality:
              raise Exception("Stereochemistry of %s different even after attempted swap. (%s and %s)" % (varAtom, vAChirality, chirality))
      else:
        varAtom.chirality = chirality
          
  def getStereochemistry(self):
    
    neighbours = self.neighbours
    nNeighbours = len(neighbours)
    
    stereochemistry = None
    
    if nNeighbours == 4:
      nHydrogens = 0
      for neighbour in neighbours:
        if neighbour.element == 'H':
          nHydrogens += 1
      if nHydrogens <= 1 and self.stereo:
        stereochemistry = self.getStereochemistryRS()
        
    elif nNeighbours == 3:
      for neighbour in neighbours:
        bond = self.getBondToAtom(neighbour)
        if bond.bondType == 'double':
          if len(neighbour.neighbours) == 3:
            stereochemistry = self.getStereochemistryEZ(neighbour)
            
    return stereochemistry

  def getStereochemistryRS(self):
    
    prio = self.getPriorities()

    if prio == None:
      return None
      
    lowPrio = prio[-1]
    
    refBondAngle = self.getBondAngle(prio[0])
    secondBondAngle = (self.getBondAngle(prio[1]) - refBondAngle) % (2*PI)
    thirdBondAngle = (self.getBondAngle(prio[2]) - refBondAngle) % (2*PI)
    
    if secondBondAngle < thirdBondAngle:
      stereo = 1
    elif secondBondAngle > thirdBondAngle:
      stereo = -1
    else:
      return None
      
    lowPrioIndex = self.stereo.index(lowPrio)
    
    if lowPrioIndex == 3:
      stereo *= -1
    elif lowPrioIndex != 1:
      lowHighAngle = abs(self.getBondAngle(lowPrio)-self.getBondAngle(self.stereo[3])) % (2*PI)
      if lowHighAngle > PI/2:
        stereo *= -1
      
        
    if stereo == 1:
      return "R"
    if stereo == -1:
      return "S"
    return None
    
  def getStereochemistryEZ(self, other):
    
    selfPrio = self.getPriorities()
    if selfPrio == None:
      return None
    otherPrio = other.getPriorities()
    if otherPrio == None:
      return None

    angleMain = self.getBondAngle(other)
    selfHighPrio = selfLowPrio = None
    otherHighPrio = otherLowPrio = None
    for atom in selfPrio:
      if atom != other:
        if selfHighPrio == None:
          selfHighPrio = atom
        else:
          selfLowPrio = atom
    for atom in otherPrio:
      if atom != self:
        if otherHighPrio == None:
          otherHighPrio = atom
        else:
          otherLowPrio = atom
    angleHighPrio = selfHighPrio.getBondAngle(otherHighPrio)
    angleLowPrio = selfHighPrio.getBondAngle(otherLowPrio)
    
    diff = abs(angleMain - angleHighPrio)
    altDiff = abs(angleMain - angleLowPrio)
    diff = min(diff, abs(2*PI-diff))
    altDiff = min(altDiff, abs(2*PI-altDiff))
    
    if diff < altDiff:
      return 'Z'
    if diff > altDiff:
      return 'E'
    
    return None

  # This function returns a list of neighbours ranked according to Cahn-Ingold-Prelog rules (not taking more than the fourth level of neighbours into account.
  # The neighbour with highest priority is first in the returned list.
  def getPriorities(self):
    
    prio = 0
    
    firstList = self.getFirstNeighbourPriorities()
    foundSimilar = False
    for i, item in enumerate(firstList):
      for otherItem in firstList[(i+1):]:
        if item[1] == otherItem[1]:
          foundSimilar = True
          break
      if foundSimilar:
        break
    if foundSimilar:
      secondList = self.getSecondNeighbourPriorities()
      thirdList = self.getThirdNeighbourPriorities()
      fourthList = self.getFourthNeighbourPriorities()
    
    n = len(firstList)
    
    prioList = [None] * n

    while prio < n:
      item = firstList[prio]
      if prio + 1 == n:
        prioList[prio] = item[0]
        prio += 1
      else:
        nextItem = firstList[prio+1]
        if item[1] != nextItem[1]:
          prioList[prio] = item[0]
          prio += 1
          continue

        similar = [prio, prio+1]
        i = 2
        while prio + i < n and firstList[prio][1] == firstList[prio+i][1]:
          similar.append(prio+i)
          i += 1
          
          
        nSim = len(similar)
        while nSim > 0:
          newN = 0
          for i in range(1, nSim):
            this = similar[i]
            prev = similar[i-1]
            if secondList[prev][-1] == secondList[this][-1] and thirdList[prev][-1] == thirdList[this][-1] and \
            fourthList[prev][-1] == fourthList[this][-1]:
              return None
              
            if secondList[prev][-1] < secondList[this][-1] or \
            (secondList[prev][-1] == secondList[this][-1] and (thirdList[prev][-1] < thirdList[this][-1] or \
            (thirdList[prev][-1] == thirdList[this][-1] and fourthList[prev][-1] < fourthList[this][-1]))):
              temp = similar[i]
              similar[i] = similar[i-1]
              similar[i-1] = temp
              newN = i
          nSim = newN
          
        for item in similar:
          prioList[prio]=firstList[item][0]
          prio += 1

    return prioList
    
  # This should actually be the atomic number, but here the mass number of the main isotope is used instead. Should still
  # sort in the same order.
  def priorityNumber(self):
    
    if self.atom.element == LINK:
      return ELEMENT_ISO_ABUN['C'][0][1]
    return ELEMENT_ISO_ABUN[self.atom.element][0][1]
    
  def getFirstNeighbourPriorities(self):
    
    priorityList = []
    
    for neighbour in self.neighbours:
      p = neighbour.priorityNumber()
      priorityList.append([neighbour, p])

    priorityList = sorted(priorityList, key=lambda neighbour: neighbour[1], reverse=True)

    return priorityList
    
  def getSecondNeighbourPriorities(self):
    
    priorityList = []
    maxLen = None
    
    for a, p in self.getFirstNeighbourPriorities():
      if a == None:
        continue
      
      localPriorityList = []
      for atom, prio in a.getFirstNeighbourPriorities():
        if atom != self:
          localPriorityList.append([atom, prio])
        bond = a.getBondToAtom(atom)
        if bond.bondType == 'double' or bond.bondType == 'triple' or a.isAromatic():
          localPriorityList.append([None, prio])
          if bond.bondType == 'triple':
            localPriorityList.append([None, prio])
          
      localPriorityList = sorted(localPriorityList, key=lambda neighbour: neighbour[1], reverse=True)
      
      l = len(localPriorityList)
      if maxLen == None or l > maxLen:
        maxLen = l
      
      priorityList.append(localPriorityList)
      
    maxLen -=1

    for localPriorityList in priorityList:
      score = 0
      for i, (a, p) in enumerate(localPriorityList):
        score += p*(10**((maxLen-i)*2))
    
      localPriorityList.append([None, score])
      
    return priorityList
    
  def getThirdNeighbourPriorities(self):
    
    priorityList = []
    maxLen = None
    
    for list in self.getSecondNeighbourPriorities():
      
      localPriorityList = []
      for a, p in list: 
        if a == None:
          continue
        
        for atom, prio in a.getFirstNeighbourPriorities():
          if atom not in self.neighbours:
            localPriorityList.append([atom, prio])
          bond = a.getBondToAtom(atom)
          if bond.bondType == 'double' or bond.bondType == 'triple' or a.isAromatic():
            localPriorityList.append([None, prio])
            if bond.bondType == 'triple':
              localPriorityList.append([None, prio])
          
      l = len(localPriorityList)
      if maxLen == None or l > maxLen:
        maxLen = l
      
      priorityList.append(localPriorityList)

    maxLen -=1

    for localPriorityList in priorityList:
      score = 0
      for i, (a, p) in enumerate(localPriorityList):
        score += p*(10**((maxLen-i)*2))
    
      localPriorityList.append([None, score])
      
    return priorityList

  def getFourthNeighbourPriorities(self):
    
    priorityList = []
    maxLen = None
    nextNeighbours = set()
    
    for list in self.getThirdNeighbourPriorities():
      
      localPriorityList = []
      for a, p in list:
        if a == None:
          continue
      
        for atom, prio in a.getFirstNeighbourPriorities():
          localPriorityList.append([atom, prio])

      l = len(localPriorityList)
      if maxLen == None or l > maxLen:
        maxLen = l
      
      priorityList.append(localPriorityList)

    maxLen -=1

    for localPriorityList in priorityList:
      score = 0
      for i, (a, p) in enumerate(localPriorityList):
        score += p*(10**((maxLen-i)*2))
    
      localPriorityList.append([None, score])

    return priorityList
