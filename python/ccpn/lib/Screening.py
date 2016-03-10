__author__ = 'luca'


import numpy as np
import pandas as pd
import matplotlib as mpl
from matplotlib import pyplot as plt
from collections import namedtuple
from math import sin, cos, pi, log
import os
from numpy import argwhere
from scipy.ndimage import maximum_filter


Peak = namedtuple('Peak', ['frequency', 'linewidth', 'intensity', 'phase'])
Peak.__new__.__defaults__ = (0,)

FIELD = 400
SW_PPM = 14
CENTER = 4.7
POINTS = 2**14

spectrum_x_ppm = np.linspace(CENTER+SW_PPM/2, CENTER-SW_PPM/2, POINTS)
spectrum_x_hz = spectrum_x_ppm * FIELD


def lorentzian(points, center, linewidth, intensity=1, phase=0):
  points = np.asarray(points)
  tau = 2/linewidth
  delta = center-points
  x = delta * tau

  absorptive = (1/(1 + x**2))/linewidth
  normCoeff = absorptive.max()

  return intensity * absorptive/normCoeff


def spectrumFromPeaks(x, peaks):
  spectrum = np.zeros(len(x))
  for peak in peaks:
      subspec = lorentzian(x, peak.frequency, peak.linewidth, intensity = peak.intensity, phase=peak.phase)
      spectrum += subspec
  return spectrum


def matchedPosition(stdPeaks, componentPeaks, tolerance:float=0.005, minimumMatches:int=1):
  '''
  Matches peaks from the std spectrum ( Std off resonance -  Std on resonance) to a given reference component.

  '''
  #
  # stdArray = np.array(stdPeaks)
  # componentArray = np.array(componentPeaks)
  #
  #
  # diff_STD_Comp = abs(componentArray - stdArray)
  # pos = [i for i in diff_STD_Comp if i <= tolerance]
  # matchedPositions = []
  # for i in range(len(pos)):
  #     matchedPos = np.argsort(diff_STD_Comp)[i]
  #     matchedPositions.append(componentPeaks[matchedPos])
  # if len(matchedPositions)>=minimumMatches:
  #   return  matchedPositions
  #

  ''''''

  matchedPositions = [stdPosition for componentPosition in componentPeaks
                            for stdPosition in stdPeaks if abs(stdPosition-componentPosition)<=tolerance]
  if len(matchedPositions)>=minimumMatches:
   return matchedPositions

def createStdDifferenceSpectrum(stdOffResonance, stdOnResonance):
  stdOffResonanceArray = stdOffResonance._apiDataSource.get1dSpectrumData()[1]
  stdOnResonanceArray = stdOnResonance._apiDataSource.get1dSpectrumData()[1]

  stdDifference = stdOffResonanceArray - stdOnResonanceArray
  return stdDifference



def estimateNoise(spectrum):
    noiseLevel = 5* np.std(spectrum)
    return noiseLevel

def writeBruker(directory, data):

  dic = {'BYTORDP': 0, # Byte order, little (0) or big (1) endian
         'NC_proc': 0, # Data scaling factor, -3 means data were multiplied by 2**3, 4 means divided by 2**4
         'SI': POINTS, # Size of processed data
         'XDIM': 0, # Block size for 2D & 3D data
         'FTSIZE': POINTS, # Size of FT output.  Same as SI except for strip plotting.
         'SW_p': SW_PPM * FIELD, # Spectral width of processed data in Hz
         'SF': FIELD, # Spectral reference frequency (center of spectrum)
         'OFFSET': SW_PPM/2 + CENTER, # ppm value of left-most point in spectrum
         'AXNUC': '<1H>',
         'LB': 5.0, # Lorentzian broadening size (Hz)
         'GB': 0, # Gaussian broadening factor
         'SSB': 0, # Sine bell shift pi/ssb.  =1 for sine and =2 for cosine.  values <2 default to sine
         'WDW': 1, # Window multiplication mode
         'TM1': 0, # End of the rising edge of trapezoidal, takes a value from 0-1, must be less than TM2
         'TM2': 1, # Beginings of the falling edge of trapezoidal, takes a value from 0-1, must be greater than TM1
         'BC_mod': 0 # Baseline correction mode (em, gm, sine, qsine, trap, user(?), sinc, qsinc, traf, trafs(JMR 71 1987, 237))
        }

  procDir = 'pdata/1'
  realFileName = '1r'
  try:
      os.makedirs(os.path.join(directory, procDir))
  except FileExistsError:
      pass

  specMax2 = np.log2(data.max())
  factor = int(29-specMax2)
  data = data * 2**factor
  dic['NC_proc'] = -factor

  with open(os.path.join(directory, procDir, 'procs'), 'w') as f:
      for k in sorted(dic.keys()):
          f.write('##${}= {}\n'.format(k, dic[k]))

  with open(os.path.join(directory, procDir, realFileName), 'wb') as f:
      f.write(data.astype('<i4').tobytes())
#
# def stdEfficency(self, spectrumOffResonance, spectrumOnResonance, stdDifferenceSpectrum):
#
#   for peak in spectrumOffResonance:

