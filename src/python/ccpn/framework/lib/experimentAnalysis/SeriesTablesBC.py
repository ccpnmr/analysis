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
__dateModified__ = "$dateModified: 2022-02-16 15:46:57 +0000 (Wed, February 16, 2022) $"
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

class SeriesFrameBC(TableFrame):
    """
    A TableData used for the Series ExperimentsAnalysis, such as ChemicalShiftMapping or Relaxation I/O.
    Columns names are created using the _assignmentHeaders followed by the _valuesHeaders.
    The table resembles an extended ChemicalShiftList table.
    This table is usually generated from a SpectrumGroup Series, but can be subclassed for building plugins etc.

    :var SERIESUNITS: str,  E.g.: 's' (for seconds), 'g' (for grams) etc.
    :var SERIESSTEPS: list, E.g.: list of floats defining the various Series steps, (time, concentration, etc).
                                    Must be of same length of _seriesValues.

    ### Columns definitions
    :var _assignmentHeaders: list of str,
                            Assignment header Columns, common to all SeriesTables. They are
                            'chain_code'           
                            'residue_code'        
                            'residue_type'        
                            'atom_name'       
                            See SeriesAnalysisVariables.py.

    :var _valuesHeaders: list of str,
                        the Values Headers Columns are defined as default by combining the
                        SERIESUNITS and Each value of the SERIESSTEPS.
                        E.g., for a RelaxationSeries with a SERIESUNITS = 's'
                        and SERIESSTEPS of [0, 5, 10, 15, 20, 25, 30]
                        the _valuesHeaders will be ['s_0', 's_5', 's_10', 's_15', 's_20', 's_25', 's_30']

    A common input SerieFrame will have the columns:
    columns = ['_ROW_UID', 'chain_code', 'residue_code', 'residue_type', 'atom_name',
               's_0', 's_5', 's_10', 's_15', 's_20', 's_25', 's_30']

    ### Data
    :var _assignmentValues: list of lists of floats, used to create the SeriesFrame rows.
                            Must be of same length of _assignmentHeaders.
    :var _seriesValues: list of lists of floats, used to create the SeriesFrame rows.
                        Must be of same length of _valuesHeaders and SERIESSTEPS.
    
    ### Example of as SeriesFrame table
    
     category      uid    ||            assignmentHeaders                         ||        valuesHeaders
     headers    |_ROW_UID || chain_code | residue_code | residue_type | atom_name || prefix_x | prefix_y | prefix_... |
                |=========||============|==============|==============|===========||==========|==========|============|
     types      |   str   ||   str      |    str       |   str        |    str    ||   float  |   float  |   float    |
                |---------||------------|--------------|--------------|-----------||----------|----------|------------|
     values     |   0     ||     A      |      1       |   ALA        |     H     ||    180   |     85   |     ...    |

    See examples in .../testing/ExampleSeriesTables.py

    """
    SERIESFRAMENAME     = ''
    SERIESFRAMETYPE     = ''
    SERIESUNITS         = 'u'
    SERIESSTEPS         = []

    _valuesHeaders      = []
    _assignmentHeaders  = sv.CONSTANT_TABLE_COLUMNS

    _assignmentValues   = []
    _seriesValues       = []

    _reservedColumns    = [sv._ROW_UID]
    _reservedColumns.extend(_assignmentHeaders)

    def __init__(self,  *args, **kwargs):
        super().__init__(*args, **kwargs)


    @property
    def seriesValues(self):
        """
        The raw data of seriesValues used in ExperimentAnalysis.
        Return: list of lists of floats. """
        return self._seriesValues

    @property
    def assignmentValues(self):
        """
        The assignment metadata associated with seriesValues used in ExperimentAnalyses. See _assignmentHeaders or
        sv.CONSTANT_TABLE_COLUMNS for header definitions.
        Together with seriesValues form the rows in the SeriesFrame.
        Return: list of lists. """
        return self._assignmentValues

    @property
    def valuesHeaders(self):
        """
        the list of column Headers for the series values.
        Can be used to filter the Table to get a new table with only the series values and index.
        e.g.:  df[df.valuesHeaders]
        :return: list of str
        """
        return self._valuesHeaders

    @property
    def assignmentHeaders(self):
        """
        the list of column Headers for the assignment values.
        Can be used to filter the Table to get a new table with only the series values and index.
        e.g.:  df[df.assignmentHeaders]
        :return: list of str
        """
        return self._assignmentHeaders

    def setSeriesValues(self, seriesValues, *args):
        """
        Set the raw data of seriesValues used in ExperimentAnalyses.
        Use 'rebuild' after setting the seriesValues.
        """
        self._seriesValues = seriesValues

    def setAssignmentValues(self, assignmentValues, *args):
        """
        Set the assignment for seriesValues used in ExperimentAnalyses.
        Use 'build' after setting the seriesValues.
        """
        self._assignmentValues = assignmentValues

    @valuesHeaders.setter
    def valuesHeaders(self, valuesHeaders:list):
        """
        Set the column definition for the valueHeaders.
        """
        self._valuesHeaders = valuesHeaders

    def setSeriesSteps(self, seriesSteps:list):
        self.SERIESSTEPS = seriesSteps

    def setSeriesUnits(self, seriesUnits:str):
        self.SERIESUNITS = seriesUnits

    def build(self):
        """
        Set the dataFrame from the _assignmentValues and seriesValues
        :return:
        """
        dataDict = self.buildFrameDictionary(self.assignmentValues, self.seriesValues)
        self.setDataFromDict(dataDict)
        return self

    def buildFromSpectrumGroup(self, spectrumGroup, thePeakProperty:str):
        """

        :param spectrumGroup: Obj SpectrumGroup
        :param thePeakProperty: any of ppmPosition, lineWidth, volume, height
        :return:
        """
        self.setSeriesSteps(spectrumGroup.series)
        self.setSeriesUnits(spectrumGroup.seriesUnits)
        _assignmentValues, _seriesValues = _getValuesFromSpectrumGroup(spectrumGroup, thePeakProperty=thePeakProperty)
        self.setAssignmentValues(_assignmentValues)
        self.setSeriesValues(_seriesValues)
        self.build()

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

        dataDict = defaultdict(list)
        if not len(assignmentValues) == len(seriesValues):
            getLogger().warn(f""" AssignmentValues and SeriesValues need to be of same length.""")
            return dataDict
        if not self._valuesHeaders:
            self._setDefaultValueHeaders()

        for ix, (_assignmentValueItems, _seriesValueItems) in enumerate(zip(assignmentValues, seriesValues)):
            dataDict[sv._ROW_UID].append(str(ix))
            if not len(self._assignmentHeaders) == len(_assignmentValueItems):
                raise ValueError(f"""AssignmentValues and AssignmentHeaders Definitions need to be of same length.""")

            if not len(self._valuesHeaders) == len(_seriesValueItems):
                raise ValueError(f"""SeriesValues and SeriesHeaders Definitions need to be of same length.""")

            for a, b in zip(self._assignmentHeaders, _assignmentValueItems):
                dataDict[a].append(b)
            for c, d in zip(self._valuesHeaders, _seriesValueItems):
                dataDict[c].append(d)
        return dataDict

    def setDataFromDict(self, dataDict):
        # self.clear()
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
        self.valuesHeaders = valueHeaders
        return valueHeaders

    def loadFromFile(self, filePath, *args, **kwargs):
        pass


