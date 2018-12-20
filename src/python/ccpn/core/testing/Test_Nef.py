#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:33 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Rasmus Fogh $"
__date__ = "$Date: 2017-07-04 15:21:05 +0000 (Tue, July 04, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
from ccpn.core.testing.WrapperTesting import WrapperTesting
from ccpn.core.lib import CcpnNefIo


class TestCommentedExample(WrapperTesting):
    # Path of project to load (None for new project
    projectPath = 'Commented_Example.nef'

    def test_commentedExample(self):
        outPath = os.path.dirname(self.project.path)[:-5] + '.out.nef'
        CcpnNefIo.saveNefProject(self.project, outPath, overwriteExisting=True)
        # TODO do diff to compare output with input


class TestCourse3e(WrapperTesting):
    # Path of project to load (None for new project
    projectPath = 'CcpnCourse3e'

    def test_Course3e(self):
        outPath = os.path.dirname(self.project.path)[:-5] + '.out.nef'
        CcpnNefIo.saveNefProject(self.project, outPath, overwriteExisting=True)
        application = self.project._appBase
        application.loadProject(outPath)
        nefOutput = CcpnNefIo.convert2NefString(application.project)
        # TODO do diff to compare nefOutput with input file


class TestCourse2c(WrapperTesting):
    # Path of project to load (None for new project
    projectPath = 'CcpnCourse2c'

    def test_Course2c(self):
        outPath = os.path.dirname(self.project.path)[:-5] + '.out.nef'
        with self.assertRaises(NotImplementedError):
            CcpnNefIo.saveNefProject(self.project, outPath, overwriteExisting=True)
        # application = self.project._appBase
        # application.loadProject(outPath)
        # nefOutput = CcpnNefIo.convert2NefString(application.project)
        # # TODO do diff to compare nefOutput with input file
