"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2023-01-06 11:14:30 +0000 (Fri, January 06, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.lib.Undo import Undo
# from ccpnmodel.ccpncore.lib.Io import Api as apiIo
from ccpnmodel.ccpncore.testing.CoreTesting import CoreTesting


class PeakUndoTest(CoreTesting):
    # Path of project to load (None for new project)
    projectPath = 'CcpnCourse1b'

    def test_new_peak_undo(self):
        project = self.project
        nmrProject = project.currentNmrProject or project.findFirstNmrProject()
        experiment = nmrProject.findFirstExperiment(name='HSQC')
        dataSource = experiment.findFirstDataSource(name='HSQC-115')
        peakList = dataSource.newPeakList()

        project._undo = undo = Undo()
        # disable the undoBlocks as V3-application is not present
        undo.allowNoApplication = True

        undo.newWaypoint()
        peak = peakList.newPeak()
        undo.undo()
        assert len(peakList.peaks) == 0, 'len(peakList.peaks) = %d' % len(peakList.peaks)

    def test_new_peak_undo_redo(self):
        project = self.project
        nmrProject = project.currentNmrProject or project.findFirstNmrProject()
        experiment = nmrProject.findFirstExperiment(name='HSQC')
        dataSource = experiment.findFirstDataSource(name='HSQC-115')
        peakList = dataSource.newPeakList()

        project._undo = undo = Undo()
        # disable the undoBlocks as V3-application is not present
        undo.allowNoApplication = True

        undo.newWaypoint()
        peak = peakList.newPeak()
        undo.undo()
        undo.redo()
        assert len(peakList.peaks) == 1, 'len(peakList.peaks) = %d' % len(peakList.peaks)