########################################################################################################################
################################           Relaxation I/O  Series Tables                ################################
########################################################################################################################

class RelaxationInputFrame(SeriesFrameBC):
    SERIESUNITS = sv.SERIES_TIME_UNITS[0]
    SERIESFRAMETYPE = sv.RELAXATION_INPUT_FRAME


class RelaxationOutputFrame(SeriesFrameBC):
    SERIESFRAMETYPE = sv.RELAXATION_OUTPUT_FRAME

########################################################################################################################
################################   Chemical Shift Mapping  I/O Series Tables            ################################
########################################################################################################################

class CSMInputFrame(SeriesFrameBC):
    SERIESUNITS = sv.SERIES_CONCENTRATION_UNITS[0]
    SERIESFRAMETYPE = sv.CSM_INPUT_FRAME


class CSMOutputFrame(SeriesFrameBC):
    SERIESFRAMETYPE = sv.CSM_OUTPUT_FRAME
    SERIESUNITS = None
    SERIESSTEPS = None
    _assignmentHeaders = sv.CONSTANT_OUTPUT_TABLE_COLUMNS
    _reservedColumns = [sv.DELTA_DELTA]



########################################################################################################################
################################                Library  functions                      ################################
########################################################################################################################

def _getValuesFromSpectrumGroup(spectrumGroup, thePeakProperty, peakListIndex=-1):
    """
    Internal
    Get the assignmentValues and seriesValues from a spectrumGroup.
    Values are used to build the  SeriesTable
    :return assignmentValues and seriesValues, both are list of lists
    """
    _assignmentValues = []
    _seriesValues = []
    spectra = spectrumGroup.spectra
    nmrAtoms = _getAssignedNmrAtoms4Spectra(spectra, peakListIndex=peakListIndex)
    for nmrAtom in nmrAtoms:
        ## get the assignmnt Values
        nmrRes = nmrAtom.nmrResidue
        _assignmentValues.append([nmrRes.nmrChain.name, nmrRes.sequenceCode, nmrRes.residueType, nmrAtom.name])
        ## get the series Peak-property values
        spectraValuesDict = nmrAtom._getAssignedPeakValues(spectra, theProperty=thePeakProperty)
        _seriesValues4Atom = []
        for spectrum in spectra:
            values = spectraValuesDict.get(spectrum, [])
            if values: ## in series should be only 1 or None. If multiple take the mean.
                _seriesValues4Atom.append(values[0] if len(values) == 1 else np.mean([v for v in values if v]))
            else:
                _seriesValues4Atom.append(None)
        _seriesValues.append(_seriesValues4Atom)
    return _assignmentValues, _seriesValues

def _getAssignedNmrAtoms4Spectra(spectra, peakListIndex=-1):
    """Get a set of assigned nmrAtoms that appear in a list of spectra. Use last peakList only as default."""
    allPeaks = [pk for sp in spectra for pk in sp.peakLists[peakListIndex].peaks]
    nmrAtoms = set(flattenLists([peak.assignedNmrAtoms for peak in allPeaks]))
    return list(nmrAtoms)


INPUT_CSM_SERIESFRAMES_DICT = {
                          sv.CSM_INPUT_FRAME: CSMInputFrame
                          }
