"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Joanna Fox, Morgan Hayward, Victoria A Higman, Luca Mureddu",
               "Eliza Płoskoń, Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2024-04-18 14:07:52 +0100 (Thu, April 18, 2024) $"
__version__ = "$Revision: 3.2.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-07-04 09:28:16 +0000 (Tue, July 04, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.popups._GroupEditorPopupABC import _GroupEditorPopupABC
from ccpn.core.ChemicalShiftList import ChemicalShiftList
from ccpn.ui.gui.widgets.PulldownListsForObjects import ChemicalShiftListPulldown


class ChemicalShiftListEditor(_GroupEditorPopupABC):
    """
    A popup to create and manage SpectrumGroups

    Used in 'New' or 'Edit' mode:
    - For creating new ChemicalShiftList (editMode==False); optionally uses passed in spectra list
      i.e. NewChemicalShiftList of SideBar and Context menu of SideBar

    - For editing existing ChemicalShiftList (editMode==True); requires ChemicalShiftList argument
      i.e. Edit of ChemicalShiftList of SideBar

    """
    _class = ChemicalShiftList
    _classItemAttribute = 'spectra'  # Attribute in _class containing items
    _classPulldown = ChemicalShiftListPulldown

    _projectNewMethod = 'newChemicalShiftList'  # Method of Project to create new _class instance
    _projectItemAttribute = 'spectra'  # Attribute name of Project containing items
    _pluralGroupName = 'Chemical Shift Lists'
    _singularGroupName = 'Chemical Shift List'

