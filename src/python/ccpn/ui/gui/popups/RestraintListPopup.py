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
__dateModified__ = "$dateModified: 2021-11-02 18:40:29 +0000 (Tue, November 02, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.popups.AttributeEditorPopupABC import AttributeEditorPopupABC
from ccpn.core.RestraintList import RestraintList
from ccpn.ui.gui.widgets.CompoundWidgets import EntryCompoundWidget, PulldownListCompoundWidget


class RestraintListPopupABC(AttributeEditorPopupABC):
    """Base class for RestraintList attributes editor popups
    """

    def _getRestraintTypes(self, obj=None):
        self.restraintType.modifyTexts(RestraintList.restraintTypes)
        self.restraintType.setIndex(0)

    klass = RestraintList  # The class whose properties are edited/displayed
    attributes = []  # A list of (attributeName, getFunction, setFunction, kwds) tuples;

    def __init__(self, parent=None, mainWindow=None, obj=None,
                 restraintList=None, structureData=None, **kwds):
        self.structureData = structureData

        super().__init__(parent=parent, mainWindow=mainWindow, obj=obj, **kwds)

    def _applyAllChanges(self, changes):
        """Apply all changes - add new restraintList
        """
        super()._applyAllChanges(changes)
        if not self.EDITMODE:
            # restraintList constraint, restraintType MUST be set
            if not self.obj.restraintType:
                self.obj.restraintType = self.restraintType.getText()

            # use the blank container as a dict for creating the new restraintList
            self.structureData.newRestraintList(**self.obj)

    # def _populateInitialValues(self):
    #     """Populate the initial values for an empty object
    #     """
    #     self.obj.name = self.klass._nextAvailableName(self.klass, self.project)


class RestraintListEditPopup(RestraintListPopupABC):
    """RestraintList attributes editor popup
    """

    attributes = [('Name', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Enter name <'}),
                  ('Comment', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}),
                  ('Restraint Type', EntryCompoundWidget, getattr, None, None, None, {}),
                  ('Molecule FilePath', EntryCompoundWidget, getattr, setattr, None, None, {})
                  ]


class RestraintListNewPopup(RestraintListPopupABC):
    """RestraintList attributes editor popup
    """

    # new requires a pulldown list for restraintType - in edit it is fixed
    attributes = [('Name', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Enter name <'}),
                  ('Comment', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}),
                  ('Restraint Type', PulldownListCompoundWidget, getattr, setattr, RestraintListPopupABC._getRestraintTypes, None, {}),
                  ('Molecule FilePath', EntryCompoundWidget, getattr, setattr, None, None, {})
                  ]
