
from ccpnmr.chemBuild.general.Constants import LINK, AROMATIC

from ccpnmr.chemBuild.model.Compound import Compound
from ccpnmr.chemBuild.model.Variant import Variant
from ccpnmr.chemBuild.model.VarAtom import VarAtom
from ccpnmr.chemBuild.model.Atom import Atom
from ccpnmr.chemBuild.model.AtomGroup import AtomGroup
from ccpnmr.chemBuild.model.Bond import Bond

MOL2_MOLTYPES = {'protein':'PROTEIN',
                 'DNA':'NUCLEIC_ACID',
                 'RNA':'NUCLEIC_ACID',
                 'DNA/RNA':'NUCLEIC_ACID',
                 'carbohydrate':'SACCHARIDE', 
                 'other':'SMALL'}

MOL2_ELEMENTMAP = {'C':'C.3', 'N':'N.3', 'O':'O.3','S':'S.3', 
                   'P':'P.3', 'H':'H', 'Br':'Br', 'Cl':'Cl',
                   'F':'F',' I':'I',' Na':'Na',' K':'K',' Ca':'Ca',
                   'Li':'Li',' Al':'Al',' Si':'Si',' Mg':'Mg',
                   'Cr':'Cr.th',' Se':'Se',' Fe':'Fe',' Cu':'Cu',
                   'Zn':'Zn',' Sn':'Sn',' Mo':'Mo',' Mn':'Mn',
                   'Co':'Co.oh'}
                    

MOL2_MOL_TAG  = '@<TRIPOS>MOLECULE'
MOL2_ATOM_TAG = '@<TRIPOS>ATOM'
MOL2_BOND_TAG = '@<TRIPOS>BOND'

MOL2_BOND_TYPES = {'single':'1', 'double':'2', 'aromatic':'ar',
                   'triple':'3', 'dative':'1', 'singleplanar':'1',
                   '1':'single', '2':'double', 'ar':'aromatic',
                   '3':'triple', 'am':'singleplanar'}
                      
def importMol2(fileName):  
  from pathlib import Path
  compoundName = Path(fileName).stem
  fileObj = open(fileName,  'r')
  compound = Compound(compoundName)
  var = Variant(compound)
  compound.defaultVars.add(var)
  
  zMin = None
  zMax = None
  
  mode = None
  line = fileObj.readline()
  atomDict = {}
  atomInfo = {}
  bondInfo = []
  usedNames = set()
  while line:
    line = line.strip()
    
    if not line:
      line = fileObj.readline()
      continue
    
    if line.startswith('#'):
      line = fileObj.readline()
      continue
    
    if line.startswith('@'):
      n = 0
      if MOL2_MOL_TAG in line:
        mode = 1
      elif  MOL2_ATOM_TAG in line:
        mode = 2
      elif MOL2_BOND_TAG in line:
        mode = 3
      else:
        mode = 0 
    
    elif mode:
      n += 1
      if mode == 1:
        if n == 1:
          if not compound.name and line:
            compound.name = line
        
      elif mode == 2:
        data = line.split()
        aNum, aName,  x, y, z,  aType = data[:6]
        atomInfo[aNum] = aType
        
        if aType in ():
          elem = '?'
        
        else:
          elem = aType.split('.')[0]
        
        if len(data) > 8:
          charge = int(float(data[8]))
        else:
          charge = 0  
        
        if aName in usedNames:
          name = None
        else:
          name = aName
          
        
        x = float(x) * 50.0
        y = float(y) * 50.0
        z = float(z) * 50.0
        atom = Atom(compound, elem, name)
        varAtom = VarAtom(var, atom, coords=(x, y, z),  charge=charge)
        atomDict[aNum] = varAtom
        usedNames.add(atom.name)
        
        if zMin is None:
          zMin = zMax = z
 
        elif z < zMin:
          zMin = z
 
        elif z > zMax:
          zMax = z
        
        if aType == 'N.4':
          varAtom.setCharge(1,  autoVar=False)
        
      elif mode == 3:
        data = line.split()
        bondInfo.append(data[1:4])
        
    
    line = fileObj.readline()
  
  fileObj.close()  
  co2Done = set()
  aromatics = set()
  
  for j,  k,  bType in bondInfo:
    varAtomA = atomDict[j]
    varAtomB = atomDict[k]
    
    bondType = MOL2_BOND_TYPES.get(bType, 'single')
    
    if bondType == 'aromatic':
      aromatics.update([varAtomA, varAtomB])
    
    aTypeA = atomInfo[j]
    aTypeB = atomInfo[k]
    
    if (bondType == 2) and set([aTypeA,  aTypeB]) == set(['C.2',  'O.co2']):
      if varAtomA.element == 'O':
        if k in co2Done:
          bondType = 1
          varAtomA.setCharge(-1)
          
        co2Done.add(k)  
        
      elif varAtomB.element == 'O':
        if j in co2Done:
          bondType = 1
          varAtomB.setCharge(-1)
          
        co2Done.add(j) 
    
    bond = Bond((varAtomA, varAtomB),  bondType,  autoVar=False)
  
  if aromatics:
    rings = var.getRings(aromatics)
    
    for varAtoms2 in rings:
      if varAtoms2 & aromatics == varAtoms2:
        AtomGroup(compound, varAtoms2, AROMATIC)
      
  compound.center((0,  0,  0))
  var.checkBaseValences()
  if (zMax-zMin) > 1e-4:
    var.deduceStereo()
                    
  return compound
  
