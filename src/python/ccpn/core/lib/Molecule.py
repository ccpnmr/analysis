"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Luca Mureddu, Simon Skinner, Geerten Vuister"
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

import typing
from ccpn.core import Chain


def duplicateAtomBonds(chainMap:typing.Dict[Chain.Chain,Chain.Chain]):
  """Duplicate atom-atom bonds within source chains to target chains,
  skipping those that already exist.

  Input is a map from source chains to corresponding trget chains.

  Atoms are mapped on matching Pids (with different chain codes"""
  if not chainMap:
    return
  project = list(chainMap.keys())[0]._project
  apiMolSystem = project._wrappedData.molSystem

  # Make source -> target APiAtom map and remove target atoms with no match in source
  apiAtomMap = {}
  for source, target in chainMap.items():
    cutat = 3+len(target.shortName)  # Cut after e.g. 'MA:B' for chain B
    prefix = 'MA:' + source.shortName  # New prefix - e.g. 'MA:E' for chain E

    for atom2 in target.atoms:
      # Get equivalent atom in source
      apid = prefix + atom2.pid[cutat:]
      atom1 = project.getByPid(apid)

      if atom1 is None:
        # Atom missing, presumably removed from original chain manually
        atom2.delete()
      else:
        # Make self-other api atom map
        apiAtomMap[atom1._wrappedData] = atom2._wrappedData

  # Make target bonds if not already present
  for genericBond in apiMolSystem.genericBonds:
    bondType = genericBond.bondType
    apiAtoms = genericBond.atoms
    fs = frozenset(apiAtomMap.get(x) for x in apiAtoms)
    if None not in fs:
      # Both atoms matched an atom on target side'
      gBond = apiMolSystem.findFirstGenericBond(atoms=fs)
      if gBond is None:
        # There is no bond in 'other' that matches the bond. Make it
        apiMolSystem.newGenericBond(atoms=fs, bondType=bondType)
