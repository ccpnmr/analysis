from ccpncore.util.Path import checkFilePath
from ccpncore.lib.spectrum.formats import Azara, Bruker, Felix, NmrPipe, NmrView, Ucsf, Varian, Xeasy
from ccpncore.lib.spectrum.Util import AZARA, BRUKER, CCPN, FELIX, NMRPIPE, NMRVIEW, UCSF, VARIAN, XEASY
import os
from ccpncore.lib.spectrum.Util import getSpectrumFileFormat
from ccpncore.lib.Spectrum import createExperiment, createDataSource, createBlockedMatrix

from ccpncore.api.memops.Implementation import Url

def loadDataSource(wrapperProject, filePath, reReadSpectrum=None):

  if reReadSpectrum is not None:
    # NBNB TBD Rasmus - this is clearly not working yet
    raise NotImplementedError("reReadSpectrum parameter not implemented yet")

  isOk, msg = checkFilePath(filePath)

  if not isOk:
    print(msg)
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
  #
  # if dataFileFormat == CCPN:
  #   return project.getSpectrum(filePath)

  formatData = paramModules[dataFileFormat].readParams(filePath)

  if formatData is None:
    msg = 'Spectrum load failed for %s'
    print(msg)
    # showError('Error', msg % filePath)
    return

  else:
    specFile, numPoints, blockSizes, wordSize, isBigEndian, \
    isFloatData, headerSize, blockHeaderSize, isotopes, specFreqs, specWidths, \
    refPoints, refPpms, sampledValues, sampledErrors, pulseProgram, dataScale = formatData

  if not os.path.exists(specFile):
    msg = 'Spectrum data file %s not found'
    print(msg)
    # showError('Error', msg % specFile)
    return

  dirName, fileName = os.path.split(specFile)
  name, fex = os.path.splitext(fileName)

  if (dataFileFormat == BRUKER) and name in ('1r','2rr','3rrr','4rrrr'):
    rest, lower = os.path.split(dirName)
    rest, mid = os.path.split(rest)

    if mid == 'pdata':
      rest, upper = os.path.split(rest)
      name = '%s-%s' % (upper, lower)

  if ':' in name:
    # Fix name to fit PID requirements. NBNB temporary fix
    name = name.replace(':','-')
  if '.' in name:
    # Fix name to fit PID requirements. NBNB temporary fix
    name = name.replace('.',',')

  if numPoints:

    if reReadSpectrum:
      spectrum = reReadSpectrum
      # NBNB TBD BROKEN - spectrum is overwritten lower down
    else:


      nmrProject = wrapperProject.nmrProject
      newExperiment = createExperiment(nmrProject, name=name, numDim=len(numPoints),
                                       sf = specFreqs, isotopeCodes=isotopes)

      dataLocationStore = nmrProject.root.newDataLocationStore(name=name)
      dataUrl = dataLocationStore.newDataUrl(url=Url(path=os.path.dirname(filePath)))
      blockMatrix = createBlockedMatrix(dataUrl, specFile, numPoints=numPoints,
                                        blockSizes=blockSizes,isBigEndian=isBigEndian)
      newDataSource = createDataSource(newExperiment,name=name,numPoints=numPoints,sw=specWidths,
                                       refppm=refPpms,refpt=refPoints,dataStore=blockMatrix)




    for i, values in enumerate(sampledValues):
      if values:
        newDataSource.setSampledData(i, values, sampledErrors[i] or None)

    # NBNB TBD BROKEN - newDataSource is not always set.
    spectrum = wrapperProject._data2Obj[newDataSource]

    return spectrum