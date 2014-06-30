from ccpncore.util.Path import checkFilePath
from ccpncore.lib.spectrum.formats import Azara, Bruker, Felix, NmrPipe, NmrView, Ucsf, Varian, Xeasy
from ccpncore.lib.spectrum.Util import AZARA, BRUKER, CCPN, FELIX, NMRPIPE, NMRVIEW, UCSF, VARIAN, XEASY
import os
from ccpncore.lib.spectrum.Util import getSpectrumFileFormat
from ccpncore.lib.Spectrum import createExperiment, createDataSource, createBlockedMatrix

from ccpncore.api.memops.Implementation import MemopsRoot
from ccpncore.api.memops.Implementation import Url
from ccpn import _Spectrum as Spectrum

def loadDataSource(project, filePath, reReadSpectrum=None):

  isOk, msg = checkFilePath(filePath)

  if not isOk:
    # showError('Error', msg)
    return

  numPoints = None

  paramModules = {AZARA:Azara, BRUKER:Bruker, FELIX:Felix,
                  NMRPIPE:NmrPipe, NMRVIEW:NmrView, UCSF:Ucsf,
                  VARIAN:Varian, XEASY:Xeasy}

  dataFileFormat = getSpectrumFileFormat(filePath)

  if dataFileFormat is None:
    msg = 'Spectrum data format could not be determined for %s'
    # showError('Error', msg % filePath)
    return

  if dataFileFormat == CCPN:
    return project.getSpectrum(filePath)

  formatData = paramModules[dataFileFormat].readParams(filePath)

  if formatData is None:
    msg = 'Spectrum load failed for %s'
    # showError('Error', msg % filePath)
    return

  else:
    specFile, numPoints, blockSizes, wordSize, isBigEndian, \
    isFloatData, headerSize, blockHeaderSize, isotopes, specFreqs, specWidths, \
    refPoints, refPpms, sampledValues, sampledErrors, pulseProgram, dataScale = formatData

  print(formatData)
  if not os.path.exists(specFile):
    msg = 'Spectrum data file %s not found'
    # showError('Error', msg % specFile)
    return

  dirName, fileName = os.path.split(specFile)
  name, fex = os.path.splitext(fileName)

  if (dataFileFormat == BRUKER) and name in ('1r','2rr','3rrr','4rrrr'):
    rest, lower = os.path.split(dirName)
    rest, mid = os.path.split(rest)

    if mid == 'pdata':
      rest, upper = os.path.split(rest)
      name = '%s:%s' % (upper, lower)

  if numPoints:

    if reReadSpectrum:
      spectrum = reReadSpectrum
    else:


      nmrProject = project._wrappedData
      print(len(numPoints))
      newExperiment = createExperiment(nmrProject, name=name, numDim=len(numPoints),
                                       sf = specFreqs, isotopeCodes=isotopes)

      dataLocationStore = project._wrappedData.root.newDataLocationStore(name=name)
      dataUrl = dataLocationStore.newDataUrl(url=Url(path=specFile))
      blockMatrix = createBlockedMatrix(dataUrl, name, numPoints=numPoints,
                                        blockSizes=blockSizes,isBigEndian=isBigEndian)
      newDataSource = createDataSource(newExperiment,name=name, numPoints=numPoints,
                                       sw=specWidths, refppm=refPpms,
                                       refpt=refPoints,dataStore=blockMatrix)



      # spectrum = Spectrum.newSpectrum(name, specFile, numPoints, blockSizes, wordSize,
      #                     isBigEndian, isFloatData, 'rb', headerSize,
      #                     blockHeaderSize, filePath, dataFileFormat,
      #                     dataScale=dataScale)

    for i, values in enumerate(sampledValues):
      if values:
        newDataSource.setSampledData(i, values, sampledErrors[i] or None)

    # newDataSource.setReferencing(isotopes, specFreqs, specWidths,
    #                         refPoints, refPpms)

    return newDataSource