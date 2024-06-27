"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2024-06-06 21:20:48 +0100 (Thu, June 06, 2024) $"
__version__ = "$Revision: 3.2.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.NmrChain import NmrChain
from ccpn.ui.gui.popups.SimpleAttributeEditorPopupABC import SimpleAttributeEditorPopupABC
from ccpn.ui.gui.widgets.MessageDialog import showMulti


class NmrChainPopup(SimpleAttributeEditorPopupABC):
    """NmrChain attributes editor popup
    """

    klass = NmrChain
    attributes = [('Name', getattr, setattr, {'backgroundText': '> Enter name <'}),
                  ('Comment', getattr, setattr, {'backgroundText': '> Optional <'}),
                  ('Is Connected', getattr, None, {}),
                  ('Chain', getattr, None, {}),
                  ]

    _CANCEL = 'Cancel'
    _OK = 'Ok'
    _DONT_SAVE = "Don't Change"

    def _applyAllChanges(self, changes):
        """Apply all changes - update atom name
        """
        name = self.edits['name'].get()
        if self.obj.chain is not None and name != self.obj.name:

            reply = showMulti('Edit NmrChain',
                              'You are changing the name of your nmrChain.\n'
                              'Do you want to change the name of the associated Chain as well?',
                              texts=[self._OK, self._CANCEL, self._DONT_SAVE],
                              okText=self._OK, cancelText=self._CANCEL,
                              parent=self,
                              dontShowEnabled=True,
                              defaultResponse=self._OK,
                              popupId=f'{self.__class__.__name__}')
            if reply == self._CANCEL:
                return
            elif reply == self._OK:
                # also rename the chain
                chain = self.obj.chain
                super()._applyAllChanges(changes)
                chain.name = name
                return

        super()._applyAllChanges(changes)
