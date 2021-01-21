#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2021-01-21 13:59:26 +0000 (Thu, January 21, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from multiprocessing.pool import ThreadPool as Pool
import os
from os.path import isfile, join
import pathlib
import pandas as pd
import time
from ccpn.util.Logging import getLogger
from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats
from tqdm import tqdm, tqdm_gui
from ccpn.util.Common import sortObjectByName, naturalSortList

################################       Excel Headers Warning      ######################################################
"""The excel headers for sample, sampleComponents, substances properties are named as the appear on the wrapper.
Changing these will fail to set the attribute"""

# SHEET NAMES
SUBSTANCE = 'Substance'
SAMPLE = 'Sample'
NOTGIVEN = 'Not Given'

# """REFERENCES PAGE"""
SPECTRUM_GROUP_NAME = 'spectrumGroupName'
EXP_TYPE = 'experimentType'
SPECTRUM_PATH = 'spectrumPath'
SUBSTANCE_NAME = 'substanceName'
# added from beta6
SPECTRUM_NAME = 'spectrumName'
SPECTRUMGROUP = 'SpectrumGroup'
SERIES = 'series'

### Substance properties: # do not change these names
comment = 'comment'
smiles = 'smiles'
synonyms = 'synonyms'
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

# """SAMPLES PAGE"""
SAMPLE_NAME = 'sampleName'

### other sample properties # do not change these names
SAMPLE_COMPONENTS = 'sampleComponents'
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

# shifts
ChemicalShift = 'ChemicalShift'
ChemicalShiftLabel = 'ChemicalShiftLabel'
ChemicalShiftAnnotation = 'ChemicalShiftAnnotation'
ChemicalShiftMerit = 'ChemicalShiftMerit'
ChemicalShiftComment = 'ChemicalShiftComment'
TimeStamp = 'TimeStamp_'
Valid = 'Valid'
Salt = 'Salt'
Other = 'Other'

SAMPLE_PROPERTIES = [comment, pH, ionicStrength, amount, amountUnit, isHazardous, creationDate, batchIdentifier,
                     plateIdentifier, rowNumber, columnNumber]

SUBSTANCE_PROPERTIES = [comment, smiles, synonyms, molecularMass, empiricalFormula, atomCount,
                        hBondAcceptorCount, hBondDonorCount, bondCount, ringCount, polarSurfaceArea,
                        logPartitionCoefficient, userCode, ]

SUBSTANCES_SHEET_COLUMNS = [SUBSTANCE_NAME, SPECTRUM_PATH, SPECTRUM_GROUP_NAME, EXP_TYPE] + SUBSTANCE_PROPERTIES
SAMPLE_SHEET_COLUMNS = [SAMPLE_NAME, SPECTRUM_GROUP_NAME, SPECTRUM_PATH, SPECTRUM_NAME]


def makeTemplate(path, fileName='lookupTemplate.xlsx', ):
    """
    :param path: path where to save the template
    :param fileName: name of template
    :return:  the file path where is saved
    """
    if path is not None:
        path = path + '/' if not path.endswith('/') else path
    file = path + fileName
    substanceDf = getDefaultSubstancesDF()
    sampleDF = getDefaultSampleDF()
    writer = pd.ExcelWriter(file, engine='xlsxwriter')
    substanceDf.to_excel(writer, sheet_name=SUBSTANCE)
    sampleDF.to_excel(writer, sheet_name=SAMPLE)
    writer.save()
    return writer


def getDefaultSubstancesDF():
    return pd.DataFrame(columns=SUBSTANCES_SHEET_COLUMNS)


def getDefaultSampleDF():
    return pd.DataFrame(columns=SAMPLE_SHEET_COLUMNS)


