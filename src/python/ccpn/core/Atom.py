"""
Module documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:27 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
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
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, deleteObject, ccpNmrV3CoreSetter, logCommandBlock
from ccpn.util.Logging import getLogger


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

    def addInterAtomBond(self, atom: 'Atom'):
        """ADVANCED Add generic bond between atoms - for creating disulfides or other crosslinks
        The bound-to atom will appear in self.boundAtoms.

        NB This function does not remove superfluous atoms (like CYS HG),
        or check for chemical plausibility. Programmer beware!"""
        project = self._project
        project._wrappedData.molSystem.newGenericBond(atoms=(self._wrappedData, atom._wrappedData))

    #from ccpn.core.NmrAtom import NmrAtom: This will break the import sequence
    @property
    def nmrAtom(self) -> typing.Optional['NmrAtom']:
        """NmrAtom to which Atom is assigned

        NB  Atom<->NmrAtom link depends solely on the NmrAtom name.
            So no notifiers on the link - notify on the NmrAtom rename instead.
        """
        try:
            return self._project.getNmrAtom(self._id)
        except:
            return None

    # GWV 20181122: removed setters between Chain/NmrChain, Residue/NmrResidue, Atom/NmrAtom
    # @nmrAtom.setter
    # def nmrAtom(self, value:'NmrAtom'):
    #   oldValue = self.nmrAtom
    #   if oldValue is value:
    #     return
    #   elif value is None:
    #     raise ValueError("Cannot set Atom.nmrAtom to None")
    #   elif oldValue is not None:
    #     raise ValueError("New assignment of Atom clashes with existing assignment")
    #   else:
    #     value.atom = self

    @property
    def isAssigned(self) -> bool:
        """
        :return: True if Atom has as NmrAtom with an associated ChemicalShift object
        """
        if self.nmrAtom is None: return False
        if not self.nmrAtom.chemicalShifts: return False  # either None or len==0
        return True

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Residue) -> list:
        """get wrappedData (MolSystem.Atoms) for all Atom children of parent Residue"""
        return parent._wrappedData.sortedAtoms()

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================


#=========================================================================================
# Connections to parents:
#=========================================================================================

def _newAtom(self: Residue, name: str, elementSymbol: str = None) -> 'Atom':
    """Create new Atom within Residue. If elementSymbol is None, it is derived from the name"""
    lastAtom = self.getAtom(name)
    if lastAtom is not None:
        raise ValueError("Cannot create %s, atom name %s already in use" % (lastAtom.longPid, name))
    if elementSymbol is None:
        elementSymbol = commonUtil.name2ElementSymbol(name)
    apiAtom = self._wrappedData.newAtom(name=name, elementSymbol=elementSymbol)
    apiAtom.expandNewAtom()
    #
    return self._project._data2Obj[apiAtom]


#
Residue.newAtom = _newAtom

# Connections to parents:
