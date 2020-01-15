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
__dateModified__ = "$dateModified: 2020-01-15 14:42:22 +0000 (Wed, January 15, 2020) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from ccpn.core.SpectrumGroup import SpectrumGroup
from ccpn.ui.gui.widgets.PulldownListsForObjects import SpectrumGroupPulldown
from ccpn.ui.gui.popups._GroupEditorPopupABC import _GroupEditorPopupABC
from ccpn.ui.gui.widgets.Tabs import Tabs
from ccpn.ui.gui.widgets.Frame import ScrollableFrame
from ccpn.util.Logging import getLogger


class SpectrumGroupEditor(_GroupEditorPopupABC):
    """
    A popup to create and manage SpectrumGroups

    Used in 'New' or 'Edit' mode:
    - For creating new SpectrumGroup (editMode==False); optionally uses passed in spectra list
      i.e. NewSpectrumGroup of SideBar and Context menu of SideBar

    - For editing existing SpectrumGroup (editMode==True); requires spectrumGroup argument
      i.e. Edit of SpectrumGroup of SideBar
    or
      For selecting and editing SpectrumGroup (editMode==True)
      i.e. Menu Spectrum->Edit SpectrumGroup...

    """
    KLASS = SpectrumGroup
    KLASS_ITEM_ATTRIBUTE = 'spectra'  # Attribute in KLASS containing items
    KLASS_PULLDOWN = SpectrumGroupPulldown

    PROJECT_NEW_METHOD = 'newSpectrumGroup'  # Method of Project to create new KLASS instance
    PROJECT_ITEM_ATTRIBUTE = 'spectra'  # Attribute of Project containing items
    PLURAL_GROUPED_NAME = 'Spectrum Groups'
    SINGULAR_GROUP_NAME = 'Spectrum Group'

    GROUP_PID_KEY = 'SG'
    ITEM_PID_KEY = 'SP'

    # make this a tabbed dialog, with the default widget going into tab 0
    USE_TAB = 0
    NUMBER_TABS = 3
