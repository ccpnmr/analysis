from math import sin, cos

from ccpnmr.chemBuild.general.Constants import LINK, AROMATIC

from ccpnmr.chemBuild.model.Compound import Compound
from ccpnmr.chemBuild.model.Variant import Variant
from ccpnmr.chemBuild.model.VarAtom import VarAtom
from ccpnmr.chemBuild.model.AtomGroup import AtomGroup
from ccpnmr.chemBuild.model.Atom import Atom
from ccpnmr.chemBuild.model.Bond import Bond

MOLFILE_ATOM_CHARGE_DICT = {'0':0,'1':3,'2':2,'3':1,'4':0,
                            '5':-1,'6':-2,'7':-3,
                            0:'0',3:'1',2:'2',1:'3',
                            -1:'5',-2:'6',-3:'7'}

MOLFILE_BOND_TYPE_DICT = {'1':'single','2':'double','3':'triple',
                          '4':'aromatic','5':'single','6':'single',
                          '7':'double','8':'single',
                          'single':'1', 'double':'2', 'triple':'3',
                          'quadruple':'8', 'aromatic':'4', 'singleplanar':'1'}

def importMolFileV2000(fileName):
  from pathlib import Path
  compoundName = Path(fileName).stem

  fileObj = open(fileName,  'r')
  compound = Compound(compoundName)
  var = Variant(compound)
  compound.defaultVars.add(var)
  
  line = fileObj.readline()
  # compound.name = line.strip() already set from filename

  line = fileObj.readline()
  # Program info

  line = fileObj.readline()
  # Comments

  line = fileObj.readline()
  nAtoms = int(line[0:3])
  nBonds = int(line[3:6])
  # Counts line
  
  atomDict = {}
  hydrogenDict = {}
  aromatics = set()
  a = 0
  
  zMin = None
  zMax = None
  
  for a in range(nAtoms):
    line = fileObj.readline()
    
    
    x = float(line[0:10].strip())
    y = float(line[10:20].strip())
    z = float(line[20:30].strip())
    elem = line[31:34].strip()
    iso  = int(line[34:36].strip())
    charge = MOLFILE_ATOM_CHARGE_DICT[line[36:39].strip()]
    stereo = int(line[39:42].strip() or '0')
    numh = int(line[42:45].strip() or '1') - 1
    stereo = int(line[45:48].strip() or '0')
    vals = int(line[48:52].strip() or '0')
 
    x = float(x) * 50.0
    y = float(y) * 50.0
    z = float(z) * 50.0
    
    if zMin is None:
      zMin = zMax = z
    
    elif z < zMin:
      zMin = z
    
    elif z > zMax:
      zMax = z
    
    name = None
    atom = Atom(compound, elem, name)
    varAtom = VarAtom(var, atom, coords=(x, y, z),  charge=charge)
 
    atomDict[a+1] = varAtom
    hydrogenDict[varAtom] = numh
  
  for b in range(nBonds):
    line = fileObj.readline()
    
    aNum1 = int(line[0:3])
    aNum2 = int(line[3:6])
    bType = MOLFILE_BOND_TYPE_DICT[line[6:9].strip()]
    
    varAtomA = atomDict[aNum1]
    varAtomB = atomDict[aNum2]
    Bond((varAtomA, varAtomB),  bType,  autoVar=False)
    
    if bType == 'aromatic':
      aromatics.add(varAtomA)
      aromatics.add(varAtomB)
  
  for varAtom, numH in list(hydrogenDict.items()):
    angles = list(varAtom.freeValences)
    x, y, z = varAtom.coords
    
    for h in range(numH):
      if angles:
        angle = angles.pop()
      else:
        angle = 0.0
      
      x2 = x + 50.0 * sin(angle)
      y2 = y + 50.0 * cos(angle)
    
      masterAtom = Atom(compound, 'H', None)
      varAtomH = VarAtom(var, masterAtom, coords=(x2, y2, z))
      Bond((varAtom, varAtomH),  'single',  autoVar=False)

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
    
def makeMolFileV2000(var):
   
   compound = var.compound
   atomList = [(va.name, va) for va in var.varAtoms if va.element != LINK]
   atomList.sort()
   atoms = [x[1] for x in atomList]
   bonds = []
   
   for bond in var.bonds:
     varAtomA, varAtomB = bond.varAtoms
     
     if varAtomA.element == LINK:
       continue

     if varAtomB.element == LINK:
       continue
   
     bonds.append(bond)
   
   chiral = 0
   for atom in atoms:
     if atom.chirality:
       chiral = 1
       break
   
   lines = []
   add = lines.append
   
   add(' ' + compound.name)
   add(' Made with CcpNmr ChemBuild')
   add('')
   
   data = (len(atoms), len(bonds), 0, 0, chiral, 0, 0, 0, 0, 0, 999)
   add('%3d%3d%3d%3d%3d%3d%3d%3d%3d%3d%3d V2000' % data)

   atomDict = {}
   for i, atom in enumerate(atoms):
     charge = MOLFILE_ATOM_CHARGE_DICT.get(atom.charge, '0')
     x, y, z = atom.coords
     data = (x/50.0, y/50.0, z/50.0, atom.element, 0, charge, 0, 1, 0, 0, 0, 0, 0, 0, 0,0)
     
     add('%10.4f%10.4f%10.4f %2s%3d%3s%3d%3d%3d%3d%3d%3d%3d%3d%3d%3d' % data)
     atomDict[atom] = i+1
  
   for bond in bonds:
     varAtomA, varAtomB = bond.varAtoms
     i = atomDict[varAtomA]
     j = atomDict[varAtomB]
     bType = MOLFILE_BOND_TYPE_DICT[bond.bondType]
    
     data = (i, j, bType, 0, 0, 0, 0)
     add('%3d%3d%3s%3d%3d%3d%3d' % data)
   
   add(' M  END')
   add(' $$$$')
   add('')
    
   return '\n'.join(lines)
 
