__author__ = 'simon1'

import pyqtgraph as pg

from ccpn.core.ChemicalShift import ChemicalShift
from ccpn.core.NmrResidue import NmrResidue
from ccpn.core.Peak import Peak
from ccpn.core.Project import Project
from ccpnmodel.ccpncore.lib.spectrum import Spectrum as spectrumLib
import typing
from ccpn.ui.gui.modules.GuiStrip import GuiStrip
from ccpn.ui.gui.modules.GuiSpectrumDisplay import GuiSpectrumDisplay

MODULE_DICT = {'ASSIGNER': 'showSequenceGraph',
               'ASSIGNMENT MODULE': 'showAssignmentModule',
               'ATOM SELECTOR': 'showAtomSelector',
               'BACKBONE ASSIGNMENT': 'showBackboneAssignmentModule',
               'CHEMICAL SHIFT LISTS':'showChemicalShiftTable',
               'MACRO EDITOR':'editMacro',
               'NMR RESIDUE TABLE': 'showNmrResidueTable',
               'PEAK LIST': 'showPeakTable',
               'PICK AND ASSIGN': 'showPickAndAssignModule',
               'REFERENCE CHEMICAL SHIFTS': 'showRefChemicalShifts',
               'RESIDUE INFORMATION': 'showResidueInformation',
               'SEQUENCE': 'toggleSequence',
               'PARASSIGN SETUP': 'showParassignSetup',
               'API DOCUMENTATION': 'showApiDocumentation',
               'PYTHON CONSOLE': 'toggleConsole',
               'NOTES EDITOR': 'showNotesEditor'
               }

LINE_COLOURS = {
  'CA': '#0000FF',
  'CB': '#2400FF',
  'CG': '#4800FF',
  'CD': '#6D00FF',
  'CE': '#9100FF',
  'CZ': '#B600FF',
  'CH': '#DA00FF',
  'C': '#FF00FF',
  'HA': '#FF0000',
  'HB': '#DA2400',
  'HG': '#B64800',
  'HD': '#916D00',
  'HE': '#6D9100',
  'HZ': '#48B600',
  'HH': '#24DA00',
  'H': '#00FF00',
  'N': '#00FFFF',
  'ND': '#3FFFBF',
  'NE': '#7FFF7F',
  'NZ': '#BFFF3F',
  'NH': '#FFFF00',
}

def navigateToPeakPosition(project:Project, peak:Peak=None,
   selectedDisplays:typing.List[GuiSpectrumDisplay]=None, strip:'GuiStrip'=None,  markPositions:bool=False):
  """
  Takes a peak and optional spectrum displays and strips and navigates the strips and spectrum displays
  to the positions specified by the peak.
  """

  if selectedDisplays is None:
    selectedDisplays = [display.pid for display in project.spectrumDisplays]

  if peak is None:
    peak = project._appBase.current.peaks[0]

  for displayPid in selectedDisplays:
    display = project.getByPid(displayPid)
    positions = peak.position
    axisCodes = peak.peakList.spectrum.axisCodes
    axisPositions = dict(zip(axisCodes, positions))
    if project._appBase.ui.mainWindow is not None:
      mainWindow = project._appBase.ui.mainWindow
    else:
      mainWindow = project._appBase._mainWindow
    task = mainWindow.task
    mark = task.newMark('white', positions, axisCodes)

    # if not strip:
    for strip in display.strips:
      for axis in strip.orderedAxes:
        try:
          axisCodeMatch = spectrumLib.axisCodeMatch(axis.code, axisCodes)
          if axisCodeMatch is not None:
            axis.position = axisPositions[axisCodeMatch]
            mark = task.newMark('white', [axis.position], [axisCodeMatch])
        except TypeError:
          pass


