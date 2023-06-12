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
__dateModified__ = "$dateModified: 2023-06-12 17:57:05 +0100 (Mon, June 12, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.NmrChain import Chain
from ccpn.ui.gui.popups.AttributeEditorPopupABC import AttributeEditorPopupABC
from ccpn.ui.gui.widgets.MessageDialog import showMulti
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.ui.gui.widgets.CompoundWidgets import EntryCompoundWidget


class ChainPopup(AttributeEditorPopupABC):
    """Chain attributes editor popup
    """

    klass = Chain
    attributes = [('Name', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Enter name <'}),
                  ('Comment', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}),
                  ('Compound Name', EntryCompoundWidget, getattr, None, None, None, {}),
                  ('NmrChain', EntryCompoundWidget, getattr, None, None, None, {}),
                  ('isCyclic', CheckBoxCompoundWidget, getattr, None, None, None, {}),
                  ]

    _CANCEL = 'Cancel'
    _OK = 'Ok'
    _DONT_SAVE = "Don't Change"

    def _applyAllChanges(self, changes):
        """Apply all changes - update atom name
        """
        name = self.edits['name'].getText()
        if self.obj.nmrChain is not None and name != self.obj.name:

            reply = showMulti('Edit Chain',
                              'You are changing the name of your Chain.\n'
                              'Do you want to change the name of the associated NmrChain as well?',
                              texts=[self._OK, self._CANCEL, self._DONT_SAVE],
                              okText=self._OK, cancelText=self._CANCEL,
                              parent=self)

            if reply == self._CANCEL:
                return

            elif reply == self._OK:
                # also rename the nmrChain
                nmrChain = self.obj.nmrChain

                super()._applyAllChanges(changes)
                nmrChain.name = name
                return

        super()._applyAllChanges(changes)
