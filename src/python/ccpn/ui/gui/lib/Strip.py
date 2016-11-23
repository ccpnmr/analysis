import typing

from ccpn.util import Common as commonUtil
from ccpn.core.ChemicalShift import ChemicalShift
from ccpn.core.NmrAtom import NmrAtom
from ccpn.ui.gui.modules.GuiStrip import GuiStrip
from ccpn.ui.gui.lib import Window

def navigateToPositionInStrip(strip, positions:typing.List[float], axisCodes:typing.List[str]=None,
                              widths:typing.List[float]=None):
  """
  Takes a strip, a list of positions and optionally, a parallel list of axisCodes.
  Navigates to specified positions in strip using axisCodes, if specified, otherwise it navigates
  to the positions in the displayed axis order of the strip.
  """
  if not axisCodes:
    axisCodes = strip.axisCodes

  for ii, axisCode in enumerate(axisCodes):
    try:
      stripAxisIndex = strip.axisCodes.index(axisCode)
    except ValueError as e:
      continue
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
            if (commonUtil.name2IsotopeCode(axisCode) == '13C' or
                commonUtil.name2IsotopeCode(axisCode) == '15N'):
              strip.orderedAxes[stripAxisIndex].width = 5
            else:
              strip.orderedAxes[stripAxisIndex].width = 0.5


def matchAxesAndNmrAtoms(strip:'GuiStrip', nmrAtoms:typing.List[NmrAtom]):

  shiftDict = {}
  shiftList = strip.spectra[0].chemicalShiftList
  for axis in strip.orderedAxes:
    shiftDict[axis.code] = []
    for atom in nmrAtoms:
      if atom._apiResonance.isotopeCode == commonUtil.name2IsotopeCode(axis.code):
        shift = shiftList.getChemicalShift(atom.id)
        if shift is not None and isPositionWithinfBounds(strip, shift, axis):
          shiftDict[axis.code].append(shift)

  return shiftDict

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

def navigateToNmrAtomsInStrip(strip:'GuiStrip', nmrAtoms:typing.List[NmrAtom], widths=None,
                              markPositions:bool=False):
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
  navigateToPositionInStrip(strip, positions, widths=widths)
  if markPositions:
    Window.markPositions(strip.project, list(shiftDict.keys()), list(shiftDict.values()))

