__author__ = 'simon1'

from ccpn.core.ChemicalShift import ChemicalShift
from ccpn.core.NmrAtom import NmrAtom
from ccpn.core.Peak import Peak
from ccpn.core.Project import Project
from ccpnmodel.ccpncore.lib.spectrum import Spectrum as spectrumLib
import typing
from ccpn.ui.gui.modules.GuiStrip import GuiStrip
from ccpn.ui.gui.modules.GuiSpectrumDisplay import GuiSpectrumDisplay

MODULE_DICT = {
  'SEQUENCE GRAPH'           : 'showSequenceGraph',
  'PEAK ASSIGNER'            : 'showPeakAssigner',
  'ATOM SELECTOR'            : 'showAtomSelector',
  'BACKBONE ASSIGNMENT'      : 'showBackboneAssignmentModule',
  'SIDECHAIN ASSIGNMENT'     : 'showSidechainAssignmentModule',
  'CHEMICAL SHIFT TABLE'     : 'showChemicalShiftTable',
  'MACRO EDITOR'             : 'editMacro',
  'NMR RESIDUE TABLE'        : 'showNmrResidueTable',
  'PEAK LIST'                : 'showPeakTable',
  'PICK AND ASSIGN'          : 'showPickAndAssignModule',
  'REFERENCE CHEMICAL SHIFTS': 'showRefChemicalShifts',
  'RESIDUE INFORMATION'      : 'showResidueInformation',
  'SEQUENCE'                 : 'toggleSequenceModule',
  'PARASSIGN SETUP'          : 'showParassignSetup',
  'API DOCUMENTATION'        : 'showApiDocumentation',
  'PYTHON CONSOLE'           : 'toggleConsole',
  'NOTES EDITOR'             : 'showNotesEditor'
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
    project._startFunctionCommandBlock('markPositions', project, axisCodes, atomPositions)
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
      project._appBase._endCommandBlock()

