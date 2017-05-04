#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:41:03 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: simon1 $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui import guiSettings

#TODO:WAYNE: move to CcpnModule/CcpnModuleArea/GuiMainWindow, depending what it is used for
# remove the file when complete

MODULE_DICT = {
  'Sequence Graph'           : 'showSequenceGraph',
  'Peak Assigner'            : 'showPeakAssigner',
  'Atom Selector'            : 'showAtomSelector',
  'Backbone Assignment'      : 'showBackboneAssignmentModule',
  'Sidechain Assignment'     : 'showSidechainAssignmentModule',
  'Chemical Shift Table'     : 'showChemicalShiftTable',
  # 'MACRO EDITOR'             : 'editMacro',
  'Nmr Residue Table'        : 'showNmrResidueTable',
  'Peak List'                : 'showPeakTable',
  'Pick And Assign'          : 'showPickAndAssignModule',
  'Reference ChemicalShifts' : 'showRefChemicalShifts',
  'ResidueInformation'       : 'showResidueInformation',
  'Sequence'                 : 'toggleSequenceModule',
  'Parassign Setup'          : 'showParassignSetup',
  # 'API DOCUMENTATION'        : 'showApiDocumentation',
  'Python Console'           : 'toggleConsole',
  'Blank Display'            : 'addBlankDisplay',
  # 'NOTES EDITOR'             : 'showNotesEditor'
               }

#TODO:WAYNE: move to GuistripNd or GuiSpectrumDisplay or somewhere relevant
# GWV moved to GuiWindow
# def markPositions(project, axisCodes, chemicalShifts):
#   """
#   Takes a strip and creates marks based on the strip axes and adds annotations where appropriate.
#   :param project: Project instance
#   :param axisCodes: The axisCodes making a mark for
#   :param chemicalShifts: A list or tuple of ChemicalShifts at whose values the marks should be made
#   """
#   project._startCommandEchoBlock('markPositions', project, axisCodes, chemicalShifts)
#   try:
#     if project._appBase.ui.mainWindow is not None:
#       mainWindow = project._appBase.ui.mainWindow
#     else:
#       mainWindow = project._appBase._mainWindow
#     task = mainWindow.task
#
#     colourDict = guiSettings.MARK_LINE_COLOUR_DICT  # maps atomName --> colour
#     for ii, axisCode in enumerate(axisCodes):
#       for chemicalShift in chemicalShifts[ii]:
#         atomName = chemicalShift.nmrAtom.name
#         # TODO: the below fails, for example, if nmrAtom.name = 'Hn', can that happen?
#         colour = colourDict.get(atomName[:2])
#         if colour:
#           task.newMark(colour, [chemicalShift.value], [axisCode], labels=[atomName])
#         else:
#           task.newMark('white', [chemicalShift.value], [axisCode])
#
#   finally:
#     project._endCommandEchoBlock()

