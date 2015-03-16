"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
import numpy

class Integral:

  def __init__(self, spectrum, points, factor=1.0, peaks=None, slope=1.0, bias=0.0):

    self.spectrum = spectrum
    self.points = points
    self.dataDimRef = self.spectrum.findFirstDataDim().findFirstDataDimRef()
    self.firstPoint = round(self.dataDimRef.pointToValue(points[0][0]), 3)
    self.lastPoint = round(self.dataDimRef.pointToValue(points[-1][0]), 3)
    # self.firstPoint = round(spectrum.pointToPpm(points[0][0], 0), 3)
    # self.lastPoint = round(spectrum.pointToPpm(points[-1][0], 0), 3)
    self.peaks = peaks
    self.slope = slope
    self.bias = bias
    self.isSelected = False
    self.volume = round(points[-1][1], 2)
    if factor:
      self.relativeVolume = round(self.volume * factor, 1)
    else:
      self.relativeVolume = self.volume

  def getPeaks(self):
    return self.peaks

  def setPeaks(self, peaks):
    self.peaks=peaks

  def addPeak(self, peak):
    self.peaks.append(peak)

  def deletePeak(self, peak):
    self.peaks.remove(peak)

  def select(self):
    self.isSelected = True

  def deselect(self):
    self.isSelected = False

  def calculateVolume(self):
    self.volume = round(self.points[-1][0], 2)
    factor = self.spectrum.integralFactor
    if factor:
      self.relativeVolume = round(self.volume * factor, 1)
    else:
      self.relativeVolume = self.volume

  def setRelativeVolume(self, relVol):

    self.relativeVolume = round(relVol, 1)
    factor = relVol / self.volume
    self.spectrum.integralFactor = factor

  def calculateRelativeVolume(self):

    self.relativeVolume = round(self.volume * self.spectrum.integralFactor, 1)

  def calculateBias(self, values, noise):

    head = 0
    points = self.points
    n = len(points)
    tail = n-1
    step = 5


    headValue = values[points[head][0]]
    tailValue = values[points[tail][0]]
    head += step
    tail -= step

    while head < tail and abs(headValue) < noise and abs(tailValue) < noise:
      headValue = values[points[head][0]]
      tailValue = values[points[tail][0]]
      head += step
      tail -= step

    head = max(head-4*step, 0)
    tail = min(tail+4*step, n-1)
    headValues = values[points[0][0]:points[head][0]]
    tailValues = values[points[tail][0]:points[-1][0]]
    if len(headValues) == 0 or len(tailValues) == 0:
      return
    headValueSum = -sum(headValues)
    tailValueSum = -sum(tailValues)
    self.bias = round((headValueSum + tailValueSum) / (len(headValues) + len(tailValues)), 3)

  def setVolume(self, volume, factor=None):
    self.volume = volume
    if factor != None:
      self.relativeVolume = factor * volume

  def delete(self):
    self.spectrum.integrals.remove(self)

  def getIntegralRegions(values, noise, peakPickLevel):
# If no peaks are selected integrals are determined automatically.
# Integrals are added if there is at least one point above the peak picking threshold and three above noise.
# Tails are added to each end of the integral and integrals are merged if overlapping.
    integrals = []
    appendIntegral = integrals.append
    tailLength = 50 # TODO: Set tailLength based on peakWidth or make it customisable
    doubleTailLength = tailLength * 2
    minLength = 3

    nPoints = len(values)

    aboveNoise = (values > noise)
    abovePeak = (values > peakPickLevel)
    bounded = numpy.hstack(([0], aboveNoise, [0]))
    # get 1 at run starts and -1 at run ends
    diffs = numpy.diff(bounded)
    starts, = numpy.where(diffs > 0)
    ends, = numpy.where(diffs < 0)
    #
    diffs = numpy.nonzero(numpy.subtract(ends, starts) > minLength)[0]

    starts = starts[diffs]
    ends = ends[diffs]

    startFlags = [True] * len(starts)

    i = 0
    while i < len(starts):
      if not any(abovePeak[starts[i]:ends[i]]):
        startFlags[i] = False
      i += 1

    starts = starts[numpy.nonzero(startFlags)]
    ends = ends[numpy.nonzero(startFlags)]
    endFlags = [True] * len(ends)
    startFlags = [True] * len(starts)

    i = 1
    while i < len(starts):
      j = i - 1
      if starts[i]-ends[j] < doubleTailLength:
        startFlags[i] = False
        endFlags[j] = False
      i += 1


    starts = starts[numpy.nonzero(startFlags)]
    ends = ends[numpy.nonzero(endFlags)]

    for i in xrange(len(starts)):
      start = max(0, starts[i]-tailLength)
      end = min(nPoints, ends[i]+tailLength)
      a = numpy.array(numpy.arange(start, end)).reshape(-1,1)
      integral = numpy.empty((len(a), 2), dtype=numpy.float32)
      integral[:, :-1] = a

      appendIntegral(integral)


    return integrals

  def setIntegrals(spectrum, values, factor = 1.0):

    spectrum.integrals = []
    append = spectrum.integrals.append

    for value in values:
      append(Integral(spectrum, value, factor))

  def calculateIntegralValues( integral, values, bias=0.0, slope=1.0):

      integral[:,1] = numpy.cumsum(values[int(integral[0,0]): int(integral[-1,0]+1)] * slope + bias)
      return integral[-1,1]



