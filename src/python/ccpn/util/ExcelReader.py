#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2025"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Morgan Hayward $"
__dateModified__ = "$dateModified: 2025-08-27 08:06:33 +0100 (Wed, August 27, 2025) $"
__version__ = "$Revision: 3.3.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
import re

import numpy as np
import pandas as pd
from ccpn.util.Logging import getLogger
from ccpn.util.Path import aPath, joinPath
from ccpn.util.Colour import name2Hex
from itertools import cycle
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar, notificationEchoBlocking, progressHandler, rebuildSidebar

from ccpn.core.Substance import _newSubstance
from ccpn.core.Sample import _newSample
from ccpn.core.SampleComponent import _newSampleComponent
from ccpn.core.SpectrumGroup import _newSpectrumGroup


################################       Excel Headers Warning      ######################################################
"""The excel headers for sample, sampleComponents, substances properties are named as the appear on the wrapper.
Changing these will fail to set the attribute"""

# SHEET NAMES
SUBSTANCE = 'Substance'
SAMPLE = 'Sample'
NOTGIVEN = 'NotGiven'
SERIES = 'Series'
SAMPLE_COMPONENT = 'SampleComponent'
SPECTRA = 'Spectra'
SPECTRUM_GROUP = 'SpectrumGroup'
# Regular expressions to identify sheets based on their names.
# This is case-insensitive as the sheets names are .lower() before matching.
SHEET_NAME_RE = {SUBSTANCE       : '^.*substance(?!.*type)',
                 SAMPLE          : '^.*sample(?!.*component|.*comp)',
                 SAMPLE_COMPONENT: '.*?sample.*?component',
                 SPECTRA         : '^.*spectr(um|a)(?!.*type|group)',
                 SPECTRUM_GROUP  : '^.*spectr(um|a).*?group'}

# """REFERENCES PAGE"""
SPECTRUM_GROUP_NAME = 'spectrumGroupName'
EXP_TYPE = 'experimentType'
SPECTRUM_PATH = 'spectrumPath'
SUBSTANCE_NAME = 'substanceName'
# added from beta6
SPECTRUM_NAME = 'spectrumName'
SPECTRUMGROUP = 'SpectrumGroup'

SPECTRUMHEXCOLOUR = 'spectrumHexColour'
SPECTRUMGROUPHEXCOLOUR = 'spectrumGroupHexColour'
POSITIVECONTOURCOLOUR = 'positiveContourColour'
NEGATIVECONTOURCOLOUR = 'negativeContourColour'
POSITIVECONTOURBASE = 'positiveContourBase'
NEGATIVECONTOURBASE = 'negativeContourBase'
INCLUDENEGATIVECONTOURS = 'includeNegativeContours'
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
SAMPLE_NUMBER = 'sampleNumber'
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

# Series
SERIES_VALUE = 'series'
SERIES_UNIT = 'seriesUnit'

# SAMPLE_PROPERTIES = [comment, pH, ionicStrength, amount, amountUnit, isHazardous, creationDate, batchIdentifier,
#                      plateIdentifier, rowNumber, columnNumber]

SAMPLE_PROPERTIES = {'name'              : str,
                     'pH'                : float,
                     'amount'            : float,
                     'amountUnits'       : str,
                     'ionicStrength'     : float,
                     'ionicStrengthUnits': str,
                     # 'creationDate'      : str,
                     'batchIdentifier'   : str,
                     'plateIdentifier'   : str,
                     'rowNumber'         : int,
                     'columnNumber'      : int,
                     'comment'           : str}

SAMPLE_PROPERTY_SYNONYMS = {'sampleName': 'name',
                            'amountUnit': 'amountUnits'}

INTER_SHEET_SAMPLE_PROPERTIES = {}

SUBSTANCE_PROPERTIES = {'name'                   : str,
                        'labelling'              : str,
                        'substanceType'          : str,
                        'userCode'               : str,
                        'smiles'                 : str,
                        'inChi'                  : str,
                        'casNumber'              : str,
                        'empiricalFormula'       : str,
                        'molecularMass'          : float,
                        'comment'                : str,
                        'synonyms'               : str,
                        'atomCount'              : int,
                        'bondCount'              : int,
                        'ringCount'              : int,
                        'hBondDonorCount'        : int,
                        'hBondAcceptorCount'     : int,
                        'polarSurfaceArea'       : float,
                        'logPartitionCoefficient': float}

SUBSTANCE_PROPERTY_SYNONYMS = {'substanceName': 'name'}

SAMPLE_COMPONENT_PROPERTIES = {'name'              : str,
                               'labelling'         : str,
                               'comment'           : str,
                               'role'              : str,
                               'concentrationUnit' : str,
                               'concentration'     : float,
                               'concentrationError': float,
                               'purity'            : float}

