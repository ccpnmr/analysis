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
__dateModified__ = "$dateModified: 2023-06-09 12:06:25 +0100 (Fri, June 09, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2023-06-05 13:00:50 +0100 (Mon, June 05, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.Project import Project
from ccpn.core._implementation.CrossReference import _CrossReference
from ccpn.ui._implementation.Mark import Mark
from ccpn.ui._implementation.Strip import Strip
from ccpn.util.Logging import getLogger


REFERENCES = '_references'


class CrossReferenceHandler():
    """
    Class to handle cross-referencing between two sets of core objects.
    """

    def __init__(self, project: Project):
        self._project = project

        # dict holding references by class-class type
        self._crossReferences = {}

    def _resetItemPids(self, coreObject, oldPid=None, action='change'):
        """Update any references to a created/deleted core object.
        """
        # as per CollectionList, handled by _finaliseAction
        try:
            for refName, ref in self._crossReferences.items():

                # is the core-object type in the reference string
                if coreObject.className in refName:
                    ref._resetItemPids(coreObject, oldPid=oldPid, action=action)

        except Exception as es:
            getLogger().debug(f'{self.__class__.__name__}:_updatePids {es}')

    def _restoreObject(self, project, apiObj=None):
        """Restore the object and cross-references after loading.
        There is no apiObj for this class, but left in to match other core object functionality.
        """
        # recover objects from project._ccpnInternal for the minute
        #   move to _postRestore to ensure that all core objects are defined
        # try:
        #     # nasty, but get the direct object, not a copy
        #     references = self._project._getInternalParameterRef(REFERENCES)
        #
        # except Exception:
        #     references = {}
        #     self._project._setInternalParameter(REFERENCES, references)

        if not (references := self._project._getInternalParameterRef(REFERENCES)):
            references = {}
            self._project._setInternalParameter(REFERENCES, references)

        # don't need to keep getting the reference
        self._crossReferences = references

        # list through the required cross-references and create as required
        for rowRefClass, colRefClass in ((Mark, Strip),):
            refName = f'{rowRefClass.className}{colRefClass.className}'

            if foundRef := references.get(refName):
                if not isinstance(foundRef, dict):
                    foundRef._restoreObject(self._project, None)

            else:
                foundRef = references[refName] = _CrossReference(project, rowRefClass.className, colRefClass.className)
                foundRef._restoreObject(self._project, None)

    #=========================================================================================
    # Get/set values in cross-reference
    #=========================================================================================

    def getValues(self, coreObject, referenceName, axis):
        """Get the cross-reference objects from the class.
        """
        if not (refClass := self._crossReferences.get(referenceName)):
            raise RuntimeError(f'{self.__class__.__name__}.getValues: referencing {referenceName} not found')

        return refClass.getValues(coreObject, axis)

    def setValues(self, coreObject, referenceName, axis, values):
        """Set the cross-reference objects from the class.
        """
        if not (refClass := self._crossReferences.get(referenceName)):
            raise RuntimeError(f'{self.__class__.__name__}.getValues: referencing {referenceName} not found')

        refClass.setValues(coreObject, axis, values)

#=========================================================================================
# Add methods to cross-referenced classes?
#=========================================================================================

# from ccpn.util.decorators import logCommand
#
# def getter(self: Mark):
#     """Return the associated strips for the mark.
#     """
#     try:
#         refHandler = self._project._crossReferencing
#         return refHandler.getValues(self, 'MarkStrip', 0)
#
#     except Exception:
#         raise RuntimeError('Mark.strips is not implemented') from None
#
# @logCommand(get='self', isProperty=True)
# def strips(self: Mark, value):
#     """Set the associated strips for the mark.
#     """
#     try:
#         refHandler = self._project._crossReferencing
#         refHandler.setValues(self, 'MarkStrip', 0, value)
#
#     except Exception:
#         raise RuntimeError('Mark.strips is not implemented') from None
#
# Mark.strips = property(getter, strips, None, 'Return the associated strips for the mark.')
#
# del getter
# del strips
#
# @property
# def getter(self: Strip):
#     """Return the associated marks for the strip.
#     """
#     try:
#         refHandler = self._project._crossReferencing
#         return refHandler.getValues(self, 'MarkStrip', 1)
#
#     except Exception:
#         raise RuntimeError('Strip.marks is not implemented') from None
#
# @logCommand(get='self', isProperty=True)
# def marks(self: Strip, values):
#     """Set the associated marks for the strip.
#     """
#     try:
#         refHandler = self._project._crossReferencing
#         refHandler.setValues(self, 'MarkStrip', 1, values)
#
#     except Exception:
#         raise RuntimeError('Strip.marks is not implemented') from None
#
# Strip.marks = property(getter, marks, None, 'Return the associated marks for the strip.')
#
# del getter
# del marks
