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
__dateModified__ = "$dateModified: 2020-09-22 09:33:23 +0100 (Tue, September 22, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank$"
__date__ = "$Date: 9/05/2017 $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.Note import Note
from ccpn.ui.gui.popups.AttributeEditorPopupABC import AttributeEditorPopupABC
from ccpn.ui.gui.widgets.CompoundWidgets import EntryCompoundWidget


class NotesPopup(AttributeEditorPopupABC):
    """Notes attributes editor popup"""

    klass = Note
    attributes = [('name', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Enter name <'}),
                  ('comment', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}),
                  ]
