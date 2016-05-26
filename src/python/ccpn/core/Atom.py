"""Module Documentation here

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

from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Residue import Residue
from ccpn.core.lib.Util import AtomIdTuple
from ccpn.util import Pid
from ccpnmodel.ccpncore.api.ccp.molecule.MolSystem import Atom as ApiAtom


# NBNB TBD add settable linkedAtoms link for non-ChemComp links ???

class Atom(AbstractWrapperObject):
  """Molecular Atom."""

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
    NB Unlike the _id and key, these do NOT have reserved characters maped to '^'"""
    parent = self._parent
    return AtomIdTuple(parent._parent.shortName, parent.sequenceCode, parent.residueType, self.name)

  @property
  def name(self) -> str:
    """Atom name string (e.g. 'HA')"""
    return self._wrappedData.name

  @property
  def boundAtoms(self) -> typing.Tuple['Atom']:
    """Atoms that are covalently bound to this Atom"""
    getDataObj = self._data2Obj.get
    boundAtoms = (getDataObj(x) for x in self._wrappedData.boundAtoms)
    return tuple(x for x in boundAtoms if x is not None)

  # Utility functions
    
  # Implementation functions

  @classmethod
  def _getAllWrappedData(cls, parent: Residue)-> list:
    """get wrappedData (MolSystem.Atoms) for all Atom children of parent Residue"""
    return parent._wrappedData.sortedAtoms()

# No 'new' function - chains are made elsewhere
    
# Connections to parents:

# Notifiers:
