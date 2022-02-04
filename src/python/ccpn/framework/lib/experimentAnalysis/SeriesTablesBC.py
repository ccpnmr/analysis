"""
This module defines base classes for Series Analysis
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-02-04 09:19:36 +0000 (Fri, February 04, 2022) $"
__version__ = "$Revision: 3.0.4 $"
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
from ccpn.util.Path import aPath
from ccpn.util.OrderedSet import OrderedSet
from ccpn.core._implementation.DataFrameABC import DataFrameABC
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv

class SeriesFrameBC(DataFrameABC):
    """
    A TableData used for the Series ExperimentsAnalysis, such as ChemicalShiftMapping or Relaxation I/O.

    This BaseTable contains constant Columns, such as

    'chain_code'           # -> str   | Chain Code
    'residue_code'         # -> str   | Residue Sequence Code (e.g.: '1', '1B')
    'residue_type'         # -> str   | Residue Type (e.g.: 'ALA')
    'atom_name'            # -> str   | Atom name (e.g.: 'Hn')

    These variables are defined in SeriesAnalysisVariables.py.

    """
    _reservedColumns = [
                        sv._ROW_UID
                         ]

    _constantColumns = sv.CONSTANT_TABLE_COLUMNS
    _reservedColumns.extend(_constantColumns)


    def __init__(self, *args, **kwargs):
        columns = self._reservedColumns
        super().__init__(columns=columns, *args, **kwargs)


    def loadFromFile(self, filePath, *args, **kwargs):
        pass


class GenericXlsxSeriesFrame(SeriesFrameBC):
    """
    A Generic Series table used for the Series ExperimentsAnalysis, such as ChemicalShiftMapping or Relaxation I/O.
    That can be created by loading a correctly formatted XLSX file.
    """



    def loadFromFile(self, filePath, fileType='xlsx',  *args, **kwargs):
        """ Read an XLSX file and add to the existing Table contents.
        File must have the mandatory (constant) Columns definitions. see docs"""
        filePath = aPath(filePath)
        df = pd.read_excel(filePath)
        for existingColumn in self.columns:
            self.pop(existingColumn)

        # self.reindex(columns=df.columns)
        for i, col in enumerate(df.columns):
            print(col, i)
            self[col] = [i]
        #
        # colData = dict((columnName, row.values[0]) for columnName, row in df.iteritems())
        # # self.insert(**colData)
        # a = self.append(colData, ignore_index=True)
        # print(self.columns)
        # print(df.values, df.to_dict())
        # for ix, row in df.iterrows():
        #     print(row.values, ix)
        #     self.loc[ix] = row.values
        # self._insertRow(df.values[0])
        # for i, v in df.iterrows():
        # self.assign(A=['np.nan'])
        # #
        # print(self)
        # self = newDf





df = GenericXlsxSeriesFrame()
filePath = '/Users/luca/Projects/AnalysisV3/src/python/ccpn/framework/lib/experimentAnalysis/testing/simpleDecayExampleData.xlsx'
df.loadFromFile(filePath)


print(df)
