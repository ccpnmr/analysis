"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-08-20 19:19:59 +0100 (Fri, August 20, 2021) $"
__version__ = "$Revision: 3.0.4 $"
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

from ccpn.util import Common as commonUtil
from ccpn.core.lib import MoleculeLib
from ccpn.core.Chain import Chain
from ccpn.core.Project import Project
from ccpn.core.Residue import Residue
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import NmrChain as ApiNmrChain
from ccpnmodel.ccpncore.lib import Constants
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, undoStackBlocking, renameObject, undoBlock


class NmrChain(AbstractWrapperObject):
    """NmrChains are used for NMR assignment. An NmrChain is by definition assigned to the
    Chain with the same shortName (if any).

    An NmrChain created without a name will be given the name
    '@ij', where ij is the serial number of the NmrChain. Names of this form are reserved.
    Setting the NmrChain shortName to None will revert to this default name.

    The order of NmrResidues within an NmrChain is not significant (they are given in sorted order).
    NmrChains with isConnected==True are used to describe connected but as yet unassigned
    stretches of NmrResidues, and here the NmrResidues are given in sequential order
    (N-terminal to C-terminal for proteins). Connected NmrChains have names of the form '#ij'
    where ij is the serial number of the NmrChain, and cannot be renamed.  Names of this form are
    reserved.
    """

    #: Short class name, for PID.
    shortClassName = 'NC'
    # Attribute it necessary as subclasses must use superclass className
    className = 'NmrChain'

    _parentClass = Project

    #: Name of plural link to instances of class
    _pluralLinkName = 'nmrChains'

    # the attribute name used by current
    _currentAttributeName = 'nmrChains'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiNmrChain._metaclass.qualifiedName()

    # CCPN properties
    @property
    def _apiNmrChain(self) -> ApiNmrChain:
        """ CCPN NmrChain matching NmrChain"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """short form of name, as used for id with illegal characters replaced by Pid.altCharacter"""
        return self._wrappedData.code.translate(Pid.remapSeparators)

    @property
    def _localCcpnSortKey(self) -> typing.Tuple:
        """Local sorting key, in context of parent."""
        return (self._wrappedData.code,)

    @property
    def shortName(self) -> str:
        """short form of name, used in Pid and to identify the NmrChain
        Names of the form '\@ijk' and '#ijk' (where ijk is an integers)
        are reserved and cannot be set. They can be obtained by the deassign command.
        Connected NmrChains (isConnected == True) always have canonical names of the form '#ijk'"""
        return self._wrappedData.code

    name = shortName

    @property
    def label(self) -> str:
        """Identifying label of NmrChain. Defaults to '?'"""
        return self._wrappedData.label

    @label.setter
    def label(self, value: str):
        """Set label of NmrChain."""
        self._wrappedData.label = value

    @name.setter
    def name(self, value:str):
        """set name of nmrResidue."""
        self.rename(value)

    @property
    def _parent(self) -> Project:
        """Parent (containing) object."""
        return self._project

    @property
    def serial(self) -> int:
        """NmrChain serial number - set at creation and unchangeable"""
        return self._wrappedData.serial

    @property
    def isConnected(self) -> bool:
        """True if this this NmrChain is a connected stretch
        (in which case the mainNmrResidues are sequentially connected)."""
        return self._wrappedData.isConnected

    @property
    def chain(self) -> Chain:
        """Chain to which NmrChain is assigned"""
        return self._project.getChain(self._id)

    @property
    def mainNmrResidues(self) -> typing.Tuple['NmrResidue']:
        """NmrResidues belonging to NmrChain that are NOT defined relative to another NmrResidue
        (sequenceCode ending in '-1', '+1', etc.) For connected NmrChains in sequential order, otherwise sorted by assignment
        """
        if not self._wrappedData:
            return ()

        result = list(self._project._data2Obj.get(x) for x in self._wrappedData.mainResonanceGroups)
        if not self.isConnected:
            result.sort()
        return tuple(result)

    @mainNmrResidues.setter
    def mainNmrResidues(self, value):
        self._wrappedData.mainResonanceGroups = [x._wrappedData for x in value]

    # @chain.setter
    # def chain(self, value:Chain):
    #   if value is None:
    #     if self.chain is None:
    #       return
    #     else:
    #       self.deassign()
    #   else:
    #     # NB The API code will throw ValueError if there is already an NmrChain with that code
    #     self.rename(value._wrappedData.code)

    @logCommand(get='self')
    def deassign(self):
        """Reset NmrChain back to its originalName, cutting all assignment links"""
        with undoBlock():
            self._wrappedData.code = None

    @logCommand(get='self')
    def assignSingleResidue(self, thisNmrResidue: typing.Union['NmrResidue'], firstResidue: typing.Union['Residue', str]):
        """Assign a single unconnected residue from the default '@-' chain"""

        project = self._project

        # if self.isConnected:
        #     raise ValueError("assignSingleResidue only allowed for single nmrResidue")

        # make sure that object exists
        if isinstance(firstResidue, str):
            xx = project.getByPid(firstResidue)
            if xx is None:
                raise ValueError("No object found matching Pid %s" % firstResidue)
            else:
                firstResidue = xx

        # check that it isn't already connected
        if firstResidue.nmrResidue is not None:
            raise ValueError("Cannot assign %s: Residue %s is already assigned"
                             % (thisNmrResidue.id, firstResidue.id))

        # If we get here we are OK - assign residues and delete NmrChain
        with undoBlock():
            thisNmrResidue._wrappedData.assignedResidue = firstResidue._wrappedData

    @logCommand(get='self')
    def assignConnectedResidues(self, firstResidue: typing.Union['Residue', str]):
        """Assign all NmrResidues in connected NmrChain sequentially,
        with the first NmrResidue assigned to firstResidue.

        Returns ValueError if NmrChain is not connected,
        or if any of the Residues are missing or already assigned"""

        apiNmrChain = self._wrappedData
        project = self._project

        if not apiNmrChain:
            return

        if not self.isConnected:
          raise ValueError("assignConnectedResidues only allowed for connected NmrChains")

        if isinstance(firstResidue, str):
            xx = project.getByPid(firstResidue)
            if xx is None:
                raise ValueError("No object found matching Pid %s" % firstResidue)
            else:
                firstResidue = xx

        apiStretch = apiNmrChain.mainResonanceGroups
        if firstResidue.nmrResidue is not None:
            raise ValueError("Cannot assign %s NmrResidue stretch: First Residue %s is already assigned"
                             % (len(apiStretch), firstResidue.id))

        residues = [firstResidue]
        for ii in range(len(apiStretch) - 1):
            res = residues[ii]
            next = res.nextResidue
            if next is None:
                raise ValueError("Cannot assign %s NmrResidues to %s Residues from Chain"
                                 % (len(apiStretch), len(residues)))
            elif next.nmrResidue is not None:
                raise ValueError("Cannot assign %s NmrResidue stretch: Residue %s is already assigned"
                                 % (len(apiStretch), next.id))

            else:
                residues.append(next)

        # check whether
        with undoBlock():

            tempChain = self.project.fetchNmrChain(firstResidue.chain.shortName)
            for ii, res in enumerate(residues):
                apiStretch[ii].assignedResidue = res._wrappedData

            # apiNmrChain.delete()

            # need the V3 operator here for the undo/redo to fire correctly
            V3nmrChain = self.project._data2Obj[apiNmrChain]
            # only delete if it is not the default chain:
            if not V3nmrChain.id.startswith('@-'):
                V3nmrChain.delete()

    @logCommand(get='self')
    def reverse(self, _force=False):
        """Reverse order of NmrResidues within NmrChain

        Illegal for assigned NmrChains, and only relevant for connected NmrChains.
        Serves mainly as building block to make disconnections easier to undo"""

        if self.chain is not None:  # and _force is False:
            raise ValueError("NmrChain is assigned (to %s) and cannot be reversed"
                             % self.chain.longPid)

        with undoBlock():
            with undoStackBlocking() as addUndoItem:
                self._wrappedData.__dict__['mainResonanceGroups'].reverse()

                addUndoItem(undo=partial(self.reverse), redo=partial(self.reverse))

    @logCommand(get='self')
    def renumberNmrResidues(self, offset: int, start: int = None, stop: int = None):
        """Renumber nmrResidues in range start-stop (inclusive) by adding offset

        The nmrResidue number is the integer starting part of the sequenceCode,
        e.g. nmrResidue '12B' is renumbered to '13B' (offset=1)
        and e.g. nmrResidue '@119' is ignored

        if start (stop) is None, there is no lower (upper) limit

        NB Will rename nmrResidues one by one, and stop on error."""

        nmrResidues = self.nmrResidues
        if offset > 0:
            nmrResidues.reverse()

        changedNmrResidues = []
        with undoBlock():

            for nmrResidue in nmrResidues:
                sequenceCode = nmrResidue.sequenceCode
                code, ss, offs = commonUtil.parseSequenceCode(sequenceCode)
                if offs is None and code is not None:
                    # offset residues are handled with their mainResidues
                    if ((start is None or code >= start)
                            and (stop is None or code <= stop)):
                        newSequenceCode = MoleculeLib._incrementedSequenceCode(nmrResidue.sequenceCode, offset)

                        nmrResidue.rename('%s.%s' % (newSequenceCode, nmrResidue.residueType or ''))
                        changedNmrResidues.append(nmrResidue)

            for nmrResidue in changedNmrResidues:
                nmrResidue._finaliseAction('rename')
                # nmrResidue._finaliseAction('change')

        if start is not None and stop is not None:
            if len(changedNmrResidues) != stop + 1 - start:
                self._project._logger.warning("Only %s nmrResidues found in range %s to %s"
                                              % (len(changedNmrResidues), start, stop))

    def _connectNmrResidues(self):
        updatingNmrChain = None
        nrs = self.nmrResidues
        for i in range(len(nrs) - 1):
            currentItem, nextItem = nrs[i], nrs[i + 1]
            if currentItem and nextItem:
                # check that the sequence codes are consecutive
                if int(nextItem.sequenceCode) == int(currentItem.sequenceCode) + 1:
                    updatingNmrChain = currentItem.connectNext(nextItem, )
        return updatingNmrChain

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Project) -> list:
        """get wrappedData (Nmr.NmrChains) for all NmrChain children of parent Project"""
        return parent._wrappedData.sortedNmrChains()

    @renameObject()
    @logCommand(get='self')
    def rename(self, value: str):
        """Rename NmrChain, changing its shortName and Pid.
        Use the 'deassign' function if you want to revert to the canonical name"""

        # NBNB TODO Allow renaming to names of the form '@123' (?)
        wrappedData = self._apiNmrChain

        if self._wrappedData.isConnected:
            raise ValueError("Connected NmrChain cannot be renamed")
        elif value == wrappedData.code:
            return
        elif wrappedData.code == Constants.defaultNmrChainCode:
            raise ValueError("NmrChain:%s cannot be renamed" % Constants.defaultNmrChainCode)

        value = self._uniqueName(project=self.project, name=value)

        # rename functions from here
        oldName = self.shortName
        self._oldPid = self.pid
        wrappedData.code = value
        return (oldName,)

    def _finaliseAction(self, action):
        if action in ['delete']:
            if self._wrappedData.implCode == '@-' and self._wrappedData.nmrProject:
                raise TypeError("NmrChain '@-' cannot be deleted")

        if not super()._finaliseAction(action):
            return

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================

    @logCommand(get='self')
    def newNmrResidue(self, sequenceCode: typing.Union[int, str] = None, residueType: str = None,
                      comment: str = None):
        """Create new NmrResidue within NmrChain.

        If NmrChain is connected, append the new NmrResidue to the end of the stretch.

        :param sequenceCode:
        :param residueType:
        :param comment:
        :return: a new NmrResidue instance.
        """
        from ccpn.core.NmrResidue import _newNmrResidue

        return _newNmrResidue(self, sequenceCode=sequenceCode, residueType=residueType,
                              comment=comment)

    @logCommand(get='self')
    def fetchNmrResidue(self, sequenceCode: typing.Union[int, str] = None,
                        residueType: str = None):
        """Fetch NmrResidue with sequenceCode=sequenceCode and residueType=residueType,
        creating it if necessary.

        if sequenceCode is None will create a new NmrResidue.

        if bool(residueType)  is False will return any existing NmrResidue that matches the sequenceCode.

        :param sequenceCode:
        :param residueType:
        :return: an NmrResidue instance.
        """
        from ccpn.core.NmrResidue import _fetchNmrResidue

        return _fetchNmrResidue(self, sequenceCode=sequenceCode, residueType=residueType)


# GWV 20181122: moved to Chain class
# def getter(self:Chain) -> typing.Optional[NmrChain]:
#   try:
#     return self._project.getNmrChain(self._id)
#   except:
#     return None
#
# def setter(self:Chain, value:NmrChain):
#   if value is None:
#      raise ValueError("nmrChain cannot be set to None")
#   else:
#      value.chain = self
# Chain.nmrChain = property(getter, setter, None, "NmrChain to which Chain is assigned")
#
# del getter
# del setter


#=========================================================================================
# Connections to parents:
#=========================================================================================

@newObject(NmrChain)
def _newNmrChain(self: Project, shortName: str = None, isConnected: bool = False, label: str = '?',
                 comment: str = None) -> NmrChain:
    """Create new NmrChain. Setting isConnected=True produces a connected NmrChain.

    See the NmrChain class for details.

    :param str shortName: shortName for new nmrChain (optional, defaults to '@ijk' or '#ijk',  ijk positive integer
    :param bool isConnected: (default to False) If true the NmrChain is a connected stretch. This can NOT be changed later
    :param str label: Modifiable NmrChain identifier that does not change with reassignment. Defaults to '@ijk'/'#ijk'
    :param str comment: comment for new nmrChain (optional)
    :return: a new nmrChain instance.
    """

    nmrProject = self._apiNmrProject

    if shortName:
        previous = self.getNmrChain(shortName.translate(Pid.remapSeparators))
        if previous is not None:
            raise ValueError("%s already exists" % previous.longPid)
        if shortName[0] in '#@':
            try:
                serial = int(shortName[1:])
            except ValueError:
                # the rest of the name is not an int. We are OK
                pass
            else:
                if serial is not None and serial > 0:
                    # this is a reserved name - try to set it with serial
                    if nmrProject.findFirstNmrChain(serial=serial) is None:
                        # We are setting a shortName that matches the passed-in serial. OK.
                        # Set isConnected to match - this overrides the isConnected parameter.
                        isConnected = (shortName[0] == '#')
                        shortName = None
                    else:
                        raise ValueError("Cannot create NmrChain with reserved name %s" % shortName)
    else:
        shortName = None

    dd = {'code': shortName, 'isConnected': isConnected, 'label': label, 'details': comment}

    newApiNmrChain = nmrProject.newNmrChain(**dd)
    result = self._data2Obj.get(newApiNmrChain)
    if result is None:
        raise RuntimeError('Unable to generate new NmrChain item')

    return result


def _fetchNmrChain(self: Project, shortName: str = None) -> NmrChain:
    """Fetch chain with given shortName; If none exists call newNmrChain to make one first

    If shortName is None returns a new NmrChain with name starting with '@'

    :param shortName:
    :return: nmrChain instance.
    """
    with undoBlock():

        if not shortName:
            result = self.newNmrChain()
        else:
            apiNmrChain = self._apiNmrProject.findFirstNmrChain(code=shortName)
            if apiNmrChain is None:
                result = self.newNmrChain(shortName=shortName)
            else:
                result = self._data2Obj.get(apiNmrChain)

    return result


# Clean-up

# Connections to parents:

#EJB 20181130: moved to project
# Project.newNmrChain = _newNmrChain
# del _newNmrChain
# Project.fetchNmrChain = _fetchNmrChain
# del _fetchNmrChain

# Notifiers:
className = ApiNmrChain._metaclass.qualifiedName()
Project._apiNotifiers.extend(
        (('_finaliseApiRename', {}, className, 'setImplCode'),
         )
        )

#GWV 20181121: removed
# Chain._setupCoreNotifier('rename', AbstractWrapperObject._finaliseRelatedObjectFromRename,
#                           {'pathToObject':'nmrChain', 'action':'rename'})

# NB Chain<->NmrChain link depends solely on the NmrChain name.
# So no notifiers on the link - notify on the NmrChain rename instead.
