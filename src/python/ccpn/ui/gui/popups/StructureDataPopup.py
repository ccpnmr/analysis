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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-02-28 11:49:01 +0000 (Mon, February 28, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.StructureData import StructureData
from ccpn.ui.gui.popups.AttributeEditorPopupABC import AttributeEditorPopupABC
from ccpn.ui.gui.widgets.CompoundWidgets import EntryCompoundWidget


class StructureDataPopup(AttributeEditorPopupABC):
    """StructureData attributes editor popup
    """

    klass = StructureData
    attributes = [('Name', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Enter name <'}),
                  ('Comment', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}),
                  ('Program Name', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}),
                  ('Program Version', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}),
                  ('Data Path', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}),
                  ('Uuid', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}),
                  ('Molecule FilePath', EntryCompoundWidget, getattr, setattr, None, None, {})
                  ]

    def _applyAllChanges(self, changes):
        """Apply all changes - add new StructureData
        """
        super()._applyAllChanges(changes)
        if not self.EDITMODE:

            # keep in-case we change structureData to 'name'
            # if 'name' in self.obj:
            #     # structureData needs title attribute instead of name
            #     _name = self.obj.name
            #     del self.obj['name']
            #     self.obj.title = _name

            # create the new StructureData from project
            self.project.newStructureData(**self.obj)

    # def _populateInitialValues(self):
    #     """Populate the initial values for an empty object
    #     """
    #     self.obj.title = self.klass._nextAvailableName(self.klass, self.project)