def _filterBrukerExperiments(brukerFilePaths, fileType='1r', multipleExp=False, expDirName='1', procDirName='1'):
    """

    :param brukerFilePaths:
    :param fileType:
    :param multipleExp: whether or not there are subdirectories after the spectrum top dir before the  acqu files and pdata dir (even one).
                        eg.a)  SpectumDir > pdata > 1 > 1r     ====  multipleExp=False
                        eg.b)  SpectumDir > 1 > pdata > 1 > 1r ====  multipleExp=True

    :param expDirName: if there are: str of folder name. e.g. '1','2'... '700'
                        eg)  SpectumDir > |1|   > pdata > 1 > 1r
                                        > |2|   > pdata > 1 > 1r
                                        > |700| > pdata > 1 > 1r
                            Default: 1
    :param procDirName: dir name straight
                         eg)  SpectumDir > 1  > pdata > |1| > 1r
                                                      > |2| > 1r
                        default: 1
    :return: list of filtered global path
    """
    filteredPaths = []
    for path in brukerFilePaths:
        if path.endswith(fileType):
            d = os.path.dirname(path)  ## directory of  1r file has to be as defaultProcsNumber
            if d.endswith(procDirName):
                if multipleExp:  # search for other expeiments and take only the one of interest.
                    pdata = os.path.dirname(d)
                    expP = os.path.dirname(pdata)
                    if expP.endswith(expDirName):
                        filteredPaths.append(path)
                else:
                    filteredPaths.append(path)
    return filteredPaths


