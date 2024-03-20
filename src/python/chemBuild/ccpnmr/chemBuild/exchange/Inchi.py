# The inchi_Stereo0D, inchi_Atom, inchi_Input, inchi_InputINCHI and inchi_Output classes are developed at NIST:
#
# International Chemical Identifier (InChI)
# Version 1
# Software version 1.02
# November 30, 2008
# Developed at NIST
# 
# The InChI library and programs are free software developed under the
# auspices of the International Union of Pure and Applied Chemistry (IUPAC);
# you can redistribute this software and/or modify it under the terms of 
# the GNU Lesser General Public License as published by the Free Software 
# Foundation:
# http://www.opensource.org/licenses/lgpl-license.php
# 


"""
        Interface to INCHI library  (used by InChI generation example)
  
  The implementation is very 'light' and is provided for
  illustrative purposes only.

"""


from os import path
import sys
import string

from ctypes import *


PYINCHI_MAXVAL = 20
PYINCHI_ATOM_EL_LEN = 6
PYINCHI_NUM_H_ISOTOPES = 3
#this flag means isotopic shift relative to avg. atw, not abs. isotopic mass
PYINCHI_ISOTOPIC_SHIFT_FLAG  = 10000


##########################################################
# 0D - S T E R E O  (if no coordinates given)
##########################################################

class inchi_Stereo0D(Structure):
  _fields_ = [("neighbor", c_short * 4),  # 4 atoms always
        ("central_atom", c_short),  # central tetrahedral atom or a central */
                              # atom of allene; otherwise NO_ATOM */
        ("type", c_byte),     # inchi_StereoType0D
        ("parity", c_byte)]   # inchi_StereoParity0D: may be a combination of two parities: */
            # ParityOfConnected | (ParityOfDisconnected << 3), see Note above */
  def dump(self):
    print("\tDump of inchi_Stereo0D structure")
    print('\t\t neighbor: ', end=' ')
    for nbr in self.neighbor:
      print(nbr, end=' ')
    print()
    print('\t\t central_atom: ', self.central_atom)
    print('\t\t type: ', self.type)
    print('\t\t parity: ', self.parity)






##########################################
# inchi_Atom
##########################################

class inchi_Atom(Structure):
  _fields_ = [("x", c_double),  # atom coordinates 
        ("y", c_double),
        ("z", c_double),
        # connectivity 
        ("neighbor", c_short * PYINCHI_MAXVAL),   # adjacency list: ordering numbers of the adjacent atoms, >= 0
        ("bond_type", c_byte * PYINCHI_MAXVAL),   # inchi_BondType 
        # 2D stereo
        ("bond_stereo", c_byte * PYINCHI_MAXVAL),   # inchi_BondStereo2D; negative if the sharp end points to another atom 
        # other atom properties
        ("elname", c_byte * PYINCHI_ATOM_EL_LEN),   # zero-terminated chemical element name: "H", "Si", etc.
        ("num_bonds", c_short ), # number of neighbors, bond types and bond stereo in the adjacency list
        ("num_iso_H", c_byte * (PYINCHI_NUM_H_ISOTOPES+1)), # implicit hydrogen atoms
                    # [0]: number of implicit non-isotopic H
                    # (exception: num_iso_H[0]=-1 means INCHI adds implicit H automatically),
                    # [1]: number of implicit isotopic 1H (protium),
                    # [2]: number of implicit 2H (deuterium),
                    # [3]: number of implicit 3H (tritium) 
        ("isotopic_mass", c_short ),    # 0 => non-isotopic; isotopic mass or 10000 + mass - (average atomic mass)
        ("radical", c_byte  ),      # inchi_Radical
        ("charge", c_byte  )]       # positive or negative; 0 => no charge

  def fdump(self, fw):
    fw.write('\t{\t --- Dump of inchi_Atom structure ---\n')
    s = ""
    for sy in self.elname:
      s = s + chr(sy)
    fw.write('\t\t element: %-s \n' % s )
    fw.write('\t\t charge: %-d radical: %-d isotopic_mass: %-d\n' %   
      (self.charge, self.radical, self.isotopic_mass) )
    fw.write('\t\t num_bonds: %-d\n' %  self.num_bonds)
    fw.write('\t\t neighbor: ')
    for nbr in self.neighbor:
      fw.write(' %-d' % nbr)
    fw.write('\n')
    fw.write('\t\t bond_types: ')
    for bt in self.bond_type:
      fw.write(' %-d ' % bt)
    fw.write('\n')
    fw.write('\t\t bond_stereos: ')
    for bs in self.bond_stereo:
      fw.write(' %-d' % bs)
    fw.write('\n')
    fw.write('\t\t num_iso_H: ')
    for ni in self.num_iso_H:
      fw.write(' %-d' % ni)
    fw.write('\n\t} \n')

  def dump(self):
    self.fdump(sys.stdout)


