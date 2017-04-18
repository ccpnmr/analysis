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

# from ccpn.core.ChemicalShift import ChemicalShift
# from ccpn.core.NmrAtom import NmrAtom
# from ccpn.core.Peak import Peak
# from ccpn.core.Project import Project
# from ccpnmodel.ccpncore.lib.spectrum import Spectrum as spectrumLib
# import typing
# from ccpn.ui.gui.modules.GuiStrip import GuiStrip
# from ccpn.ui.gui.modules.GuiSpectrumDisplay import GuiSpectrumDisplay

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

LINE_COLOURS = {
  'CA': '#0000FF',
  'CB': '#0024FF',
  'CG': '#0048FF',
  'CD': '#006DFF',
  'CE': '#0091FF',
  'CZ': '#00B6FF',
  'CH': '#00DAFF',
  'C' : '#00FFFF',
  'HA': '#FF0000',
  'HB': '#FF0024',
  'HG': '#FF0048',
  'HD': '#FF006D',
  'HE': '#FF0091',
  'HZ': '#FF00B6',
  'HH': '#FF00DA',
  'H' : '#FF00FF',
  'N' : '#00FF00',
  'ND': '#3FFF00',
  'NE': '#7FFF00',
  'NZ': '#BFFF00',
  'NH': '#FFFF00',
}


def markPositions(project, axisCodes, atomPositions):
    """
    Takes a strip and creates marks based on the strip axes and adds annotations where appropriate.
    """
    project._startCommandEchoBlock('markPositions', project, axisCodes, atomPositions)
    try:
      if project._appBase.ui.mainWindow is not None:
        mainWindow = project._appBase.ui.mainWindow
      else:
        mainWindow = project._appBase._mainWindow
      task = mainWindow.task

      for ii, axisCode in enumerate(axisCodes):
        for atomPosition in atomPositions[ii]:
          atomName = atomPosition.nmrAtom.name
          if atomName[:2] in LINE_COLOURS.keys():
            task.newMark(LINE_COLOURS[atomName[:2]], [atomPosition.value], [axisCode], labels=[atomName])
          else:
            task.newMark('white', [atomPosition.value], [axisCode])


    finally:
      project._endCommandEchoBlock()

