"""
This module defines base classes for Series Analysis
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-08-15 16:47:20 +0100 (Mon, August 15, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-02-02 14:08:56 +0000 (Wed, February 02, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import math
import numbers
import typing
import numpy as np
import pandas as pd
from collections import OrderedDict as od
from collections import defaultdict
from ccpn.core.DataTable import TableFrame
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
from ccpn.util.Logging import getLogger
from ccpn.util.Common import flattenLists
from ccpn.core.Peak import Peak

class SeriesFrameBC(TableFrame):
    """
    A TableData used for the Series ExperimentsAnalysis, such as ChemicalShiftMapping or Relaxation I/O.
    Columns names are divided in following groups assignmentProperties, spectrumProperties, peakProperties.
    """
    SERIESFRAMENAME     = ''
    SERIESFRAMETYPE     = ''

    def getRowByUID(self, uid):
        self.set_index(sv._ROW_UID, inplace=True, drop=False)
        if uid in self.index:
            return self.loc[uid]

    def _buildColumnHeaders(self):
        pass

    def loadFromFile(self, filePath, *args, **kwargs):
        pass

    @staticmethod
    def _getAtomNamesFromGroupedByHeaders(groupedDf):
        """
        join the atom names from different rows in a list
        :param groupedDf: groupedBy object
        """
        nmrAtomNames = groupedDf[sv.AssignmentPropertiesHeaders].groupby(
            sv.GROUPBYAssignmentHeaders)[sv.NMRATOMNAME].unique().transform(
            lambda x: ','.join(x)).values
        return nmrAtomNames

    def _joinTwoColumnsAsStr(self, columnName1:str=None, columnName2:str=None, newColumName:str=None, separator='-'):
        """
        Create a new column by joining values from existing columns. Keep all, don't drop columns. In-place operation.
        :return: self with a new column (if successful)
        """

        self[newColumName] = self[columnName1].astype(str) + separator + self[columnName2].astype(str)
        return self

    def joinNmrResidueCodeType(self):
        """ Merge the nmrResidue SequenceCode and ResidueType columns in a new colum (NMRRESIDUECODETYPE)"""
        ## convert the sequenceCode to str. This because pandas Automatically tries to make floats.!!
        self[sv.NMRRESIDUECODE] = self[sv.NMRRESIDUECODE].astype(str).apply(lambda x: x.replace('.0', ''))
        self._joinTwoColumnsAsStr(sv.NMRRESIDUECODE, sv.NMRRESIDUETYPE, newColumName=sv.NMRRESIDUECODETYPE, separator='-')

class InputSeriesFrameBC(SeriesFrameBC):
    """
    A TableData used for the Series ExperimentsAnalysis, such as ChemicalShiftMapping or Relaxation I/O.
    Columns names are divided in following groups assignmentProperties, spectrumProperties, peakProperties.

    ## --------- Columns definitions --------- ##
        - _UID                  : str,   value mandatory. Unique string used to index the DataFrame.

        - spectrumProperties group:
            - dimension         : int,   value mandatory
            - isotopeCode       : str,   value mandatory
            - seriesStep        : float, value mandatory
            - seriesUnit        : str,   value mandatory

        - peakProperties group:
            - collectionId      : int,   value mandatory
            - height            : float, value mandatory
            - ppmPosition       : float, value mandatory
            - lineWidth         : float, value optional
            - volume            : float, value optional

        - assignmentProperties group:
            - nmrChainCode      : str,   value optional
            - nmrResidueCode    : str,   value optional
            - nmrResidueType    : str,   value optional
            - nmrAtomName       : str,   value optional

        - pids group: all optional.  If available, changes to core objects may dynamically update the Data
            - spectrumPid       : str,   value optional
            - peakPid           : str,   value optional
            - nmrAtomPid        : str,   value optional
            - peakCollectionPid : str,   value optional

    """

    SERIESFRAMENAME     = sv.SERIESANALYSISINPUTDATA
    SERIESFRAMETYPE     = sv.SERIESANALYSISINPUTDATA

    _spectrumPropertiesHeaders      = []
    _peakPropertiesHeaders          = []
    _assignmentPropertiesHeaders    = []
    _pidHeaders                     = []

    @property
    def assignmentHeaders(self):
        """
        the list of column Headers for the assignment values.
        Can be used to filter the Table to get a new table with only the values of interest and index.
        e.g.:  df[df.assignmentHeaders]
        :return: list of str
        """
        return self._assignmentPropertiesHeaders

    @property
    def peakPropertiesHeaders(self):
        """
        the list of column Headers for the peakProperties values.
        Can be used to filter the Table to get a new table with only the values of interest and index.
        :return: list of str
        """
        return self._peakPropertiesHeaders

    @property
    def spectrumPropertiesHeaders(self):
        """
        the list of column Headers for the spectrumProperties values.
        Can be used to filter the Table to get a new table with only the values of interest and index.
        :return: list of str
        """
        return self._spectrumPropertiesHeaders

    @property
    def pidHeaders(self):
        """
        the list of column Headers for the pid values.
        :return: list of str
        """
        return self._pidHeaders

    def _buildColumnHeaders(self):
        """
        Set the Column Headers and order of appearance in the dataframe.
        :return: None
        """
        self._spectrumPropertiesHeaders = sv.SpectrumPropertiesHeaders
        self._peakPropertiesHeaders = sv.PeakPropertiesHeaders
        self._assignmentPropertiesHeaders = sv.AssignmentPropertiesHeaders
        self._pidHeaders = sv.PidHeaders
        columns = self._spectrumPropertiesHeaders   + \
                  self._peakPropertiesHeaders       + \
                  self._assignmentPropertiesHeaders + \
                  self._pidHeaders
        self.loc[-1, columns] = None # None value, because you must give a value when creating columns after init.
        self.dropna(inplace=True)    # remove  None values that were created as a temporary spaceHolder

    def _getCollectionDict4SpectrumGroup(self, spectrumGroup):
        """ _Internal. build the collection dict, so we know if a peak is in a collection.
        Note, this routine exists because peak.collection is extremely slow and here we also filter-out peaks
        which are not  in the spectrumGroup of interest."""
        collectionDict = defaultdict(list)
        for col in spectrumGroup.project.collections:
            for item in col.items:
                if isinstance(item, Peak):
                    if item.spectrum in spectrumGroup.spectra:
                        collectionDict[item].append(col)
        return collectionDict

    def buildFromSpectrumGroup(self, spectrumGroup, peakListIndices=None):
        """
        :param spectrumGroup: A core object containg the spectra ans series information
        :param peakListIndices: list of int, same length of spectra. Define which peakList index to use.
                               If None, use -1 (last created) as default for all spectra
        :return: None
        """
        # build the frame
        if self.columns.empty:
            self._buildColumnHeaders()
        spectra = spectrumGroup.spectra
        if peakListIndices is None or len(peakListIndices) != len(spectra):
            peakListIndices = [-1] * len(spectra)
        collectionDict = self._getCollectionDict4SpectrumGroup(spectrumGroup)
        i = 1
        while True: ## This because we don't know how many rows we need
            for spectrum, peakListIndex in zip(spectra, peakListIndices):
                for pk in spectrum.peakLists[peakListIndex].peaks:
                    for dimension in spectrum.dimensions:
                        try:
                            ## set the unique UID
                            self.loc[i, sv._ROW_UID] = i
                            ## build the spectrum Property Columns
                            self.loc[i, sv.DIMENSION] = dimension
                            self.loc[i, sv.ISOTOPECODE] = spectrum.getByDimensions(sv.ISOTOPECODES, [dimension])[0]
                            self.loc[i, sv.SERIESSTEP] = spectrum.getSeriesItem(spectrumGroup)
                            self.loc[i, sv.SERIESUNIT] = spectrumGroup.seriesUnits
                            self.loc[i, sv.SPECTRUMPID] = spectrum.pid
                            ## build the peak Property Columns
                            collections = collectionDict.get(pk, [])
                            for collection in collections:
                                self.loc[i, sv.COLLECTIONID] = collection.uniqueId
                                self.loc[i, sv.COLLECTIONPID] = collection.pid
                            for peakProperty in [sv._HEIGHT, sv._VOLUME]:
                                self.loc[i, peakProperty] = getattr(pk, peakProperty, None)
                            self.loc[i, sv._PPMPOSITION] = pk.getByDimensions(sv._PPMPOSITIONS, [dimension])[0]
                            self.loc[i, sv._LINEWIDTH] = pk.getByDimensions(sv._LINEWIDTHS, [dimension])[0]
                            self.loc[i, sv.PEAKPID] = pk.pid
                            ## build the assignment Property Columns
                            assignedNmrAtoms = flattenLists(pk.getByDimensions(sv.ASSIGNEDNMRATOMS, [dimension]))
                            for nmrAtom in assignedNmrAtoms:
                                self.loc[i, sv.NMRCHAINNAME] = nmrAtom.nmrResidue.nmrChain.name
                                self.loc[i, sv.NMRRESIDUECODE] = nmrAtom.nmrResidue.sequenceCode
                                self.loc[i, sv.NMRRESIDUETYPE] = nmrAtom.nmrResidue.residueType
                                self.loc[i, sv.NMRATOMNAME] = nmrAtom.name
                                self.loc[i, sv.NMRATOMPID] = nmrAtom.pid
                            i += 1
                        except Exception as e:
                            getLogger().warn(f'Cannot add row {i} for peak {pk.pid}. Skipping with error: {e}')
            break



########################################################################################################################
################################           Relaxation I/O  Series Output Table                 #########################
########################################################################################################################

class RelaxationOutputFrame(SeriesFrameBC):
    SERIESFRAMETYPE = sv.RELAXATION_OUTPUT_FRAME

########################################################################################################################
################################   Chemical Shift Mapping  I/O Series Output Table      ################################
########################################################################################################################

class CSMOutputFrame(SeriesFrameBC):

    """
    A TableData used for the CSM Series Analysis,
    Mandatory Column names are:
        ## --------- Columns definitions --------- ##
        # Group with various identifiers etc
        - _UID              : int,
        - nmrChainName      : str,
        - nmrResidueCode    : str,
        - nmrResidueType    : str,
        - nmrAtomNames      : list,
        - collectionId      : int,
        - collectionPid     : str,
        - peakPid           : str,
        # Group with calculation/calculated values
        - seriesUnit        : str,
        - seriesStep        : float,
        - seriesStepValue   : float,
        - deltaDeltaMean    : float,
        - kd                : float,
        - kd_error          : float,
        - bMax              : float,
        - bMax_error        : float,
        # Group with statistical fitting results
        - R2               : float,
        - Chi-square       : float,
        - Red-Chi-square   : float,
        - Akaike           : float,
        - Bayesian         : float,
        - Method           : str, the minimiser method used for fitting. e.g.: 'leastsq'
        - Model            : str, the minimiser model used for fitting.  e.g.: '1BindingSite'
    """

    SERIESFRAMENAME = sv.CSM_OUTPUT_FRAME
    SERIESFRAMETYPE = sv.CSM_OUTPUT_FRAME

    def _buildColumnHeaders(self):
        """
        Set the Column Headers and order of appearance in the dataframe.
        :return: None
        """
        columns = [
                    sv._ROW_UID,
                    sv.COLLECTIONID,
                    sv.COLLECTIONPID,
                    sv.PEAKPID,
                    sv.NMRCHAINNAME,
                    sv.NMRRESIDUECODE,
                    sv.NMRRESIDUETYPE,
                    sv.NMRATOMNAMES,
                    sv.SERIESUNIT,
                    sv.SERIESSTEP,
                    sv.SERIESSTEPVALUE,
                    sv.DELTADELTAMEAN,
                    sv.KD,
                    sv.KD_ERR,
                    sv.BMAX,
                    sv.BMAX_ERR,
                  ]
        columns += sv.CONSTANT_STATS_OUTPUT_TABLE_COLUMNS
        self.loc[-1, columns] = None # None value, because you must give a value when creating columns after init.
        self.dropna(inplace=True)    # remove  None values that were created as a temporary spaceHolder

########################################################################################################################
##################################        Private Library  functions                 ###################################
########################################################################################################################


def _mergeRowsByHeaders(inputData, grouppingHeaders, dropColumnNames=[sv.NMRATOMNAME],
                        rebuildUID=True, pidShortClass='NR', keep="first", ):
    """
    Merge rows by common columns.
    grouppingHeaders:  sequence of columnNames to consider for identifying duplicate rows.

    """
    from ccpn.core.lib.Pid import createPid

    newIDs =[]
    if rebuildUID:
        for assignmentValues, grouppedDF in inputData.groupby(grouppingHeaders):        ## Group by grouppingHeaders
            newUid = grouppedDF[grouppingHeaders].values[0].astype('str')
            newIDs.append(createPid(pidShortClass, *newUid))                            ## Recreate the UID
    inputData.drop_duplicates(subset=grouppingHeaders, keep=keep, inplace=True)
    inputData.drop(columns=dropColumnNames, inplace=True)
    if rebuildUID and len(inputData.index) == len(newIDs):
        inputData[sv._ROW_UID] = newIDs
    return inputData

def _getOutputFrameFromInputFrame(inputFrame, outputFrameType=RelaxationOutputFrame):
    """
    :param inputFrame: a populated input Frame with columns definition and all other class properties
    :return: outputFrame
    """
    outputFrame = outputFrameType()
    ## clone the existing values from columns
    for column in inputFrame:
        outputFrame[column] = inputFrame[column].values
    ## the parameters fitting Columns are added on the fly as may differ by Model (e.g.: amplitude, decay etc)
    ## add the statistical fitting output Columns
    fittingColumns = sv.CONSTANT_STATS_OUTPUT_TABLE_COLUMNS
    for fittingColumn in fittingColumns:
        outputFrame[fittingColumn] = [None] * len(inputFrame)
    # #clone the other properties
    outputFrame.setSeriesUnits(inputFrame.SERIESUNITS)
    outputFrame.setSeriesSteps(inputFrame.SERIESSTEPS)
    outputFrame._assignmentHeaders = inputFrame.assignmentHeaders
    outputFrame._valuesHeaders = inputFrame.valuesHeaders
    return outputFrame


INPUT_SERIESFRAME_DICT = {
                    InputSeriesFrameBC.SERIESFRAMETYPE: InputSeriesFrameBC
                    }

OUTPUT_CSM_SERIESFRAMES_DICT = {
                              sv.CSM_OUTPUT_FRAME: CSMOutputFrame,
                              }

OUTPUT_RELAXATION_SERIESFRAMES_DICT = {
                              sv.RELAXATION_OUTPUT_FRAME: RelaxationOutputFrame
                              }



ALL_SERIES_DATA_TYPES = {
                        **INPUT_SERIESFRAME_DICT,
                        **OUTPUT_CSM_SERIESFRAMES_DICT,
                        **OUTPUT_RELAXATION_SERIESFRAMES_DICT
                         }
