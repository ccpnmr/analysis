"""
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

import typing

from ccpn.util import Common as commonUtil
from ccpn.core.lib import Pid
from ccpn.core.lib.Util import AtomIdTuple
from ccpn.core.Project import Project
from ccpn.core.Residue import Residue
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpnmodel.ccpncore.api.ccp.molecule.MolSystem import Atom as ApiAtom

class Atom(AbstractWrapperObject):
  """A molecular Atom, contained in a Residue."""

  #: Class name and Short class name, for PID.
  shortClassName = 'MA'
  # Attribute it necessary as subclasses must use superclass className
  className = 'Atom'

  _parentClass = Residue

  #: Name of plural link to instances of class
  _pluralLinkName = 'atoms'
  
  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class
  _apiClassQualifiedName = ApiAtom._metaclass.qualifiedName()
  

  # CCPN properties
  @property
  def _apiAtom(self) -> ApiAtom:
    """ CCPN atom matching Atom"""
    return self._wrappedData


  @property
  def _parent(self) -> Residue:
    """Residue containing Atom."""
    return self._project._data2Obj[self._wrappedData.residue]
  
  residue = _parent
    
  @property
  def _key(self) -> str:
    """Atom name string (e.g. 'HA') regularised as used for ID"""
    return self._wrappedData.name.translate(Pid.remapSeparators)

  @property
  def _idTuple(self) -> AtomIdTuple:
    """ID as chainCode, sequenceCode, residueType, atomName namedtuple
    NB Unlike the _id and key, these do NOT have reserved characters mapped to '^'
    NB _idTuple replaces empty strings with None"""
    parent = self._parent
    ll = [parent._parent.shortName, parent.sequenceCode, parent.residueType, self.name]
    return AtomIdTuple(*(x or None for x in ll))

  @property
  def name(self) -> str:
    """Atom name string (e.g. 'HA')"""
    return self._wrappedData.name

  @property
  def boundAtoms(self) -> typing.Tuple['Atom']:
    """Atoms that are covalently bound to this Atom"""
    getDataObj = self._project._data2Obj.get
    apiAtom = self._wrappedData

    boundApiAtoms = list(apiAtom.boundAtoms)
    for apiBond in apiAtom.genericBonds:
      ll = list(apiBond.atoms)
      apiAtom2 = ll[0] if apiAtom is ll[1] else ll[1]
      boundApiAtoms.append(apiAtom2)
    boundAtoms = (getDataObj(x) for x in boundApiAtoms)
    return tuple(sorted(x for x in boundAtoms if x is not None))

  @property
  def componentAtoms(self) -> typing.Tuple['Atom']:
    """Atoms that are combined to make up this atom - reverse of 'compoundAtoms'

    For simple atoms this is empty.
    For wildcard atoms (e.g. HB%, QB) this gives the individual atoms that combine into atom.
    For non-stereo atoms (e.g. HBx, HBy, HGx%) it gives the two alternative stereospecific atoms

    Compound atoms may be nested - e.g. Valine HG1% has the components HG11, HG12, HG13
    and is itself a component of HGx%, HGy%, HG%, and QG"""
    getDataObj = self._project._data2Obj.get
    apiAtom = self._wrappedData
    return tuple(getDataObj(x) for x in self._wrappedData.components)

  @property
  def compoundAtoms(self) -> typing.Tuple['Atom']:
    """wildcard-, pseudo-, and nonstereo- atoms that incorporate this atom.
    - reverse of 'componentAtoms'

    Compound atoms may be nested - e.g. Valine HG1% has the components HG11, HG12, HG13
    and is itself a component of HGx%, HGy%, HG%, and QG"""
    getDataObj = self._project._data2Obj.get
    apiAtom = self._wrappedData
    return tuple(getDataObj(x) for x in self._wrappedData.atomGroups)

  @property
  def exchangesWithWater(self) -> bool:
    """True if atom exchanges with water on a msx time scale, and so is mostly unobservable.

    Holds for e.g. OH atoms, NH£ groups and His side chain NH protons, but NOT for amide protons """

    apiAtom = self._wrappedData
    components = apiAtom.components
    while components:
      for apiAtom in components:
        # Fastest way to get an arbitrary element from a frozen set
        break
      components = apiAtom.components
    #
    apiChemAtom = apiAtom.chemAtom
    if apiChemAtom:
      return apiChemAtom.waterExchangeable
    else:
      return False

  @property
  def isEquivalentAtomGroup(self) -> typing.Optional[bool]:
    """Is this atom a group of equivalent atoms?
    Values are:

    - True  (group of equivalent atoms, e.g. H%, ALA HB%, LYS HZ%, VAL HG1% or any M pseudoatom)

    - False (all single atoms, all xy nonstereo atoms, LEU HB%, ILE HG1%, VAL HG%,
      or any Q non-aromatic pseudoatom)

    - None  = sometimes equivalent (TYR and PHE HD%, HE%, CD%, CE%, QD, QE)
    """
    apiChemAtomSet = self._wrappedData.chemAtomSet
    if apiChemAtomSet is None:
      return False
    else:
      # NB isEquivalent is None for symmetric aromatic rings. We return True for that
      return apiChemAtomSet.isEquivalent != False


  def addInterAtomBond(self, atom:'Atom'):
    """ADVANCED Add generic bond between atoms - for creating disulfides or other crosslinks
    The bound-to atom will appear in self.boundAtoms.

    NB This function does not remove superfluous atoms (like CYS HG),
    or check for chemical plausibility. Programmer beware!"""
    project = self._project
    project._wrappedData.molSystem.newGenericBond(atoms=(self._wrappedData, atom._wrappedData))


  # Implementation functions

  @classmethod
  def _getAllWrappedData(cls, parent: Residue)-> list:
    """get wrappedData (MolSystem.Atoms) for all Atom children of parent Residue"""
    return parent._wrappedData.atoms

  def _newAtom(self:Residue, name:str, elementSymbol:str=None) -> 'Atom':
    """Create new Atom within Residue. If elementSymbol is None, it is derived from the name"""
    lastAtom = self.getAtom(name)
    if lastAtom is not None:
      raise ValueError("Cannot create %s, atom name %s already in use" % (lastAtom.longPid, name))
    if elementSymbol is None:
      elementSymbol = commonUtil.name2ElementSymbol(name)
    apiAtom = self._wrappedData.newAtom(name=name, elementSymbol=elementSymbol)
    #
    return self._project._data2Obj[apiAtom]
  #
  Residue.newAtom = _newAtom

def _expandNewAtom(atom:Atom):
  """Add compound NmrAtoms and bonds when template atoms are (re)added"""

  apiAtom = atom._wrappedData

  # NBNB This could be done differently.
  # It might be better to do this directly from the API functions
  # but in order not to mess with the complexities of the expandMolSystemAtoms
  # function (which does the same job, but in batch) this is simpler

  apiResidue = apiAtom.residue
  apiChemAtom = apiAtom.chemAtom
  if apiChemAtom is not None:
    apiChemAtomSet = apiChemAtom.chemAtomSet
    if apiChemAtomSet is not None:
      # NB, we do not want to add atoms for '*', but rather for '%'
      newName = apiChemAtomSet.name.replace('*', '%')
      apiAtomGroup = apiResidue.findFirstAtom(name=newName)
      if apiAtomGroup is None:
        # NB - this is not tested and is likely to be used VERY rarely, if at all.
        # Basically this is the case where we have a ChemAtomSet in the template,
        # had only ONE of the relevant atoms previously, and are now adding the second
        # atom, so we have to create the Atom matching the ChemAtomSet.

        # check if we now have atoms to create one
        apiAtoms = []
        for aca in apiChemAtomSet.chemAtoms:
          aa = apiResidue.findFirstAtom(name=aca.name)
          if aa is not None:
            apiAtoms.append(aa)
        if len(apiAtoms) > 1:

          # NB this is slightly heuristic,
          # but I'd say it is as good as can reasonably be expected
          if apiChemAtomSet.isEquivalent:
            atomType = 'equivalent'
          elif len(apiChemAtomSet.chemAtoms) == 2:
            atomType = 'pseudo'
          else:
            atomType = 'nonstereo'

          apiResidue.newAtom(name=newName, components=apiAtoms,
                                atomType=atomType, elementSymbol=apiChemAtomSet.elementSymbol)
      else:
        # ChemAtomSet already exists in wrapper in partial form.
        # In Practice we must be adding the third H to an NH3 group
        apiAtomGroup.addComponent(apiAtom)

      # Add bonds from template
      for apiChemBond in apiChemAtom.chemBonds:
        apiAtoms = set(apiResidue.findFirstAtom(name=x.name)
                       for x in apiChemBond.chemAtoms)
        for aa in apiAtoms:
          if aa is not None and aa is not apiAtom and aa not in apiAtom.boundAtoms:
            apiAtom.addBoundAtom(aa)

    
# Connections to parents:

# Notifiers:
Atom._setupCoreNotifier('create', _expandNewAtom)
