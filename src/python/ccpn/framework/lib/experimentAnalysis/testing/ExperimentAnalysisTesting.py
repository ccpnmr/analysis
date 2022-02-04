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

import os
import unittest
import contextlib
from ccpn.framework import Framework
from ccpn.util.Logging import getLogger
from ccpnmodel.ccpncore.testing.CoreTesting import TEST_PROJECTS_PATH
from ccpn.core.DataTable import TableFrame


class ExperimentAnalysisTestingBC(unittest.TestCase):
    """Baseclass for testing the ExperimentAnalysis ABCs"""


    @contextlib.contextmanager
    def initialSetup(self):

        self.tableFrame = TableFrame({'a': [1, 2, 3], 'b': [10, 20, 30]})

        try:
            yield
        except:
            self.tearDown()
            raise

    def setUp(self):
        with self.initialSetup():
            pass



