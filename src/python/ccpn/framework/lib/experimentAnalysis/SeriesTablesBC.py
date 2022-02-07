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
__dateModified__ = "$dateModified: 2022-02-07 19:53:31 +0000 (Mon, February 07, 2022) $"
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
import numpy
import pandas as pd
from collections import OrderedDict as od
from collections import defaultdict
from ccpn.util.Path import aPath
from ccpn.util.OrderedSet import OrderedSet
from ccpn.core._implementation.DataFrameABC import DataFrameABC
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
from ccpn.util.Logging import getLogger

class SeriesFrameBC(DataFrameABC):
    """
    A TableData used for the Series ExperimentsAnalysis, such as ChemicalShiftMapping or Relaxation I/O.
    Columns names are created using the _assignmentHeaders followed by the _valuesHeaders.

    :var SERIESUNITS: str,  E.g.: 's' (for seconds), 'g' (for grams) etc.
    :var SERIESSTEPS: list, E.g.: list of floats defining the various Series steps, (time, concentration, etc).

    ### Columns definitions
    :var _assignmentHeaders: list of str,
                            Assignment header Columns, common to all SeriesTables. They are
                            'chain_code'           # -> str   | Chain Code
                            'residue_code'         # -> str   | Residue Sequence Code (e.g.: '1', '1B')
                            'residue_type'         # -> str   | Residue Type (e.g.: 'ALA')
                            'atom_name'            # -> str   | Atom name (e.g.: 'Hn')
                            See SeriesAnalysisVariables.py.

    :var _valuesHeaders: list of str,
                        the Values Headers Columns are defined as default by combining the
                        SERIESUNITS and Each value of the SERIESSTEPS.
                        E.g., for a RelaxationSeries with a SERIESUNITS = 's'
                        and SERIESSTEPS of [0, 5, 10, 15, 20, 25, 30]
                        the _valuesHeaders will be ['s_0', 's_5', 's_10', 's_15', 's_20', 's_25', 's_30']

    A common input SerieFrame will have the columns:
    columns = ['_ROW_UID', 'chain_code', 'residue_code', 'residue_type', 'atom_name', 's_0', 's_5', 's_10', 's_15', 's_20', 's_25', 's_30']

    ### Data
    :var _assignmentValues: list of lists of floats, used to create the SeriesFrame rows
    :var _seriesValues: list of lists of floats, used to create the SeriesFrame rows


    """

    SERIESUNITS         = 'u'
    SERIESSTEPS         = []

    _valuesHeaders      = []
    _assignmentHeaders  = sv.CONSTANT_TABLE_COLUMNS # list of str, common assignment headers for all SeriesFrames

    _assignmentValues   = []
    _seriesValues       = []

    _reservedColumns    = [sv._ROW_UID] ## list of str,
    _reservedColumns.extend(_assignmentHeaders)

    def __init__(self,  *args, **kwargs):
        super().__init__( *args, **kwargs)

    @property
    def seriesValues(self):
        """
        The raw data of seriesValues used in ExperimentAnalysis.
        Return: list of lists. """
        return self._seriesValues

    @property
    def assignmentValues(self):
        """
        The assignment metadata associated with seriesValues used in ExperimentAnalyses. See _assignmentHeaders or
        sv.CONSTANT_TABLE_COLUMNS for header definitions.
        Together with seriesValues form the rows in the SeriesFrame.
        Return: list of lists. """
        return self._assignmentValues

    def setSeriesValues(self, seriesValues, *args):
        """
        Set the raw data of seriesValues used in ExperimentAnalyses.
        Use 'rebuild' after setting the seriesValues.
        """
        self._seriesValues = seriesValues

    def setAssignmentValues(self, assignmentValues, *args):
        """
        Set the assignment for seriesValues used in ExperimentAnalyses.
        Use 'rebuild' after setting the seriesValues.
        """
        self._assignmentValues = assignmentValues

    def setValuesHeaders(self, valuesHeaders):
        """
        Set the column definition for the valueHeaders.
        """
        self._valuesHeaders = valuesHeaders

    def rebuild(self):
        """
        Set the dataFrame from the _assignmentValues and seriesValues
        :return:
        """
        dataDict = self.buildFrameDictionary(self.assignmentValues, self.seriesValues)
        self.setDataFromDict(dataDict)
        return self

    def buildFromSpectrumGroup(self, spectrumGroup):
        pass

    def buildFrameDictionary(self, assignmentValues, seriesValues) -> dict:
        """
        Create a ordered Dict from a list of lists of assignmentValues and SeriesValues.
        Each set of Items of assignmentValues, seriesValues constitutes a row in the dataframe.
        Key-value dict is built using the definitions in  _assignmentColumnHeaders and _dataColumnsHeaders.
        E.g.:
            assignmentValues  =  [
                            ['A', '1', 'ALA', 'H'], # row 1
                            ['A', '2', 'ALA', 'H']  # row 2
                            ]

            seriesValues  =  [
                            [1000, 550, 316, 180, 85, 56, 31], # row 1
                            [1005, 553, 317, 182, 86, 55, 30],  # row 2
                            ]

        return: dict,  key:value (list)
                Example returned dict:
                {'_ROW_UID'     : ['0', '1'],
                 'chain_code'   : ['A', 'A'],
                 'residue_code' : ['1', '2'],
                 'residue_type' : ['ALA', 'ALA'],
                 'atom_name'    : ['H', 'H'],
                 'Time_1'       : [1000, 1005],
                 'Time_2'       : [550, 553],
                 ...})
         """

        data = defaultdict(list)
        if not len(assignmentValues) == len(seriesValues):
            getLogger().warn(f""" AssignmentValues and SeriesValues need to be of same length.""")
            return data
        if not self._valuesHeaders:
            self._setDefaultValueHeaders()

        for ix, (_assignmentValueItems, _seriesValueItems) in enumerate(zip(assignmentValues, seriesValues)):
            data[sv._ROW_UID].append(str(ix))
            if not len(self._assignmentHeaders) == len(_assignmentValueItems):
                getLogger().warn(f"""AssignmentValues and AssignmentHeaders Definitions need to be of same length.""")
                return data

            if not len(self._valuesHeaders) == len(_seriesValueItems):
                getLogger().warn(f"""SeriesValues and AeriesHeaders Definitions need to be of same length.""")
                return data

            for a, b in zip(self._assignmentHeaders, _assignmentValueItems):
                data[a].append(b)
            for c, d in zip(self._valuesHeaders, _seriesValueItems):
                data[c].append(d)
        return data

    def setDataFromDict(self, dataDict):
        self.clear()
        for header in dataDict:
            self[header] = dataDict[header]

    def _setDefaultValueHeaders(self, prefix=None):
        """

        Set a default name for each series column.
        E.g. for a Relaxation Series with a SERIESUNITS = 's' and SERIESSTEPS of [0, 5, 10, 15, 20, 25, 30]
        the columns will be ['s_0', 's_5', 's_10', 's_15', 's_20', 's_25', 's_30']
        :param prefix: str. Default SERIESUNITS + sv.SEP (underscore)
        :return: list of str
        """
        valueHeaders = []
        if not prefix:
            prefix = f'{self.SERIESUNITS}{sv.SEP}'
        if self.SERIESSTEPS:
            valueHeaders = [f'{prefix}{str(step)}' for step in self.SERIESSTEPS]
        elif not self.SERIESSTEPS:
            ## give a suffix from enumerated series values
            if len(self.seriesValues)>0:
                valueHeaders = [f'{prefix}{str(i)}' for i, v in enumerate(self.seriesValues[0])]
        else:
            ## cannot proceed. Needs some minimal information on how to name the Series Columns
            raise RuntimeError('Impossible to set DefaultValueHeaders. Set first the SERIESSTEPS')
        self.setValuesHeaders(valueHeaders)
        return valueHeaders


    def loadFromFile(self, filePath, *args, **kwargs):
        pass


