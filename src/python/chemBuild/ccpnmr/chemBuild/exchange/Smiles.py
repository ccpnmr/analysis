from math import sin, cos, atan2, pi

from ccpnmr.chemBuild.general.Constants import AROMATIC

from ccpnmr.chemBuild.model.Compound import Compound
from ccpnmr.chemBuild.model.Variant import Variant
from ccpnmr.chemBuild.model.VarAtom import VarAtom
from ccpnmr.chemBuild.model.Atom import Atom
from ccpnmr.chemBuild.model.AtomGroup import AtomGroup
from ccpnmr.chemBuild.model.Bond import Bond

organicAtoms = set(["B", "C", "N", "O", "P", "S", "F", "Cl", "Br", "I"])
cnos = set(["C", "N", "O", "S"])

def importSmiles(smilesString):
  
  compound = Compound('Unnamed')
  var = Variant(compound)
  compound.defaultVars.add(var)
  
  aromatics = set()
  exludeHydrogens = set()
  rings = {}
  branch = []
  chirals = {}
  
  def _addStereo(varAtom1, varAtom2):

    varAtom1.stereo.append(varAtom2)
    
    if len(varAtom1.stereo) == 4:
      if chirals[varAtom1] > 0:
        a, b, c, d = varAtom1.stereo
        varAtom1.stereo = [a, d, c, b]
 
      del chirals[varAtom1]
  
  n = len(smilesString)
  
  i = 0
  hIndex = 1
  prev = None
  bondType = 'single'
  configList = ''
  lastDouble = None
  addOrder = []
   
  while i < n:
    element = None
    charge = 0
    chiral = 0
    numH = None
    isAromatic = False
    char = smilesString[i:i+1]
    
    if prev:
      x, y, z = prev.coords
    
    else:
      x = 0.0
      y = 0.0
      z = 0.0
    
    if char.isspace():
      i += 1
      continue
      
    if smilesString[i:i+2] in organicAtoms:
      element = smilesString[i:i+2]
    
    elif char.upper() in organicAtoms:
      element = char.upper()
      
      if (element in cnos) and  char.islower():
        isAromatic = True
    
    elif char == '[':
      
      i += 1
      char = smilesString[i:i+1]
      while char.isdigit(): # isotope label
        i += 1
        char = smilesString[i:i+1]
      
      element = char.upper()
      if (element in cnos) and  char.islower():
        isAromatic = True
      
      i += 1
      char = smilesString[i:i+1]
      
      if char == '@':
        i += 1
        chiral = -1
        char = smilesString[i:i+1]

      if char == '@':
        i += 1
        chiral = 1
        char = smilesString[i:i+1]
      
      if char not in 'H+-]':
        element += char
        
        i += 1
        char = smilesString[i:i+1]

      if char == 'H':
        numH = 1
        
        i += 1
        char = smilesString[i:i+1]
        
        if char.isdigit():
          numH = int(char)
          
          i += 1
          char = smilesString[i:i+1]
      
      if char == '+':
        while char == '+':
          charge += 1
 
          i += 1
          char = smilesString[i:i+1]
        
        if char.isdigit():
          charge = int(char)
       
          i += 1
          char = smilesString[i:i+1]
       
        
      if char == '-':

        while char == '-':
          charge -= 1

          i += 1
          char = smilesString[i:i+1]
        
        if char.isdigit():
          charge = -int(char)
    
          i += 1
          char = smilesString[i:i+1]
    
    if char == '=':
      bondType = 'double'
      
    elif char == '#':
      bondType = 'triple'

    elif char == ':':
      bondType = 'aromatic'

    elif char == '-':
      bondType = 'single'

    elif char.isdigit() or char == '%':

      if char.isdigit():
        ringKey = char
      
      else:
        i += 1
        char = smilesString[i:i+1]
        ringKey = '' 
        
        while char.isdigit():
          ringKey += char
          
          i += 1
          char = smilesString[i:i+1]
        
        i -= 1
        char = smilesString[i:i+1]        
          
      if ringKey in rings:
        varAtomB, bondTypeB = rings[ringKey]
        Bond((varAtomB, prev),  bondTypeB,  autoVar=False)
        
        if bondTypeB == 'double':
          lastDouble = (prev, varAtomB)

        if prev in chirals:
          _addStereo(prev, varAtomB)

        if varAtomB in chirals:
          _addStereo(varAtomB, prev)
        
        var.minimise2d(maxCycles=4)
        
        if ringKey in varAtomB.stereo:
          index = varAtomB.stereo.index(ringKey)
          varAtomB.stereo[index] = prev

        if ringKey in prev.stereo:
          index = prev.stereo.index(ringKey)
          prev.stereo[index] = varAtomB
        
        del rings[ringKey]
        
      else:
        rings[ringKey] = prev, bondType
        
        if prev in chirals:
          _addStereo(prev, ringKey)
        
      bondType = 'single'

    elif char == '(':
      branch.append(prev)
    
    elif char == ')':
      if branch:
        prev = branch.pop()

    elif char == '/':
      configList += char
   
    elif char == '\\':
      configList += char
    
    elif char == '@':
      # TBD proper coordinate-based, clock or anti
      prev.setChirality('RS')

    elif char == '.':
      bondType = None

    elif char == '>':
      bondType = None
      
    if element:    
      atom = Atom(compound, element, None)
      
      angle = 1.57
      if prev:
        prev.updateValences()
        freeValences = prev.freeValences
        
        if freeValences:
          numVal = len(freeValences)
          m = numVal//2
          
          if numVal % 2 == 0:
            angle1 = freeValences[m-1] % (2*pi)
            angle2 = freeValences[m] % (2*pi)
            s = (sin(angle1) + sin(angle2)) / 2.0
            c = (cos(angle1) + cos(angle2)) / 2.0
            angle = atan2(s,c)
          
          else:
            angle = freeValences[m] 
                    
      x += 50.0 * sin(angle)
      y += 50.0 * cos(angle)
       
      varAtom = VarAtom(var, atom, coords=(x, y, z),  charge=charge)
      varAtom.updateValences()
      addOrder.append(varAtom)
      
      if chiral:
        varAtom.stereo = [prev,]
        chirals[varAtom] = chiral
      
      if isAromatic:
        aromatics.add(varAtom)
      
      if numH:
        angles = list(varAtom.freeValences)
                
        for h in range(numH):
          if angles:
            angle = angles.pop()
          else:
            angle = 0.0
      
          x2 = x + 50.0 * sin(angle)
          y2 = y + 50.0 * cos(angle)
           
          name = 'H%d' % hIndex
          hIndex += 1
          masterAtom = Atom(compound, 'H', name)
          varAtomH = VarAtom(var, masterAtom, coords=(x2, y2, z))
          Bond((varAtom, varAtomH),  'single',  autoVar=False)
          
          if varAtom in chirals:
            _addStereo(varAtom, varAtomH)
     
      elif numH == 0:
        exludeHydrogens.add(varAtom)
      
      if prev and bondType:
        Bond((varAtom, prev),  bondType,  autoVar=False)
        
        if bondType == 'double':
          lastDouble = (prev, varAtom)
          
        bondType = 'single'
        prev.updateValences()
        varAtom.updateValences()
      else:
        bondType = 'single'
      
      for varAtomB in list(chirals.keys()):
        if varAtomB in varAtom.neighbours:
          _addStereo(varAtomB, varAtom)
      
      if lastDouble and len(configList) > 1:
        
        config = configList[-2:]
        varAtomA, varAtomB = lastDouble
        x1, y1, z1 = varAtomA.coords
        x2, y2, z2 = varAtomB.coords
        
        dx = x2-x1
        dy = y2-y1
        
        angle = atan2(dx, dy)
        
        cx = (x1+x2)/2.0
        cy = (y1+y2)/2.0
        
        da = 1.57
        nudge = 30.0

        if config == '/\\':
          x3 = nudge * sin(angle+da)
          y3 = nudge * cos(angle+da)
          
          x1 += x3
          x2 += x3
          y1 += y3
          y2 += y3
          varAtomA.coords = x1, y1, z1
          varAtomB.coords = x2, y2, z2
        
        elif config == '//':
          x3 = nudge * sin(angle+da)
          y3 = nudge * cos(angle+da)
          
          x1 += x3
          y1 += y3
          varAtomA.coords = x1, y1, z1

          x3 = nudge * sin(angle-da)
          y3 = nudge * cos(angle-da)
          
          x2 += x3
          y2 += y3
          varAtomB.coords = x2, y2, z2
        
        elif config == '\\\\':

          x3 = nudge * sin(angle-da)
          y3 = nudge * cos(angle-da)
          
          x1 += x3
          y1 += y3
          varAtomA.coords = x1, y1, z1

          x3 = nudge * sin(angle+da)
          y3 = nudge * cos(angle+da)
          
          x2 += x3
          y2 += y3
          varAtomB.coords = x2, y2, z2
        
        elif config == '\\/':
          x3 = nudge * sin(angle-da)
          y3 = nudge * cos(angle-da)
          
          x1 += x3
          x2 += x3
          y1 += y3
          y2 += y3
          varAtomA.coords = x1, y1, z1
          varAtomB.coords = x2, y2, z2
        
        lastDouble = None
    
      prev = varAtom
    
    
    i += 1
      
  # set aromatics
  
  if aromatics:
    rings = var.getRings(aromatics)
    
    for varAtoms2 in rings:
      if varAtoms2 & aromatics == varAtoms2:
        varAtoms3 = [va for va in addOrder if va in varAtoms2]
      
        x, y, z = var.getCentroid(varAtoms3)
        dAngle = 2.0 * pi / float(len(varAtoms3))
        
        angle = 0.0
        for j, va in enumerate(varAtoms3):
          x1 = x + 50.0 * sin(angle)
          y1 = y + 50.0 * cos(angle)
          va.coords = (x1, y1, z)
          angle += dAngle
        
        AtomGroup(compound, varAtoms2, AROMATIC)
        var.minimise2d(varAtoms2, maxCycles=50)
  
  
  # add H
  for varAtom in list(var.varAtoms):
    if varAtom.element not in cnos:
      continue
    
    if varAtom in exludeHydrogens:
      continue
    
    varAtom.updateValences()
    newAtoms = []
    x, y, z = varAtom.coords

    for angle in list(varAtom.freeValences):
      x2 = x + 34.0 * sin(angle)
      y2 = y + 34.0 * cos(angle)
      
      name = 'H%d' % hIndex
      hIndex += 1
      
      masterAtom = Atom(compound, 'H', name)
      hydrogen = VarAtom(var, masterAtom, coords=(x2,y2, z))
      Bond((hydrogen, varAtom), 'single', autoVar=False)
      
      
  compound.center((0,  0,  0))
  var.minimise2d(maxCycles=50)
  var.minimise3d(maxCycles=50)
  var.minimise2d(maxCycles=50)
  var.checkBaseValences()
  #var.shuffleStereo()
    
  return compound