##########################################
# Structure -> InChI, GetINCHI() 
##########################################

class inchi_Input(Structure):
  # the caller is responsible for the data allocation and deallocation
  _fields_ = [("atom", POINTER(inchi_Atom)),    # actually, pointer to array of inchi_Atom pointers
        ("stereo0D", POINTER(inchi_Stereo0D)), # actually, pointer to array of inchi_Stereo0D
        ("szOptions", c_char_p), # InChI options: space-delimited; each is preceded by '/' or '-' 
        ("num_atoms", c_short), #c_int), # number of atoms in the compound < 1024 
        ("num_stereo0D", c_short)]  # number of 0D stereo elements 





# /* InChI -> Structure, GetStructFromINCHI() */
# typedef struct tagINCHI_InputINCHI {
#     /* the caller is responsible for the data allocation and deallocation */
#     char *szInChI;     /* InChI ASCIIZ string to be converted to a strucure */
#     char *szOptions;   /* InChI options: space-delimited; each is preceded by */
#                        /* '/' or '-' depending on OS and compiler */
# } inchi_InputINCHI;




##########################################################
# InChI -> Structure, GetStructFromINCHI() 
##########################################################

class inchi_InputINCHI(Structure):
  _fields_ = [("szInChI", c_char_p),  # InChI ASCIIZ string to be converted to a strucure 
        ("szOptions", c_char_p)]  # InChI options: space-delimited; each is preceded by
                              # '/' or '-' depending on OS and compiler */

#  the caller is responsible for the data allocation and deallocation



##########################################################################
# inchi_Output
##########################################################################

class inchi_Output(Structure):
  # zero-terminated C-strings allocated by GetINCHI()
  # to deallocate all of them call FreeINCHI() (see below)

  _fields_ = [("szInChI", POINTER(c_char) ), # c_char_p
        ("szAuxInfo", POINTER(c_char) ), 
        ("szMessage", POINTER(c_char) ), 
        ("szLog", POINTER(c_char) ) ]  # c_char_p)]

  def dump(self):
    print("\tDump of inchi_Output structure")
    print('\t\t',self.szInChI)
    print('\t\t',self.szAuxInfo)
    print('\t\t',self.szMessage)
    print('\t\t',self.szLog)


    

def make_pystring(p):
  s = ""  
  try:
    for c in p:
      if c=='\0':
        break
      s = s + c
  except:
    pass
  return s


##########################################################################
# InChI -> Structure
##########################################################################

class inchi_OutputStruct(Structure):
# 4 pointers are allocated by GetStructFromINCHI() 
# to deallocate all of them call FreeStructFromINCHI()
#_fields_ = [("atom", c_long),     # actually, pointer to array of inchi_Atom
      #("stereo0D", c_long), # actually, pointer to array of inchi_Stereo0D

  _fields_ = [("atom", POINTER(inchi_Atom)),   # actually, pointer to array of inchi_Atom
        ("stereo0D", POINTER(inchi_Stereo0D)), # actually, pointer to array of inchi_Stereo0D
        ("num_atoms", c_short),                  # number of atoms in the structure < 1024
        ("num_stereo0D", c_short),               # number of 0D stereo elements 

        ("szMessage", POINTER(c_char)), # Error/warning ASCIIZ message
        ("szLog", POINTER(c_char)), # log-file ASCIIZ string, contains a human-readable list
          # of recognized options and possibly an Error/warning message
        ("WarningFlags", (c_ulong * 2) * 2)]   # warnings, see INCHIDIFF in inchicmp.h



