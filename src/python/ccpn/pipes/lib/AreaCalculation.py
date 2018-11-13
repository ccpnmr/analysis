"""
Automatic Area calculation

Calculate the area under the peak curve. To calculate the peak limits is used an arbitrary line that will cross the
spectrum in each peak. The intersecting line will be by default the estimated noise level threshold for the spectrum.
Eg the standard deviation of all the peaks height. The intersecting points will be the peak's limits.

The area is calculated using the composite trapezoidal rule.
"""


#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:39 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


import numpy as np
from scipy.integrate import trapz
from ccpn.core.IntegralList import _getPeaksLimits

from ccpn.util.Logging import getLogger , _debug3





def _calculateIntegrals(x, y):
  limitsPairs = _getPeaksLimits(x, y)
  integrals = []
  for i in limitsPairs:
    index01 = np.where((x <= i[0]) & (x >= i[1]))
    integral = trapz(index01)
    pos = abs(i[0] + i[1]) / 2
    integrals.append((pos, integral))
  return integrals


def _getIntegralRegions(x, y):
  ''' Just for coloring a plot
  return: array of points '''
  limitsPairs = _getPeaksLimits(x, y)
  integralRegions = []
  for i in limitsPairs:
    index01 = np.where((x <= i[0]) & (x >= i[1]))
    y_region = y[index01]
    x_region = x[index01]
    integralRegions.append((x_region, y_region))
  return integralRegions


def _matchingPosition(data, limitMax, limitMin):
  ''' copied from experimental analysis
  In this example will use numpy  logical and argwhere a condition is met.
  Data: the list of peak positions.
  limitRange: the limit to add on the left and on the right
  :return: array with matching positions
  '''
  return data[np.argwhere(np.logical_and(data <= limitMax, data >= limitMin))]


def _getMultiplet(peaks, limitA, limitB):
  ''' CCPNmr specific
  :param peaks: list of peaks from a full peakList obj
  :param limitA: limit range from where is supposed to start/finish the multiplet
  :param limitB: limit range from where is supposed to start/finish the multiplet
  :return: list of peaks that can be considered a multiplet of the same peak
  '''
  multiplet = []
  for peak in peaks:
    matchedPosition = _matchingPosition(np.array(peak.position), limitA, limitB)
    if matchedPosition:
      multiplet.append(peak)
  if len(multiplet) > 0:
    return multiplet
  else:
    return []


def _calculateCenterOfMass(multiplet):
  '''  CCPNmr specific

  :param multiplet: list of peaks that can be considered a multiplet of the same peak.
  :return: the center of mass of the multiplet that can be used as peak position
           if you consider the multiplet as a single peak
  '''

  if len(multiplet) > 0:
    peakPositions = [peak.position[0] for peak in multiplet]
    peakIntensities = [peak.height for peak in multiplet]
    numerator = []
    for p, i in zip(peakPositions, peakIntensities):
      numerator.append(p * i)
    centerOfMass = sum(numerator) / sum(peakIntensities)
    return centerOfMass


def _getMultipletIntensity(multiplet):
  'return the heighest peak intensity across the multiplet peaks'
  if len(multiplet) > 0:
    return max([peak.height for peak in multiplet])



def _addAreaValuesToPeaks(spectrum, peakList, noiseThreshold=None, minimalLineWidth=0.01):
  ''' CCPNmr specific

  Create new multiplets. Needs a peakList with already picked peaks (with peak positions and height).
   This function will not replace any peak in the original peakList. It will be like a copy of the first plus the new peak will
   have  limits ,  Area, lineWidth,  center of mass as position, height.
   If multiplets they will be calculated as a single peak.

   Integral objs will be added to the spectrum IntegralList

   '''

  # TODO excludeRegions
  x, y = np.array(spectrum.positions), np.array(spectrum.intensities)
  if noiseThreshold is None or 0.0:
    intersectingLine = None
  else:
    intersectingLine = [noiseThreshold] * len(x)
  limitsPairs = _getPeaksLimits(x, y, intersectingLine)

  peaks = []
  # integrals = []

  newMultipletList = spectrum.newMultipletList()
  # if spectrum.integralLists:
  #   integralList = spectrum.integralLists[0]
  # else:
  #   integralList = spectrum.newIntegralList()

  for i in limitsPairs:
    lineWidth = abs(i[0] - i[1]) # calculate line width
    if lineWidth > minimalLineWidth:  # an attempt to exclude noise
      index01 = np.where((x <= i[0]) & (x >= i[1])) # calculate integrals
      values = spectrum.intensities[index01]

      integral = trapz(values)
      multipletPeaks = _getMultiplet(peakList.peaks, limitA=i[0], limitB=i[1]) # get multiplets
      if len(multipletPeaks) == 0:
        continue
      # calculate center of mass position for multiplets, these will be the new peak position and the multipl will be counted as one single peak.
      # centerOfMass = _calculateCenterOfMass(multipletPeaks)
      # calculate new intensity for multiplet ( if single peak stays the same)
      # height = _getMultipletIntensity(multipletPeaks)
      # if centerOfMass and  height is not None:
      ## create a new Peak object
      spectrum.project.suspendNotification()
      try:
        multiplet = newMultipletList.newMultiplet(peaks = multipletPeaks, volume= float(integral))
        multiplet.lineWidths= (lineWidth,)
        if len(multipletPeaks)==1:
          peak = multipletPeaks[0]
          peak.lineWidths = (lineWidth,)
          peak.volume = float(integral)

        # peak = newPeakList.newPeak(height= height, position = (centerOfMass,),volume= float(integral),lineWidths= (lineWidth,))
        # peaks.append(peak)
        # integral = integralList.newIntegral(value=float(integral), limits=[[min(i), max(i)],])
        # integrals.append(integral)
      except Exception as e:
        getLogger().warning('Error: %s' %e)

      finally:
        spectrum.project.resumeNotification()
