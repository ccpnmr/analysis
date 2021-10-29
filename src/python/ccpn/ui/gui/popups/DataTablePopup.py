"""
Module Documentation here
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
__dateModified__ = "$dateModified: 2021-10-29 17:00:13 +0100 (Fri, October 29, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-10-29 12:20:52 +0100 (Fri, October 29, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.DataTable import DataTable
from ccpn.ui.gui.popups.AttributeEditorPopupABC import AttributeEditorPopupABC
from ccpn.ui.gui.widgets.CompoundWidgets import EntryCompoundWidget


class DataTablePopup(AttributeEditorPopupABC):
    """DataTable attributes editor popup
    """

    # _fixedWidth = False

    klass = DataTable
    attributes = [('Name', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Enter name <'}),
                  ('Comment', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}),
                  ]

    def _applyAllChanges(self, changes):
        """Apply all changes - add new dataTable
        """
        super()._applyAllChanges(changes)
        if not self.EDITMODE:
            # create the new dataTable
            self.project.newDataTable(**self.obj)
