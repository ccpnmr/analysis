#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-06-04 16:43:28 +0100 (Fri, June 04, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

# from ccpn.ui.gui import guiSettings
#
#
# #TODO:WAYNE: move to CcpnModule/CcpnModuleArea/GuiMainWindow, depending what it is used for
# # remove the file when complete
#
# MODULE_DICT = {
#     'Sequence Graph'          : 'showSequenceGraph',
#     'Peak Assigner'           : 'showPeakAssigner',
#     'Atom Selector'           : 'showAtomSelector',
#     'Backbone Assignment'     : 'showBackboneAssignmentModule',
#     'Sidechain Assignment'    : 'showSidechainAssignmentModule',
#     'Chemical Shift Table'    : 'showChemicalShiftTable',
#     # 'MACRO EDITOR'             : 'editMacro',
#     'Nmr Residue Table'       : 'showNmrResidueTable',
#     'Peak List'               : 'showPeakTable',
#     'Pick And Assign'         : 'showPickAndAssignModule',
#     'Reference ChemicalShifts': 'showRefChemicalShifts',
#     'ResidueInformation'      : 'showResidueInformation',
#     'Sequence'                : 'toggleSequenceModule',
#     'Parassign Setup'         : 'showParassignSetup',
#     # 'API DOCUMENTATION'        : 'showApiDocumentation',
#     'Python Console'          : 'toggleConsole',
#     'Blank Display'           : 'addBlankDisplay',
#     # 'NOTES EDITOR'             : 'showNotesEditor'
#     }
