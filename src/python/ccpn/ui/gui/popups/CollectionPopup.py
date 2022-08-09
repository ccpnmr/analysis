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
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-08-09 14:27:34 +0100 (Tue, August 09, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-10-29 16:10:20 +0100 (Fri, October 29, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from functools import partial
from ccpn.core.Collection import Collection
from ccpn.ui.gui.popups.AttributeEditorPopupABC import AttributeEditorPopupABC
from ccpn.ui.gui.widgets.CompoundWidgets import EntryCompoundWidget, ListCompoundWidget
from ccpn.ui.gui.popups.Dialog import _verifyPopupApply
from ccpn.core.lib.ContextManagers import queueStateChange


class CollectionPopup(AttributeEditorPopupABC):
    """Collection attributes editor popup
    """

    def _getItems(self, obj, *args):
        """Populate collection items
        """
        data = []
        if isinstance(self, Collection):
            for item in self.items:
                data.append(str(item.pid))
        return data

    def _postInitListWidget(self, *args):
        """Populate collection items
        """
        itemsListWidget = self.items

        # hide the pulldown and move the label down a row
        itemsListWidget.showPulldownList(False)
        itemsListWidget.layout().addWidget(itemsListWidget.label, 1, 0)

        listWidget = itemsListWidget.listWidget
        listWidget.model().rowsRemoved.connect(self._queueRemoveItem)
        listWidget.cleared.connect(self._queueRemoveItem)

    @queueStateChange(_verifyPopupApply)
    def _queueRemoveItem(self, *args):
        """Queue changes to the items
        """
        pids = self.items.getTexts()
        return partial(self._setItemsToCollections, pids)

    def _setItemsToCollections(self, pids):
        """Sets newItems to collections
        """
        objs = self.project.getObjectsByPids(pids)
        if isinstance(self.obj, Collection):
            self.obj.items = objs

    klass = Collection
    attributes = [('Name', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Enter name <'}),
                  ('Comment', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}),
                  ('Items', ListCompoundWidget, _getItems, None, _postInitListWidget, None, {}),
                  ]

    def _applyAllChanges(self, changes):
        """Apply all changes - add new collection
        """
        super()._applyAllChanges(changes)
        if not self.EDITMODE:
            # create the new collection
            self.project.newCollection(**self.obj)
