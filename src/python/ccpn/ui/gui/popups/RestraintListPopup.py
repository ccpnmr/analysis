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
__dateModified__ = "$dateModified: 2020-05-28 11:18:20 +0100 (Thu, May 28, 2020) $"
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
from ccpn.util.AttrDict import AttrDict


class RestraintListPopupABC(AttributeEditorPopupABC):

    def _getRestraintTypes(self, obj=None):
        self.restraintType.modifyTexts(RestraintList.restraintTypes)
        self.restraintType.setIndex(0)

    klass = RestraintList  # The class whose properties are edited/displayed
    attributes = []  # A list of (attributeName, getFunction, setFunction, kwds) tuples;

    def __init__(self, parent=None, mainWindow=None, obj=None,
                 restraintList=None, dataSet=None, editMode=False, **kwds):
        self.EDITMODE = editMode
        self.dataSet = dataSet

        super().__init__(parent=parent, mainWindow=mainWindow, obj=obj, **kwds)

        if self.dataSet is None and self.obj is not None:
            self.dataSet = self.obj.dataSet

        if not self.EDITMODE:
            self._getRestraintTypes()

    def _applyAllChanges(self, changes):
        """Apply all changes - add new restraintList
        """
        if self.EDITMODE:
            super()._applyAllChanges(changes)
        else:

            # make a blank container dict into which the new values will go
            self.obj = _blankContainer(self)
            super()._applyAllChanges(changes)

            # restraintList constraint, restraintType MUST be set
            if not self.obj.restraintType:
                self.obj.restraintType = self.restraintType.getText()

            # use the blank container as a dict for creating the new object
            self.dataSet.newRestraintList(**self.obj)

class RestraintListEditPopup(RestraintListPopupABC):

    attributes = [('name', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Enter name <'}),
                  ('comment', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}),
                  ('restraintType', EntryCompoundWidget, getattr, None, None, None, {}),
                  ]


class RestraintListNewPopup(RestraintListPopupABC):
    WINDOWPREFIX = 'New '

    # new requires a pulldown list for restraintType - in edit it is fixed
    attributes = [('name', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Enter name <'}),
                  ('comment', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}),
                  ('restraintType', PulldownListCompoundWidget, getattr, setattr, RestraintListPopupABC._getRestraintTypes, None, {}),
                  ]


class _blankContainer(AttrDict):
    """
    Class to simulate a blank object in new/edit popup.
    """

    def __init__(self, popupClass):
        """Create a list of attributes from the container class
        """
        super().__init__()
        for attr in popupClass.attributes:
            self[attr[0]] = None
