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
__dateModified__ = "$dateModified: 2022-02-02 19:07:11 +0000 (Wed, February 02, 2022) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-02-02 14:08:56 +0000 (Wed, February 02, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from unittest import expectedFailure, skip
from ccpn.framework.lib.experimentAnalysis.testing.ExperimentAnalysisTesting import ExperimentAnalysisTestingBC


class RelaxationAnalysisBC_Test(ExperimentAnalysisTestingBC):
    # Path of project to load (None for new project)
    projectPath = None

    #=========================================================================================
    # setUp       initialise a new project
    #=========================================================================================

    def setUp(self):
        """
        Test the RelaxationAnalysisBC class contains the right methods.
        """
        from ccpn.framework.lib.experimentAnalysis.RelaxationAnalysisBC import RelaxationAnalysisBC
        with self.initialSetup():
            self.seriesAnalysisABC = RelaxationAnalysisBC()

    #=========================================================================================
    #
    #=========================================================================================

    def test_RelaxationAnalysis(self):
        from ccpn.util.OrderedSet import OrderedSet
        message = "fittingModels class-variable is not of instance OrderedSet."
        self.assertIsInstance(self.seriesAnalysisABC.fittingModels, OrderedSet, message)
