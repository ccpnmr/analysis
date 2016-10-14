__author__ = 'luca'


import numpy as np
# import pandas as pd

from collections import namedtuple
# from math import sin, cos, pi, log
import os
import decimal

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


def matchedPosition(samplePeaks, componentPeaks, tolerance:float=0.005, minimumMatches:int=1):
  '''
  Matches peak positions from the sample spectrum to a given reference component.

  '''

  matchedPositions = [samplePosition for componentPosition in componentPeaks
                      for samplePosition in samplePeaks if abs(samplePosition - componentPosition) <= tolerance]
  if len(matchedPositions)>=minimumMatches:
   return set(list(matchedPositions))

def _subtractTwoSpectra(stdOffResonance, stdOnResonance):
  stdOffResonanceArray = stdOffResonance._apiDataSource.get1dSpectrumData()[1]
  stdOnResonanceArray = stdOnResonance._apiDataSource.get1dSpectrumData()[1]

  stdDifference = stdOffResonanceArray - stdOnResonanceArray
  return stdDifference

def getPeakPositions(spectrum):
  if len(spectrum.peakLists)>0:
    return [peak.position[0] for peak in spectrum.peakLists[0].peaks]
  else:
    print('No peakList found')

def getSampleSpectraByExpType(sample, expType):
  spectra = []
  for spectrum in sample.spectra:
    if spectrum.experimentType == str(expType):
      spectra.append(spectrum)
  return spectra



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


def matchSTDToReference(project, minDistance):
  for sample in project.samples:
    if not sample.isVirtual:
      componentList = []

      spectrumOffResonance = [spectrum for spectrum in sample.spectra if spectrum.comment == 'spectrum_Off_Res']
      spectrumOffResonancePeaks = [peak for peak in spectrumOffResonance[0].peakLists[0].peaks]

      spectrumOnResonance = [spectrum for spectrum in sample.spectra if spectrum.comment == 'spectrum_On_Res']
      spectrumOnResonancePeaks = [peak for peak in spectrumOnResonance[0].peakLists[0].peaks]

      stdSpectrum = [spectrum for spectrum in sample.spectra if spectrum.comment == 'spectrum_STD']
      stdPeakList = [peak for peak in stdSpectrum[0].peakLists[0].peaks]
      stdPosition = [peak.position[0] for peak in stdPeakList]

      for sampleComponent in sample.sampleComponents:
        componentPeakList = [peak for peak in sampleComponent.substance.referenceSpectra[0].peakLists[0].peaks]
        componentPosition = [peak.position[0] for peak in componentPeakList]
        componentDict = {sampleComponent: componentPosition}
        componentList.append(componentDict)
        newPeakList = sampleComponent.substance.referenceSpectra[0].newPeakList()

      for components in componentList:
        for sampleComponent, peakPositions in components.items():
          match = matchedPosition(stdPosition, peakPositions, tolerance=float(minDistance),
                                  minimumMatches=1)  # self.minimumPeaksBox.value())
          if match is not None:
            newHit = sample.spectra[0].newSpectrumHit(substanceName=str(sampleComponent.name))
            for position in match:
              newPeakListPosition = sampleComponent.substance.referenceSpectra[0].peakLists[1].newPeak(
                position=[position], height=0.00)

            merit = _stdEfficency(spectrumOffResonancePeaks, spectrumOnResonancePeaks, stdPosition, minDistance)
            if len(merit) > 0:
              newHit.meritCode = str(merit[0]) + '%'


def _loadSpectrumDifference(project, path, sample, SGname='SG:STD'):
  newSpectrumStd = project.loadData(path)
  newSpectrumStd[0].comment = 'spectrum_STD'
  newSpectrumStd[0].scale = float(0.1)
  spectrumName = str(newSpectrumStd[0].name)

  sample.spectra += (newSpectrumStd[0],)
  print(sample.spectra)
  spectrumGroupSTD = project.getByPid(SGname)
  spectrumGroupSTD.spectra += (newSpectrumStd[0],)
  print(newSpectrumStd[0].id, 'created and loaded in the project')

def createStdDifferenceSpectrum(project, filePath):
  for sample in project.samples:
    if not sample.isVirtual:
      if len(sample.spectra) > 0:
        # FIXME correct spectrum.comment when new exp type STD off on are ready in the api
        spectrumOffResonance = [spectrum for spectrum in sample.spectra if spectrum.comment == 'spectrum_Off_Res']
        spectrumOnResonance = [spectrum for spectrum in sample.spectra if spectrum.comment == 'spectrum_On_Res']

        spectrumDiff = _subtractTwoSpectra(spectrumOffResonance[0], spectrumOnResonance[0])
        if filePath.endswith("/"):
          path = filePath + sample.name + '_Std'
        else:
          path = filePath + '/' + sample.name + '_Std_diff'
        writeBruker(path, spectrumDiff)
        _loadSpectrumDifference(project, str(path) + '/pdata/1/1r', sample)


def _stdEfficency(spectrumOffResonancePeaks, spectrumOnResonancePeaks, matchedPositions, minDistance):

  efficiency = []
  for position in matchedPositions:
    for onResPeak in spectrumOnResonancePeaks:
      for offResPeak in spectrumOffResonancePeaks:



        if abs(offResPeak.position[0] - onResPeak.position[0]) <= float(minDistance) and offResPeak.position[0] == position:
          differenceHeight = abs(offResPeak.height - onResPeak.height)
          fullValue = ((abs(offResPeak.height - onResPeak.height)) / offResPeak.height) * 100
          value = decimal.Decimal(fullValue).quantize(decimal.Decimal('.01'), rounding=decimal.ROUND_DOWN)
          efficiency.append(value)

  return efficiency
