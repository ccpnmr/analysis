"""General utilities

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

from ccpncore.util import pid


def dihedralName(project, restraintItem:tuple) -> str:
  """Get dihedral angle name from four-element atomId tuple"""

  if len(restraintItem) == 4:
    # Dihedrals must have four atomId items

    residues = []
    atomNames = []
    for atomId in restraintItem:
      ll = pid.splitId(atomId)
      atomNames.append(ll[-1])
      residues.append(project.getById(pid.makePid('Residue', *ll[:3])))

    if None in atomNames or None in residues:
      # These are not correct atomId. Just return NOne
      return None

    if residues[0]._wrappedData.molResidue.nextMolResidue is residues[-1]._wrappedData.molResidue:
      # last residue is sequential successor to first
      if (atomNames == ['N', 'CA', 'C', 'N'] and
          residues[0] is residues[1] and
          residues[0] is residues[2]):
        return 'PSI'
      elif (atomNames == ['C', 'N', 'CA', 'C'] and
          residues[1] is residues[2] and
          residues[1] is residues[3]):
        return 'PHI'
  #
  return None




