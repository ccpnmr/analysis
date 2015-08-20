__author__ = 'simon1'

from ccpn.lib.assignment import getIsotopeCodeOfAxis

def navigateToPeakPosition(project, peak=None, selectedDisplays=None, markPositions=False):

  if selectedDisplays is None:
    selectedDisplays = project.spectrumDisplays

  if peak is None:
    peak = project._appBase.current.peaks[0]

  for display in selectedDisplays:
    positions = peak.position
    axisCodes = peak.peakList.spectrum.axisCodes
    axisPositions = dict(zip(axisCodes, positions))
    if len(display.orderedAxes) > 2:
      try:
        zAxes = display.strips[0].orderedAxes[2:]
        zAxes[0].position = axisPositions[zAxes[0].code]
      except KeyError:
        zAxes = display.strips[0].orderedAxes[2:]
        zAxes[0].position = axisPositions[zAxes[0].code[0]]


def navigateToNmrResidue(project, nmrResidue=None, selectedDisplays=None, markPositions=False):

  if selectedDisplays is None:
      selectedDisplays = project.spectrumDisplays

  if nmrResidue is None:
    nmrResidue = project._appBase.current.nmrResidues[0]

  for display in selectedDisplays:
    # for strip in display.strips:
    shiftDict = {}
    for axis in display.strips[0].orderedAxes:
      shiftDict[axis.code] = []
      for atom in nmrResidue.atoms:
        if atom.apiResonance.isotopeCode == getIsotopeCodeOfAxis(axis.code):
          shift = project.chemicalShiftLists[0].findChemicalShift(atom)
          if shift is not None:
            if isPositionWithinfBounds(display.strips[0], shift, axis):
              shiftDict[axis.code].append(shift.value)
    task = project._appBase.mainWindow.task
    axisCodes = [axis.code for axis in display.strips[0].orderedAxes]
    atomPositions = [shiftDict[axis.code] for axis in display.strips[0].orderedAxes]
    if len(shiftDict[display.strips[0].orderedAxes[2].code]) > 0:
      display.strips[0].changeZPlane(position=shiftDict[display.strips[0].orderedAxes[2].code][0])

    if markPositions is True:
      markPositions = []
      for pos1 in atomPositions[0]:
        for pos2 in atomPositions[1]:
          newMarkPosition = [pos1, pos2, atomPositions[2][0]]
          markPositions.append(newMarkPosition)
      for markPosition in markPositions:
        mark = task.newMark('white', markPosition, axisCodes)

    if len(shiftDict[display.strips[0].orderedAxes[2].code]) > 1:
      shifts = shiftDict[display.strips[0].orderedAxes[2].code][1:]
      for shift in shifts:
        newStrip = display.strips[0].clone()
        newStrip.changeZPlane(position=shift)
        if markPositions is True:
          markPositions = []
          for pos1 in atomPositions[0]:
            for pos2 in atomPositions[1]:
              newMarkPosition = [pos1, pos2, atomPositions[2][shifts.index(shift)]]
              markPositions.append(newMarkPosition)
          for markPosition in markPositions:
            mark = task.newMark('white', markPosition, axisCodes)


def isPositionWithinfBounds(strip, shift, axis):

      minima = []
      maxima = []
      for spectrumView in strip.spectrumViews:
        print(axis.code, spectrumView.spectrum.axisCodes)
        index = spectrumView.spectrum.axisCodes.index(axis.code)
        minima.append(spectrumView.spectrum.spectrumLimits[index][0])
        maxima.append(spectrumView.spectrum.spectrumLimits[index][1])
      return min(minima) < shift.value <= max(maxima)