class RelaxationFrame(SeriesFrameBC):

    SERIESUNITS = 's'

    def setSeriesValues(self, seriesValues, prefix=sv.TIME_):
        """
        Set the raw data of seriesValues used in ExperimentAnalyses.
        Use 'rebuild' after setting the seriesValues.
        """
        self._seriesValues = seriesValues
        # add placeholders as _assignmentValues if not available.
        if self._seriesValues and not self._assignmentValues:
            placeholders = ['']*len(self._seriesValues)
            self._assignmentValues = placeholders

    # def _setDefaultValueHeaders(self, prefix=sv.TIME_):
    #     """ Set the default prefix to sv.TIME_ """
    #     super()._setDefaultValueHeaders(prefix=prefix)





class GenericXlsxSeriesFrame(SeriesFrameBC):
    """
    A Generic Series table used for the Series ExperimentsAnalysis, such as ChemicalShiftMapping or Relaxation I/O.
    That can be created by loading a correctly formatted XLSX file.

    # TESTING
    """

    def loadFromFile(self, filePath, fileType='xlsx',  *args, **kwargs):
        """ Read an XLSX file and add to the existing Table contents.
        File must have the mandatory (constant) Columns definitions. see docs"""
        filePath = aPath(filePath)
        df = pd.read_excel(filePath)
        for existingColumn in self.columns:
            self.pop(existingColumn)

        for i, col in enumerate(df.columns):
            self[col] = [i]