#typedef struct tagINCHI_OutputStruct {
    #inchi_Atom     *atom;         /* array of num_atoms elements */
  #inchi_Stereo0D *stereo0D;     /* array of num_stereo0D 0D stereo elements or NULL */
    #AT_NUM          num_atoms;    /* number of atoms in the structure < 1024 */
    #AT_NUM          num_stereo0D; /* number of 0D stereo elements */
    #char           *szMessage;    /* Error/warning ASCIIZ message */
    #char           *szLog;        /* log-file ASCIIZ string, contains a human-readable list */
                                  #/* of recognized options and possibly an Error/warning message */
    #unsigned long  WarningFlags[2][2]; /* warnings, see INCHIDIFF in inchicmp.h */
                                       #/* [x][y]: x=0 => Reconnected if present in InChI otherwise Disconnected/Normal
                                                  #x=1 => Disconnected layer if Reconnected layer is present
                                                  #y=1 => Main layer or Mobile-H
                                                  #y=0 => Fixed-H layer
                                        #*/
#}inchi_OutputStruct;


from ccpnmr.chemBuild.model.Atom import Atom
from ccpnmr.chemBuild.model.Bond import Bond
from ccpnmr.chemBuild.model.Compound import Compound
from ccpnmr.chemBuild.model.VarAtom import VarAtom
from ccpnmr.chemBuild.model.Variant import Variant
from ccpnmr.chemBuild.model.Bond import BOND_TYPE_VALENCES, BOND_STEREO_DICT
from memops.qtgui.MessageDialog import showError, showWarning
  
