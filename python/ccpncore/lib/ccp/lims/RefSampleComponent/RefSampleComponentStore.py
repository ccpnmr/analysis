"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
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
from ccpncore.api.ccp.molecule.Molecule import Molecule

def fetchMolComponent(self:"RefSampleComponentStore", molecule:Molecule,
                      labeling:str=None) -> "AbstractComponent":
  """fetch or create new MolComponent matching Molecule name and (if not None) labeling
  labeling for new MolComponents default to std
  NB pre-existing RefComponents returned may be of other types (Cell, Substance or Composite)
   if their names match the molecule
  """
  name = molecule.name
  if labeling is None:
    # Pick any MolComponent regardless of labeling
    result = (self.findFirstRefComponent(name=name, labeling='std') or
              self.findFirstRefComponent(name=name))
    # Any new molComponent must be 'std'
    labeling = 'std'
  else:
    # labeling passed in. Use it.
    result = self.findFirstRefComponent(name=name, labeling=labeling)

  if result is None:
    # Finalise, so molecule does not change 'underneath' substance
    molecule.isFinalised = True
    seqString = molecule.seqString or '(%s)' % ','.join(x.code3Letter
                                                        for x in molecule.sortedMolResidues())
    result = self.newMolComponent(name=name, labeling=labeling, synonyms=molecule.commonNames,
                                  details=molecule.details, smiles=molecule.smiles,
                                  empiricalFormula=molecule.empiricalFormula,
                                  molecularMass=molecule.molecularMass, molType=molecule.molType,
                                  seqString=seqString)
  #
  return result