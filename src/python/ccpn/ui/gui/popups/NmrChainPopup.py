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
__dateModified__ = "$dateModified: 2020-05-29 14:03:47 +0100 (Fri, May 29, 2020) $"
__version__ = "$Revision: 3.0.1 $"
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


class NmrChainPopup(SimpleAttributeEditorPopupABC):
    """
    NmrChain attributes editor popup
    """

    klass = NmrChain
    attributes = [('name', getattr, setattr, {'backgroundText': '> Enter name <'}),
                  ('comment', getattr, setattr, {'backgroundText': '> Optional <'}),
                  ('isConnected', getattr, None, {}),
                  ('chain', getattr, None, {}),
                  ]

    hWidth = 120