SAMPLE_COMPONENT_PROPERTY_SYNONYMS = {'substanceName': 'name'}

SPECTRUM_PROPERTIES = {'name'                   : str,
                       'path'                   : str,
                       'experimentType'         : str,
                       'comment'                : str,
                       'sampleName'             : str,
                       'sliceColour'            : str,
                       'positiveContourColour'  : str,
                       'negativeContourColour'  : str,
                       'positiveContourBase'    : float,
                       'negativeContourBase'    : float,
                       'includeNegativeContours': bool,
                       'spectrumGroupName'          : str,
                       'spectrumGroupNames'         : str}

SPECTRUM_PROPERTY_SYNONYMS = {'spectrumName': 'name',
                              'spectrumPath': 'path',
                              'spectrumGroup': 'spectrumGroupName',
                              'spectrumGroup': 'spectrumGroupNames'}

INTER_SHEET_SPECTRUM_PROPERITES = {'spectrumPath'     : 'path',
                                   'experimentType'   : 'experimentType',
                                   'spectrumName'     : 'name',
                                   'spectrumGroupName': 'spectrumGroupName'}

# SUBSTANCE_PROPERTIES = [comment, smiles, synonyms, molecularMass, empiricalFormula, atomCount,
#                         hBondAcceptorCount, hBondDonorCount, bondCount, ringCount, polarSurfaceArea,
#                         logPartitionCoefficient, userCode, ]
#
# SUBSTANCES_SHEET_COLUMNS = [SUBSTANCE_NAME,
#                                         SPECTRUM_PATH,
#                                         SPECTRUM_GROUP_NAME,
#                                         SPECTRUMHEXCOLOUR,
#                                         SPECTRUMGROUPHEXCOLOUR, EXP_TYPE] \
#                                        + SUBSTANCE_PROPERTIES
#
# SAMPLE_SHEET_COLUMNS = [SAMPLE_NAME,
#                         SPECTRUM_GROUP_NAME,
#                         SPECTRUM_PATH,
#                         SPECTRUM_NAME,
#                         SPECTRUMHEXCOLOUR,
#                         SPECTRUMGROUPHEXCOLOUR] \
#                        + SAMPLE_PROPERTIES
#
# SERIES_SHEET_COLUMNS = [
#     SPECTRUM_GROUP_NAME,
#     SPECTRUM_PATH,
#     SPECTRUM_NAME,
#     SERIES_VALUE,
#     SERIES_UNIT,
#     SPECTRUMHEXCOLOUR,
#     SPECTRUMGROUPHEXCOLOUR]

TOP_SG_COLOURS = ['red',
                  'blue',
                  'purple',
                  'green',
                  'gold',
                  'dimgrey',
                  'darksalmon',
                  'orangered'
                  'firebrick',
                  'tan',
                  'beige',
                  ]