def makeMol2(var):
  compound = var.compound
  
  lines = []
  add = lines.append
  
  add('# Created with CcpNmr ChemBuild')
  add(MOL2_MOL_TAG)
  add('"%s"' % compound.name)
  
  uniqBonds = set()
  bonds = []
  for bond in var.bonds:
    varAtomA, varAtomB = bond.varAtoms
    if varAtomA.element == LINK:
      continue
    
    if varAtomB.element == LINK:
      continue
   
    bonds.append(bond)
    uniqBonds.add(frozenset(bond.varAtoms))

  add('%d %d' % (len(var.varAtoms),  len(uniqBonds)))
  add(MOL2_MOLTYPES.get(compound.ccpMolType,  'SMALL'))
  add('USER_CHARGES')
  add(MOL2_ATOM_TAG)
  
  atoms = [(a.name,  a) for a in var.varAtoms]
  atoms.sort()
  atoms = [x[1] for x in atoms]
  atomDict = {}
  
  for i, atom in enumerate(atoms):
    elem = atom.element
    if elem == LINK:
      continue
    
    atomDict[atom] = i+1
    if elem in ('C', 'N',):
      for bond in atom.bonds:
        if bond.bondType == 'triple':
          atomType = elem + '.1'
          break
        elif bond.bondType == 'double':
          atomType = elem + '.2'
          break
      else:
        if (elem == 'N') and (len(atom.bonds) == 4):
          atomType = 'N.4'
        else:  
          atomType = MOL2_ELEMENTMAP[elem]
    
    elif elem in ('O', 'S'):
      for bond in atom.bonds:
        if bond.bondType == 'double':
          atomType = elem + '.2'
          break
      else:
        atomType = MOL2_ELEMENTMAP[elem]
      
    else:
      atomType = MOL2_ELEMENTMAP.get(elem,  'HEV')    
    
    x, y, z = [xyz/50.0 for xyz in atom.coords]
    add('%d %s %.3f %.3f %.3f %s' % (i+1,  atom.name,  x,  y,  z,  atomType))
  
  add(MOL2_BOND_TAG)
  done = set()
  
  coSet = set(['C','O'])
  
  i = 0
  for bond in bonds:
    key = frozenset(bond.varAtoms)
    if key in done:
      continue
    i += 1  
    done.add(key)  
    atomA, atomB = bond.varAtoms
    j = atomDict[atomA]
    k = atomDict[atomB]
    
    if bond.bondType == 'singleplanar':
      bondType = '1'
      
      if (atomA.element == 'N') and (atomB.element == 'C'):
        for bond2 in atomB.bonds:
          if (bond2 is not bond) and (bond2.bondType == 'double'):
            elements = set([a.element for a in bond2.varAtoms])
            if elements == coSet:
              bondType = 'am'
              break
              
      if (atomA.element == 'C') and (atomB.element == 'V'):
        for bond2 in atomA.bonds:
          if (bond2 is not bond) and (bond2.bondType == 'double'):
            elements = set([a.element for a in bond2.varAtoms])
            if elements == coSet:
              bondType = 'am'
              break
    
    else:
      bondType = MOL2_BOND_TYPES[bond.bondType]
    
    add('%d %d %d %s' % (i, j, k, bondType))

  return '\n'.join(lines)
