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
__dateModified__ = "$dateModified: 2022-11-30 11:22:07 +0000 (Wed, November 30, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-10-29 12:20:52 +0100 (Fri, October 29, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

import contextlib
from ccpn.core.ViolationTable import ViolationTable
from ccpn.ui.gui.popups.AttributeEditorPopupABC import AttributeEditorPopupABC
from ccpn.ui.gui.widgets.CompoundWidgets import EntryCompoundWidget, PulldownListCompoundWidget


_TABLEATTRIBUTE = 'restraintTable'
_OBJECTATTRIBUTE = '_restraintTableLink'


class ViolationTablePopup(AttributeEditorPopupABC):
    """ViolationTable attributes editor popup
    """

    def _getRestraintTableList(self, restraintTable):
        """Populate the restraintTable pulldown
        """
        self.restraintTable.modifyTexts([''] + [x.pid for x in self._structureData.restraintTables])
        with contextlib.suppress(Exception):
            self.restraintTable.select(self._parentViolationTable._restraintTableLink.pid)

    klass = ViolationTable
    attributes = [('Name', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Enter name <'}),
                  ('RestraintTable', PulldownListCompoundWidget, getattr, setattr, _getRestraintTableList, None, {}),
                  ('Comment', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}),
                  ]

    def __init__(self, parent=None, mainWindow=None, obj=None,
                 violationTable=None, structureData=None, **kwds):
        # obj is defined for edit-popup, and None for new-popup
        self._structureData = structureData or (obj and obj.structureData)
        self._parentViolationTable = obj

        super().__init__(parent=parent, mainWindow=mainWindow, obj=obj, **kwds)

    def _applyAllChanges(self, changes):
        """Apply all changes - add new violationTable
        """
        super()._applyAllChanges(changes)
        if not self.EDITMODE:
            # removed duplicate name - restraintTable exists in the object as _restraintTableLink
            if hasattr(self.obj, _TABLEATTRIBUTE):
                delattr(self.obj, _TABLEATTRIBUTE)

            # create the new violationTable
            self._structureData.newViolationTable(**self.obj)

    def _getValue(self, attr, getFunction, default):
        """Function for getting the attribute, called by _queueSetValue
        Subclassed to modify the visible-attribute to the protected core-class attribute
        """
        if attr == _TABLEATTRIBUTE:
            # modify duplicate name - restraintTable exists in the object as _restraintTableLink
            attr = _OBJECTATTRIBUTE

        return super()._getValue(attr, getFunction, default)

    def _setValue(self, attr, setFunction, value):
        """Function for setting the attribute, called by _applyAllChanges
        Subclassed to modify the visible-attribute to the protected core-class attribute
        """
        if attr == _TABLEATTRIBUTE:
            # modify duplicate name - restraintTable exists in the object as _restraintTableLink
            attr = _OBJECTATTRIBUTE

        super()._setValue(attr, setFunction, value)
