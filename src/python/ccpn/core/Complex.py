"""

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-11-02 17:47:51 +0000 (Mon, November 02, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import typing
from functools import partial

from ccpn.util.Common import _validateName
from ccpn.core.Project import Project
from ccpn.core.Chain import Chain
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpnmodel.ccpncore.api.ccp.molecule.MolSystem import Chain as ApiChain
from ccpnmodel.ccpncore.api.ccp.molecule.MolSystem import ChainGroup as ApiChainGroup
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, renameObject


COMPLEX = 'complex'
COMPLEXCOMMENT = 'complexComment'


class Complex(AbstractWrapperObject):
    """A group of Chains, which can be used as a single object to describe a
    molecular complex."""

    #: Class name and Short class name, for PID.
    shortClassName = 'MX'
    # Attribute it necessary as subclasses must use superclass className
    className = 'Complex'

    _parentClass = Project

    #: Name of plural link to instances of class
    _pluralLinkName = 'complexes'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiChainGroup._metaclass.qualifiedName()

    # CCPN properties
    @property
    def _apiChainGroup(self) -> ApiChainGroup:
        """ CCPN Project ChainGroup"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """Residue local ID"""
        return self._wrappedData.name.translate(Pid.remapSeparators)

    @property
    def name(self) -> str:
        """Name of Complex, part of identifier"""
        return self._wrappedData.name

    @name.setter
    def name(self, value: str):
        """set name of Complex."""
        self.rename(value)

    @property
    def serial(self) -> str:
        """Serial number of Complex, used for sorting"""
        return self._wrappedData.serial

    @property
    def _parent(self) -> Project:
        """Parent (containing) object."""
        return self._project

    @property
    def chains(self) -> typing.Tuple[Chain, ...]:
        """Chains that make up Complex."""
        data2Obj = self._project._data2Obj
        return tuple(sorted(data2Obj[x] for x in self._wrappedData.chains))

    @chains.setter
    def chains(self, value):
        getDataObj = self._project._data2Obj.get
        value = [getDataObj(x) if isinstance(x, str) else x for x in value]
        self._wrappedData.chains = [x._wrappedData for x in value]

    @property
    def comment(self) -> str:
        """Free-form text comment"""
        comment = self.getParameter(COMPLEX, COMPLEXCOMMENT)
        return comment

    @comment.setter
    def comment(self, value: str):
        """set optional comment of Complex."""
        if not isinstance(value, (str, type(None))):
            raise ValueError("comment must be a string/None.")

        self.setParameter(COMPLEX, COMPLEXCOMMENT, value)

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Project) -> list:
        """get wrappedData for all Complexes linked to NmrProject"""
        molSystem = parent._wrappedData.molSystem
        if molSystem is None:
            return []
        else:
            return molSystem.sortedChainGroups()

    @renameObject()
    @logCommand(get='self')
    def rename(self, value: str):
        """Rename Complex, changing its name and Pid.
        """
        _validateName(self.project, Complex, value=value, allowWhitespace=False)

        # rename functions from here
        oldName = self.name
        self._wrappedData.__dict__['name'] = value
        return (oldName,)

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

@newObject(Complex)
def _newComplex(self: Project, name: str, chains=(), serial: int = None, comment: str = None) -> Complex:
    """Create new Complex.

    See the Complex class for details.

    :param name:
    :param chains:
    :param serial: optional serial number.
    :param comment: optional comment.
    :return: a new Complex instance.
    """

    if not name:
        name = Complex._nextAvailableName(Complex, self)
    _validateName(self, Complex, name)

    if name and Pid.altCharacter in name:
        raise ValueError("Character %s not allowed in ccpn.Complex.name" % Pid.altCharacter)

    if chains:
        getByPid = self._project.getByPid
        chains = [getByPid(x) if isinstance(x, str) else x for x in chains]

    result = self._data2Obj.get(self._wrappedData.molSystem.newChainGroup(name=name))
    if result is None:
        raise RuntimeError('Unable to generate new Complex item')

    if comment:
        result.comment = comment

    if serial is not None:
        try:
            result.resetSerial(serial)
        except ValueError:
            self.project._logger.warning("Could not reset serial of %s to %s - keeping original value"
                                         % (result, serial))

    if chains:
        result.chains = chains

    return result


#EJB 20181205 moved to Project
# Project.newComplex = _newComplex
# del _newComplex


# reverse link Chain.complexes
def getter(self: Chain) -> typing.Tuple[Complex, ...]:
    data2Obj = self._project._data2Obj
    return tuple(sorted(data2Obj[x] for x in self._wrappedData.chainGroups))


def setter(self: Chain, value):
    self._wrappedData.chainGroups = [x._wrappedData for x in value]


#
Chain.complexes = property(getter, setter, None, "Complexes that contain Chain")
del getter
del setter

# Extra Notifiers to notify changes in Chain-Complex link
className = ApiChainGroup._metaclass.qualifiedName()
Project._apiNotifiers.extend(
        (('_modifiedLink', {'classNames': ('Chain', 'Complex')}, className, 'addChain'),
         ('_modifiedLink', {'classNames': ('Chain', 'Complex')}, className, 'removeChain'),
         ('_modifiedLink', {'classNames': ('Chain', 'Complex')}, className, 'setChains'),
         )
        )
className = ApiChain._metaclass.qualifiedName()
Project._apiNotifiers.extend(
        (('_modifiedLink', {'classNames': ('Chain', 'Complex')}, className, 'addChainGroup'),
         ('_modifiedLink', {'classNames': ('Chain', 'Complex')}, className, 'removeChainGroup'),
         ('_modifiedLink', {'classNames': ('Chain', 'Complex')}, className, 'setChainGroups'),
         )
        )
