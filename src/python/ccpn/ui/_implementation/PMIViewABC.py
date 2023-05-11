"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2023-05-11 19:16:27 +0100 (Thu, May 11, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2023-04-28 17:16:13 +0100 (Fri, April 28, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

import typing

from ccpn.core.lib import Pid
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib.ContextManagers import undoStackBlocking


class PMIViewABC(AbstractWrapperObject):
    """Peak/Integral/Multiplet View for 1D or nD core objects
    """

    #: Short class name, for PID.
    shortClassName = 'Undefined'
    # Attribute it necessary as subclasses must use superclass className
    className = 'Undefined'

    _parentClass = 'Undefined'
    _parentClassName = 'Undefined'

    #: Name of plural link to instances of class
    _pluralLinkName = 'Undefined'

    #: List of child classes.
    _childClasses = []

    _isGuiClass = True

    # Qualified name of matching API class
    _apiClassQualifiedName = None

    #=========================================================================================
    # CCPN properties
    #=========================================================================================

    @property
    def _parent(self):
        """List containing -view."""
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    @property
    def _key(self) -> str:
        """id string - """
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    @property
    def _localCcpnSortKey(self) -> typing.Tuple:
        """Local sorting key, in context of parent."""
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    @property
    def textOffset(self) -> tuple:
        """X,Y text annotation offset."""
        return self._wrappedData.textOffset

    @textOffset.setter
    def textOffset(self, value: tuple):
        """Set the textOffset for the view.
        """
        try:
            with undoStackBlocking():
                # this is a gui operation and shouldn't need an undo
                self._wrappedData.textOffset = value

        except Exception as es:
            raise TypeError(f'{self.__class__.__name__}:textOffset must be a tuple of int/floats') from es

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: typing.Any) -> list:
        """get wrappedData in serial number order
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    def _resetIds(self):
        """Reset the ids when renamed.
        Different  from abstractWrapperObject as the _id needs to be hacked to remove
        the strip identifier.
        """
        # reset id
        oldId = self._id
        project = self._project
        parent = self._parent

        # strip the 'strip' identifier from the _id as this can change the peakView pid
        # when strips are deleted, _id was originally associated with the stripPeakListView
        parentId = self._parent._id.split(Pid.IDSEP)
        del parentId[1]
        parentId = Pid.IDSEP.join(parentId)

        className = self.className

        _id = '%s%s%s' % (parentId, Pid.IDSEP, self._key)
        sortKey = list(parent._ccpnSortKey[2:] + self._localCcpnSortKey)
        # strip the 'strip' identifier as above
        del sortKey[1]

        self._id = _id
        self._ccpnSortKey = (id(project), list(project._className2Class.keys()).index(className)) + tuple(sortKey)

        # update pid:object mapping dictionary
        dd = project._pid2Obj.get(className)
        if dd is None:
            dd = {}
            project._pid2Obj[className] = dd
            project._pid2Obj[self.shortClassName] = dd
        # assert oldId is not None
        if oldId in dd:
            del dd[oldId]
        dd[_id] = self

    def delete(self):
        """PeakViews cannot be deleted, except as a consequence of deleting other things.
        """
        raise RuntimeError(f"{str(self._pluralLinkName)} cannot be deleted.")

    def _finaliseAction(self, action: str, **actionKwds):
        if super()._finaliseAction(action, **actionKwds):

            if action == 'change':
                self.peak._finaliseAction(action)

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    # None