def navigateToNmrResidue(project:Project, nmrResidue:NmrResidue,
                         selectedDisplays:typing.List[GuiSpectrumDisplay]=None,
                         strip:'GuiStrip'=None,  markPositions:bool=False):
  """
  Takes an NmrResidue and optional spectrum displays and strips and navigates the strips
  and spectrum displays to the positions specified by the peak.
  """
  if selectedDisplays is None:
    selectedDisplays = project.spectrumDisplays

  if not strip:
    for display in selectedDisplays:
      shiftDict = {}
      for axis in display.strips[0].orderedAxes:
        shiftDict[axis.code] = []
        for atom in nmrResidue.nmrAtoms:
          if atom._apiResonance.isotopeCode == spectrumLib.name2IsotopeCode(axis.code):
            shift = project.chemicalShiftLists[0].getChemicalShift(atom.id)
            if shift is not None and isPositionWithinfBounds(display.strips[0], shift, axis):
              shiftDict[axis.code].append(shift)

      if len(display.axisCodes) > 2:

        atomPositions = shiftDict[display.strips[0].axisOrder[2]]
        display.strips[0].orderedAxes[2].position = atomPositions[0].value
        if len(atomPositions) > 1:
          for i in range(len(atomPositions[1:])):
            display.addStrip()

      atomPositions2 = [shiftDict[axis.code] for axis in display.strips[0].orderedAxes[:2]]
      for guiStrip in display.strips:
        for ii, axis in enumerate(guiStrip.orderedAxes[:2]):
          if len(atomPositions2[ii]) > 0:
            if len(atomPositions2[ii]) == 1:
              for atomPosition in atomPositions2[ii]:
                axis.position = atomPosition.value
            else:
              atomPositionValues = [a.value for a in atomPositions2[ii]]
              width = max(atomPositionValues) - min(atomPositionValues)
              position = min(atomPositionValues) + (width/2)
              axis.position = position
              axis.width = width

        if markPositions:
          markPositionsInStrips(project, guiStrip, guiStrip.orderedAxes[:2], atomPositions2)

  elif strip:
    shiftDict = {}
    for axis in strip.orderedAxes:
      shiftDict[axis.code] = []
      for atom in nmrResidue.nmrAtoms:
        if atom._apiResonance.isotopeCode == spectrumLib.name2IsotopeCode(axis.code):
          shift = project.chemicalShiftLists[0].getChemicalShift(atom.id)
          if shift is not None:
            shiftDict[axis.code].append(shift)
    atomPositions = [shiftDict[axis.code] for axis in strip.orderedAxes]
    for ii, axis in enumerate(strip.orderedAxes):
      if len(atomPositions[ii]) > 0:
        if len(atomPositions[ii]) == 1:
          for atomPosition in atomPositions[ii]:
            axis.position = atomPosition.value
        else:
          atomPositionValues = [a.value for a in atomPositions[ii]]
          width = max(atomPositionValues) - min(atomPositionValues)
          position = min(atomPositionValues) + (width/2)
          axis.position = position
          axis.width = width
    if markPositions:
      markPositionsInStrips(project, strip, strip.orderedAxes, atomPositions)


def markPositionsInStrips(project, strip, axes, atomPositions):
    if project._appBase.ui.mainWindow is not None:
      mainWindow = project._appBase.ui.mainWindow
    else:
      mainWindow = project._appBase._mainWindow
    task = mainWindow.task
    for ii, axis in enumerate(axes):
      for atomPosition in atomPositions[ii]:

        atomName = atomPosition.nmrAtom.name
        if atomName[:2] in LINE_COLOURS.keys():
          task.newMark(LINE_COLOURS[atomName[:2]], [atomPosition.value], [axis.code])
          textItem = pg.TextItem(atomName, color=LINE_COLOURS[atomName[:2]])
          if ii == 0:
            y = strip.plotWidget.plotItem.vb.mapSceneToView(strip.viewBox.boundingRect().bottomLeft()).y()
            textItem.anchor = pg.Point(0, 1)
            textItem.setPos(atomPosition.value, y)
            strip.plotWidget.addItem(textItem)
            strip.xAxisAtomLabels.append(textItem)
          if ii == 1:
            x = strip.plotWidget.plotItem.vb.mapSceneToView(strip.viewBox.boundingRect().bottomLeft()).x()
            textItem.anchor = pg.Point(0, 0)
            textItem.setPos(x, atomPosition.value)
            strip.plotWidget.addItem(textItem)
            strip.yAxisAtomLabels.append(textItem)
        else:
          task.newMark('white', [atomPosition.value], [axis.code])



def isPositionWithinfBounds(strip:'GuiStrip', shift:ChemicalShift, axis:object):
  """
  Determines whether a given shift if within the bounds of the specified axis of the specified
    strip.

    NBNB Bug Fixed by Rasmus 13/3/2016.
    This was not used then. Maybe it should be?
  """
  minima = []
  maxima = []

  axisIndex = strip.axisOrder.index(axis.code)
  for spectrumView in strip.spectrumViews:
    spectrumIndices = spectrumView._displayOrderSpectrumDimensionIndices
    index = spectrumIndices[axisIndex]
    minima.append(spectrumView.spectrum.spectrumLimits[index][0])
    maxima.append(spectrumView.spectrum.spectrumLimits[index][1])
    # print(shift, strip, axis.code)
    # if axis.code in spectrumView.spectrum.axisCodes:
    #   index = spectrumView.spectrum.axisCodes.index(axis.code)
    #   minima.append(spectrumView.spectrum.spectrumLimits[index][0])
    #   maxima.append(spectrumView.spectrum.spectrumLimits[index][1])
  if len(maxima) < 1:
    return True
  else:
    return min(minima) < shift.value <= max(maxima)


