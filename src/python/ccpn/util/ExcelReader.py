#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from collections import Counter
import os
import csv
from collections import OrderedDict
import pathlib
import pandas as pd
from ccpn.util.Logging import getLogger , _debug3
######################### Excel Headers ##################
"""The excel headers for sample, sampleComponents, substances properties are named as the appear on the wrapper.
Changing these will fail to set the attribute"""

# SHEET NAMES
SUBSTANCES = 'Substances'
SAMPLES = 'Samples'
NOTGIVEN = 'Not Given'

# '''REFERENCES PAGE'''
SPECTRUM_GROUP_NAME = 'spectrumGroupName'
EXP_TYPE = 'expType'
SPECTRUM_PATH = 'spectrumPath'
SUBSTANCE_NAME = 'substanceName'
### Substance properties: # do not change these names
comment  = 'comment'
smiles = 'smiles'
synonyms = 'synonyms'
stereoInfo = 'stereoInfo'
molecularMass = 'molecularMass'
empiricalFormula = 'empiricalFormula'
atomCount = 'atomCount'
hBondAcceptorCount = 'hBondAcceptorCount'
hBondDonorCount = 'hBondDonorCount'
bondCount = 'bondCount'
ringCount = 'ringCount'
polarSurfaceArea = 'polarSurfaceArea'
logPartitionCoefficient = 'logPartitionCoefficient'
userCode = 'userCode'
sequenceString = 'sequenceString'
casNumber = 'casNumber'

# '''SAMPLES PAGE'''
SAMPLE_NAME = 'sampleName'
SPECTRUM_1H = 'spectrum_1H'

### other sample properties # do not change these names
SAMPLE_COMPONENTS = 'referenceComponents'
pH = 'pH'
ionicStrength = 'ionicStrength'
amount = 'amount'
amountUnit = 'amountUnit'
isHazardous = 'isHazardous'
creationDate = 'creationDate'
batchIdentifier = 'batchIdentifier'
plateIdentifier = 'plateIdentifier'
rowNumber = 'rowNumber'
columnNumber = 'columnNumber'

SpectrumType = 'spectrumType'
BRUKER = 'Bruker'



SAMPLE_PROPERTIES =     [comment, pH, ionicStrength,  amount , amountUnit,isHazardous,creationDate, batchIdentifier,
                         plateIdentifier,rowNumber,columnNumber]

SUBSTANCE_PROPERTIES =  [comment,smiles,synonyms,stereoInfo,molecularMass,empiricalFormula,atomCount,
                         hBondAcceptorCount,hBondDonorCount, bondCount,ringCount,polarSurfaceArea,
                         logPartitionCoefficient,userCode,]


def _groupper(lst):
  '''Groups the same values in lists . Returns a new list with one item of each sublist '''
  counteredGroups = Counter(lst)
  sortedGroups = [[k, ] * v for k, v in counteredGroups.items()]
  return [i for j in sortedGroups for i in list(set(j))]