class ExcelReader(object):

    # from ccpn.util.decorators import profile
    # @profile
    def __init__(self, project, excelPath):
        """
        :param project: the ccpnmr Project object
        :param excelPath: excel file path

        This reader will process excel files containing one or more sheets.
        The file needs to contain  either the word Substances or Samples in the sheets name.

        The user can load a file only with Substances or Samples sheet or both. Or a file with enumerate sheets
        called eg Samples_Exp_1000, Samples_Exp_1001 etc.

        The project will create new Substances and/or Samples and SpectrumGroups only once for a given name.
        Therefore, dropping twice the same file, or giving two sheets with same sample/substance/spectrumGroup name
        will fail to create new objects.



        Reader Steps:

        - Parse the sheet/s and return a dataframe for each sheet containing at least the str name Substances or Samples
        - Create Substances and/or samples if not existing in the project else skip with warning
        - For each row create a dict and link to the obj eg. {Substance: {its dataframe row as dict}
        - Create SpectrumGroups if not existing in the project else add a suffix
        - Load spectra on project and dispatch to the object. (e.g. SU.referenceSpectra, SA.spectra, SG.spectra)
        - set all attributes for each object as in the wrapper


        """
        from ccpn.core.lib.ContextManagers import undoBlock, undoBlockWithoutSideBar, notificationEchoBlocking

        self._project = project
        self.excelPath = excelPath
        self.pandasFile = pd.ExcelFile(self.excelPath)
        self.sheets = self._getSheets(self.pandasFile)
        self.dataframes = self._getDataFrameFromSheets(self.sheets)

        # self._project.blankNotification()
        # getLogger().info('Loading Excel File...')

        # with undoBlockWithoutSideBar():
        #     getLogger().info('Loading Excel File...')
        #     with notificationEchoBlocking():
        self._tempSpectrumGroupsSpectra = {}  # needed to improve the loading speed
        self.substancesDicts = self._createSubstancesDataFrames(self.dataframes)
        self.samplesDicts = self._createSamplesDataDicts(self.dataframes)
        self.spectrumGroups = self._createSpectrumGroups(self.dataframes)

        getLogger().info('Loading Substances metadata...')
        self._dispatchAttrsToObjs(self.substancesDicts)
        getLogger().info('Loading Substances Spectra...')
        self._loadSpectraForSheet(self.substancesDicts)
        getLogger().info('Loading Samples metadata...')
        self._dispatchAttrsToObjs(self.samplesDicts)
        getLogger().info('Loading Samples Spectra...')
        self._loadSpectraForSheet(self.samplesDicts)
        getLogger().info('Loading SpectrumGroups...')
        self._fillSpectrumGroups()
        getLogger().info('Loading from Excel completed...')

        # self._project.unblankNotification()

    ######################################################################################################################
    ######################                  PARSE EXCEL                     ##############################################
    ######################################################################################################################

    def _getSheets(self, pandasfile):
        """return: list of the sheet names"""
        return pandasfile.sheet_names

    def _getDataFrameFromSheet(self, sheetName):
        'Creates the dataframe for the sheet. If Values are not set, fills None with NOTGIVEN (otherwise can give errors)'
        dataFrame = self.pandasFile.parse(sheetName)
        dataFrame.fillna(NOTGIVEN, inplace=True)
        return dataFrame

    def _getDataFrameFromSheets(self, sheetNamesList):
        """Reads sheets containing the names SUBSTANCES or SAMPLES and creates a dataFrame for each"""

        dataFrames = []
        for sheetName in [name for name in sheetNamesList if SUBSTANCE in name]:
            dataFrames.append(self._getDataFrameFromSheet(sheetName))
        for sheetName in [name for name in sheetNamesList if SAMPLE in name]:
            dataFrames.append(self._getDataFrameFromSheet(sheetName))

        return dataFrames

    ######################################################################################################################
    ######################                  CREATE SUBSTANCES               ##############################################
    ######################################################################################################################

    def _createSubstancesDataFrames(self, dataframesList):
        """Creates substances in the project if not already present, For each substance link a dictionary of all its values
         from the dataframe row. """
        from ccpn.core.Substance import _newSubstance

        substancesDataFrames = []
        for dataFrame in dataframesList:
            for dataFrameAsDict in dataFrame.to_dict(orient="index").values():
                if SUBSTANCE_NAME in dataFrame.columns:
                    for key, value in dataFrameAsDict.items():
                        if key == SUBSTANCE_NAME:
                            if self._project is not None:
                                if not self._project.getByPid('SU:' + str(value) + '.'):
                                    substance = _newSubstance(self._project, name=str(value))
                                    substancesDataFrames.append({substance: dataFrameAsDict})
                                else:
                                    getLogger().warning('Impossible to create substance %s. A substance with the same name already '
                                                        'exsists in the project. ' % value)

        return substancesDataFrames

    ######################################################################################################################
    ######################                  CREATE SAMPLES                  ##############################################
    ######################################################################################################################

    def _createSamplesDataDicts(self, dataframesList):
        """Creates samples in the project if not already present, For each sample link a dictionary of all its values
         from the dataframe row. """
        samplesDataFrames = []
        ## first creates samples without duplicates,
        samples = self._createSamples(dataframesList)
        if len(samples) > 0:
            ## Second creates dataframes to dispatch the properties,
            for dataFrame in dataframesList:
                for dataFrameAsDict in dataFrame.to_dict(orient="index").values():
                    if SAMPLE_NAME in dataFrame.columns:
                        for key, value in dataFrameAsDict.items():
                            if key == SAMPLE_NAME:
                                if self._project is not None:
                                    sample = self._project.getByPid('SA:' + str(value))
                                    if sample is not None:
                                        samplesDataFrames.append({sample: dataFrameAsDict})

        return samplesDataFrames

    def _createSamples(self, dataframesList):
        from ccpn.core.Sample import _newSample

        samples = []
        for dataFrame in dataframesList:
            if SAMPLE_NAME in dataFrame.columns:
                saNames = list(set((dataFrame[SAMPLE_NAME])))
                saNames = naturalSortList(saNames, False)
                for name in saNames:
                    if not self._project.getByPid('SA:' + str(name)):
                        sample = _newSample(self._project, name=str(name))
                        samples.append(sample)

                    else:
                        getLogger().warning('Impossible to create sample %s. A sample with the same name already '
                                            'exsists in the project. ' % name)
        return samples

    ######################################################################################################################
    ######################            CREATE SPECTRUM GROUPS                ##############################################
    ######################################################################################################################

    def _createSpectrumGroups(self, dataframesList):
        """Creates SpectrumGroup in the project if not already present. Otherwise finds another name a creates new one.
        dropping the same file over and over will create new spectrum groups each time"""
        spectrumGroups = []
        for dataFrame in dataframesList:
            if SPECTRUM_GROUP_NAME in dataFrame.columns:
                for groupName in list(set((dataFrame[SPECTRUM_GROUP_NAME]))):
                    # name = self._checkDuplicatedSpectrumGroupName(groupName)
                    newSG = self._createNewSpectrumGroup(groupName)
                    self._tempSpectrumGroupsSpectra[groupName] = []
                    spectrumGroups.append(newSG)
        return spectrumGroups

    ##keep this code
    # def _checkDuplicatedSpectrumGroupName(self, name):
    #   'Checks in the preject if a spectrumGroup name exists already and returns a new available name '
    #   if self._project:
    #     for sg in self._project.spectrumGroups:
    #       if sg.name == name:
    #         name += '@'
    #     return name

    def _createNewSpectrumGroup(self, name):
        from ccpn.core.SpectrumGroup import _newSpectrumGroup

        if self._project:
            if not self._project.getByPid('SG:' + str(name)):
                return _newSpectrumGroup(self._project, name=str(name))
            else:
                getLogger().warning('Impossible to create the spectrumGroup %s. A spectrumGroup with the same name already '
                                    'exsists in the project. ' % name)

                # name = self._checkDuplicatedSpectrumGroupName(name)
                # self._createNewSpectrumGroup(name)

    ######################################################################################################################
    ######################             LOAD SPECTRA ON PROJECT              ##############################################
    ######################################################################################################################

    def _loadSpectraForSheet(self, dictLists):
        """
        If only the file name is given:
        - All paths are relative to the excel file! So the spectrum file of bruker top directory must be in the same directory
        of the excel file.
        If the full path is given, from the root to the spectrum file name, then it uses that.
        """
        _args = []
        # todo change hardcoded / for path
        if self._project is not None:
            for objDict in dictLists:
                for obj, dct in objDict.items():
                    for key, value in dct.items():
                        if key == SPECTRUM_PATH:
                            value = str(value)  # no point of being int/float
                            if os.path.exists(value):
                                # if isinstance(value, str):  # means it's a pathlike str### the full path is given:
                                self._addSpectrum(filePath=value, dct=dct, obj=obj)

                            else:  ### needs to find the path from the excel file:
                                self.directoryPath = str(pathlib.Path(self.excelPath).parent)
                                filePath = self.directoryPath + '/' + str(value)
                                if os.path.exists(filePath):  ### is a folder, e.g Bruker type. The project can handle.
                                    self._addSpectrum(filePath=filePath, dct=dct, obj=obj)


                                else:  ### is a spectrum file, The project needs to get the extension: e.g .hdf5
                                    newFilePath = os.path.dirname(filePath)
                                    try:
                                        filesWithExtension = [f for f in os.listdir(newFilePath) if isfile(join(newFilePath, f))]
                                        for fileWithExtension in filesWithExtension:
                                            if len(os.path.splitext(fileWithExtension)) > 0:
                                                if '/' in value:  # is a relative path from the excel plus file without extension
                                                    value = value.split('/')[-1]
                                                if os.path.splitext(fileWithExtension)[0] == value:
                                                    filePath = newFilePath + '/' + fileWithExtension
                                                    self._addSpectrum(filePath=filePath, dct=dct, obj=obj)
                                    except Exception as e:
                                        getLogger().warning(e)

    def _addSpectrum(self, filePath, dct, obj):
        """
        :param filePath: spectrum full file path
        :param dct:  dict with information for the spectrum. eg EXP type
        :obj: obj to link the spectrum to. E.g. Sample or Substance,
        """
        name = dct.get(SPECTRUM_NAME)
        if not name:
            name = obj.name
        if filePath.endswith('1r'):  # Not ideal implementation. But makes the loader much faster down the model by skipping internal loops.
            data = self._project._loadSpectrum(filePath, 'Bruker', str(name))
        else:
            data = self._project.loadData(filePath)
        if data is not None:
            if len(data) > 0:
                # sp = data[0]
                # sp.rename(name)
                self._linkSpectrumToObj(obj, sp, dct)
                if EXP_TYPE in dct:  # use exp name as it is much faster and safer to save than exp type.
                    data[0].experimentName = dct[EXP_TYPE]

                    # getLogger().debug3(msg=(e, data[0], dct[EXP_TYPE]))

    ######################################################################################################################
    ######################              ADD SPECTRUM TO RELATIVE OBJECTS              ####################################
    ######################################################################################################################

    def _linkSpectrumToObj(self, obj, spectrum, dct):
        from ccpn.core.Sample import Sample
        from ccpn.core.Substance import Substance
        from ccpn.core.Spectrum import SPECTRUMSERIES, SPECTRUMSERIESITEMS

        if isinstance(obj, Substance):
            obj.referenceSpectra += (spectrum,)

        if isinstance(obj, Sample):
            obj.spectra += (spectrum,)

        for key, value in dct.items():
            if key == SPECTRUM_GROUP_NAME:
                # spectrumGroup = self._project.getByPid('SG:' + str(value))
                tempSGspectra = self._tempSpectrumGroupsSpectra.get(str(value))
                if tempSGspectra is not None:
                    tempSGspectra.append(spectrum)
                # if spectrumGroup is not None: # this strategy is very slow. do not use here.
                #     spectrumGroup.spectra += (spectrum,)
                if SERIES in dct:  # direct insertion of series values for speed optimisation
                    spectrum.setParameter(SPECTRUMSERIES, SPECTRUMSERIESITEMS, {'SG:' + str(value): dct[SERIES]})

    def _fillSpectrumGroups(self):
        for sgName, spectra in self._tempSpectrumGroupsSpectra.items():
            spectrumGroup = self._project.getByPid('SG:' + str(sgName))
            if spectrumGroup is not None:
                spectrumGroup.spectra = spectra

    ######################################################################################################################
    ######################            DISPATCH ATTRIBUTES TO RELATIVE OBJECTS         ####################################
    ######################################################################################################################

    def _dispatchAttrsToObjs(self, dataDicts):
        from ccpn.core.Sample import Sample
        from ccpn.core.Substance import Substance

        for objDict in dataDicts:
            for obj, dct in objDict.items():
                if isinstance(obj, Substance):
                    self._setWrapperProperties(obj, SUBSTANCE_PROPERTIES, dct)

                if isinstance(obj, Sample):
                    self._setWrapperProperties(obj, SAMPLE_PROPERTIES, dct)
                    self._createSampleComponents(obj, dct)

    def _setWrapperProperties(self, wrapperObject, properties, dataframe):
        for attr in properties:
            if attr == synonyms:
                value = self._getDFValue(attr, dataframe)
                if value is not None:
                    setattr(wrapperObject, attr, (value,))
            else:
                try:
                    if getattr(wrapperObject, attr) is None or getattr(wrapperObject, attr) == 0:
                        setattr(wrapperObject, attr, self._getDFValue(attr, dataframe))

                except Exception:  #wrapper needs a int
                    value = self._getDFValue(attr, dataframe)
                    if value is not None:
                        setattr(wrapperObject, attr, int(value))

                except:
                    print('Value  not set for %s' % attr)
                    getLogger().debug3(msg=('Value  not set for %s' % attr))

    def _getDFValue(self, header, data):
        value = [[excelHeader, value] for excelHeader, value in data.items()
                 if excelHeader == str(header) and value != NOTGIVEN]
        if len(value) > 0:
            return value[0][1]

    ######################################################################################################################
    ######################                    ADD SAMPLE COMPONENTS                   ####################################
    ######################################################################################################################

    def _createSampleComponents(self, sample, data):
        from ccpn.core.SampleComponent import _newComponent

        sampleComponentsNames = [[header, sampleComponentName] for header, sampleComponentName in data.items() if
                                 header == SAMPLE_COMPONENTS and sampleComponentName != NOTGIVEN]
        if len(sample.sampleComponents) == 0:
            if len(sampleComponentsNames) > 0:
                for name in sampleComponentsNames[0][1].split(','):
                    if not self._project.getByPid('SC:' + str(name)):
                        sampleComponent = _newComponent(sample, name=(str(name)))
                        sampleComponent.role = 'Compound'
