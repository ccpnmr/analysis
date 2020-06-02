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
__dateModified__ = "$dateModified: 2020-06-02 09:52:52 +0100 (Tue, June 02, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.Complex import Complex
from ccpn.ui.gui.widgets.PulldownListsForObjects import ComplexPulldown
from ccpn.ui.gui.popups._GroupEditorPopupABC import _GroupEditorPopupABC


class ComplexEditorPopup(_GroupEditorPopupABC):
    """
    A popup to create and manage Complexes
    """
    KLASS = Complex
    KLASS_ITEM_ATTRIBUTE = 'chains'  # Attribute in KLASS containing items
    KLASS_PULLDOWN = ComplexPulldown

    PROJECT_NEW_METHOD = 'newComplex'  # Method of Project to create new KLASS instance
    PROJECT_ITEM_ATTRIBUTE = 'chains'  # Attribute of Project containing items

    PLURAL_GROUPED_NAME = 'Complexes'
    SINGULAR_GROUP_NAME = 'Complex'

    ITEM_PID_KEY = 'MC'
    GROUP_PID_KEY = 'MX'

    def __init__(self, parent=None, mainWindow=None, editMode=True, obj=None, defaultItems=None, size=(500, 350), **kwds):
        """
        Initialise the widget, note defaultItems is only used for create
        """
        super().__init__(parent=parent, mainWindow=mainWindow, editMode=editMode, obj=obj,
                         defaultItems=defaultItems, size=size, **kwds)