class ExcelReader(object):
  def __init__(self, project, excelPath):
    """
    :param project: the ccpnmr Project object
    :param excelPath: excel file path

    This reader will process excel files containing one or more sheets.
    The file needs to contain  either the word Substances or Samples in the sheets name.

    The user can load a file only with Substances or Samples sheet or both. Or a file with enumerate sheets
    called eg Samples_Exp_1000, Samples_Exp_1001 etc in which the sample information stays the same but changes only the
    spectra recorded with it. The spectra will be loaded in a new SpectrumGroup with the same name plus a suffix '@'.

    The project will create new Substances and/or Samples only once for a given name.
     Therefore, dropping twice the same file, or giving two sheets with same sample name will fail to create new objects.
     However  if  the user wants to drop a file with only spectra changed and preserve the sample information, He can drop
     the file with same sample names and the spectra will be loaded in a different SpectrumGroup Name.


    Reader Steps:

    - Parse the sheet/s and return a dataframe for each sheet containing at least the str name Substances or Samples
    - Create Substances and/or samples if not existing in the project else skip with warning
    - Create SpectrumGroups if not existing in the project else add a suffix 
    - Load spectra on project
    - dispatch spectra to appropriate 'parent' (e.g. referenceSubstance, Sample.spectra, SG.spectra)
    - set all attributes for each object as in the wrapper


    """

    self._project = project
    self.excelPath = excelPath
    self.pandasFile = pd.ExcelFile(self.excelPath)
    self.sheets = self._getSheets(self.pandasFile)
    self.dataframes = self._getDataFrameFromSheets(self.sheets)
    self.substances = self._createSubstances(self.dataframes)
    self.samples = self._createSamples(self.dataframes)
    self.spectrumGroups = self._createSpectrumGroups(self.dataframes)
    self.spectra = self._loadSpectraOnProject(self.dataframes)

    # self._createDataFrames()
    #
    #
    # self.directoryPath = self._getWorkingDirectoryPath()


    # self.brukerDirs = self._getBrukerTopDirs()
    # if self.referencesDataFrame[SpectrumType].all() == BRUKER:
    #   self.fullFilePaths = self._getFullBrukerFilePaths()
    #   self.spectrumFormat = BRUKER
    # if self.referencesDataFrame[SpectrumType].all() == HDF5:
    #   self.fullFilePaths = self._getFullHDF5FilePaths()
    #   self.spectrumFormat = HDF5
    #
    # self._loadReferenceSpectrumToProject()
    # self._createReferencesDataDicts()
    # self._initialiseParsingSamples()

  ######################################################################################################################
  ######################                  PARSE EXCEL                     ##############################################
  ######################################################################################################################

  def _getSheets(self, pandasfile):
    '''return: list of the sheet names'''
    return  pandasfile.sheet_names

  def _getDataFrameFromSheet(self, sheetName):
    'Creates the dataframe for the sheet. If Values are not set, fills None with NOTGIVEN (otherwise can give errors)'
    dataFrame = self.pandasFile.parse(sheetName)
    dataFrame.fillna(NOTGIVEN, inplace=True)
    return dataFrame

  def _getDataFrameFromSheets(self, sheetNamesList):
    '''Reads sheets containing the names SUBSTANCES or SAMPLES and creates a dataFrame for each'''

    dataFrames = []
    for sheetName in [name for name in sheetNamesList if SUBSTANCES in name]:
      dataFrames.append(self._getDataFrameFromSheet(sheetName))
    for sheetName in [name for name in sheetNamesList if SAMPLES in name]:
      dataFrames.append(self._getDataFrameFromSheet(sheetName))
    return dataFrames



  ######################################################################################################################
  ######################                  CREATE SUBSTANCES               ##############################################
  ######################################################################################################################

  def _createSubstances(self, dataframesList):
    '''Creates substances in the project if not already present'''
    substances = []
    for dataFrame in dataframesList:
      if SUBSTANCE_NAME in dataFrame.columns:
        for name in dataFrame[SUBSTANCE_NAME]:
          if self._project is not None:
            if not self._project.getByPid('SU:'+name+'.'):
              substance = self._project.newSubstance(name=name)
              substances.append(substance)
            else:
              getLogger().warning('Impossible to create substance %s. A substance with the same name already '
                                  'exsists in the project. ' % name)

    return substances



  ######################################################################################################################
  ######################                  CREATE SAMPLES                  ##############################################
  ######################################################################################################################

  def _createSamples(self, dataframesList):
    '''Creates samples in the project if not already present'''
    samples = []
    for dataFrame in dataframesList:
      if SAMPLE_NAME in dataFrame.columns:

        filteredSamplesNames = _groupper(dataFrame[SAMPLE_NAME])

        for name in filteredSamplesNames:
          if self._project is not None:
            if not self._project.getByPid('SA:'+name):
              sample = self._project.newSample(name=name)
              samples.append(sample)
            else:
              getLogger().warning('Impossible to create sample %s. A sample with the same name already '
                                  'exsists in the project. ' % name)

    return samples


  ######################################################################################################################
  ######################            CREATE SPECTRUM GROUPS                ##############################################
  ######################################################################################################################



  def _createSpectrumGroups(self, dataframesList):
    '''Creates SpectrumGroup in the project if not already present. Otherwise finds another name a creates new one.
    dropping the same file over and over will create new spectrum groups each time'''
    spectrumGroups = []
    for dataFrame in dataframesList:
      if SPECTRUM_GROUP_NAME in dataFrame.columns:
        filteredSGNames = _groupper(dataFrame[SPECTRUM_GROUP_NAME])
        for groupName in filteredSGNames:
          name = self._checkDuplicatedSpectrumGroupName(groupName)
          newSG =  self._createNewSpectrumGroup(name)
          spectrumGroups.append(newSG)
    return spectrumGroups


  def _checkDuplicatedSpectrumGroupName(self, name):
    'Checks in the preject if a spectrumGroup name exists already and returns a new available name '
    if self._project:
      for sg in self._project.spectrumGroups:
        if sg.name == name:
          name += '@'
      return name

  def _createNewSpectrumGroup(self, name):
    if self._project:
      if not self._project.getByPid('SG:' + name):
        return self._project.newSpectrumGroup(name=str(name))
      else:
        name = self._checkDuplicatedSpectrumGroupName(name)
        self._createNewSpectrumGroup(name)


  ######################################################################################################################
  ######################            LOAD SPECTRA ON PROJECT              ##############################################
  ######################################################################################################################


  def _loadSpectraOnProject(self, dataframesList):
    '''
    If only the file name is given:
    - All paths are relative to the excel file! So the spectrum file of bruker top directory must be in the same directory
    of the excel file.
    If the full path is given, from the root to the spectrum file name, then tries to use that.
    '''

    for dataFrame in dataframesList:
      if SPECTRUM_PATH in dataFrame.columns:
        for filePath in dataFrame[SPECTRUM_PATH]:
          if os.path.exists(filePath):
            spectrum = self._project.loadData(filePath)



    self.directoryPath = self._getWorkingDirectoryPath()


  def _getWorkingDirectoryPath(self):
    xlsLookupPath = pathlib.Path(self.excelPath)
    return str(xlsLookupPath.parent)

  def _getBrukerTopDirs(self):
    dirs = os.listdir(str(self.directoryPath))
    excludedFiles = ('.DS_Store', '.xls')
    brukerDirs = [dir for dir in dirs if not dir.endswith(excludedFiles)]
    return brukerDirs

  def _getFullHDF5FilePaths(self):
    paths = []
    for spectrumName in self.referencesDataFrame[SPECTRUM_NAME]:
      path = self.directoryPath + '/' + str(spectrumName)+'.hdf5'
      paths.append(str(path))
    print(paths)
    return paths

  def _getFullBrukerFilePaths(self):
    fullPaths = []
    for spectrumName in self.brukerDirs:
      path = self.directoryPath + '/' + spectrumName
      for dirname, dirnames, filenames in os.walk(path):
        for filename in filenames:
          if filename == '1r':
            fullPath = os.path.join(dirname, filename)
            fullPaths.append(fullPath)
    return fullPaths

  def _loadReferenceSpectrumToProject(self):

    for spectrumName in self.referencesDataFrame[SPECTRUM_NAME]:
      for path in self.fullFilePaths:
        for item in path.split('/'):
          if str(item).endswith('.hdf5'):
            item = item.split('.')[0]
          if item == spectrumName:
            data = self._project.loadData(path)
            if data is not None:
              if len(data)>0:
                spectrum = data[0]


  def _createReferencesDataDicts(self):
    spectrum = None
    for data in self.referencesDataFrame.to_dict(orient="index").values():
      for key, value in data.items():
        if key == SPECTRUM_NAME:
          if self.spectrumFormat == BRUKER:
            spectrum = self._project.getByPid('SP:'+str(value)+'-1')
          else:
            spectrum = self._project.getByPid('SP:'+str(value))
          if spectrum is not None:
            dataDict = {spectrum: data}
            self._dispatchSpectrumToProjectGroups(dataDict)
            self._createNewSubstance(dataDict)


  def _initialiseParsingSamples(self):
    self._createSamplesDataDicts()
    for samplesDataDict in self.samplesDataDicts:
      self._getSampleSpectra(samplesDataDict)


  def _createSamplesDataDicts(self):
    self.samplesDataDicts = []
    for data in self.samplesDataFrame.to_dict(orient="index").values():
      for key, value in data.items():
        if key == SAMPLE_NAME:
          sample = self._project.newSample(str(value))
          dataDict = {sample: data}
          self._setWrapperProperties(sample, SAMPLE_PROPERTIES, data)
          self._addSampleComponents(sample, data)
          self.samplesDataDicts.append(dataDict)

  def _addSampleComponents(self, sample, data):
    sampleComponents = [[header, sampleComponentName] for header, sampleComponentName in data.items() if
                        header == SAMPLE_COMPONENTS]
    for name in sampleComponents[0][1].split(','):
      sampleComponent = sample.newSampleComponent(name=(str(name) + '-1'))
      sampleComponent.role = 'Compound'


  def _getSampleSpectra(self, samplesDataDict):
    for sample, data in samplesDataDict.items():
      for spectrumNameHeader, experimentType in EXP_TYPES.items():
        spectrum = self._getSpectrum(data, spectrumNameHeader)
        if spectrum:
          if spectrumNameHeader == SPECTRUM_OFF_RESONANCE:
            spectrum.comment = SPECTRUM_OFF_RESONANCE
          if spectrumNameHeader == SPECTRUM_ON_RESONANCE:
            spectrum.comment = SPECTRUM_ON_RESONANCE
          spectrum.experimentType = experimentType
          sample.spectra += (spectrum, )


  def _getSpectrum(self, data, header):
      spectrumName = [[excelHeader, value] for excelHeader, value in data.items()
                                  if excelHeader == header and value != NOTGIVEN]
      if len(spectrumName)>0:
        brukerDir = [str(spectrumName[0][1])]
        path = self._getFullBrukerFilePaths()
        spectrum = self._project.loadData(path[0])
        return spectrum[0]





  def _addSpectrumToSpectrumGroup(self, spectrumGroup, spectrum):
    spectrumGroup.spectra += (spectrum,)

  def _dispatchSpectrumToProjectGroups(self, dataDict):
    for spectrum, data in dataDict.items():
      spectrumGroupName = data[GROUP_NAME]
      spectrumGroup = self._project.getByPid('SG:'+spectrumGroupName)
      if spectrumGroup is not None:
        self._addSpectrumToSpectrumGroup(spectrumGroup, spectrum)

  def _createNewSubstance(self, dataDict):
    for spectrum, data in dataDict.items():
      substance = self._project.newSubstance(name=spectrum.id)
      substance.referenceSpectra = [spectrum]
      self._setWrapperProperties(substance, SUBSTANCE_PROPERTIES, data)

  def _setWrapperProperties(self, wrapperObject, properties, dataframe):
    for property in properties:
      if property == 'synonyms':
        setattr(wrapperObject, property, (self._getDFValue(property, dataframe),))
      else:
        try:
          setattr(wrapperObject, property, self._getDFValue(property, dataframe))
        except Exception as e:
          _debug3(getLogger(), msg=(e, property))


  def _getDFValue(self, header, data):
    value = [[excelHeader, value] for excelHeader, value in data.items()
                     if excelHeader == str(header) and value != NOTGIVEN]
    if len(value) > 0:
      return value[0][1]


if False:
  ExcelReader(project=None, excelPath='/Users/luca/AnalysisV3/data/testProjects/AnalysisScreen_Demo1/demoDataset_Lookup/Lookup_Demo.xls')