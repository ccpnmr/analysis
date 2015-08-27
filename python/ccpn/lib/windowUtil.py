__author__ = 'simon1'

from ccpn.lib.Assignment import getIsotopeCodeOfAxis

def navigateToPeakPosition(project, peak=None, selectedDisplays=None, strip=None,  markPositions=False):

  if selectedDisplays is None:
    selectedDisplays = [display.pid for display in project.spectrumDisplays]

  if peak is None:
    peak = project._appBase.current.peaks[0]

  for displayPid in selectedDisplays:
    display = project.getById(displayPid)
    positions = peak.position
    axisCodes = peak.peakList.spectrum.axisCodes
    axisPositions = dict(zip(axisCodes, positions))
    task = project._appBase.mainWindow.task
    mark = task.newMark('white', positions, axisCodes)

    # if not strip:
    for strip in display.strips:
      strip.orderedAxes[0].position = axisPositions[strip.orderedAxes[0].code]
    #     strip.orderedAxes[1].position = axisPositions[strip.orderedAxes[1].code]
    # elif strip:
    #   strip.orderedAxes[0].position = axisPositions[strip.orderedAxes[0].code]
    #   strip.orderedAxes[1].position = axisPositions[strip.orderedAxes[1].code]

    if len(display.orderedAxes) > 2:
      if not strip:
        try:
          for strip in display.strips:
            zAxes = strip.orderedAxes[2:]
            zAxes[0].position = axisPositions[zAxes[0].code]
        except KeyError:
          for strip in display.strips:
            zAxes = strip.orderedAxes[2:]
            zAxes[0].position = axisPositions[zAxes[0].code[0]]
      else:
        try:
          for strip in display.strips:
            zAxes = strip.orderedAxes[2:]
            zAxes[0].position = axisPositions[zAxes[0].code]
        except KeyError:
          for strip in display.strips:
            zAxes = strip.orderedAxes[2:]
            zAxes[0].position = axisPositions[zAxes[0].code[0]]


def navigateToNmrResidue(project, nmrResidue, selectedDisplays=None, markPositions=False):

  if selectedDisplays is None:
    selectedDisplays = project.spectrumDisplays

  for displayPid in selectedDisplays:
    display = project.getById(displayPid)
    print(display)
    # for strip in display.strips:
    shiftDict = {}
    for axis in display.strips[0].orderedAxes:
      shiftDict[axis.code] = []
      for atom in nmrResidue.atoms:
        if atom.apiResonance.isotopeCode == getIsotopeCodeOfAxis(axis.code):
          shift = project.chemicalShiftLists[0].findChemicalShift(atom)
          print(shift)
          if shift is not None:
            if isPositionWithinfBounds(display.strips[0], shift, axis):
              shiftDict[axis.code].append(shift.value)
    task = project._appBase.mainWindow.task
    axisCodes = [axis.code for axis in display.strips[0].orderedAxes]
    atomPositions = [shiftDict[axis.code] for axis in display.strips[0].orderedAxes]
    if len(shiftDict[display.strips[0].orderedAxes[2].code]) > 0:
      display.strips[0].changeZPlane(position=shiftDict[display.strips[0].orderedAxes[2].code][0])
      display.orderedStrips[0].orderedAxes[0].position = shiftDict[display.strips[0].orderedAxes[0].code][0]

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

  # elif strip is not None:
  #   shiftDict = {}
  #   for axis in strip.orderedAxes:
  #     shiftDict[axis.code] = []
  #     for atom in nmrResidue.atoms:
  #       if atom.apiResonance.isotopeCode == getIsotopeCodeOfAxis(axis.code):
  #         shift = project.chemicalShiftLists[0].findChemicalShift(atom)
  #         print(shift)
  #         if shift is not None:
  #           if isPositionWithinfBounds(strip, shift, axis):
  #             shiftDict[axis.code].append(shift.value)
  #   task = project._appBase.mainWindow.task
  #   axisCodes = [axis.code for axis in strip.orderedAxes]
  #   atomPositions = [shiftDict[axis.code] for axis in strip.orderedAxes]
  #   if len(shiftDict[strip.orderedAxes[2].code]) > 0:
  #     strip.changeZPlane(position=shiftDict[strips[0].orderedAxes[2].code][0])
  #     display.orderedStrips[0].orderedAxes[0].position = shiftDict[display.strips[0].orderedAxes[0].code][0]
  #
  #   if markPositions is True:
  #     markPositions = []
  #     for pos1 in atomPositions[0]:
  #       for pos2 in atomPositions[1]:
  #         newMarkPosition = [pos1, pos2, atomPositions[2][0]]
  #         markPositions.append(newMarkPosition)
  #     for markPosition in markPositions:
  #       mark = task.newMark('white', markPosition, axisCodes)
  #
  #   if len(shiftDict[display.strips[0].orderedAxes[2].code]) > 1:
  #     shifts = shiftDict[display.strips[0].orderedAxes[2].code][1:]
  #     for shift in shifts:
  #       newStrip = display.strips[0].clone()
  #       newStrip.changeZPlane(position=shift)
  #       if markPositions is True:
  #         markPositions = []
  #         for pos1 in atomPositions[0]:
  #           for pos2 in atomPositions[1]:
  #             newMarkPosition = [pos1, pos2, atomPositions[2][shifts.index(shift)]]
  #             markPositions.append(newMarkPosition)
  #         for markPosition in markPositions:
  #           mark = task.newMark('white', markPosition, axisCodes)

def isPositionWithinfBounds(strip, shift, axis):

      minima = []
      maxima = []
      for spectrumView in strip.spectrumViews:
        print(axis.code, spectrumView.spectrum.axisCodes)
        index = spectrumView.spectrum.axisCodes.index(axis.code)
        minima.append(spectrumView.spectrum.spectrumLimits[index][0])
        maxima.append(spectrumView.spectrum.spectrumLimits[index][1])
      return min(minima) < shift.value <= max(maxima)


