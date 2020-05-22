"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-05-22 19:02:20 +0100 (Fri, May 22, 2020) $"
__version__ = "$Revision: 3.0.1 $"
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


class RestraintListEditPopup(AttributeEditorPopupABC):
    EDITMODE = True

    klass = RestraintList
    attributes = [('name', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Enter name <'}),
                  ('comment', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}),
                  ('restraintType', EntryCompoundWidget, getattr, None, None, None, {}),
                  ]

    def __init__(self, parent=None, mainWindow=None, obj=None,
                 restraintList=None, dataSet=None, editMode=False, **kwds):
        self.EDITMODE = editMode
        self.dataSet = dataSet

        super().__init__(parent=parent, mainWindow=mainWindow, obj=obj, **kwds)

        if self.dataSet is None and self.obj is not None:
            self.dataSet = self.obj.dataSet


class RestraintListNewPopup(RestraintListEditPopup):
    EDITMODE = False
    WINDOWPREFIX = 'New '

    def _getRestraintTypes(self, obj=None):
        self.restraintType.modifyTexts(RestraintList.restraintTypes)

    klass = RestraintList
    attributes = [('name', EntryCompoundWidget, None, setattr, None, None, {'backgroundText': '> Enter name <'}),
                  ('comment', EntryCompoundWidget, None, setattr, None, None, {'backgroundText': '> Optional <'}),
                  ('restraintType', PulldownListCompoundWidget, None, setattr, None, None, {}),
                  ]

    def __init__(self, *args, **kwds):
        super(RestraintListNewPopup, self).__init__(*args, **kwds)

        self._getRestraintTypes()

    def _applyAllChanges(self, changes):
        """Apply all changes - add new restraintList
        """
        name = self.name.getText()
        comment = self.comment.getText()

        restraintType = self.restraintType.getText()
        self.dataSet.newRestraintList(name=name, restraintType=restraintType, comment=comment)

    def _setValue(self, attr, setFunction, value):
        """Not needed here - subclass so does no operation
        """
        pass
