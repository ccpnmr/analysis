"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
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
__dateModified__ = "$dateModified: 2022-11-15 16:51:16 +0000 (Tue, November 15, 2022) $"
__version__ = "$Revision: 3.1.0 $"
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
    _class = Complex
    _classPulldown = ComplexPulldown

    _classItemAttribute = 'chains'  # Attribute in _class containing items

    _projectNewMethod = 'newComplex'  # Method of Project to create new _class instance
    _projectItemAttribute = 'chains'  # Attribute of Project containing items

    # define these
    _singularItemName = 'Chain'  # eg 'Spectrum'
    _pluralItemName = 'Chains'  # eg 'Spectra'
