"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================
import os

from ccpncore.util import Common as commonUtil
from ccpncore.util.typing import Sequence
from ccpncore.lib import Constants
from ccpncore.lib.spectrum import Spectrum as spectrumLib
# from ccpncore.lib.spectrum.Spectrum import createBlockedMatrix
from ccpncore.lib.spectrum.formats import Azara, Bruker, Felix, NmrPipe, NmrView, Ucsf, Varian, Xeasy
from ccpncore.lib.Io.Formats import AZARA, BRUKER, FELIX, NMRPIPE, NMRVIEW, UCSF, VARIAN, XEASY
from ccpncore.util.Path import checkFilePath

from ccpncore.api.memops.Implementation import Url

# Default parameters - 10Hz/pt, 0.1ppm/point for 1H; 10 Hz/pt, 1ppm/pt for 13C
# NB this is in order to give simple numbers. it does NOT match the gyromagnetic ratios
DEFAULT_SPECTRUM_PARAMETERS = {
  '1H':{'numPoints':128, 'sf':100., 'sw':1280, 'refppm':11.8, 'refpt':0, },
  '13C':{'numPoints':256, 'sf':10., 'sw':2560, 'refppm':236., 'refpt':0, }
}
for tag,val in Constants.DEFAULT_ISOTOPE_DICT.items():
  # Without additional info, set other one-letter isotopes (including 15N) to match carbon 13
  if len(tag) == 1 and val and val not in DEFAULT_SPECTRUM_PARAMETERS:
    DEFAULT_SPECTRUM_PARAMETERS[val] = DEFAULT_SPECTRUM_PARAMETERS['13C']

def loadDataSource(self:'NmrProject', filePath, dataFileFormat):

  isOk, msg = checkFilePath(filePath)

  if not isOk:
    print(msg)
    # showError('Error', msg)
    return

  numPoints = None

  paramModules = {AZARA:Azara, BRUKER:Bruker, FELIX:Felix,
                  NMRPIPE:NmrPipe, NMRVIEW:NmrView, UCSF:Ucsf,
                  VARIAN:Varian, XEASY:Xeasy}

  # dataFileFormat = getSpectrumFileFormat(filePath)
  if dataFileFormat is None:
    msg = 'Spectrum data format could not be determined for %s' % filePath
    print(msg)
    return None
  #
  # if dataFileFormat == CCPN:
  #   return project.getSpectrum(filePath)

  formatData = paramModules[dataFileFormat].readParams(filePath)

  if formatData is None:
    msg = 'Spectrum load failed for "%s": could not read params' % filePath
    print(msg)
    return None

  else:
    fileType, specFile, numPoints, blockSizes, wordSize, isBigEndian, \
    isFloatData, headerSize, blockHeaderSize, isotopes, specFreqs, specWidths, \
    refPoints, refPpms, sampledValues, sampledErrors, pulseProgram, dataScale = formatData

  if not os.path.exists(specFile):
    msg = 'Spectrum data file %s not found' % specFile
    print(msg)
    return None

  # NBNB TBD REDO!
  # This way of setting DataLocationStores and DataUrls is HOPELESS, STUPID KLUDGE!!
  # If we want each file to have an individual name with no support for grouping
  # them, let us for Gods sake remove the fancy stuff from the model.
  # Or at least refrain from creating individual DataLocationStores
  # when you only ever need one!
  # Rasmus Fogh

  dirName, fileName = os.path.split(specFile)
  name, fex = os.path.splitext(fileName)

  if (dataFileFormat == BRUKER) and name in ('1r','2rr','3rrr','4rrrr'):
    rest, lower = os.path.split(dirName)
    rest, mid = os.path.split(rest)

    if mid == 'pdata':
      rest, upper = os.path.split(rest)
      name = '%s-%s' % (upper, lower)

  while any(x.findFirstDataSource(name=name) for x in self.experiments):
    name = commonUtil.incrementName(name)

  numberType = 'float' if isFloatData else 'int'
  experiment = self.createExperiment(name=name, numDim=len(numPoints),
                                sf=specFreqs, isotopeCodes=isotopes)


  dataLocationStore = self.root.newDataLocationStore(name=name)
  dataUrl = dataLocationStore.newDataUrl(url=Url(path=os.path.dirname(filePath)))
  # NBNB TBD - this is WRONG
  # the dataUrl should be made from dirName, NOT to the filePath directory.
  blockMatrix = spectrumLib.createBlockedMatrix(dataUrl, specFile, numPoints=numPoints,
                                                blockSizes=blockSizes, isBigEndian=isBigEndian,
                                                numberType=numberType, headerSize=headerSize,
                                                nByte=wordSize, fileType=fileType)
  dataSource = experiment.createDataSource(name=name, numPoints=numPoints, sw=specWidths,
                                refppm=refPpms, refpt=refPoints, dataStore=blockMatrix)

  for i, values in enumerate(sampledValues):
    if values:
      dataSource.setSampledData(i, values, sampledErrors[i] or None)

  experiment.resetAxisCodes()

  return dataSource


def createDummySpectrum(self:'NmrProject', axisCodes:Sequence[str],
                      name=None) -> 'DataSource':
  """Make Experiment and DataSource with no data from list of standard atom axisCodes"""

  # Set up parameters and make Experiment
  numDim = len(axisCodes)
  isotopeCodes = tuple(spectrumLib.name2IsotopeCode(x) for x in axisCodes)
  if name is None:
    expName = ''.join(x for x in ''.join(axisCodes) if not x.isdigit())
  else:
    expName = name
  experiment = self.createExperiment(name=expName, numDim=numDim,
                                           sf=[DEFAULT_SPECTRUM_PARAMETERS[x]['sf']
                                               for x in isotopeCodes], axisCodes=axisCodes,
                                           isotopeCodes=isotopeCodes)
  # Make dataSource with default parameters
  params = dict((tag,[DEFAULT_SPECTRUM_PARAMETERS[x][tag] for x in isotopeCodes])
                for tag in ('sw', 'refppm', 'refpt', 'numPoints'))
  #
  specName = '%s@%s' %(expName, experiment.serial) if name is None else name
  return experiment.createDataSource(name=specName, **params)

def createExperiment(self:'NmrProject', name:str, numDim:int, sf:Sequence,
                     isotopeCodes:Sequence, isAcquisition:Sequence=None, axisCodes=None,
                     **additionalParameters) -> 'Experiment':
  """Create Experiment object ExpDim, and one ExpDimRef per ExpDim.
  Additional parameters to Experiment object are passed in additionalParameters"""

  experiment = self.newExperiment(name=name, numDim=numDim, **additionalParameters)

  if isAcquisition is None:
    isAcquisition = (False,) * numDim

  if experiment.shiftList is None:
    # Set shiftList, creating it if necessary
    shiftLists = [x for x in self.sortedMeasurementLists() if x.className == 'ShiftList']
    if len(shiftLists) == 1:
      shiftList = shiftLists[0]
    else:
      shiftList = (self.findFirstMeasurementList(className='ShiftList', name='default') or
                   self.newShiftList(name='default'))
    experiment.shiftList = shiftList

  for n, expDim in enumerate(experiment.sortedExpDims()):
    expDim.isAcquisition = isAcquisition[n]
    ic = isotopeCodes[n]
    if ic:
      params = {'sf':sf[n], 'unit':'ppm'}
      params['isotopeCodes'] = (ic,) if isinstance(ic, str) else ic
      if axisCodes:
        ac = axisCodes[n]
        if ac is not None:
          params['axisCode'] = ac
      expDim.newExpDimRef(**params)

  return experiment