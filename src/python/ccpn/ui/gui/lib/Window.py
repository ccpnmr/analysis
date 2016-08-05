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


def navigateToPositionInStrip(strip, positions, axisCodes=None, widths=None):
  """
  Takes a strip, a list of positions and optionally, a parallel list of axisCodes.
  Navigates to specified positions in strip using axisCodes, if specified, otherwise it navigates
  to the positions in the displayed axis order of the strip.
  """
  if not axisCodes:
    axisCodes = strip.axisCodes


  axisCodeMapping = [spectrumLib.axisCodeMatch(code, strip.axisCodes) for code in axisCodes]
  for ii, axisCode in enumerate(strip.axisCodes):
    stripAxisIndex = axisCodeMapping.index(axisCode)
    if positions[ii]:
      strip.orderedAxes[stripAxisIndex].position = positions[ii]
    if widths:
      if widths[ii]:
        # if this item in the list contains a float, set the axis width to that float value
        if isinstance(widths[ii], float):
          strip.orderedAxes[stripAxisIndex].width = widths[ii]
        elif isinstance(widths[ii], str):
          # if the list item is a str with value, full, reset the corresponding axis
          if widths[ii] == 'full':
            strip.resetAxisRange(stripAxisIndex)
          if widths[ii] == 'default' and stripAxisIndex < 2:
            # if the list item is a str with value, default, set width to 5ppm for heteronuclei and 0.5ppm for 1H
            if spectrumLib.name2IsotopeCode(axisCode) == '13C' or spectrumLib.name2IsotopeCode(axisCode) == '15N':
              strip.orderedAxes[stripAxisIndex].width = 5
            else:
              strip.orderedAxes[stripAxisIndex].width = 0.5


def makeStripPlot(spectrumDisplay, nmrAtomPairs, autoWidth=True):

  numberOfStrips = len(spectrumDisplay.strips)

  # Make sure there are enough strips to display nmrAtomPairs
  if numberOfStrips < len(nmrAtomPairs):
    for ii in range(numberOfStrips, len(nmrAtomPairs)):
      spectrumDisplay.strips[-1].clone()

  # loop through strips and navigate to appropriate position in strip
  for ii, strip in enumerate(spectrumDisplay.strips):
    if autoWidth:
      widths = ['default'] * len(strip.axisCodes)
    else:
      widths = None
    navigateToNmrAtomsInStrip(nmrAtomPairs[ii], strip, widths=widths)



def navigateToPeakPosition(project:Project, peak:Peak=None,
   selectedDisplays:typing.List[GuiSpectrumDisplay]=None, strip:'GuiStrip'=None):
  """
  Takes a peak and optional spectrum displays and strips and navigates the strips and spectrum displays
  to the positions specified by the peak.
  """

  if selectedDisplays is None and not strip:
    selectedDisplays = [display.pid for display in project.spectrumDisplays]

  if peak is None:
    if project._appBase.current.peaks[0]:
      peak = project._appBase.current.peaks[0]
    else:
      print('No peak passed in')
      return

  positions = peak.position
  axisCodes = peak.axisCodes

  if not strip:
    for displayPid in selectedDisplays:
      display = project.getByPid(displayPid)
      for strip in display.strips:
        navigateToPositionInStrip(strip, positions, axisCodes)
  else:
    navigateToPositionInStrip(strip, positions, axisCodes)



def matchAxesAndNmrAtoms(strip, nmrAtoms):

  shiftDict = {}
  shiftList = strip.spectra[0].chemicalShiftList
  for axis in strip.orderedAxes:
    shiftDict[axis.code] = []
    for atom in nmrAtoms:
      if atom._apiResonance.isotopeCode == spectrumLib.name2IsotopeCode(axis.code):
        shift = shiftList.getChemicalShift(atom.id)
        if shift is not None and isPositionWithinfBounds(strip, shift, axis):
          shiftDict[axis.code].append(shift)

  return shiftDict


def navigateToNmrAtomsInStrip(nmrAtoms:typing.List[NmrAtom], strip:'GuiStrip'=None,  widths=None, markPositions:bool=False):
  """
  Takes an NmrResidue and optional spectrum displays and strips and navigates the strips
  and spectrum displays to the positions specified by the peak.
  """

  if not strip:
    print('no strip specified')
    return

  shiftDict = matchAxesAndNmrAtoms(strip, nmrAtoms)
  # atomPositions = shiftDict[strip.axisOrder[2]]
  atomPositions = [[x.value for x in shiftDict[axisCode]] for axisCode in strip.axisOrder]
  positions = []
  for atomPos in atomPositions:
    if atomPos:
      if len(atomPos) < 2:
        positions.append(atomPos[0])
      else:
        positions.append(max(atomPos)-min(atomPos)/2)
    else:
      positions.append('')
  navigateToPositionInStrip(strip, positions, strip.axisOrder, widths=widths)


def markPositions(project, axisCodes, atomPositions):
    """
    Takes a strip and creates marks based on the strip axes and adds annotations where appropriate.
    """
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

def isPositionWithinfBounds(strip:'GuiStrip', shift:ChemicalShift, axis:object):
  """
  Determines whether a given shift is within the bounds of the specified axis of the specified
  strip.

  NBNB Bug Fixed by Rasmus 13/3/2016.
  This was not used then. Maybe it should be?

  Modified to use aliasingLimits instead of spectrumLimits. Rasmus, 24/7/2016

  """
  minima = []
  maxima = []

  axisIndex = strip.axisOrder.index(axis.code)

  for spectrumView in strip.spectrumViews:
    spectrumIndices = spectrumView._displayOrderSpectrumDimensionIndices
    index = spectrumIndices[axisIndex]
    minima.append(spectrumView.spectrum.aliasingLimits[index][0])
    maxima.append(spectrumView.spectrum.aliasingLimits[index][1])

  if len(maxima) < 1:
    return True
  else:
    return min(minima) < shift.value <= max(maxima)


