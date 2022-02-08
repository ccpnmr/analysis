"""
This module contains dateFrames examples used in the Series Analysis tools
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
__dateModified__ = "$dateModified: 2022-02-08 13:10:32 +0000 (Tue, February 08, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-02-02 14:08:56 +0000 (Wed, February 02, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
import unittest
import contextlib
import pandas as pd
from collections import OrderedDict as od
from collections import defaultdict
from ccpn.core.DataTable import TableFrame
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
from ccpn.framework.lib.experimentAnalysis.SeriesTablesBC import SeriesFrameBC, RelaxationInputFrame



def getRelaxationFrameExample():
    SERIESSTEPS = [0, 5, 10, 15, 20, 25, 30]
    SERIESUNITS = 's'
    _assignmentValues = [['A', '1', 'ALA', 'H'], # row 1
                        ['A', '2', 'ALA', 'H']]  # row 2

    _seriesValues = [[1000, 550, 316, 180, 85, 56, 31], # row 1
                    [1005, 553, 317, 182, 86, 55, 30]]  # row 2

    df = RelaxationInputFrame()
    df.setSeriesSteps(SERIESSTEPS)
    df.setSeriesUnits(SERIESUNITS)
    df.setAssignmentValues(_assignmentValues)
    df.setSeriesValues(_seriesValues)
    df.build()
    return df

