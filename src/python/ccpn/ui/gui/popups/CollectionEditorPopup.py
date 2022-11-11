"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
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
__dateModified__ = "$dateModified: 2022-11-15 15:44:02 +0000 (Tue, November 15, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2022-11-11 11:28:58 +0100 (Fri, November 11, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.popups._GroupEditorPopupABC import _GroupEditorPopupABC
from ccpn.core.Collection import Collection

from ccpn.ui.gui.widgets.PulldownListsForObjects import CollectionPulldown


class CollectionPopup(_GroupEditorPopupABC):
    """A class to maintain edit the collections
    """

    _class = Collection  # e.g. SpectrumGroup
    _classPulldown = CollectionPulldown  # SpectrumGroupPulldown
    _enableClassPulldown = False

    # define these
    _singularItemName = 'Item'  # eg 'Spectrum'
    _pluralItemName = 'Items'  # eg 'Spectra'

    def _allCoreObjects(self, project):
        """:return a list with all the project's core objects
        """
        #TODO: remove depency on _pid2Obj by wrapping it in a Project method
        result = []
        for _className, _itemDict in project._pid2Obj.items():

            # check is we have a result,
            # all object are referenced twice: both short and long pid's,
            # e.g. SP and Spectrum
            #
            if _itemDict is not None:
                _values = list(_itemDict.values())
                if len(_values) > 0 and _values[0] not in result:
                    result.extend(_values)

        return result

    def getItems(self) -> list:
        """Get the items that can be included in the group
        :return A list of items
        """
        items = [obj for obj in self._allCoreObjects(self.project)
                     if not (obj.shortClassName in ['SR'] or
                             obj._isGuiClass or
                             obj == self.obj
                             )
                 ]

        return items

    def newObject(self, name, comment=None):
        """Create a new object with name, comment. Add items
        """
        obj = self.project.newCollection(name=name, comment=comment)
        return obj

    def setObjectItems(self, items):
        """et the items of the object; i.e. the items that form the group
        """
        if (obj := self.obj) is not None:
            obj.items = items

    def getObjectItems(self) -> list:
        """Get the items from self.object; i.e. the items that form the group
        :return A list of items
        """
        if (obj := self.obj) is not None:
            return obj.items
        else:
            return []
