__author__ = 'simon1'

from ccpn import ChemicalShift, NmrResidue, Peak, Project
from ccpncore.lib.spectrum import Spectrum as spectrumLib
from ccpncore.util import Types
from application.core.modules.GuiStrip import GuiStrip
from application.core.modules.GuiSpectrumDisplay import GuiSpectrumDisplay

MODULE_DICT = {'ASSIGNER':'showAssigner',
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


def navigateToPeakPosition(project:Project, peak:Peak=None,
   selectedDisplays:Types.List[GuiSpectrumDisplay]=None, strip:GuiStrip=None,  markPositions:bool=False):
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
    task = project._appBase.mainWindow.task
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
    #   strip.orderedAxes[1].position = axisPositions[strip.orderedAxes[1].code]
    # elif strip:
    #   strip.orderedAxes[0].position = axisPositions[strip.orderedAxes[0].code]
    #   strip.orderedAxes[1].position = axisPositions[strip.orderedAxes[1].code]

    # if len(display.orderedAxes) > 2:
    #   if not strip:
    #     try:
    #       for strip in display.strips:
    #         axisCodeMapping = spectrumLib.axisCodeMatch(strip.orderedAxes[2].code, axisCodes)
    #         zAxes = strip.orderedAxes[2:]
    #         zAxes[0].position = axisPositions[zAxes[0].code]
    #     except KeyError:
    #       for strip in display.strips:
    #         zAxes = strip.orderedAxes[2:]
    #         zAxes[0].position = axisPositions[zAxes[0].code[0]]
    #   else:
    #     try:
    #       for strip in display.strips:
    #         zAxes = strip.orderedAxes[2:]
    #         zAxes[0].position = axisPositions[zAxes[0].code]
    #     except KeyError:
    #       for strip in display.strips:
    #         zAxes = strip.orderedAxes[2:]
    #         zAxes[0].position = axisPositions[zAxes[0].code[0]]


def navigateToNmrResidue(project:Project, nmrResidue:NmrResidue,
                         selectedDisplays:Types.List[GuiSpectrumDisplay]=None,
                         strip:GuiStrip=None,  markPositions:bool=False):
  """
  Takes an NmrResidue and optional spectrum displays and strips and navigates the strips and spectrum displays
  to the positions specified by the peak.
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
            if shift is not None:
              shiftDict[axis.code].append(shift.value)

      task = project._appBase.mainWindow.task

      atomPositions = shiftDict[display.strips[0].orderedAxes[2].code]
      display.strips[0].orderedAxes[2].position = atomPositions[0]
      for atomPosition in atomPositions[1:]:
        newStrip = display.addStrip()
        newStrip.orderedAxes[2].position = atomPosition
      # for strip in display.strips:

        #
        #
        #
      for strip in display.strips:
        atomPositions2 = [shiftDict[axis.code] for axis in strip.orderedAxes[:2]]
        for ii, axis in enumerate(strip.orderedAxes[:2]):
          for atomPosition in atomPositions2[ii]:
            axis.position = atomPosition
            if markPositions:
              task.newMark('white', [atomPosition], [axis.code])
  elif strip:
    shiftDict = {}
    for axis in strip.orderedAxes:
      shiftDict[axis.code] = []
      for atom in nmrResidue.nmrAtoms:
        if atom._apiResonance.isotopeCode == spectrumLib.name2IsotopeCode(axis.code):
          shift = project.chemicalShiftLists[0].getChemicalShift(atom.id)
          if shift is not None:
            shiftDict[axis.code].append(shift.value)



    task = project._appBase.mainWindow.task


    atomPositions = [shiftDict[axis.code] for axis in strip.orderedAxes]

    for ii, axis in enumerate(strip.orderedAxes):
      for atomPosition in atomPositions[ii]:
        axis.position = atomPosition
        if markPositions:
          task.newMark('white', [atomPosition], [axis.code])



def isPositionWithinfBounds(strip:GuiStrip, shift:ChemicalShift, axis:object):
  """
  Determines whether a given shift if within the bounds of the specified axis of the specified
    strip.
  """
  minima = []
  maxima = []
  for spectrumView in strip.spectrumViews:
    index = spectrumView.spectrum.axisCodes.index(axis.code)
    minima.append(spectrumView.spectrum.spectrumLimits[index][0])
    maxima.append(spectrumView.spectrum.spectrumLimits[index][1])
  return min(minima) < shift.value <= max(maxima)


