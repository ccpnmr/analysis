"""Module Documentation here

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



def getChemAtomSetFromAtoms(atoms):
  """ Get a ChemAtomSet that matches all atoms

  .. describe:: Input

  List of Nmr.AtomSet or NmrConstraint.FixedAtomSet

  .. describe:: Output

  ChemComp.ChemAtomSet (or None)

  """

  chemAtoms = [x.chemAtom for x in atoms]
  if None in chemAtoms:
    return None

  chemAtomSets = set(x.chemAtomSet for x in chemAtoms)
  if None in chemAtomSets:
    return None

  nChemAtoms = 0
  for chemAtomSet in chemAtomSets:
    nChemAtoms += len(chemAtomSet.chemAtoms)
  if nChemAtoms != len(atoms):
    return None

  while len(chemAtomSets) > 1:
    chemAtomSets = set(x.chemAtomSet for x in chemAtomSets)
    if None in chemAtomSets:
      return None
  else:
    return chemAtomSets.pop()