def makeTemplate(path, fileName='lookupTemplate.xlsx', ):
    """
    :param path: path where to save the template
    :param fileName: name of template
    :return:  the file path where is saved
    """
    if path is None:
        raise ValueError("path cannot be None.")
    file = joinPath(path, fileName)
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
                        eg.a)  SpectrumDir > pdata > 1 > 1r     ====  multipleExp=False
                        eg.b)  SpectrumDir > 1 > pdata > 1 > 1r ====  multipleExp=True

    :param expDirName: if there are: str of folder name. e.g. '1','2'... '700'
                        eg)  SpectrumDir > |1|   > pdata > 1 > 1r
                                        > |2|   > pdata > 1 > 1r
                                        > |700| > pdata > 1 > 1r
                            Default: 1
    :param procDirName: dir name straight
                         eg)  SpectrumDir > 1  > pdata > |1| > 1r
                                                      > |2| > 1r
                        default: 1
    :return: list of filtered global path
    """
    filteredPaths = []
    for path in brukerFilePaths:
        path = aPath(path)
        if path.basename == fileType:
            dirBasename = path.filepath.basename  ## directory of  1r file has to be as defaultProcsNumber
            if dirBasename == procDirName:
                if multipleExp:  # search for other expeiments and take only the one of interest.
                    expP = path.filepath
                    # pdata = expP.parents[0]
                    if expP.basename == expDirName:
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
        self._totalProcessesCount = 0
        self.substanceLinks = {}
        self.sampleLinks = {}
        self.spectrumLinks = {}
        self._project = project
        self.excelPath = aPath(excelPath)
        self._project.excelPath = self.excelPath
        self.pandasFile = pd.ExcelFile(self.excelPath)
        self.sheets = self._getSheets(self.pandasFile)
        self.dataframes = self._getDataFrameFromSheets(self.sheets)
        self._project.dataFrames = self.dataframes
        self.extraDataFrames = {SUBSTANCE       : [],
                                SAMPLE          : [],
                                SAMPLE_COMPONENT: [],
                                SPECTRA         : [],
                                SPECTRUM_GROUP  : []}

    def load(self):
        """Load the actual data in the project
        """
        if SERIES in self.sheets:
            getLogger().info('Loading Series...')
            self._loadSeries()
            getLogger().info('Loading from Excel completed...')
            return
        self._addDefaultSpectrumColours = True
        self._tempSpectrumGroupsSpectra = {}  # needed to improve the loading speed
        for dataFrame in self.dataframes[SUBSTANCE]:
            self._createSubstances(dataFrame)
        for dataFrame in self.dataframes[SAMPLE]:
            self._createSamples(dataFrame)
        for dataFrame in self.dataframes[SAMPLE_COMPONENT]:
            self._createSampleComponents(dataFrame)
        text = f'Loading Spectra'
        spectraCount = sum([len(df) for df in self.dataframes[SPECTRA]])
        if len(self.dataframes[SPECTRA]) > 0:
            with rebuildSidebar():
                with progressHandler(title='Loading Data', maximum=spectraCount, text=text,
                                     hideCancelButton=True, ) as progress:
                    progressVal = 0
                    for index, dataFrame in enumerate(self.dataframes[SPECTRA]):
                        progress.setValue(int(progressVal))
                        self._loadSpectra(dataFrame, progress, progressVal)
                        progressVal += (len(dataFrame))

        # self.substancesDicts = self._createSubstancesDataFrames(self.dataframes)
        # self._project.excelSubstancesDicts = self.substancesDicts
        # self.samplesDicts = self._createSamplesDataDicts(self.dataframes)
        # self.spectrumGroups = self._createSpectrumGroups(self.dataframes)
        # self._totalProcessesCount = 5
        #
        # processCount = 1
        # #### Loading Substances metadata #######
        # getLogger().info('Loading Substances metadata...')
        # self._dispatchAttrsToObjs(self.substancesDicts, processCount=processCount, sheetName='Substances')
        # processCount += 1
        #
        # #### Loading Substances Spectra #######
        # getLogger().info('Loading Substances Spectra...')
        # self._loadSpectraForSheet(self.substancesDicts, processCount=processCount, sheetName='Substances')
        # processCount += 1
        #
        # #### Loading Samples metadata #######
        # getLogger().info('Loading Samples metadata...')
        # self._dispatchAttrsToObjs(self.samplesDicts, processCount=processCount, sheetName='Samples')
        # processCount += 1
        #
        # #### Loading Substances Spectra #######
        # getLogger().info('Loading Samples Spectra...')
        # self._loadSpectraForSheet(self.samplesDicts, processCount=processCount, sheetName='Samples')
        # processCount += 1
        #
        # #### Loading SpectrumGroups #######
        # getLogger().info('Loading SpectrumGroups...')
        # self._fillSpectrumGroups(processCount=processCount, sheetName='')
        #
        # getLogger().info('Loading from Excel completed...')

        # self._project.unblankNotification()

    #=========================================================================================
    # Parse Excel:
    #=========================================================================================

    def _getSheets(self, pandasfile):
        """return: list of the sheet names"""
        return pandasfile.sheet_names

    def _getDataFrameFromSheet(self, sheetName):
        'Creates the dataframe for the sheet. If Values are not set, fills None with NOTGIVEN (otherwise can give errors)'
        dataFrame = self.pandasFile.parse(sheetName)
        # dataFrame.fillna(NOTGIVEN, inplace=True)
        return dataFrame

    def _getDataFrameFromSheets(self, sheetNamesList):
        """Reads sheets containing the names SUBSTANCES, SAMPLES, SAMPLE_COMPONENT, SERIES and/or SPECTRA and creates a dataFrame for each.
        Returns a dictionary of each sheet type."""
        targetNames = [SUBSTANCE, SAMPLE, SAMPLE_COMPONENT, SERIES, SPECTRA]
        # dataFrames = {targetName: [self._getDataFrameFromSheet(sheetName) for sheetName in sheetNamesList if targetName in sheetName] for targetName in targetNames}
        dataFrames = {targetName: [] for targetName in targetNames}
        # for sheetName in sheetNamesList:
        #     for targetName in targetNames:
        #         if targetName in sheetName and not (targetName == SAMPLE and SAMPLE_COMPONENT in sheetName):
        #             dataFrames[targetName].append(self._getDataFrameFromSheet(sheetName))
        for sheetName in sheetNamesList:
            for targetName, regEx in SHEET_NAME_RE.items():
                if re.match(regEx, sheetName.lower()):
                    dataFrames[targetName].append(self._getDataFrameFromSheet(sheetName))
        return dataFrames

    #=========================================================================================
    # Create Series:
    #=========================================================================================

    def _loadSeries(self):
        # createSeries from SpectrumGroups
        for df in self.dataframes:
            for ix, seriesGroup in df.groupby(SPECTRUM_GROUP_NAME, sort=False):
                seriesName = seriesGroup[SPECTRUM_GROUP_NAME].unique()[0]
                spectra = []
                seriesValues = []
                seriesUnit = None
                for rix, row in seriesGroup.iterrows():
                    dct = row.to_dict()
                    spPath = row[SPECTRUM_PATH]
                    spectra.append(self._loadSpectumFromPath(spPath, dct, obj=None))
                    seriesValues.append(row.get(SERIES_VALUE))
                    seriesUnit = row.get(SERIES_UNIT)

                spGroup = self._createNewSpectrumGroup(seriesName)
                spGroup.spectra = spectra
                spGroup.series = tuple(seriesValues)
                spGroup.seriesUnits = seriesUnit

    #=========================================================================================
    # Create Substances:
    #=========================================================================================

    # def _createSubstancesDataFrames(self, dataframesList):
    #     """Creates substances in the project if not already present, For each substance link a dictionary of all its values
    #      from the dataframe row. """
    #     from ccpn.core.Substance import _newSubstance
    #
    #     substancesDataFrames = []
    #     for dataFrame in dataframesList:
    #         for dataFrameAsDict in dataFrame.to_dict(orient="index").values():
    #             if SUBSTANCE_NAME in dataFrame.columns:
    #                 for key, value in dataFrameAsDict.items():
    #                     if key == SUBSTANCE_NAME:
    #                         if self._project is not None:
    #                             if not self._project.getByPid('SU:' + str(value) + '.'):
    #                                 substance = _newSubstance(self._project, name=str(value))
    #                                 substancesDataFrames.append({substance: dataFrameAsDict})
    #                             else:
    #                                 getLogger().warning('Impossible to create substance %s. A substance with the same name already '
    #                                                     'exsists in the project. ' % value)
    #
    #     return substancesDataFrames

    def _createSubstances(self, substancesDf):
        """Create Substance object from the data in the Substance sheet."""
        spectraDf = self._checkForSpectrumData(substancesDf)
        substancesDf = self._tidyDataFrame(substancesDf, SUBSTANCE_PROPERTIES, SUBSTANCE_PROPERTY_SYNONYMS)
        spectraDf['substanceName'] = substancesDf['name']
        for index, line in substancesDf.iterrows():
            properties = {key: value(line[key]) for key, value in SUBSTANCE_PROPERTIES.items() if line.notna()[key]}
            if properties.get('synonyms') is not None:
                properties['synonyms'] = self._convertStringToList(properties['synonyms'])
            substance = self._createSubstance(properties)
            self.substanceLinks[properties['name']] = substance

    def _createSubstance(self, properties):
        """Checks if the substance is already in the project and creates it if not."""
        labelling = properties['labelling'] if 'labelling' in properties.keys() else None
        substancePid = f'SU:{properties["name"]}.{labelling}'
        substance = self._project.getByPid(substancePid)
        if not substance:
            substance = _newSubstance(self._project, **properties)
        return substance

    #=========================================================================================
    # Create Samples:
    #=========================================================================================

    # def _createSamplesDataDicts(self, dataframesList):
    #     """Creates samples in the project if not already present, For each sample link a dictionary of all its values
    #      from the dataframe row. """
    #     samplesDataFrames = []
    #     ## first creates samples without duplicates,
    #     samples = self._createSamples(dataframesList)
    #     if len(samples) > 0:
    #         ## Second creates dataframes to dispatch the properties,
    #         for dataFrame in dataframesList:
    #             for dataFrameAsDict in dataFrame.to_dict(orient="index").values():
    #                 if SAMPLE_NAME in dataFrame.columns:
    #                     for key, value in dataFrameAsDict.items():
    #                         if key == SAMPLE_NAME:
    #                             if self._project is not None:
    #                                 sample = self._project.getByPid('SA:' + str(value))
    #                                 if sample is not None:
    #                                     samplesDataFrames.append({sample: dataFrameAsDict})
    #
    #     return samplesDataFrames
    #
    # def _createSamples(self, dataframesList):
    #     from ccpn.util.Common import naturalSortList
    #     from ccpn.core.Sample import _newSample
    #
    #     samples = []
    #     for dataFrame in dataframesList:
    #         if SAMPLE_NAME in dataFrame.columns:
    #             saNames = list(set((dataFrame[SAMPLE_NAME])))
    #             saNames = naturalSortList(saNames, False)
    #             for name in saNames:
    #                 if not self._project.getByPid('SA:' + str(name)):
    #                     sample = _newSample(self._project, name=str(name))
    #                     samples.append(sample)
    #
    #                 else:
    #                     getLogger().warning('Impossible to create sample %s. A sample with the same name already '
    #                                         'exsists in the project. ' % name)
    #     return samples

    def _createSamples(self, samplesDf):
        """Handles a dataframe of Samples and passes each row to _createSample to make a Sample object."""
        spectraDf = self._checkForSpectrumData(samplesDf)
        self._checkForSampleComponents(samplesDf)
        samplesDf = self._tidyDataFrame(samplesDf, SAMPLE_PROPERTIES, SAMPLE_PROPERTY_SYNONYMS)
        spectraDf['sampleName'] = samplesDf['name']
        for index, line in samplesDf.iterrows():
            properties = {key: value(line[key]) for key, value in SAMPLE_PROPERTIES.items() if line.notna()[key]}
            if 'creationDate' in properties.keys():  # Handle creation date as an exception to the type enforcements. Pandas loads dates as Timestamps which is not accepted by Sample or convertable in the same was as other python objects.
                properties['creationDate'] = line['creationDate'].to_pydatetime()
            sample = self._createSample(properties)
            self.sampleLinks[properties['name']] = sample

    def _createSample(self, properties):
        """Checks if the sample exists in the project and creates it if not."""
        samplePid = f'SA:{properties["name"]}'
        sample = self._project.getByPid(samplePid)
        if not sample:
            sample = _newSample(self._project, **properties)
        return sample

    #=========================================================================================
    # Create Sample Components:
    #=========================================================================================

    def _createSampleComponents(self, sampleComponentsDf):
        """Creates SampleComponent objects from the data in the Sample_Component sheet."""
        sampleComponentsDf = self._tidyDataFrame(sampleComponentsDf, SAMPLE_COMPONENT_PROPERTIES, SAMPLE_COMPONENT_PROPERTY_SYNONYMS)
        for index, line in sampleComponentsDf.iterrows():
            if line.isna()['sampleName']:
                continue
            sample = self.sampleLinks[line['sampleName']]
            properties = {key: value(line[key]) for key, value in SAMPLE_COMPONENT_PROPERTIES.items() if line.notna()[key]}
            # substance = self.substanceLinks[line['substanceName']] if line.notna()['substanceName'] else None
            # properties['name'] = substance.name
            # sample = samplesDf.loc[samplesDf['name'] == line['sampleName'], 'sample'].iloc[0]
            sampleComponent = self._createSampleComponent(sample, **properties)
            # sampleComponentsDf.at[index, 'sampleComponent'] = sampleComponent
        # return sampleComponentsDf

    def _createSampleComponent(self, sample, **properties):
        sampleComponent = _newSampleComponent(sample, **properties)
        return sampleComponent

    #=========================================================================================
    # Load Spectra:
    #=========================================================================================

    # def _loadSpectra(self, samplesDf, spectraDf):
    #     return
    #     """Load the spectra from the data in the Spectra sheet, apply any modifications e.g. colour, and assign to a Sample."""
    #     spectraDf['spectrum'] = ''
    #     with progressHandler(title='Loading',
    #                          maximum=len(spectraDf),
    #                          text='Loading Spectra',
    #                          hideCancelButton=True) as progress:
    #         for index, line in spectraDf.iterrows():
    #             # Get some variables.
    #             spectrumDirectory = Path(line['spectrumDirectory'])
    #             spectrumFileName = str(line['spectrumFileName'])
    #             spectrumName = str(line['name']) if line.notna()['name'] else None
    #             spectrumGroupName = str(line['spectrumGroupName']) if line.notna()['spectrumGroupName'] else None
    #             sampleName = line['sampleName']
    #             experimentType = str(line['experimentType']) if line.notna()['experimentType'] else None
    #             # Load the spectrum.
    #             fullPath = spectrumDirectory.joinpath(spectrumFileName)
    #             spectrum = application.loadData(str(fullPath))[0]
    #             # Make any modifications to the spectrum.
    #             if spectrumName is not None:
    #                 if spectrumName != spectrum.name:
    #                     spectrum.rename(spectrumName)
    #             else:
    #                 spectraDf.at[index, 'name'] = spectrumFileName
    #             if experimentType is not None:
    #                 spectrum.experimentType = experimentType
    #             if isinstance(line['sliceColour'], str):
    #                 spectrum.sliceColour = line['sliceColour']
    #             # Assign the spectra to their SpectrumGroups.
    #             if spectrumGroupName in [spectrumGroup.name for spectrumGroup in project.spectrumGroups]:
    #                 spectrumGroup = project.getByPid(f'SG:{spectrumGroupName}')
    #                 spectrumGroup.addSpectrum(spectrum)
    #             elif spectrumGroupName is not None:
    #                 project.newSpectrumGroup(name=spectrumGroupName, spectra=[spectrum])
    #             # Assign the spectrum to its Sample.
    #             if sampleName in samplesDf['name'].values:
    #                 sample = samplesDf.loc[samplesDf['name'] == sampleName, 'sample'].iloc[0]
    #                 spectrum.sample = sample
    #             # Add the sample object to the record.
    #             spectraDf.at[index, 'spectrum'] = spectrum
    #             progress.setValue(index)
    #     return spectraDf

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

    ######################################################################################################################
    ######################             LOAD SPECTRA ON PROJECT              ##############################################
    ######################################################################################################################

    def _loadSpectumFromPath(self, path, dct, obj=None):

        newSpectrum = None
        excelSpectrumPath = aPath(str(path))

        if excelSpectrumPath.exists():
            ### We have the absolute (full path)
            newSpectrum = self._addSpectrum(filePath=excelSpectrumPath, dct=dct, obj=obj)
        else:
            ### We are in a relative path scenario
            self.directoryPath = self.excelPath.filepath
            globalFilePath = aPath(joinPath(self.directoryPath, excelSpectrumPath))
            if globalFilePath.exists():
                ### it is a folder, e.g Bruker type. We can handle it already.
                newSpectrum = self._addSpectrum(filePath=globalFilePath, dct=dct, obj=obj)
            else:
                ### it is a single spectrum file name or relative path for a single file,
                ### e.g.: "mySpectrum" or "mySpectrum.hdf5" or "myDir/mySpectrum.hdf5"
                globalDirFilePath = globalFilePath.filepath
                globalfilePaths = globalDirFilePath.listDirFiles()
                for _globalfilePath in globalfilePaths:
                    if _globalfilePath.basename == excelSpectrumPath.basename:
                        newSpectrum = self._addSpectrum(filePath=_globalfilePath, dct=dct, obj=obj)
        return newSpectrum

    def _loadSpectra(self, spectraDf, progress, progressVal):
        """
        Handles a dataframe of spectra details to load the spectra into the project.
        """
        spectraDf = self._tidyDataFrame(spectraDf, SPECTRUM_PROPERTIES, SPECTRUM_PROPERTY_SYNONYMS)
        for index, line in spectraDf.iterrows():
            properties = {key: value(line[key]) for key, value in SPECTRUM_PROPERTIES.items() if line.notna()[key]}
            if not properties.get('path') and line.get('spectrumDirectory') is not None and line.get('spectrumFileName') is not None:
                properties['path'] = str(line['spectrumDirectory']) + '/' + str(line['spectrumFileName'])
            spectrumPath = self._buildGlobalPath(properties['path'])
            if not spectrumPath:
                continue
            spectrum = self._loadSpectrum(spectrumPath, properties)
            # Assign a sample to the spectrum if appropriate.
            if 'sampleName' in line.keys() and line.get('sampleName') in self.sampleLinks.keys():
                spectrum.sample = self.sampleLinks[line.get('sampleName')]
            # Assign reference substances if appropriate:
            if 'substanceName' in line.keys() and line.get('substanceName') in self.substanceLinks.keys():
                spectrum.referenceSubstances += (self.substanceLinks[line.get('substanceName')],)
            # Assign to spectrum groups if appropriate.
            spectrumGroups = []
            if 'spectrumGroups' in line.keys():
                spectrumGroupNames = self._convertStringToList(line['spectrumGroups'])
                spectrumGroups = [_newSpectrumGroup(self._project, str(spectrumGroupName)) if not self._project.getByPid('SG:' + str(spectrumGroupName)) else self._project.getByPid('SG:' + str(spectrumGroupName)) for spectrumGroupName in spectrumGroupNames]
            elif 'spectrumGroupName' in line.keys():
                spectrumGroupName = str(line['spectrumGroupName'])
                spectrumGroups = [_newSpectrumGroup(self._project, spectrumGroupName)] if not self._project.getByPid('SG:' + spectrumGroupName) else [self._project.getByPid('SG:' + spectrumGroupName)]
            self._assignSpectrumToSpectrumGroups(spectrum, spectrumGroups)
            progressVal += 1
            progress.setValue(int(progressVal))

    def _buildGlobalPath(self, pathProperty):
        excelSpectrumPath = aPath(pathProperty)
        if excelSpectrumPath.exists():
            ### We have the absolute (full path)
            return excelSpectrumPath
        else:
            ### We are in a relative path scenario
            self.directoryPath = self.excelPath.filepath
            globalFilePath = aPath(joinPath(self.directoryPath, excelSpectrumPath))
            if globalFilePath.exists():
                ### it is a folder, e.g Bruker type. We can handle it already.
                return globalFilePath
            else:
                ### it is a single spectrum file name or relative path for a single file,
                ### e.g.: "mySpectrum" or "mySpectrum.hdf5" or "myDir/mySpectrum.hdf5"
                globalDirFilePath = globalFilePath.filepath
                globalfilePaths = globalDirFilePath.listDirFiles()
                for _globalfilePath in globalfilePaths:
                    if _globalfilePath.basename == excelSpectrumPath.basename:
                        return _globalfilePath
        return None

    def _loadSpectrum(self, spectrumPath, properties):
        """
        Method for loading the spectra in the manner described by the Excel file.
        Unlike the other objects, we do not build these from scratch and so cannot rely on method arguments.
        Instead, the spectrum is loaded and modified as specified.
        """
        spectrum = self._project.application.loadData(spectrumPath)[0]
        # Handle spectrum naming.
        spectrumName = properties.get('name')
        if spectrumName is not None:
            if spectrumName != spectrum.name:
                spectrum.rename(spectrumName)
        # Handle experiment type.
        experimentType = properties.get('experimentType')
        if experimentType is not None:
            spectrum.experimentType = experimentType  # use exp name as it is much faster and safer to save than exp type.
        # Handle spectrum colouring and contours.
        spectrum.sliceColour = properties.get(SPECTRUMHEXCOLOUR, spectrum.sliceColour)
        spectrum.positiveContourColour = properties.get(POSITIVECONTOURCOLOUR, spectrum.positiveContourColour)
        spectrum.negativeContourColour = properties.get(NEGATIVECONTOURCOLOUR, spectrum.negativeContourColour)
        spectrum.positiveContourBase = properties.get(POSITIVECONTOURBASE, spectrum.positiveContourBase)
        spectrum.negativeContourBase = properties.get(NEGATIVECONTOURBASE, spectrum.negativeContourBase)
        incNeg = properties.get(INCLUDENEGATIVECONTOURS)
        includeNegativeContours = False if incNeg in ['no', 'N', 'No', 'n', None, NOTGIVEN] else True
        spectrum.includeNegativeContours = includeNegativeContours
        return spectrum

    def _assignSpectrumToSpectrumGroups(self, spectrum, spectrumGroups):
        for spectrumGroup in spectrumGroups:
            spectrumGroup.addSpectrum(spectrum)

    def _addSpectrum(self, filePath, dct, obj):
        """
        :param filePath: spectrum full file path
        :param dct:  dict with information for the spectrum. eg EXP type
        :obj: obj to link the spectrum to. E.g. Sample or Substance,
        """
        name = dct.get(SPECTRUM_NAME)
        if not name and obj is not None:
            name = obj.name

        data = self._project.application.loadData(filePath)
        if data is not None and len(data) > 0:
            sp = data[0]
            if not sp.name == name:
                sp.rename(name)

            if obj is not None:
                self._linkSpectrumToObj(obj, sp, dct)
            if EXP_TYPE in dct:  # use exp name as it is much faster and safer to save than exp type.
                sp.experimentName = dct[EXP_TYPE]
                # getLogger().debug3(msg=(e, data[0], dct[EXP_TYPE]))

            sp.sliceColour = dct.get(SPECTRUMHEXCOLOUR, sp.sliceColour)
            sp.positiveContourColour = dct.get(POSITIVECONTOURCOLOUR, sp.positiveContourColour)
            sp.negativeContourColour = dct.get(NEGATIVECONTOURCOLOUR, sp.negativeContourColour)
            sp.positiveContourBase = dct.get(POSITIVECONTOURBASE, sp.positiveContourBase)
            sp.negativeContourBase = dct.get(NEGATIVECONTOURBASE, sp.negativeContourBase)
            incNeg = dct.get(INCLUDENEGATIVECONTOURS)
            includeNegativeContours = False if incNeg in ['no', 'N', 'No', 'n', None, NOTGIVEN] else True
            sp.includeNegativeContours = includeNegativeContours
            self._addDefaultSpectrumColours = False
            return sp

    ######################################################################################################################
    ######################              ADD SPECTRUM TO RELATIVE OBJECTS              ####################################
    ######################################################################################################################

    def _linkSpectrumToObj(self, obj, spectrum, dct):
        from ccpn.core.Sample import Sample
        from ccpn.core.Substance import Substance

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
                if SERIES_VALUE in dct:  # direct insertion of series values for speed optimisation
                    spectrum._setInternalParameter(spectrum._SERIESITEMS, {'SG:' + str(value): dct[SERIES_VALUE]})

    def _fillSpectrumGroups(self, processCount, sheetName=None):

        colourNames = cycle(TOP_SG_COLOURS)
        loopLenght = len(self._tempSpectrumGroupsSpectra.items())
        process = f'Performing actions {str(processCount)}/{str(self._totalProcessesCount)}:'
        text = f'Loading SpectrumGroups'
        text = f"""{process}\n{text}"""
        with progressHandler(title='Loading Data', maximum=loopLenght, text=text,
                             hideCancelButton=True, ) as progress:

            for i, (sgName, spectra) in enumerate(self._tempSpectrumGroupsSpectra.items()):
                progress.setValue(i)
                spectrumGroup = self._project.getByPid('SG:' + str(sgName))
                if spectrumGroup is not None:
                    spectrumGroup.spectra = spectra
                # give some default colours
                if self._addDefaultSpectrumColours:
                    hexColour = name2Hex(next(colourNames))
                    spectrumGroup.sliceColour = hexColour
                    for sp in spectra:
                        sp.sliceColour = hexColour

    ######################################################################################################################
    ######################            DISPATCH ATTRIBUTES TO RELATIVE OBJECTS         ####################################
    ######################################################################################################################

    def _dispatchAttrsToObjs(self, dataDicts, processCount, sheetName):
        from ccpn.core.Sample import Sample
        from ccpn.core.Substance import Substance

        loopLenght = len(dataDicts)
        process = f'Performing actions {str(processCount)}/{str(self._totalProcessesCount)}:'
        text = f'Loading Spectra for {sheetName}'
        text = f"""{process}\n{text}"""
        with progressHandler(title='Loading Data', maximum=loopLenght, text=text,
                             hideCancelButton=True, ) as progress:

            for i, objDict in enumerate(dataDicts):
                progress.setValue(i)
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
                    currentAttrValue = getattr(wrapperObject, attr)
                    newDataValue = self._getDFValue(attr, dataframe)
                    if currentAttrValue in [None, 0]:
                        setattr(wrapperObject, attr, newDataValue)
                    else:
                        if attr == comment:
                            setattr(wrapperObject, attr, newDataValue)

                except Exception:  #wrapper needs a int
                    value = self._getDFValue(attr, dataframe)
                    if value is not None:
                        setattr(wrapperObject, attr, int(value))
                except:
                    getLogger().debug3(msg=('Value  not set for %s' % attr))

    def _getDFValue(self, header, data):
        value = [[excelHeader, value] for excelHeader, value in data.items()
                 if excelHeader == str(header) and value != NOTGIVEN]
        if len(value) > 0:
            return value[0][1]

    ######################################################################################################################
    ######################                    ADD SAMPLE COMPONENTS                   ####################################
    ######################################################################################################################

    # def _createSampleComponents(self, sample, data):
    #     from ccpn.core.SampleComponent import _newComponent
    #
    #     sampleComponentsNames = [[header, sampleComponentName] for header, sampleComponentName in data.items() if
    #                              header == SAMPLE_COMPONENTS and sampleComponentName != NOTGIVEN]
    #     if len(sample.sampleComponents) == 0:
    #         if len(sampleComponentsNames) > 0:
    #             # check if is , or ; separated
    #             splitter = ','
    #             if ';' in sampleComponentsNames[0][1]:
    #                 splitter = ';'
    #             for name in sampleComponentsNames[0][1].split(splitter):
    #                 if not self._project.getByPid('SC:' + str(name)):
    #                     sampleComponent = _newComponent(sample, name=(str(name)))
    #                     sampleComponent.role = 'Compound'

    def _tidyDataFrame(self, dataFrame, properties, propertySynonyms):
        """
        Tidies up a dataframe so that the contents can be converted into the appropriate objects:
        Replaces the synonyms into the object property names.
        Adds columns of any missing properties.
        Removes duplicated columns.
        """
        dataFrame = dataFrame.rename(columns=propertySynonyms)
        dataFrame = pd.concat([dataFrame, pd.DataFrame(index=dataFrame.index, columns=properties.keys())], axis=1)
        dataFrame = dataFrame.loc[:, ~dataFrame.columns.duplicated()]
        return dataFrame

    def _checkForSpectrumData(self, dataFrame):
        columns = [column for column in dataFrame.columns if column in INTER_SHEET_SPECTRUM_PROPERITES.keys()]
        spectraDf = pd.DataFrame(data=dataFrame[columns], columns=columns)
        if not spectraDf.empty:
            self._project.spectraDf = spectraDf
            self.dataframes[SPECTRA].append(spectraDf)
        return spectraDf

    def _checkForSampleComponents(self, dataFrame):
        if 'sampleComponents' in dataFrame.columns:
            for index, row in dataFrame.iterrows():
                sampleName = row['sampleName']
                substanceNames = self._convertStringToList(str(row['sampleComponents']))
                data = {'sampleName': [sampleName] * len(substanceNames), 'substanceName': substanceNames}
                sampleComponentDf = pd.DataFrame(data)
                self.dataframes[SAMPLE_COMPONENT].append(sampleComponentDf)

    def _convertStringToList(self, listString):
        splitter = ','
        if ';' in listString:
            splitter = ';'
        stringAsList = listString.split(splitter)
        return stringAsList