# def makeInchi(variant):
#
#   libDir = path.join(path.dirname(__file__), '..', '..', '..', '..', '..', 'c', 'inchi', '')
#
#   opsys = sys.platform
#   if (opsys[:3]=='win'):
#     libname = 'libinchi.dll'
#   else:
#     libname = 'libinchi.so'
#
#   libinchi = cdll.LoadLibrary(libDir+libname)
#
#   atoms = list(variant.varAtoms)
#   bonds = variant.bonds
#   nAtoms = len(atoms)
#   nBonds = len(bonds)
#
#   # Make array of inchi_Atom (storage space) anf resp. pointers
#
#   iatoms = (inchi_Atom * nAtoms) ()
#   piatoms = (POINTER(inchi_Atom) * nAtoms) ()
#
#   valences = []
#
#   for ia, atom in enumerate(atoms):
#
#     # Make inchi_Atom
#
#     elname = (c_byte * PYINCHI_ATOM_EL_LEN) (PYINCHI_ATOM_EL_LEN*0)
#     num_iso_H = (c_byte * (PYINCHI_NUM_H_ISOTOPES+1)) ((PYINCHI_NUM_H_ISOTOPES+1)*0)
#     neighbor = (c_short * PYINCHI_MAXVAL) (PYINCHI_MAXVAL*0)
#     bond_type = (c_byte * PYINCHI_MAXVAL) (PYINCHI_MAXVAL*0)
#     bond_stereo = (c_byte * PYINCHI_MAXVAL) (PYINCHI_MAXVAL*0)
#
#     (x, y, z) = atom.coords
#     z = 0
#     y = -y
#     for count, e in enumerate(atom.element):
#       elname[count] = ord(e)
#     radical = 0
#     charge = atom.charge
#     isotopic_mass = 0
#     numBonds = keptBonds = len(atom.neighbours)
#
#     count = 0
#     for atomNeighbour in atom.neighbours:
#       neighbourNr = atoms.index(atomNeighbour)
#
#       # InChI does not like repetition of bonds.
#       if neighbourNr <= ia:
#         keptBonds -= 1
#         continue
#
#       neighbor[count] = neighbourNr
#       bond = atom.getBondToAtom(atomNeighbour)
#       bond_type[count] = BOND_TYPE_VALENCES[bond.bondType]
#       if bond_type[count] == 1 and atom.isAromatic() and atomNeighbour.isAromatic():
#         bond_type[count] = 4
#         #print atom, atomNeighbour
#       if atom.stereo or atomNeighbour.stereo:
#         if atom.stereo:
#           for index, stereo in enumerate(atom.stereo):
#             if stereo == atomNeighbour:
#               break
#           multiplier = 1
#           stereoCnt = numBonds
#         else:
#           for index, stereo in enumerate(atomNeighbour.stereo):
#             if stereo == atom:
#               break
#           multiplier = -1
#           stereoCnt = len(atomNeighbour.neighbours)
#
#         stereoDict = BOND_STEREO_DICT[stereoCnt]
#         direction = stereoDict[index]
#         if direction >= 1:
#           bond_stereo[count] = multiplier * 1
#         elif direction <= -1:
#           bond_stereo[count] = multiplier * 6
#         #print atom, atomNeighbour, direction, multiplier, bond_stereo[count]
#
#       count += 1
#
#     iatoms[ia] = inchi_Atom(
#         x, y, z,
#         neighbor,
#         bond_type,
#         bond_stereo,
#         elname,
#         keptBonds,
#         num_iso_H,
#         isotopic_mass,
#         radical,
#         charge)
#
#     #piatoms[ia] = pointer(iatoms[ia])
#
#   istereo0D = (inchi_Stereo0D * 1) ()
#   #pistereo0D = (POINTER(inchi_Stereo0D) * 1) ()
#
#   inchiInput = inchi_Input(
#       iatoms,   # inchi-style atoms
#       istereo0D,      # stereo0D (empty)
#       bytes("", 'utf-8'),    # command line switches
#       nAtoms,    # natoms
#       0   # num_stereo0D
#       )
#
#   #szInChI  = create_string_buffer(1) # NB: will be reallocd by inchi dll
#   #szAuxInfo  = create_string_buffer(1)
#   #szMessage = create_string_buffer(1)
#   #szLog = create_string_buffer(1)
#   inchiOutput = inchi_Output()
#   #inchiOutput = inchi_Output( cast(szInChI, POINTER(c_char)),
#       #cast(szAuxInfo, POINTER(c_char)),
#       #cast(szMessage, POINTER(c_char)),
#       #cast(szLog, POINTER(c_char)) )
#
#
#   # Call DLL function(s)
#
#   result = libinchi.GetINCHI(byref(inchiInput), byref(inchiOutput))  # 0 = okay,
#                 # 1 => warning,
#                 # 2=>error,
#                 # 3=>fatal
#
#   if result >= 2:
#     showError('InChI creation error:', make_pystring(inchiOutput.szLog), parent=None)
#     return None
#   elif result == 1:
#     showWarning('InChI creation warning:', make_pystring(inchiOutput.szLog), parent=None)
#     print('InChI creation warning:')
#
#   # Process results
#
#   si = make_pystring(inchiOutput.szInChI)
#
#   libinchi.FreeINCHI(byref(inchiOutput))
#
#   return si
#
# def importInchi(inchiString):
#
#   compound = Compound('Unnamed')
#   var = Variant(compound)
#   compound.defaultVars.add(var)
#
#   libDir = path.join(path.dirname(__file__), '..', '..', '..', '..', '..', 'c', 'inchi', '')
#
#   opsys = sys.platform
#   if (opsys[:3]=='win'):
#     libname = 'libinchi.dll'
#   else:
#     libname = 'libinchi.so'
#
#   libinchi = cdll.LoadLibrary(libDir+libname)
#
#   inchiString = inchiString.strip()
#
#   inchiBytes = bytes(inchiString, 'utf-8')
#
#   #inchiInput = inchi_InputINCHI(inchiString, "")
#   inchiInput = inchi_InputINCHI(inchiBytes, bytes("", 'utf-8'))
#
#   inchiOutput = inchi_OutputStruct()
#
#   result = libinchi.GetStructFromINCHI(byref(inchiInput), byref(inchiOutput))
#
#   if result >= 2:
#     showError('InChI reading error:', make_pystring(inchiOutput.szLog), parent=None)
#     return None
#   elif result == 1:
#     showWarning('InChI reading warning:', make_pystring(inchiOutput.szLog), parent=None)
#
#   inchiAtoms = inchiOutput.atom
#   nAtoms = inchiOutput.num_atoms
#
#   if nAtoms == 0:
#     showError('Could not create compound from InChI.', 'No InChI error reported', parent=None)
#     return None
#
#   mapping = []
#
#   for i in range(nAtoms):
#     iAtom = inchiAtoms[i]
#     element = ""
#     for eln in iAtom.elname:
#       element = element + chr(eln)
#     element = make_pystring(element)
#     charge = iAtom.charge
#
#     a = Atom(compound, element, None)
#     va = VarAtom(var, a, charge = charge)
#
#     mapping.append(va)
#
#   for i in range(nAtoms):
#     iAtom = inchiAtoms[i]
#     va = mapping[i]
#
#     for b in range(iAtom.num_bonds):
#       neighbor = iAtom.neighbor[b]
#       bt = iAtom.bond_type[b]
#
#       if bt == 2:
#         bondType = 'double'
#       elif bt == 3:
#         bondType = 'triple'
#       else:
#         bondType = 'single'
#
#
#       nva = mapping[neighbor]
#
#       bond = Bond([va, nva], bondType)
#
#     # Add hydrogens.
#     newAtoms = []
#     for val in va.freeValences:
#       masterAtom = Atom(compound, 'H', None)
#       VarAtom(None, masterAtom) # All vars
#
#       hydrogen = var.atomDict[masterAtom]
#       newAtoms.append(hydrogen)
#
#     for newAtom in newAtoms:
#       Bond((va, newAtom), autoVar=True)
#
#   stereo0D = inchiOutput.stereo0D
#
#   for i in range(inchiOutput.num_stereo0D):
#
#     stereo = stereo0D[i]
#
#     if stereo.type == 1:
#       stereoAtom1 = mapping[stereo.neighbor[1]]
#       stereoAtom2 = mapping[stereo.neighbor[2]]
#       if stereo.parity == 1:
#         stereoAtom1.chirality = 'Z'
#         stereoAtom2.chirality = 'Z'
#       elif stereo.parity == 2:
#         stereoAtom1.chirality = 'E'
#         stereoAtom2.chirality = 'E'
#
#     elif stereo.type == 2:
#       stereoAtom = mapping[stereo.central_atom]
#       prio = stereoAtom.getPriorities()
#
#       branches = stereoAtom.getBranchesSortedByLength()
#       if len(branches) == 4:
#         stereoAtom.stereo = [branches[3], branches[0], branches[2], branches[1]]
#       elif len(branches) >= 4:
#         stereoAtom.stereo = [branches[3], branches[0], branches[2], branches[1], branches[4:]]
#
#       n0 = mapping[stereo.neighbor[0]]
#       n1 = mapping[stereo.neighbor[1]]
#       n2 = mapping[stereo.neighbor[2]]
#       n3 = mapping[stereo.neighbor[3]]
#       n0Prio = prio.index(n0)
#       n1Prio = prio.index(n1)
#       n2Prio = prio.index(n2)
#       n3Prio = prio.index(n3)
#
#       # If the InChI atom order is not the same as ChemBuild priorities the chirality needs to be flipped.
#       if n0Prio != 3 or n1Prio != 2 or n2Prio !=1 or n3Prio !=0:
#         flip = True
#       else:
#         flip = False
#
#       if stereo.parity == 1:
#         if flip:
#           stereoAtom.chirality = 'R'
#         else:
#           stereoAtom.chirality = 'S'
#       elif stereo.parity == 2:
#         if flip:
#           stereoAtom.chirality = 'S'
#         else:
#           stereoAtom.chirality = 'R'
#
#   libinchi.FreeStructFromINCHI(byref(inchiOutput))
#
#   return compound
  
