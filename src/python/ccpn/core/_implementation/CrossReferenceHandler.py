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
__dateModified__ = "$dateModified: 2023-07-13 11:59:18 +0100 (Thu, July 13, 2023) $"
__version__ = "$Revision: 3.2.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2023-06-05 13:00:50 +0100 (Mon, June 05, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.Project import Project
from ccpn.core._implementation.CrossReference import _CrossReferenceABC
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

                # is the core-object type in the reference string - ignore those without leading underscore
                if coreObject.className in refName and refName.startswith('_'):
                    ref._resetItemPids(coreObject, oldPid=oldPid, action=action)

        except Exception as es:
            getLogger().debug(f'{self.__class__.__name__}:_updatePids {es}')

    def _restoreObject(self, project, apiObj=None):
        """Restore the object and cross-references after loading.
        There is no apiObj for this class, but left in to match other core object functionality.
        """
        # recover objects from project._ccpnInternal - note the 'ParameterRef', we don't want a copy
        if not (references := self._project._getInternalParameterRef(REFERENCES)):
            references = {}
            self._project._setInternalParameter(REFERENCES, references)

        # don't need to keep getting the reference
        self._crossReferences = references

        # generate tuple of (rowKlass, columnKlass) for the registered classes
        refPairs = _CrossReferenceABC.registeredReferencePairs()

        # list through the required cross-references and create as required
        for rowRefClass, colRefClass in refPairs:
            refName = f'_{rowRefClass.className}{colRefClass.className}'

            if foundRef := references.get(refName):
                if not isinstance(foundRef, dict):
                    try:
                        foundRef._restoreObject(self._project, None)

                    except Exception:
                        # rebuild as contains an error
                        getLogger().debug('--> strange error')
                        foundRef = references[refName] = _CrossReferenceABC._new(rowRefClass.className, colRefClass.className)
                        foundRef._restoreObject(self._project, None)

            else:
                foundRef = references[refName] = _CrossReferenceABC._new(rowRefClass.className, colRefClass.className)
                foundRef._restoreObject(self._project, None)

        # load the deprecated ones - mistake by Ed :|
        for rowRefClass, colRefClass in refPairs:
            refName = f'{rowRefClass.className}{colRefClass.className}'

            if references.get(refName):
                del references[refName]

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
            raise RuntimeError(f'{self.__class__.__name__}.setValues: referencing {referenceName} not found')

        refClass.setValues(coreObject, axis, values)
