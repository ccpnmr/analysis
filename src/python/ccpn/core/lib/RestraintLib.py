"""General utilities for Restraints

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.lib import Pid


def dihedralName(project, restraintItem:tuple) -> str:
  """Get dihedral angle name from four-element atomId tuple"""

  if len(restraintItem) == 4:
    # Dihedrals must have four atomId items

    residues = []
    atomNames = []
    for atomId in restraintItem:
      ll = Pid.splitId(atomId)
      if None in ll:
        project._logger.info("Could not calculate dihedral name - unrecognised atom in %s"
                             % (restraintItem,))
        return None
      atomNames.append(ll[-1])
      residues.append(project.getByPid(Pid.createPid('Residue', *ll[:3])))

    if None in atomNames or None in residues:
      # These are not correct atomId. Just return NOne
      return None

    if residues[0]._wrappedData.molResidue.nextMolResidue is residues[-1]._wrappedData.molResidue:
      # last residue is sequential successor to first
      # Sequential dihedrals for protein, DNA, and RNA
      if (atomNames == ['N', 'CA', 'C', 'N'] and
          residues[0] is residues[1] and
          residues[0] is residues[2]):
        return 'PSI'
      elif (atomNames == ['C', 'N', 'CA', 'C'] and
          residues[1] is residues[2] and
          residues[1] is residues[3]):
        return 'PHI'
      elif (atomNames == ['CA', 'C', 'N', 'CA'] and
          residues[0] is residues[1] and
          residues[2] is residues[3]):
        return 'OMEGA'
      elif atomNames == ("O3'", "P", "O5'", "C5'"):
        return 'ALPHA'
      elif atomNames == ("C4'", "C3'", "O3'", "P"):
        return 'EPSILON'
      elif atomNames == ("C3'", "O3'", "P", "O5'"):
        return 'ZETA'
    elif (
        residues[0] is residues[1] and
        residues[1] is residues[2] and
        residues[2] is residues[3] ):
      # Intraresidue dihedrals. NB, CHI dihedrals will only catch standard residues
      # and others with the same atom names
      if (atomNames[:3] == ['N', 'CA', 'CB'] and
          atomNames[3] in ('CG', 'OG', 'SG', 'CG1')):
        return 'CHI1'
      elif (atomNames[:2] == ['CA', 'CB'] and
            atomNames[2] in ('CG', 'CG1') and
            atomNames[3] in ('CD', 'CD1', 'ND1', 'SD')):
        return 'CHI2'
      elif atomNames[:2] == ('CB', 'CG'):
        if atomNames[2:] in (('CD', 'OE1'), ('CD', 'CE'), ('CD', 'NE'), ('SD', 'CE'),):
          return 'CHI3'
      elif atomNames in (('CG', 'CD', 'CE', 'NZ'), ('CG', 'CD', 'NE', 'CZ')):
        return 'CHI4'
      elif atomNames == ('CD', 'NE', 'CZ', 'NH1'):
        return 'CHI5'
      elif atomNames in (("O4'", "C1'", 'N1', 'C2'), ("O4'", "C1'", 'N9', 'C4')):
        return 'CHI'
      elif atomNames == ("P", "O5'", "C5'", "C4'"):
        return 'BETA'
      elif atomNames == ("O5'", "C5'", "C4'", "C3'"):
        return 'GAMMA'
      elif atomNames == ("C5'", "C4'", "C3'", "O3'"):
        return 'DELTA'
  #
  return None




